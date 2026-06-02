"""CLI for the 1 Marcus recon part-number relink engine.

Example:
    python -m triage.one_marcus_recon.cli \\
        --input "Candidates/inventory recon/...CANDIDATE_v2.xlsx" \\
        --date auto \\
        --output "Outputs/1_Marcus_Recon_2026-05-28_WEBSAFE.xlsx"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .date_inference import AmbiguousDateError
from .exporter import run_recon


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m triage.one_marcus_recon.cli",
        description="Relink the dated Part Numbers tab and produce a Web Excel-safe recon workbook.",
    )
    p.add_argument("--input", required=True, help="Source recon workbook (.xlsx).")
    p.add_argument("--date", default="auto", help="Update date (ISO/M-D-YYYY) or 'auto'.")
    p.add_argument("--output", help="Output .xlsx path. Defaults under Outputs/.")
    p.add_argument("--part-number-tab", help="Explicit source Part Numbers tab to rename.")
    p.add_argument("--pivot-tab", help="Pivot/recon module tab name (reporting only).")
    p.add_argument("--dry-run", action="store_true", help="Report intended changes; write nothing.")
    p.add_argument("--strict", action="store_true", help="Fail on ambiguous date candidates.")
    p.add_argument("--report-json", help="Write the recon report JSON to this path.")
    return p


def _default_output(input_path: str) -> str:
    return str(Path("Outputs") / "1_Marcus_Recon_WEBSAFE.xlsx")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    output = args.output or _default_output(args.input)

    try:
        result = run_recon(
            args.input,
            output_path=output,
            cli_date=args.date,
            part_number_tab=args.part_number_tab,
            pivot_tab=args.pivot_tab,
            dry_run=args.dry_run,
            strict=args.strict,
        )
    except AmbiguousDateError as exc:
        print(json.dumps({"error": "ambiguous_date", "detail": str(exc)}, indent=2))
        return 2

    report = result.report.to_dict()
    print(json.dumps(report, indent=2))

    if args.report_json:
        Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not result.report.webexcel_preflight_pass:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
