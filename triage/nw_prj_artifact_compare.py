"""
Three-way reconciliation: prior dashboard, roster log, manual admin scratch.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.nw_prj_config import is_repair_filename
from triage.nw_prj_dashboard_validator import review_status_bucket
from triage.nw_prj_dashboard_rows import DashboardRow, load_dashboard_rows, row_key


@dataclass
class CompareInputs:
    dashboard_path: Optional[str] = None
    roster_path: Optional[str] = None
    admin_scratch_path: Optional[str] = None
    official_admin_path: Optional[str] = None


@dataclass
class CompareReport:
    inputs: Dict[str, str] = field(default_factory=dict)
    admin_authority: str = "manual_admin_scratch"
    active_rows: List[Dict[str, Any]] = field(default_factory=list)
    archive_rows: List[Dict[str, Any]] = field(default_factory=list)
    rich_guard_rows: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "inputs": dict(self.inputs),
            "admin_authority": self.admin_authority,
            "active_count": len(self.active_rows),
            "archive_count": len(self.archive_rows),
            "rich_guard_count": len(self.rich_guard_rows),
            "warnings": list(self.warnings),
            "failures": list(self.failures),
            "active_rows": self.active_rows[:500],
            "archive_rows": self.archive_rows[:500],
        }


def _partial_hours(h: Any) -> bool:
    try:
        v = float(h)
        return 0 < v < 8
    except (TypeError, ValueError):
        return False


def compare_artifacts(inputs: CompareInputs) -> CompareReport:
    rpt = CompareReport()
    paths = {
        "dashboard": inputs.dashboard_path,
        "roster": inputs.roster_path,
        "admin_scratch": inputs.admin_scratch_path,
        "official_admin": inputs.official_admin_path,
    }
    for k, v in paths.items():
        if v:
            rpt.inputs[k] = str(Path(v).resolve())
            if is_repair_filename(Path(v).name):
                rpt.failures.append(f"repaired_input:{k}:{Path(v).name}")

    if not inputs.admin_scratch_path:
        rpt.failures.append("missing_admin_scratch")
        return rpt

    rpt.admin_authority = "manual_admin_scratch"
    if inputs.official_admin_path and not inputs.admin_scratch_path:
        rpt.admin_authority = "official_admin_workbook"
        rpt.warnings.append("official_admin_without_scratch")

    prior: Dict[str, DashboardRow] = {}
    if inputs.dashboard_path:
        prior = {row_key(r): r for r in load_dashboard_rows(inputs.dashboard_path)}

    # Seed from prior dashboard with carry-forward
    for key, row in prior.items():
        bucket = review_status_bucket(row.review_status)
        out = row.to_dict()
        if bucket == "skipped_gray" or bucket == "resolved_green":
            rpt.archive_rows.append(out)
        else:
            if _partial_hours(row.roster_latest_hours):
                out["Work Queue Status"] = out.get("Work Queue Status") or "AMBER"
                out["Reason Code"] = out.get("Reason Code") or "PARTIAL_HOURS_REVIEW"
            rpt.active_rows.append(out)

    # Rich Guard: admin full day with weak roster
    for row in rpt.active_rows:
        admin_h = row.get("Current Admin Value") or row.get("Roster Latest Hours")
        roster_h = row.get("Roster Latest Hours")
        try:
            ah = float(admin_h) if admin_h not in (None, "") else None
            rh = float(roster_h) if roster_h not in (None, "") else None
        except (TypeError, ValueError):
            ah = rh = None
        if ah is not None and ah >= 8 and (rh is None or rh < ah):
            guard = dict(row)
            guard["Work Queue Status"] = "RICH_GUARD"
            guard["Reason Code"] = "PRESERVE_ADMIN_FULL_DAY"
            guard["Action Needed"] = (
                "Preserve admin full/long-day hours unless explicit short-day evidence exists."
            )
            rpt.rich_guard_rows.append(guard)

    # Demote gray resurrection
    active_keys = {row_key(DashboardRow.from_dict(r)) for r in rpt.active_rows}
    for key, row in prior.items():
        if review_status_bucket(row.review_status) == "skipped_gray" and key in active_keys:
            rpt.warnings.append(f"gray_resurrection:{key}")

    return rpt


def main() -> None:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Compare NW PRJ dashboard artifacts")
    ap.add_argument("--dashboard")
    ap.add_argument("--roster")
    ap.add_argument("--admin-scratch", required=True)
    ap.add_argument("--official-admin")
    args = ap.parse_args()
    rpt = compare_artifacts(
        CompareInputs(
            dashboard_path=args.dashboard,
            roster_path=args.roster,
            admin_scratch_path=args.admin_scratch,
            official_admin_path=args.official_admin,
        )
    )
    print(json.dumps(rpt.to_dict(), indent=2))


if __name__ == "__main__":
    main()
