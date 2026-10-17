"""Spark profile for larger exports; the offline demo does not require Spark."""

import argparse
from pathlib import Path

import pyspark.sql.functions as f
from pyspark.ml.feature import StopWordsRemover, Tokenizer
from pyspark.sql import SparkSession


def init_spark() -> SparkSession:
    return SparkSession.builder.appName("pkt-scrape-process").getOrCreate()


def list_top_words(input_path: str | Path, *, number_to_include: int = 30,
                   extra_stop_words: list[str] | None = None, spark: SparkSession | None = None):
    """Return only the requested top rows; do not collect an unbounded result."""
    # ``getOrCreate`` can reuse a default session even when no active session is
    # reported.  This library function therefore never owns or stops a session.
    spark = spark or SparkSession.getActiveSession() or init_spark()
    try:
        path = str(input_path)
        df = spark.read.parquet(path) if path.endswith(".parquet") else spark.read.csv(path, header=True, escape='"')
        tokenizer = Tokenizer(inputCol="description", outputCol="words_token")
        tokenized = tokenizer.transform(df).select("uuid", "words_token")
        stop_words = list(set((extra_stop_words or []) + StopWordsRemover().getStopWords()))
        cleaned = StopWordsRemover(inputCol="words_token", outputCol="words_clean", stopWords=stop_words).transform(tokenized)
        rows = (cleaned.withColumn("word", f.explode("words_clean"))
                .groupBy("word").count().orderBy(f.desc("count")).limit(number_to_include).collect())
        return [(row["word"], row["count"]) for row in rows]
    finally:
        # Callers that create a session are responsible for closing it.
        pass


def main() -> None:
    """Standalone Spark entry point; it explicitly owns the session it creates."""
    parser = argparse.ArgumentParser(description="List the most frequent words in a CSV or Parquet export")
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    spark = init_spark()
    try:
        for word, count in list_top_words(args.input_path, number_to_include=args.limit, spark=spark):
            print(f"{word}\t{count}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
