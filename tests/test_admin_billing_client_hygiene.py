"""Client-facing billing exports must not expose internal timekeeping evidence."""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

from tests.fixtures.admin_billing_summary.builders import build
from triage.admin_billing_summary.cli import run
from triage.admin_billing_summary.preflight import (
    client_text_violations,
    preflight_billing_summary,
)
from triage.artifact_profiles import load_profile
from triage.xlsx_utils import fix_inlinestr


def _all_text(path: str) -> str:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    try:
        values = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                values.extend(str(v) for v in row if v is not None)
        return "\n".join(values)
    finally:
        wb.close()


def _april_manifest(tmp_path: Path) -> dict:
    fixtures = build(tmp_path / "fixtures")
    return run(
        roster_log=str(fixtures["roster"]),
        out_dir=str(tmp_path / "out"),
        months=["2026-04"],
        websafe=True,
    )


def test_client_export_excludes_employee_and_punch_detail(tmp_path):
    manifest = _april_manifest(tmp_path)
    client = manifest["per_month"]["2026-04"]["outputs"]["client"]
    wb = openpyxl.load_workbook(client["workbook"], data_only=True, read_only=True)
    try:
        assert wb.sheetnames == [
            "Start Here",
            "Executive Dashboard",
            "Monthly Summary",
            "Project Summary",
            "Apr 26",
        ]
    finally:
        wb.close()

    text = _all_text(client["workbook"])
    for fixture_person in ("Mensa Dee", "Rao Tully", "Solo Vant"):
        assert fixture_person not in text
    for internal_label in (
        "Clock In",
        "Clock Out",
        "Review Net Hours",
        "Review row count",
        "Source roster",
        "Override > Worked > Assignment > Live default",
    ):
        assert internal_label not in text
    assert client["websafe_preflight_pass"] is True
    preflight = json.loads(Path(client["preflight_json"]).read_text(encoding="utf-8"))
    assert preflight["client_hygiene_pass"] is True


def test_client_export_states_support_and_historical_period_boundary(tmp_path):
    manifest = _april_manifest(tmp_path)
    client = manifest["per_month"]["2026-04"]["outputs"]["client"]
    text = _all_text(client["workbook"])
    assert "Client billing support copy" in text
    assert "not a standalone invoice or new billing request" in text
    assert "not reopened, rebilled, or superseded" in text
    assert "retained internally and excluded from this client copy" in text


def test_internal_export_retains_audit_detail(tmp_path):
    manifest = _april_manifest(tmp_path)
    internal = manifest["per_month"]["2026-04"]["outputs"]["internal"]
    wb = openpyxl.load_workbook(internal["workbook"], read_only=True)
    try:
        assert "Tech Summary" in wb.sheetnames
        assert "Tech Project Summary" in wb.sheetnames
        assert "April Neuron Hours" in wb.sheetnames
        assert "Review Flags" in wb.sheetnames
    finally:
        wb.close()


def test_client_profile_omits_technician_tabs():
    prof = load_profile("admin_billing_summary")
    assert prof.variant == "client"
    assert "Tech Summary" not in prof.required_sheets
    assert "Tech Project Summary" not in prof.required_sheets
    assert "Start Here" in prof.required_sheets
    assert "{{expect_neuron_tab}}" in prof.required_sheets


def test_client_text_violations_decode_xml_entities():
    raw = "Override &gt; Worked &gt; Assignment &gt; Live default"
    hits = client_text_violations(raw)
    assert "Override > Worked > Assignment > Live default" in hits
    assert client_text_violations("Clock In / Clock Out") == ["Clock In", "Clock Out"]
    assert client_text_violations("aggregate Neuron support only") == []
    assert "TECH" in client_text_violations("<si><t>TECH</t></si>")
    assert "TECH" not in client_text_violations("Start Here / technician punch detail")


def test_client_preflight_rejects_bonita_punch_headers(tmp_path):
    manifest = _april_manifest(tmp_path)
    client = manifest["per_month"]["2026-04"]["outputs"]["client"]["workbook"]
    wb = openpyxl.load_workbook(client)
    try:
        wb["Apr 26"]["B1"] = "TECH"
        wb["Apr 26"]["G1"] = "ASSIGNMENT"
        wb.save(client)
    finally:
        wb.close()
    fix_inlinestr(client)
    pf = preflight_billing_summary(client, variant="client", expect_neuron_tab="Apr 26")
    assert pf["client_hygiene_pass"] is False
    failures = "\n".join(pf["client_hygiene_failures"])
    assert "TECH" in failures
    assert "ASSIGNMENT" in failures
