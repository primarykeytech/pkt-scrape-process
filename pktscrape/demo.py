"""Offline, synthetic end-to-end demonstration."""

from pathlib import Path

import boto3
from moto import mock_aws

from .analysis import top_words, write_word_cloud
from .exporter import export_records
from .sources import OfflineHtmlSource
from .storage import DynamoExperienceRepository

SYNTHETIC_HTML = """
<article>
  <div class="experience" data-record-id="fixture:a">The sample participant found the workflow clear and calm.</div>
  <div class="experience" data-record-id="fixture:b">A second synthetic participant found the workflow clear and useful.</div>
  <div class="experience" data-record-id="fixture:c">This offline example uses no personal or scraped content.</div>
</article>
"""


def run_demo(output_dir: str | Path) -> dict[str, Path | int]:
    """Run HTML -> typed records -> Moto DynamoDB -> CSV/Parquet -> PNG."""
    records = OfflineHtmlSource(
        SYNTHETIC_HTML, classification="synthetic-demo", content_class="experience", title="offline fixture"
    ).experiences()
    with mock_aws():
        table = boto3.resource("dynamodb", region_name="us-east-1").create_table(
            TableName="pkt-scrape-demo",
            KeySchema=[{"AttributeName": "uuid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "uuid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        repository = DynamoExperienceRepository(table=table)
        repository.save_many(records)
        persisted = repository.list_all()
    csv_path, parquet_path = export_records(persisted, output_dir)
    image_path = write_word_cloud(top_words(persisted), Path(output_dir) / "wordcloud.png")
    return {"records": len(persisted), "csv": csv_path, "parquet": parquet_path, "wordcloud": image_path}
