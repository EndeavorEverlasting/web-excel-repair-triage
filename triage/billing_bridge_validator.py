"""
triage/billing_bridge_validator.py
----------------------------------
Billing-specific validation wrapper for Web Excel compatibility.

Runs the existing gate battery plus a billing profile check, then writes a
structured JSON report into billing_runs/YYYY-MM/validation/.

All operations are READ-ONLY (no workbook modification).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.gate_checks import run_all as run_gate_all, GateReport
from triage.billing_workbook_profile import profile_workbook, BillingProfileResult


def _run_id_default(month: str) -> str:
    seq = 1
    return f"billing-{month}-{seq:03d}"


def _month_from_run_id(run_id: str) -> str:
    parts = run_id.split("-")
    if len(parts) >= 2:
        return f"{parts[1]}-{parts[2]}"
    return time.strftime("%Y-%m")


@dataclass
class BillingValidationReport:
    run_id: str
    candidate_workbook: str
    status: str = "pass"
    web_excel_safe: bool = False
    checks: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    profile: Optional[dict] = None
    validation_dir: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "candidate_workbook": self.candidate_workbook,
            "status": self.status,
            "web_excel_safe": self.web_excel_safe,
            "checks": dict(self.checks),
            "warnings": list(self.warnings),
            "failures": list(self.failures),
            "profile": self.profile,
            "validation_dir": self.validation_dir,
        }


def _gate_verdict(report: GateReport) -> Dict[str, str]:
    """Map GateReport findings into per-check verdict strings."""
    verdicts: Dict[str, str] = {}
    failing = report.failing_gates()

    # Stage 1: ZIP well-formedness is implicit (GateReport would raise on bad ZIP)
    verdicts["zip_scan"] = "pass"

    # Stage 2
    verdicts["stop_ship_tokens"] = "fail" if report.stopship else "pass"

    # Stage 3
    verdicts["relationships"] = "fail" if report.rels_missing else "pass"

    # Stage 4
    verdicts["tables"] = "fail" if report.tablecolumn_lf else "pass"

    # Stage 5
    cf_issues = bool(report.cf_ref or report.styles_dxf or report.cf_policy_deploymenttracker)
    verdicts["conditional_formatting"] = "fail" if cf_issues else "pass"

    # Stage 6
    ss_issues = bool(report.shared_ref_oob or report.shared_ref_bbox)
    verdicts["shared_strings"] = "fail" if ss_issues else "pass"

    # Stage 7
    formula_warn = bool(report.stopship)  # stopship already fail, but warn if present
    calc_warn = bool(report.calcchain_invalid)
    verdicts["formulas"] = "warn" if (formula_warn or calc_warn) else "pass"

    # Stage 8
    verdicts["xml_wellformed"] = "fail" if report.xml_wellformed else "pass"
    verdicts["illegal_control_chars"] = "fail" if report.illegal_control else "pass"

    return verdicts


def validate_billing_workbook(
    path: str,
    run_id: Optional[str] = None,
    month: Optional[str] = None,
    out_root: str = "Outputs/billing_runs",
) -> BillingValidationReport:
    """Validate a single billing workbook and write the report.

    Returns the BillingValidationReport (caller can also inspect .to_dict()).
    Writes:
      <out_root>/<YYYY-MM>/validation/<run_id>_validation_report.json
    """
    candidate = Path(path).name
    resolved_month = month or time.strftime("%Y-%m")
    resolved_run_id = run_id or _run_id_default(resolved_month)

    report = BillingValidationReport(
        run_id=resolved_run_id,
        candidate_workbook=candidate,
    )

    # Quick ZIP sanity
    try:
        with zipfile.ZipFile(path, "r") as z:
            z.testzip()
    except Exception as exc:
        report.status = "fail"
        report.web_excel_safe = False
        report.failures.append(f"ZIP integrity: {exc}")
        report.checks["zip_scan"] = "fail"
        return _write_report(report, out_root, resolved_month)

    # Run gate battery
    gate = run_gate_all(path)
    gate_dict = gate.to_dict()
    report.checks = _gate_verdict(gate)

    # Run billing profile
    profile = profile_workbook(path)
    report.profile = profile.to_dict()

    if not profile.is_billing_workbook:
        report.warnings.append(
            "Workbook does not match known billing profile (low confidence)."
        )
    else:
        report.checks["billing_profile"] = "pass"

    # Collate warnings from gates
    for key, val in report.checks.items():
        if val == "warn":
            report.warnings.append(f"{key}: non-blocking issue detected")
        elif val == "fail":
            report.failures.append(f"{key}: blocking issue detected")

    # Determine overall status
    if report.failures:
        report.status = "fail"
        report.web_excel_safe = False
    elif report.warnings:
        report.status = "warn"
        report.web_excel_safe = False
    else:
        report.status = "pass"
        report.web_excel_safe = True

    return _write_report(report, out_root, resolved_month)


def _write_report(
    report: BillingValidationReport,
    out_root: str,
    month: str,
) -> BillingValidationReport:
    validation_dir = Path(out_root) / month / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    report.validation_dir = str(validation_dir)

    out_path = validation_dir / f"{report.run_id}_validation_report.json"
    out_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Billing Bridge Web Excel validator (read-only)"
    )
    parser.add_argument("workbook", help="Path to candidate .xlsx workbook")
    parser.add_argument("--run-id", default=None, help="Billing run ID")
    parser.add_argument("--month", default=None, help="YYYY-MM folder segment")
    parser.add_argument("--out-root", default="Outputs/billing_runs", help="Output root")
    parser.add_argument("--quiet", action="store_true", help="Only output JSON path")
    args = parser.parse_args()

    if not Path(args.workbook).exists():
        print(f"ERROR: file not found: {args.workbook}", file=sys.stderr)
        raise SystemExit(2)

    result = validate_billing_workbook(
        path=args.workbook,
        run_id=args.run_id,
        month=args.month,
        out_root=args.out_root,
    )

    out_file = Path(result.validation_dir) / f"{result.run_id}_validation_report.json"
    if args.quiet:
        print(str(out_file))
    else:
        print(json.dumps(result.to_dict(), indent=2))
        print(f"\nReport written: {out_file}")


if __name__ == "__main__":
    _cli()
