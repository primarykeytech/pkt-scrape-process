"""Optional local Dagster OSS assets for the offline replay-to-analytics flow."""

import json
from dataclasses import dataclass
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    AssetSelection,
    ConfigurableResource,
    DefaultScheduleStatus,
    Definitions,
    MetadataValue,
    ScheduleDefinition,
    asset,
    define_asset_job,
)
from filelock import FileLock, Timeout

from .demo import SYNTHETIC_HTML
from .incremental import current_snapshot
from .quality import QualityPolicy
from .raw import capture_batch, replay_batch
from .sql_analytics import analyze_snapshot


@dataclass(frozen=True)
class PublishedSnapshot:
    """The exact generation produced by one replay, retained for downstream lineage."""

    batch: Path
    snapshot: Path


class LocalPipelineConfig(ConfigurableResource):
    """Configuration for the deliberately offline local asset graph."""

    artifacts_root: str = "artifacts/dagster"
    source_id: str = "dagster-offline-fixture"
    source_url: str = "synthetic://dagster-offline"
    html: str = SYNTHETIC_HTML
    rejection_threshold: int = 0

    @property
    def root(self) -> Path:
        return Path(self.artifacts_root)

    @property
    def raw_root(self) -> Path:
        return self.root / "raw"

    @property
    def publication_root(self) -> Path:
        return self.root / "published"


@asset(group_name="offline_replay")
def saved_raw_batch(context: AssetExecutionContext, local_pipeline: LocalPipelineConfig) -> Path:
    """Capture only built-in synthetic HTML; this asset never performs network I/O."""
    batch = capture_batch(
        local_pipeline.raw_root,
        local_pipeline.html,
        source_url=local_pipeline.source_url,
        source_id=local_pipeline.source_id,
    )
    context.log.info("Saved offline raw batch %s", batch.name)
    context.add_output_metadata(
        {"batch": MetadataValue.path(str(batch)), "source_id": local_pipeline.source_id}
    )
    return batch


@asset(group_name="offline_replay")
def quality_gated_publication(
    context: AssetExecutionContext,
    local_pipeline: LocalPipelineConfig,
    saved_raw_batch: Path,
) -> PublishedSnapshot:
    """Replay one batch under a host-local single-writer lock and retain its generation path."""
    lock = FileLock(str(local_pipeline.root / ".dagster-publication.lock"))
    try:
        with lock.acquire(timeout=0):
            result = replay_batch(
                saved_raw_batch,
                local_pipeline.publication_root,
                policy=QualityPolicy(local_pipeline.rejection_threshold),
            )
            snapshot = current_snapshot(local_pipeline.publication_root)
            if snapshot is None:
                raise RuntimeError("quality-gated replay did not publish a snapshot")
            state = json.loads((snapshot / "state.json").read_text(encoding="utf-8"))
            if state.get("provenance", {}).get("batch_id") != saved_raw_batch.name:
                raise RuntimeError(
                    "published snapshot lineage does not match the replayed raw batch"
                )
    except Timeout as error:
        raise RuntimeError(
            "another Dagster replay is already publishing this artifact root"
        ) from error

    context.log.info(
        "Published generation %s from raw batch %s", snapshot.name, saved_raw_batch.name
    )
    context.add_output_metadata(
        {
            "batch": MetadataValue.path(str(saved_raw_batch)),
            "snapshot": MetadataValue.path(str(snapshot)),
            "records": result.records,
            "application_writes": result.application_writes,
        }
    )
    return PublishedSnapshot(batch=saved_raw_batch, snapshot=snapshot)


@asset(group_name="offline_replay")
def accepted_parquet(
    context: AssetExecutionContext, quality_gated_publication: PublishedSnapshot
) -> Path:
    """Expose only the accepted Parquet output from the generation just published."""
    parquet = quality_gated_publication.snapshot / "experiences.parquet"
    if not parquet.is_file():
        raise RuntimeError("quality-gated publication is missing its Parquet export")
    context.add_output_metadata(
        {
            "parquet": MetadataValue.path(str(parquet)),
            "snapshot": MetadataValue.path(str(quality_gated_publication.snapshot)),
        }
    )
    return parquet


@asset(group_name="offline_replay")
def duckdb_analytics_report(
    context: AssetExecutionContext,
    quality_gated_publication: PublishedSnapshot,
    accepted_parquet: Path,
) -> dict:
    """Run bounded DuckDB aggregates against the exact upstream published generation."""
    expected_parquet = quality_gated_publication.snapshot / "experiences.parquet"
    if accepted_parquet != expected_parquet:
        raise RuntimeError("Parquet lineage does not match the quality-gated publication")
    report = analyze_snapshot(quality_gated_publication.snapshot)
    if report.snapshot != quality_gated_publication.snapshot:
        raise RuntimeError("DuckDB analytics resolved a different published generation")
    result = report.to_dict()
    context.add_output_metadata(
        {
            "snapshot": MetadataValue.path(str(report.snapshot)),
            "records": report.summary["records"],
            "quality": MetadataValue.json(report.quality),
        }
    )
    return result


offline_replay_and_analytics_job = define_asset_job(
    "offline_replay_and_analytics", selection=AssetSelection.all()
)

daily_offline_demo = ScheduleDefinition(
    name="daily_offline_demo",
    job=offline_replay_and_analytics_job,
    cron_schedule="0 9 * * *",
    default_status=DefaultScheduleStatus.STOPPED,
    description="Optional local synthetic replay; intentionally stopped by default.",
)

defs = Definitions(
    assets=[saved_raw_batch, quality_gated_publication, accepted_parquet, duckdb_analytics_report],
    resources={"local_pipeline": LocalPipelineConfig()},
    jobs=[offline_replay_and_analytics_job],
    schedules=[daily_offline_demo],
)
