#!/usr/bin/env python3
"""Operator CLI for Evaluation session setup and report export."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from network.evaluation_exporter import (  # noqa: E402
    connect_evaluation,
    default_week_period,
    export_evaluation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="NetGenix Evaluation report automation")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("connect-evaluation", help="Open a browser and save an authenticated session")
    export = commands.add_parser("export", help="Download an Evaluation KPI ZIP")
    export.add_argument("--start", type=date.fromisoformat)
    export.add_argument("--end", type=date.fromisoformat)
    export.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    if args.command == "connect-evaluation":
        connect_evaluation()
        print("Evaluation session saved.")
        return

    start, end = (args.start, args.end) if args.start and args.end else default_week_period()
    if bool(args.start) != bool(args.end):
        parser.error("--start and --end must be provided together")
    result = export_evaluation_report(start, end, headless=not args.headed)
    print(result.zip_path)


if __name__ == "__main__":
    main()
