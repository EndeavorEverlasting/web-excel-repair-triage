"""CLI for roster log review queue XML graft engine."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .run import run


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m triage.roster_log_review_queue",
        description="XML-graft engine for roster log review queue + global Live CF.",
    )
    p.add_argument(
        "--mode",
        choices=["blank", "full", "graft", "review-only", "live-cf-only"],
        default="full",
        help="Pipeline stage(s) to run.",
    )
    p.add_argument("--input", help="Source roster .xlsx (required except blank).")
    p.add_argument("--output", "--out", dest="output", required=True, help="Output .xlsx path.")
    p.add_argument("--provenance-out", help="Provenance JSON path.")
    p.add_argument("--zip-out", help="Two-entry ZIP (xlsx + provenance.json).")
    p.add_argument(
        "--months",
        nargs="+",
        help="Months for blank template (e.g. 2026-04 2026-05).",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(
            mode=args.mode,
            input_path=args.input,
            output_path=args.output,
            provenance_out=args.provenance_out,
            zip_out=args.zip_out,
            months=args.months,
        )
    except (ValueError, NotImplementedError, FileNotFoundError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2

    print(json.dumps(result.provenance or {"output": result.output_path}, indent=2))

    if not result.preflight_pass:
        for err in result.errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
