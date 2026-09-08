"""Roster Log V2 normalized-allocation, reporting, and Web Excel regressions."""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from triage.roster_log_v2.builder import build_roster_workbook
from triage.roster_log_v2.report import report_snapshot
from triage.roster_log_v2.schema import normalize_state, reconcile_state
from triage.web_excel_compatibility_rules import inspect_web_excel_package


def _base_state():
    return {
        "schema_version": "roster-log-v2/v1",
        "projects": ["Northwell", "H&H"],
        "workstreams": ["Project Delivery", "Management"],
        "attendance": [
            {
                "date": "2026-09-01",
                "staff": "Operator",
                "clock_in": "08:00",
                "clock_out": "17:00",
                "paid_hours": 8,
                "default_project": "Northwell",
            }
        ],
        "allocations": [],
    }


def test_single_project_day_is_default() -> None:
    state = normalize_state(_base_state())
    assert len(state["allocations"]) == 1
    assert state["allocations"][0]["project"] == "Northwell"
    assert state["allocations"][0]["basis"] == "DEFAULT"
    assert state["allocations"][0]["hours"] == 8
    rec = reconcile_state(state)[0]
    assert rec.mode == "SINGLE"
    assert rec.project_count == 1
    assert rec.reconciled


def test_existing_v1_explicit_allocation_defaults_to_explicit_basis() -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "hours": 8}
    ]
    normalized = normalize_state(state)
    assert normalized["allocations"][0]["basis"] == "EXPLICIT"


def test_non_nth_default_can_be_overridden_without_becoming_reported_project() -> None:
    state = _base_state()
    state["attendance"][0]["default_project"] = "Mobile Device Support / iPhone Support"
    state["allocations"] = [
        {
            "allocation_id": "NTH-1",
            "date": "2026-09-01",
            "staff": "Operator",
            "project": "Wave-3 Neurons & Cybernets",
            "basis": "OVERRIDE",
            "hours": 8,
            "notes": "Explicit Neuron assignment overrides non-NTH default project.",
        }
    ]
    normalized = normalize_state(state)
    assert normalized["attendance"][0]["default_project"] == "Mobile Device Support / iPhone Support"
    assert normalized["allocations"][0]["basis"] == "OVERRIDE"

    report = report_snapshot(normalized)
    assert report["paid_hours"] == 8
    assert report["allocated_hours"] == 8
    assert [row["project"] for row in report["projects"]] == ["Wave-3 Neurons & Cybernets"]
    assert "Mobile Device Support / iPhone Support" not in {row["project"] for row in report["projects"]}


def test_multi_project_day_is_normal_when_hours_reconcile() -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "H&H", "basis": "EXPLICIT", "workstream": "Management", "hours": 6.4},
        {"allocation_id": "A2", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "basis": "EXPLICIT", "workstream": "Project Delivery", "hours": 1.6},
    ]
    rec = reconcile_state(state)[0]
    assert rec.mode == "MULTI"
    assert rec.project_count == 2
    assert rec.allocated_hours == 8
    assert rec.variance == 0
    assert rec.reconciled


def test_project_report_is_sorted_and_counts_days_without_double_counting() -> None:
    state = _base_state()
    state["attendance"].append(
        {"date": "2026-09-02", "staff": "Operator", "paid_hours": 8, "default_project": "Northwell"}
    )
    state["allocations"] = [
        {"allocation_id": "Z1", "date": "2026-09-01", "staff": "Operator", "project": "Zeta", "basis": "EXPLICIT", "hours": 2},
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "Alpha", "basis": "EXPLICIT", "hours": 6},
        {"allocation_id": "A2", "date": "2026-09-02", "staff": "Operator", "project": "Alpha", "basis": "EXPLICIT", "hours": 3},
        {"allocation_id": "A3", "date": "2026-09-02", "staff": "Operator", "project": "Alpha", "basis": "EXPLICIT", "hours": 5},
    ]
    report = report_snapshot(state)
    assert report["paid_hours"] == 16
    assert report["allocated_hours"] == 16
    assert report["variance"] == 0
    assert report["multi_project_days"] == 1
    assert [row["project"] for row in report["projects"]] == ["Alpha", "Zeta"]
    alpha = report["projects"][0]
    assert alpha == {
        "project": "Alpha",
        "allocated_hours": 14.0,
        "day_count": 2,
        "staff_count": 1,
        "allocation_count": 3,
    }


def test_workbook_mode_counts_distinct_projects_not_allocation_rows(tmp_path: Path) -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "basis": "EXPLICIT", "workstream": "PM", "hours": 3},
        {"allocation_id": "A2", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "basis": "EXPLICIT", "workstream": "Configuration", "hours": 5},
    ]
    rec = reconcile_state(state)[0]
    assert rec.mode == "SINGLE"
    assert rec.project_count == 1

    out = tmp_path / "same_project_two_rows.xlsx"
    result = build_roster_workbook(state, out, require_reconciled=True)
    assert result["project_report"] == [
        {"project": "Northwell", "allocated_hours": 8.0, "day_count": 1, "staff_count": 1, "allocation_count": 2}
    ]

    wb = openpyxl.load_workbook(out, data_only=False)
    try:
        assert wb["Project Allocations"]["J1"].value == "Distinct Project First?"
        assert "COUNTIFS($B$2:B2" in wb["Project Allocations"]["J2"].value
        assert "COUNTIFS($B$2:B3" in wb["Project Allocations"]["J3"].value
        assert "$J$2:$J$3" in wb["Attendance"]["G2"].value
        assert wb["Project Allocations"].column_dimensions["J"].hidden
    finally:
        wb.close()


def test_operator_can_call_whole_day_one_project() -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "basis": "EXPLICIT", "workstream": "Project Delivery", "hours": 8}
    ]
    rec = reconcile_state(state)[0]
    assert rec.mode == "SINGLE"
    assert rec.reconciled


def test_invalid_allocation_basis_is_rejected() -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "basis": "GUESSED", "hours": 8}
    ]
    with pytest.raises(ValueError, match="allocation basis must be one of"):
        normalize_state(state)


def test_only_variance_is_reconciliation_failure() -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "hours": 5},
        {"allocation_id": "A2", "date": "2026-09-01", "staff": "Operator", "project": "H&H", "hours": 2},
    ]
    rec = reconcile_state(state)[0]
    assert rec.mode == "MULTI"
    assert not rec.reconciled
    assert rec.variance == 1


def test_allocation_without_attendance_is_rejected() -> None:
    state = _base_state()
    state["allocations"] = [
        {"date": "2026-09-02", "staff": "Operator", "project": "Northwell", "hours": 8}
    ]
    with pytest.raises(ValueError, match="allocation without attendance day"):
        normalize_state(state)


def test_generated_workbook_is_webexcel_safe_and_has_reporting_contract(tmp_path: Path) -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "H&H", "basis": "EXPLICIT", "hours": 6.4},
        {"allocation_id": "A2", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "basis": "EXPLICIT", "hours": 1.6},
    ]
    out = tmp_path / "Roster_Log_V2.xlsx"
    result = build_roster_workbook(state, out, require_reconciled=True)
    assert result["preflight"]["preflight_pass"]
    assert result["report_version"] == "roster-log-v2-project-report/v1"
    assert result["paid_hours"] == result["allocated_hours"] == 8
    assert result["multi_project_days"] == 1
    assert [row["project"] for row in result["project_report"]] == ["H&H", "Northwell"]
    assert inspect_web_excel_package(out) == []

    wb = openpyxl.load_workbook(out, data_only=False)
    try:
        assert wb.sheetnames == ["Dashboard", "Attendance", "Project Allocations", "Project Report", "Dictionaries", "Review Queue", "Read Me"]
        assert wb["Attendance"]["F1"].value == "Default / Fallback Project"
        assert "$J$2:$J$3" in wb["Attendance"]["G2"].value
        assert "$G$2:$G$3" in wb["Attendance"]["H2"].value
        assert wb["Project Allocations"]["E1"].value == "Allocation Basis"
        assert wb["Project Allocations"]["E2"].value == "EXPLICIT"
        assert wb["Project Report"]["A2"].value == "H&H"
        assert wb["Project Report"]["B2"].value == 6.4
        assert wb["Project Report"]["A3"].value == "Northwell"
        assert wb["Project Report"]["C4"].value is None
        assert wb["Review Queue"].max_row == 1
        readme = " ".join(str(wb["Read Me"].cell(r, 1).value or "") for r in range(1, wb["Read Me"].max_row + 1))
        assert "Once explicit Project Allocations exist" in readme
        assert "Project Mode counts distinct projects" in readme
        assert "Project Report is deterministic" in readme
        assert "does not manufacture an 80/20 split" in readme
    finally:
        wb.close()


def test_unreconciled_workbook_routes_variance_to_review(tmp_path: Path) -> None:
    state = _base_state()
    state["allocations"] = [
        {"allocation_id": "A1", "date": "2026-09-01", "staff": "Operator", "project": "Northwell", "hours": 7}
    ]
    out = tmp_path / "draft.xlsx"
    result = build_roster_workbook(state, out)
    assert result["unreconciled_days"] == 1
    wb = openpyxl.load_workbook(out, data_only=False)
    try:
        assert wb["Review Queue"]["C2"].value == "ALLOCATION_VARIANCE"
        assert wb["Review Queue"]["F2"].value == 1
    finally:
        wb.close()


def test_local_web_app_exposes_basis_normalization_and_deterministic_reports() -> None:
    root = Path(__file__).resolve().parents[1]
    html = (root / "web" / "roster-log-v2" / "index.html").read_text(encoding="utf-8")
    js = (root / "web" / "roster-log-v2" / "app.js").read_text(encoding="utf-8")
    assert "Default / fallback project" in html
    assert "Allocation basis" in html
    assert "OVERRIDE — correction" in html
    assert "Project report CSV" in html
    assert "Project report JSON" in html
    assert "localStorage" in js
    assert "normalizeLocalState" in js
    assert "reportSnapshot" in js
    assert "exportProjectReportCsv" in js
    assert "exportProjectReportJson" in js
    assert 'basis: "DEFAULT"' in js
    assert 'basis: "EXPLICIT"' in js
    assert "localeCompare" not in js
    assert "fetch(" not in js
