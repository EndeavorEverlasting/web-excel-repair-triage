"""Admin Billing Summary (My Preferred Format) - fixture-only tests."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import openpyxl
import pytest

from triage.admin_billing_summary.aggregator import build_month_summary
from triage.admin_billing_summary.cli import run
from tests.fixtures.admin_billing_summary.builders import build

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "admin_billing_summary"


@pytest.fixture(scope="module")
def fixtures():
    return build(FIXTURE_DIR)


@pytest.fixture(scope="module")
def april(fixtures):
    return build_month_summary(str(fixtures["roster"]), "2026-04")


@pytest.fixture(scope="module")
def generated(fixtures, tmp_path_factory):
    out = tmp_path_factory.mktemp("abs_out")
    return run(
        roster_log=str(fixtures["roster"]),
        out_dir=str(out),
        months=["2026-04", "2026-05"],
        prior=str(fixtures["prior"]),
        websafe=True,
        repo_root=REPO_ROOT,
    )


# 1 ─ CLI import smoke
def test_cli_imports():
    mod = importlib.import_module("triage.admin_billing_summary.cli")
    assert hasattr(mod, "run") and hasattr(mod, "main")


# 2 ─ Override beats worked-project
def test_override_beats_worked(april):
    rec = [r for r in april.records if r.tech == "Mensa Dee" and r.date.day == 3]
    assert len(rec) == 1
    assert rec[0].project == "Neuron Deployments"
    assert rec[0].project_source == "override"


# 3 ─ Worked-project beats Live default (both directions)
def test_worked_beats_default(april):
    mensa2 = [r for r in april.records if r.tech == "Mensa Dee" and r.date.day == 2][0]
    assert mensa2.project == "Projects Team" and mensa2.project_source == "worked"
    rao1 = [r for r in april.records if r.tech == "Rao Tully" and r.date.day == 1][0]
    assert rao1.project == "Neuron Deployments" and rao1.project_source == "worked"


# 4 ─ Net = gross - lunch; long shift flagged
def test_net_hours_and_long_shift(april):
    solo = [r for r in april.records if r.tech == "Solo Vant"][0]
    assert solo.gross_span == 17.0
    assert solo.lunch == 1.0
    assert solo.net_hours == 16.0
    assert solo.long_shift is True


# 5 ─ Project Summary rollup
def test_project_summary(april):
    by = {r.project: r for r in april.project_rows}
    assert by["Neuron Deployments"].net_hours == 40.0
    assert by["Neuron Deployments"].worked_days == 4
    assert by["Neuron Deployments"].tech_count == 3
    assert by["Projects Team"].net_hours == 8.0


# 6 ─ Tech Summary lists multiple projects
def test_tech_summary_multiproject(april):
    mensa = [r for r in april.tech_rows if r.tech == "Mensa Dee"][0]
    assert mensa.projects == "Neuron Deployments, Projects Team"


# 7 ─ Tech Project Summary splits by project
def test_tech_project_summary(april):
    pairs = {(r.tech, r.project): r for r in april.tech_project_rows}
    assert (("Mensa Dee", "Neuron Deployments")) in pairs
    assert (("Mensa Dee", "Projects Team")) in pairs
    assert pairs[("Mensa Dee", "Projects Team")].net_hours == 8.0


# 8 ─ Executive metrics
def test_executive_metrics(april):
    assert april.total_net == 48.0
    assert april.total_gross == 53.0
    assert april.projects_reflected == 2
    assert april.techs_reflected == 3


# 9 ─ Workbook tab set + both charts
def test_workbook_tabs_and_charts(generated):
    wb_path = generated["per_month"]["2026-04"]["workbook"]
    wb = openpyxl.load_workbook(wb_path)  # not read_only, so charts load
    expected = ["Executive Summary", "Project Summary", "Tech Summary",
                "Tech Project Summary", "Trucking Reference", "Billing Bucket Snapshot",
                "Time Alignment", "Roster QA - Internal", "Daily Detail - Internal",
                "Build Notes", "Next Chat Prompt", "Apr 26"]
    assert wb.sheetnames == expected
    assert len(wb["Project Summary"]._charts) == 1
    assert len(wb["Tech Project Summary"]._charts) == 1
    wb.close()


# 10 ─ Apr 26 tracker is Neuron-only
def test_april_tracker_neuron_only(generated):
    wb = openpyxl.load_workbook(generated["per_month"]["2026-04"]["workbook"], read_only=True)
    ws = wb["Apr 26"]
    rows = [r for r in ws.iter_rows(min_row=3, values_only=True) if r[1]]
    wb.close()
    assert len(rows) == 4  # Mensa(Apr01,Apr03), Rao(Apr01), Solo(Apr02); Mensa Apr02=Projects Team excluded
    assert all(str(r[5]).startswith("Northwell - Neuron") for r in rows)


# 11 ─ May 26 tracker present and Neuron-only
def test_may_tracker(generated):
    wb = openpyxl.load_workbook(generated["per_month"]["2026-05"]["workbook"], read_only=True)
    assert "May 26" in wb.sheetnames
    ws = wb["May 26"]
    rows = [r for r in ws.iter_rows(min_row=3, values_only=True) if r[1]]
    wb.close()
    assert len(rows) == 2  # Mensa May02, Solo May02; Mensa May01=iPhone Support excluded


# 12 ─ Preflight passes
def test_preflight_passes(generated):
    assert generated["per_month"]["2026-04"]["websafe_preflight_pass"] is True
    assert generated["per_month"]["2026-05"]["websafe_preflight_pass"] is True


# 13 ─ Delta vs prior April copy
def test_delta_vs_prior(generated):
    delta = generated["per_month"]["2026-04"]["delta_vs_prior"]
    assert delta is not None
    by = {d["Project"]: d for d in delta["by_project"]}
    assert by["Neuron Deployments"]["Delta"] == 13.0  # current 40 - prior 27
    assert delta["total_net_delta"] == 13.0           # current 48 - prior 35
