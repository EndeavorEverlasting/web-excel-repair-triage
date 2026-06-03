"""CLI and orchestration for roster log comparison."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from triage.roster_log_compare.cf_compare import compare_conditional_formatting
from triage.roster_log_compare.expected_hours import compare_expected_hours
from triage.roster_log_compare.header_styles import compare_header_styles
from triage.roster_log_compare.live_diff import compare_live
from triage.roster_log_compare.load import resolve_path
from triage.roster_log_compare.metadata import compare_metadata
from triage.roster_log_compare.models import ComparisonResult
from triage.roster_log_compare.override_check import compare_override_tables
from triage.roster_log_compare.report import write_comparison_workbook
from triage.roster_log_compare.structure import compare_structure
from triage.roster_log_compare.verdict import compute_verdict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_comparison(
    left: str | Path,
    right: str | Path,
    *,
    live_include_formatting: bool = False,
) -> Dict[str, Any]:
    left_p = Path(left).resolve()
    right_p = Path(right).resolve()
    if not left_p.is_file():
        raise FileNotFoundError(f"Left workbook not found: {left_p}")
    if not right_p.is_file():
        raise FileNotFoundError(f"Right workbook not found: {right_p}")

    metadata = compare_metadata(left_p, right_p)
    structure = compare_structure(left_p, right_p)
    live = compare_live(left_p, right_p, include_formatting=live_include_formatting)
    header = compare_header_styles(left_p, right_p)
    cf = compare_conditional_formatting(left_p, right_p)
    override = compare_override_tables(left_p, right_p)
    expected = compare_expected_hours(left_p, right_p)

    verdict, extra_risks = compute_verdict(metadata, live, cf, override, expected, header)
    risks = extra_risks

    result = ComparisonResult(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        left={"path": str(left_p), "filename": left_p.name},
        right={"path": str(right_p), "filename": right_p.name},
        verdict=verdict,
        risk_flags=risks,
        sections={
            "metadata": metadata,
            "structure": structure,
            "live": live,
            "header_styles": header,
            "conditional_formatting": cf,
            "override_table": override,
            "expected_hours": expected,
        },
    )
    return result.to_dict()


def run(
    left: str,
    right: str,
    out_xlsx: str,
    json_out: str,
    *,
    repo_root: Optional[Path] = None,
    live_include_formatting: bool = False,
) -> Dict[str, Any]:
    root = repo_root or _REPO_ROOT
    left_p = resolve_path(left, root)
    right_p = resolve_path(right, root)
    payload = run_comparison(
        left_p, right_p, live_include_formatting=live_include_formatting,
    )
    jpath = resolve_path(json_out, root)
    xpath = resolve_path(out_xlsx, root)
    jpath.parent.mkdir(parents=True, exist_ok=True)
    jpath.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_comparison_workbook(payload, xpath)
    return payload


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="triage.roster_log_compare.compare",
        description="Compare two Active Roster Log workbooks (read-only).",
    )
    ap.add_argument("--left", required=True, help="Older / baseline candidate path")
    ap.add_argument("--right", required=True, help="Newer / challenger candidate path")
    ap.add_argument("--out", required=True, help="Output comparison .xlsx path")
    ap.add_argument("--json-out", required=True, help="Output comparison .json path")
    ap.add_argument("--repo-root", default=None)
    ap.add_argument(
        "--live-include-formatting",
        action="store_true",
        help="Include formatting-only differences on Live sheets",
    )
    args = ap.parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    payload = run(
        args.left, args.right, args.out, args.json_out,
        repo_root=root,
        live_include_formatting=args.live_include_formatting,
    )
    print(json.dumps({"verdict": payload.get("verdict"), "json_out": args.json_out, "out": args.out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
