import subprocess
import sys

from dagster import DefaultScheduleStatus, materialize

from pktscrape.dagster_defs import (
    LocalPipelineConfig,
    accepted_parquet,
    daily_offline_demo,
    defs,
    duckdb_analytics_report,
    quality_gated_publication,
    saved_raw_batch,
)


ASSETS = [saved_raw_batch, quality_gated_publication, accepted_parquet, duckdb_analytics_report]


def _materialize(root, **config):
    return materialize(
        ASSETS,
        resources={"local_pipeline": LocalPipelineConfig(artifacts_root=str(root), **config)},
        raise_on_error=False,
    )


def test_definitions_load_and_schedule_is_stopped_by_default():
    asset_keys = {key.to_user_string() for key in defs.resolve_asset_graph().get_all_asset_keys()}
    assert asset_keys == {
        "saved_raw_batch",
        "quality_gated_publication",
        "accepted_parquet",
        "duckdb_analytics_report",
    }
    assert daily_offline_demo.default_status is DefaultScheduleStatus.STOPPED


def test_materializes_saved_raw_replay_parquet_and_duckdb_report(tmp_path):
    result = _materialize(tmp_path)

    assert result.success
    report = result.output_for_node("duckdb_analytics_report")
    published = result.output_for_node("quality_gated_publication")
    assert report["summary"]["records"] == 3
    assert report["snapshot"] == str(published.snapshot)
    assert (published.snapshot / "experiences.parquet").is_file()


def test_repeat_materialization_replays_safely_without_duplicate_records(tmp_path):
    first = _materialize(tmp_path)
    second = _materialize(tmp_path)

    assert first.success and second.success
    first_published = first.output_for_node("quality_gated_publication")
    second_published = second.output_for_node("quality_gated_publication")
    assert first_published.snapshot != second_published.snapshot
    assert second.output_for_node("duckdb_analytics_report")["summary"]["records"] == 3


def test_quality_failure_prevents_parquet_and_analytics_materialization(tmp_path):
    result = _materialize(
        tmp_path,
        html='<div class="experience" data-record-id="bad"></div>',
    )

    assert not result.success
    assert result.get_step_failure_events()[0].step_key == "quality_gated_publication"
    materialized = {
        event.event_specific_data.materialization.asset_key.to_user_string()
        for event in result.get_asset_materialization_events()
    }
    assert materialized == {"saved_raw_batch"}


def test_base_cli_import_does_not_require_dagster():
    script = """
import builtins
import sys
real_import = builtins.__import__
def blocked(name, *args, **kwargs):
    if name == 'dagster' or name.startswith('dagster.'):
        raise ImportError('Dagster deliberately unavailable')
    return real_import(name, *args, **kwargs)
builtins.__import__ = blocked
from pktscrape.__main__ import main
sys.argv = ['pktscrape', '--help']
main()
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], check=False, capture_output=True, text=True
    )

    assert completed.returncode == 0, completed.stderr
    assert "Offline-first scrape/process demonstration" in completed.stdout
