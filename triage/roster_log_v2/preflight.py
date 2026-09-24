"""Fail-closed Roster Log V2 workbook preflight."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from triage.web_excel_compatibility_rules import inspect_web_excel_package

REQUIRED_SHEETS = [
    "Dashboard",
    "Attendance",
    "Project Allocations",
    "Project Report",
    "Dictionaries",
    "Review Queue",
    "Read Me",
]


def preflight_roster_v2(path: str | Path) -> Dict[str, Any]:
    from openpyxl import load_workbook

    p = Path(path)
    errors: List[str] = []
    if not p.exists():
        return {"preflight_pass": False, "errors": ["file_not_found"]}

    package_issues = inspect_web_excel_package(p)
    errors.extend(f"webexcel:{issue.code}:{issue.part}" for issue in package_issues)

    try:
        wb = load_workbook(p, read_only=False, data_only=False)
    except Exception as exc:  # pragma: no cover - package gate normally catches this
        return {"preflight_pass": False, "errors": errors + [f"open:{exc}"]}

    try:
        for name in REQUIRED_SHEETS:
            if name not in wb.sheetnames:
                errors.append(f"missing_sheet:{name}")

        for name in REQUIRED_SHEETS:
            if name in wb.sheetnames and not wb[name].protection.sheet:
                errors.append(f"unprotected_snapshot_sheet:{name}")

        if all(name in wb.sheetnames for name in ("Attendance", "Project Allocations")):
            attendance_headers = [cell.value for cell in wb["Attendance"][1]]
            allocation_headers = [cell.value for cell in wb["Project Allocations"][1]]
            for header in ("Default / Fallback Project", "Allocated Hours", "Variance", "Reconciled?"):
                if header not in attendance_headers:
                    errors.append(f"attendance_header:{header}")
            for header in (
                "Allocation ID",
                "Project / Billing Scope",
                "Allocation Basis",
                "Allocated Hours",
                "Distinct Project First?",
            ):
                if header not in allocation_headers:
                    errors.append(f"allocation_header:{header}")
            if not wb["Project Allocations"].column_dimensions["J"].hidden:
                errors.append("allocation_helper:Distinct Project First? must be hidden")

        if "Project Report" in wb.sheetnames:
            report_headers = [cell.value for cell in wb["Project Report"][1]]
            for header in ("Project", "Allocated Hours", "Days", "Staff", "Allocation Rows"):
                if header not in report_headers:
                    errors.append(f"project_report_header:{header}")

        if "Dictionaries" in wb.sheetnames:
            dictionary_headers = [cell.value for cell in wb["Dictionaries"][1]]
            if "Allocation Basis" not in dictionary_headers:
                errors.append("dictionary_header:Allocation Basis")

        if "Read Me" in wb.sheetnames:
            text = " ".join(
                str(wb["Read Me"].cell(row=r, column=1).value or "")
                for r in range(1, min(wb["Read Me"].max_row, 24) + 1)
            )
            for phrase in (
                "protected DERIVED SNAPSHOT",
                "website/JSON state is the editable authority",
                "Default / Fallback Project is attendance metadata",
                "Once explicit Project Allocations exist",
                "Multi-project days are supported",
                "allocated hours must reconcile",
                "Project Mode counts distinct projects",
                "Project Report is a deterministic build-time projection",
            ):
                if phrase not in text:
                    errors.append(f"missing_contract_text:{phrase}")
    finally:
        wb.close()

    return {
        "preflight_pass": not errors,
        "errors": errors,
        "web_excel_issue_count": len(package_issues),
        "required_sheets": REQUIRED_SHEETS,
        "authority": "DERIVED / PUBLISH-ONLY",
    }
