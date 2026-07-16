"""Evidence-pack exact reconciliation and chart-reference guards."""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from tests.fixtures.nw_prj_neuron_track_hours.bonita_fixtures import build_bonita_fixtures
from triage.nw_prj_neuron_track_hours.bonita_resolver import resolve_bonita_shifts
from triage.nw_prj_neuron_track_hours.evidence_pack_cli import run

MONTHS = ["2026-04", "2026-05"]


def _roster(tmp_path: Path) -> Path:
    return build_bonita_fixtures(tmp_path / "fixtures")["roster"]


def _allocation_with_wrong_hours(roster: Path, path: Path) -> None:
    resolution = resolve_bonita_shifts(str(roster), MONTHS)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Allocation"
    ws.append([
        "DATE", "DAY", "TECH NAME", "START TIME", "END TIME", "TOTAL HOURS",
        "PROJECT NAME", "TASK / ASSIGNMENT TYPE", "SUPPORTING WORK / NOTES",
    ])
    for index, shift in enumerate(resolution.shifts):
        ws.append([
            shift.date,
            shift.day,
            shift.tech,
            shift.start_time,
            shift.end_time,
            shift.total_hours + (1 if index == 0 else 0),
            shift.project_name,
            "Configurations",
            "",
        ])
    wb.save(path)
    wb.close()


def test_strict_allocation_rejects_date_tech_match_with_wrong_hours(tmp_path: Path) -> None:
    roster = _roster(tmp_path)
    allocation = tmp_path / "wrong-hours.xlsx"
    _allocation_with_wrong_hours(roster, allocation)
    with pytest.raises(ValueError, match=r"exactly by Date \+ Tech \+ Hours"):
        run(
            roster_log=str(roster),
            allocation_source=str(allocation),
            out_dir=str(tmp_path / "out"),
            months=MONTHS,
            repo_root=Path(__file__).resolve().parents[1],
        )


def test_visual_summary_charts_reference_correct_tables(tmp_path: Path) -> None:
    roster = _roster(tmp_path)
    manifest = run(
        roster_log=str(roster),
        out_dir=str(tmp_path / "out"),
        months=MONTHS,
        repo_root=Path(__file__).resolve().parents[1],
    )
    wb = openpyxl.load_workbook(manifest["outputs"]["workbook"])
    charts = wb["Visual Summary"]._charts
    assert len(charts) == 2
    tech, task = charts
    assert tech.series[0].val.numRef.f.startswith("'Visual Summary'!$B$8:$B$")
    assert tech.series[0].cat.numRef.f.startswith("'Visual Summary'!$A$8:$A$")
    assert task.series[0].val.numRef.f.startswith("'Visual Summary'!$F$8:$F$")
    assert task.series[0].cat.numRef.f.startswith("'Visual Summary'!$E$8:$E$")
    wb.close()
