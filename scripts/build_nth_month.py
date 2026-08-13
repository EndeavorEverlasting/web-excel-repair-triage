#!/usr/bin/env python3
"""Build or fail-closed-check a single-month Neuron Track Hours artifact."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from triage.nth_month_readiness import inspect_month_readiness
from triage.nth_monthly_artifact import build_month_artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and build one month of Neuron Track Hours from authoritative roster attendance.")
    parser.add_argument("--roster-log", required=True, type=Path)
    parser.add_argument("--month", required=True, help="YYYY-MM")
    parser.add_argument("--out-dir", type=Path, default=Path("Outputs/nth-month"))
    parser.add_argument("--pinned", nargs="*", default=[])
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    readiness = inspect_month_readiness(args.roster_log, args.month)
    if args.check_only:
        print(json.dumps(readiness.to_dict(), indent=2))
        return 0 if readiness.status == "READY" else 2

    if readiness.status != "READY":
        print(json.dumps(readiness.to_dict(), indent=2))
        return 2

    manifest = build_month_artifact(
        roster_log=args.roster_log,
        month_key=args.month,
        out_dir=args.out_dir,
        pinned_techs=args.pinned,
    )
    print(json.dumps(manifest, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
