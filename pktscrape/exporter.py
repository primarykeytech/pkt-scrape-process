"""Portable export formats for normalized records."""

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from .models import Experience


def export_records(records: Iterable[Experience], output_dir: str | Path) -> tuple[Path, Path]:
    """Write CSV and Parquet files, returning their paths."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([record.to_item() for record in records], columns=["uuid", "classification", "description", "title", "content_hash"])
    csv_path = destination / "experiences.csv"
    parquet_path = destination / "experiences.parquet"
    frame.to_csv(csv_path, index=False)
    frame.to_parquet(parquet_path, index=False)
    return csv_path, parquet_path
