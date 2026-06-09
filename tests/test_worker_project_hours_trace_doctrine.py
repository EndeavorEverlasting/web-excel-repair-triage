from __future__ import annotations

import datetime as dt

import pytest

from triage.admin_billing_summary.aggregator import build_month_summary
from triage.admin_billing_summary.reader import read_month


def _build_trace_workbook(tmp_path):
    """Build a minimal roster that exercises all project-resolution surfaces."""
    openpyxl = pytest.importorskip("openpyxl")

    wb = openpyxl.Workbook()

    live = wb.active
    live.title = "Live - May 2026"
    live.append(["Attendance Log"])
    live.append([
        "Staff Name",
        "Project",
        "May 01 - Clock In",
        "May 01 - Clock Out",
        "May 02 - Clock In",
        "May 02 - Clock Out",
        "May 03 - Clock In",
        "May 03 - Clock Out",
        "May 04 - Clock In",
        "May 04 - Clock Out",
    ])
    live.append([
        "Richard Perez",
        "Live Default Project",
        dt.time(9, 0),
        dt.time(17, 0),
        dt.time(9, 0),
        dt.time(17, 0),
        dt.time(9, 0),
        dt.time(17, 0),
        dt.time(9, 0),
        dt.time(17, 0),
    ])

    worked = wb.create_sheet("Worked Projects - May 2026")
    worked.append(["Worked Projects"])
    worked.append([
        "Staff Name",
        "Default Project",
        dt.datetime(2026, 5, 1),
        dt.datetime(2026, 5, 2),
        dt.datetime(2026, 5, 3),
        dt.datetime(2026, 5, 4),
    ])
    worked.append([
        "Richard Perez",
        "Worked Default",
        "Worked Project",
        "Worked Project Overridden",
        "",
        "",
    ])

    assignments = wb.create_sheet("Assignments - May 2026")
    assignments.append(["May 2026 - Project Assignments"])
    assignments.append([
        "Staff Name",
        "Default Project",
        dt.datetime(2026, 5, 1),
        dt.datetime(2026, 5, 2),
        dt.datetime(2026, 5, 3),
        dt.datetime(2026, 5, 4),
    ])
    assignments.append([
        "Richard Perez",
        "Assignment Default",
        "Assignment Ignored By Worked",
        "Assignment Ignored By Override",
        "Assignment Project",
        "",
    ])
    assignments.append([])
    assignments.append(["Overrides (only if different from Default Project)"])
    assignments.append(["Override Staff Name", "Override Date", "Override Project", "Notes"])
    assignments.append([
        "Richard Perez",
        dt.datetime(2026, 5, 2),
        "Override Project",
        "Richard-reviewed override",
    ])

    path = tmp_path / "worker_trace_roster.xlsx"
    wb.save(path)
    return path


def test_read_month_resolves_worker_project_by_date_with_full_precedence(tmp_path):
    """A worker's project is resolved per date, not from one monthly default."""
    path = _build_trace_workbook(tmp_path)

    records, warnings, malformed = read_month(path, "2026-05")

    assert warnings == []
    assert malformed == []
    assert len(records) == 4

    by_day = {record.date.day: record for record in records}

    assert by_day[1].project == "Worked Project"
    assert by_day[1].project_source == "worked"

    assert by_day[2].project == "Override Project"
    assert by_day[2].project_source == "override"
    assert "Richard-reviewed override" in by_day[2].note

    assert by_day[3].project == "Assignment Project"
    assert by_day[3].project_source == "assignment"

    assert by_day[4].project == "Live Default Project"
    assert by_day[4].project_source == "live_default"

    assert {record.net_hours for record in records} == {7.0}


def test_month_summary_traces_worker_hours_by_project(tmp_path):
    """Worker/project rollup must preserve multiple projects for one worker."""
    path = _build_trace_workbook(tmp_path)

    summary = build_month_summary(str(path), "2026-05")

    rich_rows = [row for row in summary.tech_project_rows if row.tech == "Richard Perez"]
    assert len(rich_rows) == 4

    hours_by_project = {row.project: row.net_hours for row in rich_rows}
    assert hours_by_project == {
        "Worked Project": 7.0,
        "Override Project": 7.0,
        "Assignment Project": 7.0,
        "Live Default Project": 7.0,
    }

    tech_summary = [row for row in summary.tech_rows if row.tech == "Richard Perez"]
    assert len(tech_summary) == 1
    assert tech_summary[0].worked_days == 4
    assert tech_summary[0].net_hours == pytest.approx(28.0)
    assert "Override Project" in tech_summary[0].projects
    assert "Worked Project" in tech_summary[0].projects
