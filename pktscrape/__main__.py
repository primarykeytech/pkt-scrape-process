"""Command-line entry point."""

import argparse
from pathlib import Path

from .demo import run_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline-first scrape/process demonstration")
    subcommands = parser.add_subparsers(dest="command", required=True)
    demo = subcommands.add_parser("demo", help="run the synthetic offline demonstration")
    demo.add_argument("--output", type=Path, default=Path("artifacts/demo"))
    args = parser.parse_args()
    if args.command == "demo":
        result = run_demo(args.output)
        print(f"Created {result['records']} synthetic records in {args.output}")
        for name in ("csv", "parquet", "wordcloud"):
            print(f"{name}: {result[name]}")


if __name__ == "__main__":
    main()
