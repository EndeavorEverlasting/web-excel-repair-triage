"""Cybernet target sprint contract, resolver, and CLI tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from triage.cybernet_targets.cli import run
from triage.cybernet_targets.config import load_scope, normalize_site, targets_schema
from triage.cybernet_targets.compare import carry_forward_manual_status
from triage.cybernet_targets.extractor import (
    extract_wave3_targets,
    read_all_wave_workbook,
    read_sprint_dashboard,
)
from triage.cybernet_targets.resolver import reconcile_amb, resolve_sprint_targets
from tests.fixtures.cybernet_targets.fixtures import build_all_fixtures

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "cybernet_targets"
REAL_ALL_WAVE = REPO_ROOT / "Candidates/configuration targets/ALL WAVE ANESTHESIA MACHINES for Tim 6-1-2026.xlsx"
REAL_DASH = REPO_ROOT / "Candidates/configuration targets/Targets_Wave3_Live_Dashboard_WebExcelSafe_2026-05-26.xlsx"
REAL_DEPLOY = REPO_ROOT / "Candidates/configuration targets/Active Deployment Tracker 2026-05-06 6-1-2026.xlsx"


@pytest.fixture(scope="module")
def fixture_paths(tmp_path_factory):
    base = FIXTURE_DIR
    if not (base / "mini_all_wave.xlsx").exists():
        build_all_fixtures(base)
    return build_all_fixtures(base)


def test_schema_loads():
    schema = targets_schema()
    assert schema["schema_version"] == "cybernet_targets_sprint_v1"
    assert "HH" in schema["sprint_site_tabs"]
    assert "00_CF_Dictionary" in schema["required_sheets"]


def test_scope_config_loads():
    scope = load_scope()
    assert scope["active_scope"] == ["HH", "JTM", "AMB", "SSUH"]
    assert 1 in scope["excluded_waves"]
    assert scope["reader_anchors"]["neuron_cybernet"]["header_row"] == 6


def test_site_alias_ssh_to_ssuh():
    aliases = load_scope()["site_aliases"]
    assert normalize_site("SSH", aliases) == "SSUH"
    assert normalize_site("Wave 3 AMB", aliases) == "AMB"


def test_wave_exclusion(fixture_paths):
    scope = load_scope()
    data = read_all_wave_workbook(fixture_paths["all_wave"], scope)
    targets = extract_wave3_targets(data, scope)
    waves = {t.wave for t in targets}
    assert "1" not in waves
    assert "2" not in waves
    sites = {t.source_site for t in targets}
    assert "Out of Scop HH" not in sites


def test_mini_sprint_target_counts(fixture_paths):
    scope = load_scope()
    data = read_all_wave_workbook(fixture_paths["all_wave"], scope)
    wave3 = extract_wave3_targets(data, scope)
    sprint = read_sprint_dashboard(fixture_paths["sprint_dashboard"], scope)
    rpt = resolve_sprint_targets(wave3, data, sprint, scope)
    cmp = carry_forward_manual_status(rpt.targets, sprint, scope)
    counts = {s: sum(1 for t in cmp.targets if t.site == s) for s in scope["active_scope"]}
    assert counts["HH"] == 2
    assert counts["JTM"] == 2
    assert counts["AMB"] == 2
    assert counts["SSUH"] == 2


def test_amb_reconciliation_three_layers(fixture_paths):
    scope = load_scope()
    data = read_all_wave_workbook(fixture_paths["all_wave"], scope)
    wave3 = extract_wave3_targets(data, scope)
    sprint = read_sprint_dashboard(fixture_paths["sprint_dashboard"], scope)
    rpt = resolve_sprint_targets(wave3, data, sprint, scope)
    layers = {r.layer for r in rpt.amb_reconciliation}
    assert "sprint_consolidated" in layers
    assert "wave3_cybernet" in layers
    assert "ane_wave2_hardware" in layers
    assert len(rpt.amb_raw) == 3
    assert any("amb_count_mismatch" in w for w in rpt.warnings)


def test_carry_forward_imaged(fixture_paths):
    scope = load_scope()
    data = read_all_wave_workbook(fixture_paths["all_wave"], scope)
    wave3 = extract_wave3_targets(data, scope)
    sprint = read_sprint_dashboard(fixture_paths["sprint_dashboard"], scope)
    rpt = resolve_sprint_targets(wave3, data, sprint, scope)
    cmp = carry_forward_manual_status(rpt.targets, sprint, scope)
    hh_or8 = next(t for t in cmp.targets if t.site == "HH" and t.location == "OR 8")
    assert hh_or8.imaged == "Yes"
    assert hh_or8.labeled == "Yes"


def test_ssuh_replaces_placeholder_locations(fixture_paths):
    scope = load_scope()
    data = read_all_wave_workbook(fixture_paths["all_wave"], scope)
    wave3 = extract_wave3_targets(data, scope)
    sprint = read_sprint_dashboard(fixture_paths["sprint_dashboard"], scope)
    rpt = resolve_sprint_targets(wave3, data, sprint, scope)
    ssuh_locs = {t.location for t in rpt.targets if t.site == "SSUH"}
    assert "CATH LAB" in ssuh_locs
    assert "MRI" in ssuh_locs
    assert "Imaging Pipeline" not in ssuh_locs


def test_cli_on_fixtures(fixture_paths, tmp_path):
    out = tmp_path / "Outputs" / "cybernet_targets" / "test_run"
    out.mkdir(parents=True)
    manifest = run(
        all_wave=str(fixture_paths["all_wave"]),
        existing_dashboard=str(fixture_paths["sprint_dashboard"]),
        deployment_tracker=str(fixture_paths["deployment_tracker"]),
        out_dir=str(out),
        as_of="2026-06-01-test",
        websafe=True,
        repo_root=REPO_ROOT,
    )
    assert manifest["total_active_targets"] == 8
    assert Path(manifest["outputs"]["workbook"]).exists()
    assert Path(manifest["outputs"]["amb_reconciliation_csv"]).exists()


@pytest.mark.skipif(not REAL_ALL_WAVE.exists(), reason="Real Candidates workbooks not present")
def test_real_workbook_93_targets(tmp_path):
    out = tmp_path / "Outputs" / "cybernet_targets" / "real_run"
    out.mkdir(parents=True)
    manifest = run(
        all_wave=str(REAL_ALL_WAVE),
        existing_dashboard=str(REAL_DASH),
        deployment_tracker=str(REAL_DEPLOY) if REAL_DEPLOY.exists() else None,
        out_dir=str(out),
        as_of="2026-06-01",
        websafe=True,
        repo_root=REPO_ROOT,
    )
    assert manifest["total_active_targets"] == 93
    assert manifest["site_counts"]["HH"] == 24
    assert manifest["site_counts"]["JTM"] == 23
    assert manifest["site_counts"]["AMB"] == 6
    assert manifest["site_counts"]["SSUH"] == 40
    assert manifest["amb_counts"]["wave3_cybernet_raw"] == 11
    ssuh_targets = json.loads(Path(manifest["outputs"]["targets_json"]).read_text(encoding="utf-8"))
    ssuh = [t for t in ssuh_targets if t["Site"] == "SSUH"]
    assert all(t["Location"] != "Imaging Pipeline" for t in ssuh)
    assert manifest["blank_hostnames"] > 0
