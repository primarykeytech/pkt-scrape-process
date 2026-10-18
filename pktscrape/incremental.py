"""Incremental local demo with immutable published generations."""
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

import boto3
from moto import mock_aws

from .analysis import top_words, write_word_cloud
from .exporter import export_records
from .models import Experience
from .sources import OfflineHtmlSource
from .storage import DynamoExperienceRepository


@dataclass(frozen=True)
class IncrementalResult:
    new: int
    changed: int
    unchanged: int
    records: int
    application_writes: int


def current_snapshot(output_dir: str | Path) -> Path | None:
    pointer = Path(output_dir) / "current.json"
    return Path(json.loads(pointer.read_text())["generation"]) if pointer.exists() else None


def _previous(output: Path) -> dict[str, Experience]:
    snapshot = current_snapshot(output)
    if not snapshot:
        return {}
    return {key: Experience(**value) for key, value in json.loads((snapshot / "state.json").read_text())["records"].items()}


def classify(previous, incoming):
    ids = [item.uuid for item in incoming]
    if len(ids) != len(set(ids)):
        raise ValueError("incoming record IDs must be unique")
    new, changed, unchanged = [], [], []
    for item in incoming:
        old = previous.get(item.uuid)
        (new if old is None else unchanged if old.content_hash == item.content_hash else changed).append(item)
    return new, changed, unchanged


def run_incremental_demo(output_dir: str | Path, html: str, *, source_id: str = "offline-fixture", provenance: dict | None = None, fail_before_pointer: bool = False, fail_after_pointer: bool = False) -> IncrementalResult:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    previous = _previous(output)
    incoming = OfflineHtmlSource(html, classification="synthetic-demo", content_class="experience", title=source_id).experiences()
    new, changed, unchanged = classify(previous, incoming)
    # Missing input IDs are retained: this is delta ingestion, not snapshot mirroring.
    next_records = previous | {item.uuid: item for item in new + changed}
    with mock_aws():
        table = boto3.resource("dynamodb", region_name="us-east-1").create_table(TableName="pkt-scrape-demo", KeySchema=[{"AttributeName":"uuid","KeyType":"HASH"}], AttributeDefinitions=[{"AttributeName":"uuid","AttributeType":"S"}], BillingMode="PAY_PER_REQUEST")
        repo = DynamoExperienceRepository(table=table)
        repo.save_many(previous.values())  # ephemeral Moto rehydration, not application upserts
        repo.save_many(new + changed)
        persisted = repo.list_all()
    generation = output / "generations" / uuid.uuid4().hex
    generation.mkdir(parents=True)
    try:
        export_records(persisted, generation)
        write_word_cloud(top_words(persisted), generation / "wordcloud.png")
        (generation / "state.json").write_text(json.dumps({"records": {k:v.to_item() for k,v in next_records.items()}, "provenance": provenance or {}}, indent=2))
        if fail_before_pointer:
            raise RuntimeError("simulated failure before pointer publication")
        temporary = output / "current.tmp"
        pointer = output / "current.json"
        temporary.write_text(json.dumps({"generation": str(generation)}))
        os.replace(temporary, pointer)
        if fail_after_pointer:
            raise RuntimeError("simulated failure after pointer publication")
    except Exception:
        if current_snapshot(output) != generation:
            shutil.rmtree(generation, ignore_errors=True)
        raise
    return IncrementalResult(len(new), len(changed), len(unchanged), len(next_records), len(new) + len(changed))
