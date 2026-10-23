"""Optional, local-only Spark analysis and runtime verification.

PySpark is imported lazily so installing or importing the base offline demo
does not require a Java runtime.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def spark_environment_diagnostics() -> list[str]:
    """Return actionable Java diagnostics without starting a JVM."""
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if not java.is_file():
            return [f"JAVA_HOME points to {java_home!r}, but {java} does not exist."]
        return [f"JAVA_HOME uses {java}."]
    java_on_path = shutil.which("java")
    if java_on_path:
        return [f"JAVA_HOME is unset; using java on PATH: {java_on_path}."]
    return ["Neither JAVA_HOME nor java on PATH identifies a Java runtime."]


def _spark_modules() -> tuple[Any, Any, Any]:
    try:
        import pyspark.sql.functions as functions
        from pyspark.ml.feature import StopWordsRemover, Tokenizer
        from pyspark.sql import SparkSession
    except ModuleNotFoundError as error:
        if error.name and error.name.startswith("pyspark"):
            raise RuntimeError(
                "PySpark is not installed. Install the optional Spark profile with "
                "`python -m pip install -r requirements/spark.txt`."
            ) from error
        raise
    return SparkSession, functions, (StopWordsRemover, Tokenizer)


def init_spark() -> Any:
    """Start a local Spark session and attach useful Java setup context on failure."""
    SparkSession, _, _ = _spark_modules()
    # PySpark defaults to ``python3``, which is commonly absent on Windows even
    # when the driver is running from a healthy virtual environment. Preserve a
    # caller's explicit worker choice, otherwise keep worker and driver aligned.
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    try:
        return (
            SparkSession.builder.master("local[2]")
            .appName("pkt-scrape-process")
            .config("spark.ui.enabled", "false")
            .getOrCreate()
        )
    except Exception as error:
        diagnostics = " ".join(spark_environment_diagnostics())
        raise RuntimeError(
            "Spark could not start. Spark 3.5.x requires Java 8u371+, 11, or 17. "
            f"{diagnostics}"
        ) from error


def list_top_words(
    input_path: str | Path,
    *,
    number_to_include: int = 30,
    extra_stop_words: list[str] | None = None,
    spark: Any | None = None,
) -> list[tuple[str, int]]:
    """Return only the requested top rows; do not collect an unbounded result."""
    SparkSession, functions, features = _spark_modules()
    StopWordsRemover, Tokenizer = features
    # ``getOrCreate`` can reuse a default session even when no active session is
    # reported. This library function therefore never owns or stops a session.
    spark = spark or SparkSession.getActiveSession() or init_spark()
    path = str(input_path)
    dataframe = (
        spark.read.parquet(path)
        if path.endswith(".parquet")
        else spark.read.csv(path, header=True, escape='"')
    )
    tokenizer = Tokenizer(inputCol="description", outputCol="words_token")
    tokenized = tokenizer.transform(dataframe).select("uuid", "words_token")
    stop_words = list(set((extra_stop_words or []) + StopWordsRemover().getStopWords()))
    cleaned = StopWordsRemover(
        inputCol="words_token", outputCol="words_clean", stopWords=stop_words
    ).transform(tokenized)
    rows = (
        cleaned.withColumn("word", functions.explode("words_clean"))
        .groupBy("word")
        .count()
        .orderBy(functions.desc("count"), functions.asc("word"))
        .limit(number_to_include)
        .collect()
    )
    return [(row["word"], row["count"]) for row in rows]


def verify_local_spark(output: str | Path) -> list[tuple[str, int]]:
    """Exercise a transformation and Parquet round trip with an owned session.

    The target must not exist; this avoids deleting a caller's data during a
    diagnostic check. The session is always stopped by this command.
    """
    output_path = Path(output)
    if output_path.exists():
        raise FileExistsError(f"Verification output already exists: {output_path}")
    spark = init_spark()
    try:
        # Delay filesystem creation until Spark itself is healthy. A startup
        # failure therefore leaves the requested output path reusable.
        output_path.mkdir(parents=True)
        source_path = output_path / "source.parquet"
        result_path = output_path / "top_words.parquet"
        source = spark.createDataFrame(
            [("one", "alpha bravo alpha"), ("two", "charlie alpha")],
            ["uuid", "description"],
        )
        source.write.parquet(str(source_path))
        top_words = list_top_words(source_path, number_to_include=3, spark=spark)
        expected = [("alpha", 3), ("bravo", 1), ("charlie", 1)]
        if top_words != expected:
            raise AssertionError(f"Unexpected top words: {top_words!r}")
        spark.createDataFrame(top_words, ["word", "count"]).write.parquet(str(result_path))
        round_trip = [
            (row["word"], row["count"])
            for row in spark.read.parquet(str(result_path)).orderBy("word").collect()
        ]
        if round_trip != sorted(expected):
            raise AssertionError(f"Unexpected Parquet round trip: {round_trip!r}")
        return top_words
    finally:
        spark.stop()


def main() -> None:
    """Run bounded analysis or a self-contained local Spark verification."""
    parser = argparse.ArgumentParser(description="Optional local Spark analysis")
    subcommands = parser.add_subparsers(dest="command", required=True)
    top_words = subcommands.add_parser("top-words", help="list frequent words in CSV or Parquet")
    top_words.add_argument("input_path", type=Path)
    top_words.add_argument("--limit", type=int, default=30)
    verify = subcommands.add_parser("verify", help="run a local transform and Parquet round trip")
    verify.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "verify":
        for word, count in verify_local_spark(args.output):
            print(f"{word}\t{count}")
        print(f"Spark verification output: {args.output}")
        return
    spark = init_spark()
    try:
        for word, count in list_top_words(args.input_path, number_to_include=args.limit, spark=spark):
            print(f"{word}\t{count}")
    finally:
        spark.stop()
