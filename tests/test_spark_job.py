"""Local Spark tests; skipped in the lightweight base profile."""

import os
from pathlib import Path

import pytest


pytest.importorskip("pyspark")
if os.environ.get("RUN_SPARK_TESTS") != "1":
    pytest.skip("set RUN_SPARK_TESTS=1 to run the JVM-dependent Spark profile", allow_module_level=True)

from pktscrape.spark_job import spark_environment_diagnostics, verify_local_spark


def test_verify_local_spark_transforms_and_round_trips_parquet(tmp_path: Path) -> None:
    assert verify_local_spark(tmp_path / "spark-verification") == [
        ("alpha", 3),
        ("bravo", 1),
        ("charlie", 1),
    ]


def test_verify_local_spark_does_not_overwrite_output(tmp_path: Path) -> None:
    output = tmp_path / "existing-output"
    output.mkdir()
    with pytest.raises(FileExistsError):
        verify_local_spark(output)


def test_java_diagnostics_identify_a_missing_java_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JAVA_HOME", str(Path("missing-java-home")))
    assert "does not exist" in spark_environment_diagnostics()[0]
