"""Read-only DuckDB analytics over one published Parquet generation."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class SnapshotAnalytics:
    """A bounded analytics report tied to one immutable published generation."""

    snapshot: Path
    publication_state_filesystem_mtime_utc: str
    provenance: dict
    quality: dict
    summary: dict
    by_classification: list[dict]

    def to_dict(self) -> dict:
        return {
            "snapshot": str(self.snapshot),
            "publication_state_filesystem_mtime_utc": self.publication_state_filesystem_mtime_utc,
            "provenance": self.provenance,
            "quality": self.quality,
            "summary": self.summary,
            "by_classification": self.by_classification,
        }


def _published_generation(output_dir: str | Path) -> Path:
    output = Path(output_dir).resolve()
    pointer = output / "current.json"
    if not pointer.is_file():
        raise ValueError("published snapshot pointer is missing")
    try:
        generation_value = json.loads(pointer.read_text(encoding="utf-8"))["generation"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("published snapshot pointer is invalid") from error
    if not isinstance(generation_value, str) or not generation_value:
        raise ValueError("published snapshot pointer is invalid")
    generation = Path(generation_value).resolve()
    generations = (output / "generations").resolve()
    if generation.parent != generations or not generation.is_dir():
        raise ValueError("published snapshot generation is invalid")
    return generation


def _state(snapshot: Path) -> dict:
    state_path = snapshot / "state.json"
    if not state_path.is_file():
        raise ValueError("published snapshot state is missing")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("published snapshot state is invalid") from error
    if not isinstance(state, dict):
        raise ValueError("published snapshot state is invalid")
    records = state.get("records")
    provenance = state.get("provenance")
    quality = state.get("quality")
    if (
        not isinstance(records, dict)
        or not isinstance(provenance, dict)
        or not isinstance(quality, dict)
    ):
        raise ValueError("published snapshot state is invalid")
    required_record_fields = {"uuid", "classification", "description", "title", "content_hash"}
    for record_id, record in records.items():
        if (
            not isinstance(record_id, str)
            or not record_id
            or not isinstance(record, dict)
            or set(record) != required_record_fields
            or any(not isinstance(record[field], str) for field in required_record_fields)
            or record["uuid"] != record_id
        ):
            raise ValueError("published snapshot state is invalid")
    if (
        not isinstance(quality.get("policy_version"), str)
        or not quality["policy_version"]
        or type(quality.get("accepted")) is not int
        or type(quality.get("rejected")) is not int
        or quality["accepted"] < 0
        or quality["rejected"] < 0
    ):
        raise ValueError("published snapshot state is invalid")
    return state


def analyze_published_snapshot(output_dir: str | Path) -> SnapshotAnalytics:
    """Query accepted records from the generation selected by ``current.json`` once."""
    snapshot = _published_generation(output_dir)
    state = _state(snapshot)
    parquet = snapshot / "experiences.parquet"
    if not parquet.is_file():
        raise ValueError("published snapshot Parquet export is missing")

    with duckdb.connect(database=":memory:") as connection:
        relation = connection.from_parquet(str(parquet))
        relation.create_view("experiences")
        summary_columns = connection.execute(
            """
            SELECT
                count(*) AS records,
                count(DISTINCT uuid) AS distinct_record_ids,
                count(DISTINCT content_hash) AS distinct_contents,
                coalesce(round(avg(length(description)), 2), 0) AS average_description_characters
            FROM experiences
            """
        ).fetchone()
        classification_rows = connection.execute(
            """
            SELECT
                classification,
                count(*) AS records,
                count(DISTINCT content_hash) AS distinct_contents,
                coalesce(round(avg(length(description)), 2), 0) AS average_description_characters
            FROM experiences
            GROUP BY classification
            ORDER BY records DESC, classification ASC
            LIMIT 20
            """
        ).fetchall()

    state_path = snapshot / "state.json"
    return SnapshotAnalytics(
        snapshot=snapshot,
        publication_state_filesystem_mtime_utc=datetime.fromtimestamp(
            state_path.stat().st_mtime, tz=UTC
        ).isoformat(),
        provenance=state.get("provenance", {}),
        quality=state.get("quality", {}),
        summary=dict(
            zip(
                (
                    "records",
                    "distinct_record_ids",
                    "distinct_contents",
                    "average_description_characters",
                ),
                summary_columns,
                strict=True,
            )
        ),
        by_classification=[
            dict(
                zip(
                    (
                        "classification",
                        "records",
                        "distinct_contents",
                        "average_description_characters",
                    ),
                    row,
                    strict=True,
                )
            )
            for row in classification_rows
        ],
    )
