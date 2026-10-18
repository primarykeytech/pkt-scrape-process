"""Incremental, restart-safe local demonstration pipeline."""

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


def _load_checkpoint(path: Path) -> dict[str, Experience]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {record_id: Experience(**item) for record_id, item in payload["records"].items()}


def _write_checkpoint(path: Path, records: dict[str, Experience]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"records": {key: value.to_item() for key, value in records.items()}}, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def classify(previous: dict[str, Experience], incoming: list[Experience]) -> tuple[list[Experience], list[Experience], list[Experience]]:
    new, changed, unchanged = [], [], []
    for record in incoming:
        old = previous.get(record.uuid)
        if old is None:
            new.append(record)
        elif old.content_hash == record.content_hash:
            unchanged.append(record)
        else:
            changed.append(record)
    return new, changed, unchanged


def run_incremental_demo(output_dir: str | Path, html: str, *, fail_before_publish: bool = False) -> IncrementalResult:
    """Process synthetic HTML and atomically publish only a fully successful run.

    Moto is intentionally ephemeral; the JSON checkpoint makes separate CLI
    invocations incremental.  It is a local checkpoint, not a cross-system
    exactly-once guarantee.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / ".incremental-state.json"
    previous = _load_checkpoint(checkpoint)
    incoming = OfflineHtmlSource(html, classification="synthetic-demo", content_class="experience", title="offline fixture").experiences()
    new, changed, unchanged = classify(previous, incoming)
    next_records = previous | {record.uuid: record for record in new + changed}

    with mock_aws():
        table = boto3.resource("dynamodb", region_name="us-east-1").create_table(
            TableName="pkt-scrape-demo", KeySchema=[{"AttributeName": "uuid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "uuid", "AttributeType": "S"}], BillingMode="PAY_PER_REQUEST"
        )
        repository = DynamoExperienceRepository(table=table)
        repository.save_many(next_records.values())
        persisted = repository.list_all()

    staging = output / f".staging-{uuid.uuid4().hex}"
    try:
        csv_path, parquet_path = export_records(persisted, staging)
        image_path = write_word_cloud(top_words(persisted), staging / "wordcloud.png")
        if fail_before_publish:
            raise RuntimeError("simulated failure before publication")
        for artifact in (csv_path, parquet_path, image_path):
            os.replace(artifact, output / artifact.name)
        _write_checkpoint(checkpoint, next_records)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return IncrementalResult(len(new), len(changed), len(unchanged), len(next_records))
