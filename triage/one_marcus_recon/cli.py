"""CLI for the 1 Marcus recon engine (generate + relink modes).

Examples:
    python -m triage.one_marcus_recon.cli relink \\
        --input "Candidates/inventory recon/Try Again Asshole - 1M_Recon_READY.xlsx" \\
        --output "Outputs/one_marcus_recon/1M_Recon_READY_relink.xlsx"

    python -m triage.one_marcus_recon.cli generate \\
        --input "tests/fixtures/.../integrated_source.xlsx" \\
        --output "Outputs/one_marcus_recon/generated.xlsx"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .date_inference import AmbiguousDateError
from .exporter import run_generate, run_recon
from .integrated_guard import IntegratedWorkbookError
from triage.output_policy import (
    SourcePathWriteForbiddenError,
    allocate_run_dir,
    assert_output_path_allowed,
    ensure_run_subdirs,
)


def _add_shared_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--input", required=True, help="Source integrated recon workbook (.xlsx).")
    p.add_argument("--date", default="auto", help="Update date (ISO/M-D-YYYY) or 'auto'.")
    p.add_argument("--output", help="Output .xlsx path. Defaults under Outputs/.")
    p.add_argument("--part-number-tab", help="Explicit source Part Numbers tab.")
    p.add_argument("--dry-run", action="store_true", help="Report intended changes; write nothing.")
    p.add_argument("--strict", action="store_true", help="Fail on ambiguous date candidates.")
    p.add_argument("--report-json", help="Write the recon report JSON to this path.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m triage.one_marcus_recon.cli",
        description="Generate or relink One Marcus inventory recon workbooks.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    gen = sub.add_parser(
        "generate",
        help="Clean-render for sanitized 2-sheet fixtures only (not integrated READY workbooks).",
    )
    _add_shared_args(gen)

    relink = sub.add_parser(
        "relink",
        help="Surgical Part Numbers tab relink on an existing integrated workbook.",
    )
    _add_shared_args(relink)
    relink.add_argument("--pivot-tab", help="Pivot/recon module tab name (reporting only).")
    return p


def _default_generate_output(_input_path: str) -> str:
    run = allocate_run_dir("one_marcus_recon", "generate")
    ensure_run_subdirs(run, ("delivery",))
    return str(run / "delivery" / "1M_Recon_generated.xlsx")


def _default_relink_output(_input_path: str) -> str:
    run = allocate_run_dir("one_marcus_recon", "relink")
    ensure_run_subdirs(run, ("delivery",))
    return str(run / "delivery" / "1M_Recon_relink.xlsx")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "generate":
            output = args.output or _default_generate_output(args.input)
            assert_output_path_allowed(args.input, output_path=output)
            result = run_generate(
                args.input,
                output_path=output,
                cli_date=args.date,
                part_number_tab=args.part_number_tab,
                dry_run=args.dry_run,
                strict=args.strict,
            )
        else:
            output = args.output or _default_relink_output(args.input)
            assert_output_path_allowed(args.input, output_path=output)
            result = run_recon(
                args.input,
                output_path=output,
                cli_date=args.date,
                part_number_tab=args.part_number_tab,
                pivot_tab=getattr(args, "pivot_tab", None),
                dry_run=args.dry_run,
                strict=args.strict,
            )
    except AmbiguousDateError as exc:
        print(json.dumps({"error": "ambiguous_date", "detail": str(exc)}, indent=2))
        return 2
    except SourcePathWriteForbiddenError as exc:
        print(json.dumps({"error": "source_path_write_forbidden", "detail": str(exc)}, indent=2))
        return 2
    except IntegratedWorkbookError as exc:
        print(json.dumps({"error": "integrated_workbook_use_relink_not_generate", "detail": str(exc)}, indent=2))
        return 2

    report = result.report.to_dict()
    print(json.dumps(report, indent=2))

    if args.report_json:
        Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.command == "generate":
        if (
            not result.report.webexcel_preflight_pass
            or not result.report.operational_pass
            or not result.report.baseline_compare_pass
        ):
            return 1
        return 0

    if not result.report.webexcel_preflight_pass or not result.report.baseline_compare_pass:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
