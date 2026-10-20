"""Command-line entry point."""

import argparse
import json
from pathlib import Path

from .demo import SYNTHETIC_HTML, run_demo
from .incremental import run_incremental_demo
from .quality import QualityPolicy
from .raw import capture_batch, replay_batch
from .sql_analytics import analyze_published_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline-first scrape/process demonstration")
    subcommands = parser.add_subparsers(dest="command", required=True)
    demo = subcommands.add_parser("demo", help="run the synthetic offline demonstration")
    demo.add_argument("--output", type=Path, default=Path("artifacts/demo"))
    incremental = subcommands.add_parser(
        "incremental-demo", help="run or safely rerun the persistent synthetic demo"
    )
    incremental.add_argument("--output", type=Path, default=Path("artifacts/incremental-demo"))
    incremental.add_argument("--rejection-threshold", type=int, default=0)
    capture = subcommands.add_parser("capture-demo", help="save a raw synthetic batch")
    capture.add_argument("--raw-root", type=Path, default=Path("artifacts/raw"))
    replay = subcommands.add_parser("replay", help="reprocess a saved batch without network access")
    replay.add_argument("batch", type=Path)
    replay.add_argument("--output", type=Path, default=Path("artifacts/incremental-demo"))
    replay.add_argument("--rejection-threshold", type=int, default=0)
    analytics = subcommands.add_parser(
        "analytics", help="query the accepted current Parquet generation with DuckDB"
    )
    analytics.add_argument("--output", type=Path, default=Path("artifacts/incremental-demo"))
    args = parser.parse_args()
    if args.command == "demo":
        result = run_demo(args.output)
        print(f"Created {result['records']} synthetic records in {args.output}")
        for name in ("csv", "parquet", "wordcloud"):
            print(f"{name}: {result[name]}")
    if args.command == "incremental-demo":
        result = run_incremental_demo(
            args.output, SYNTHETIC_HTML, policy=QualityPolicy(args.rejection_threshold)
        )
        print(
            f"new={result.new} changed={result.changed} unchanged={result.unchanged} records={result.records}"
        )
    if args.command == "capture-demo":
        print(
            capture_batch(
                args.raw_root,
                SYNTHETIC_HTML,
                source_url="synthetic://offline",
                source_id="offline-fixture",
            )
        )
    if args.command == "replay":
        result = replay_batch(
            args.batch, args.output, policy=QualityPolicy(args.rejection_threshold)
        )
        print(
            f"new={result.new} changed={result.changed} unchanged={result.unchanged} records={result.records}"
        )
    if args.command == "analytics":
        print(
            json.dumps(analyze_published_snapshot(args.output).to_dict(), indent=2, sort_keys=True)
        )


if __name__ == "__main__":
    main()
