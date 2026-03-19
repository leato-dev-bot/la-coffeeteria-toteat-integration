from __future__ import annotations

import argparse
from datetime import date

from .config import load_settings
from .db import connect
from .monitor import build_status_summary, load_progress
from .sync import run_sync


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Toteat sync CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="Run Toteat sync")
    sync.add_argument("--mode", choices=["daily", "backfill", "range"], required=True)
    sync.add_argument("--start", type=date.fromisoformat)
    sync.add_argument("--end", type=date.fromisoformat)
    sync.add_argument("--exclude-endpoints", default="")

    sub.add_parser("status", help="Show current progress status")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()

    if args.command == "status":
        with connect(settings) as conn:
            print(build_status_summary(conn))
        return

    exclude_endpoints = [x.strip() for x in args.exclude_endpoints.split(",") if x.strip()]
    with connect(settings) as conn:
        rows = run_sync(conn, settings, args.mode, args.start, args.end, exclude_endpoints=exclude_endpoints)
    print(f"Loaded {rows} raw payloads into toteat.raw_api_responses")


if __name__ == "__main__":
    main()
