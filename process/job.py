"""Compatibility wrapper for the packaged optional Spark profile."""

import argparse
from pathlib import Path

from pktscrape.spark_job import init_spark, list_top_words, main, spark_environment_diagnostics

__all__ = ["init_spark", "list_top_words", "main", "spark_environment_diagnostics"]


def legacy_main() -> None:
    """Preserve the original ``python process/job.py INPUT --limit N`` form."""
    parser = argparse.ArgumentParser(description="List frequent words in a CSV or Parquet export")
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
    legacy_main()


if __name__ == "__main__":
    main()
