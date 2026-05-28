"""
NW PRJ dashboard v6 validation — schema + gate battery + profile checks.
READ-ONLY.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.gate_checks import run_all, GateReport
from triage.nw_prj_config import (
    dashboard_schema,
    is_repair_filename,
    resolved_review_statuses,
    skipped_review_statuses,
    stop_ship_tokens,
)


def _sheet_names_in_workbook(path: Path) -> List[str]:
    with zipfile.ZipFile(path, "r") as z:
        if "xl/workbook.xml" not in z.namelist():
            return []
        import re as _re
        wb = z.read("xl/workbook.xml").decode("utf-8", errors="ignore")
        return _re.findall(r'<sheet\b[^>]*\bname="([^"]+)"', wb)


def _has_cf_dictionary(sheet_names: List[str]) -> bool:
    schema = dashboard_schema()
    required = schema["cf_dictionary_sheet"]
    if required in sheet_names:
        return True
    return any(required in n for n in sheet_names)


def check_cf_dictionary_exists(path: str) -> List[dict]:
    names = _sheet_names_in_workbook(Path(path))
    if not names:
        return [{"issue": "unreadable_workbook"}]
    if not _has_cf_dictionary(names):
        return [{"issue": "missing_cf_dictionary", "sheets": names[:30]}]
    return []


def check_column_a_override_wins(path: str) -> List[dict]:
    """
    Heuristic: flag CF blocks that reference RC* or SEARCH("AMBER") on sheets
    that look like dashboard active queues — contract smell.
    """
    hits: List[dict] = []
    forbidden = stop_ship_tokens().get("cf_forbidden_patterns", [])
    with zipfile.ZipFile(path, "r") as z:
        for name in z.namelist():
            if not name.startswith("xl/worksheets/"):
                continue
            s = z.read(name).decode("utf-8", errors="ignore")
            if "conditionalFormatting" not in s:
                continue
            for pat in forbidden:
                if re.search(pat, s):
                    hits.append({"part": name, "pattern": pat})
                    break
    return hits


@dataclass
class NwPrjDashboardValidationReport:
    path: str
    web_excel_safe: bool = False
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    gate: Optional[Dict[str, Any]] = None
    profile_checks: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "web_excel_safe": self.web_excel_safe,
            "failures": list(self.failures),
            "warnings": list(self.warnings),
            "gate": self.gate,
            "profile_checks": dict(self.profile_checks),
        }


def validate_nw_prj_dashboard(path: str) -> NwPrjDashboardValidationReport:
    p = Path(path)
    rpt = NwPrjDashboardValidationReport(path=str(p.resolve()))

    if is_repair_filename(p.name):
        rpt.failures.append(f"repair_filename_stop_ship:{p.name}")

    gate = run_all(str(p))
    rpt.gate = gate.to_dict()
    if not gate.pass_all:
        for k, n in gate.failing_gates().items():
            rpt.failures.append(f"gate:{k} ({n})")

    cf_dict = check_cf_dictionary_exists(str(p))
    rpt.profile_checks["cf_dictionary_exists"] = "pass" if not cf_dict else "fail"
    if cf_dict:
        rpt.failures.append("missing_cf_dictionary")

    col_a = check_column_a_override_wins(str(p))
    rpt.profile_checks["column_a_override_wins"] = "pass" if not col_a else "fail"
    if col_a:
        rpt.failures.append("column_a_cf_override_risk")

    rpt.web_excel_safe = not rpt.failures
    return rpt


def review_status_bucket(status: str) -> str:
    s = (status or "").strip()
    if s in resolved_review_statuses():
        return "resolved_green"
    if s in skipped_review_statuses():
        return "skipped_gray"
    return "active"


def main() -> None:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Validate NW PRJ dashboard v6 workbook")
    ap.add_argument("workbook")
    args = ap.parse_args()
    rpt = validate_nw_prj_dashboard(args.workbook)
    print(json.dumps(rpt.to_dict(), indent=2))
    raise SystemExit(0 if rpt.web_excel_safe else 1)


if __name__ == "__main__":
    main()
