"""Admin Billing Summary — OpenAI-format fixture tests."""
from __future__ import annotations

import importlib
import json
import zipfile
from pathlib import Path

import openpyxl
import pytest

from triage.admin_billing_summary.aggregator import build_month_summary
from triage.admin_billing_summary.cli import run
from triage.admin_billing_summary.exporter import build_workbook
from triage.admin_billing_summary.preflight import preflight_billing_summary
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


def test_cli_imports():
    mod = importlib.import_module("triage.admin_billing_summary.cli")
    assert hasattr(mod, "run") and hasattr(mod, "main")


def test_override_beats_worked(april):
    rec = [r for r in april.records if r.tech == "Mensa Dee" and r.date.day == 3]
    assert len(rec) == 1
    assert rec[0].project == "Neuron Deployments"
    assert rec[0].project_source == "override"


def test_worked_beats_default(april):
    mensa2 = [r for r in april.records if r.tech == "Mensa Dee" and r.date.day == 2][0]
    assert mensa2.project == "Projects Team" and mensa2.project_source == "worked"
    rao1 = [r for r in april.records if r.tech == "Rao Tully" and r.date.day == 1][0]
    assert rao1.project == "Neuron Deployments" and rao1.project_source == "worked"


def test_net_hours_and_long_shift(april):
    solo = [r for r in april.records if r.tech == "Solo Vant"][0]
    assert solo.gross_span == 17.0
    assert solo.lunch == 1.0
    assert solo.net_hours == 16.0
    assert solo.long_shift is True


def test_project_summary(april):
    by = {r.project: r for r in april.project_rows}
    assert by["Neuron Deployments"].net_hours == 40.0
    assert by["Projects Team"].net_hours == 8.0


def test_executive_metrics(april):
    assert april.total_net == 48.0
    assert april.techs_reflected == 3


def test_internal_tabs_and_tables(generated):
    internal = generated["per_month"]["2026-04"]["outputs"]["internal"]["workbook"]
    wb = openpyxl.load_workbook(internal)
    neuron_hours = "April Neuron Hours"
    expected = [
        "Start Here", "Executive Dashboard", "Monthly Summary", "Project Summary",
        "Tech Summary", "Tech Project Summary", neuron_hours,
        "Apr 26", "Review Flags", "CF Dictionary", "WebExcel QC",
    ]
    assert wb.sheetnames == expected
    assert len(wb["Project Summary"].tables) >= 1
    assert len(wb["Project Summary"]._charts) == 1
    with zipfile.ZipFile(internal) as z:
        assert len([n for n in z.namelist() if n.startswith("xl/tables/")]) >= 9
    wb.close()


def test_client_tabs_clean(generated):
    client = generated["per_month"]["2026-04"]["outputs"]["client"]["workbook"]
    wb = openpyxl.load_workbook(client)
    assert "Review Flags" not in wb.sheetnames
    assert "WebExcel QC" not in wb.sheetnames
    assert "Apr 26" in wb.sheetnames
    wb.close()


def test_neuron_detail_matches_summary(april, tmp_path):
    out = tmp_path / "internal.xlsx"
    build_workbook(april, str(out), variant="internal")
    wb = openpyxl.load_workbook(out, data_only=True)
    ws = wb["April Neuron Hours"]
    detail_net = 0.0
    for row in ws.iter_rows(min_row=6, values_only=True):
        if row[-1] is not None:
            detail_net += float(row[-1])
    wb.close()
    assert round(detail_net, 2) == april.net_for_bucket("Neurons")


def test_bonita_tab_neuron_only(generated):
    wb = openpyxl.load_workbook(
        generated["per_month"]["2026-04"]["outputs"]["internal"]["workbook"],
        read_only=True,
    )
    ws = wb["Apr 26"]
    rows = [r for r in ws.iter_rows(min_row=3, values_only=True) if r[1]]
    wb.close()
    assert len(rows) == 4
    assert all(str(r[5]).startswith("Northwell - Neuron") for r in rows)


def test_preflight_passes(generated):
    for variant in ("internal", "client"):
        assert generated["per_month"]["2026-04"]["outputs"][variant]["websafe_preflight_pass"] is True
        assert generated["per_month"]["2026-05"]["outputs"][variant]["websafe_preflight_pass"] is True


def test_delta_vs_prior(generated):
    delta = generated["per_month"]["2026-04"]["delta_vs_prior"]
    assert delta is not None
    by = {d["Project"]: d for d in delta["by_project"]}
    assert by["Neuron Deployments"]["Delta"] == 13.0
    assert delta["total_net_delta"] == 13.0


def test_no_repair_inlinestr_on_export(tmp_path, april):
    out = tmp_path / "test.xlsx"
    build_workbook(april, str(out), variant="client")
    pf = preflight_billing_summary(str(out), variant="client", expect_neuron_tab="Apr 26")
    assert pf["preflight_pass"] is True
    assert "inlineStr" not in pf.get("token_failures", [])
