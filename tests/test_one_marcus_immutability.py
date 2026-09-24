"""Tests for One Marcus source immutability guards."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.one_marcus_recon import fixtures as fx
from triage.one_marcus_recon.baseline_gate import run_baseline_gate
from triage.one_marcus_recon.exporter import run_generate, run_recon
from triage.one_marcus_recon.integrated_guard import IntegratedWorkbookError, assert_generate_allowed
from triage.one_marcus_recon.path_guard import SourcePathWriteForbiddenError, assert_output_path_allowed


def test_rejects_output_under_candidates():
    repo = Path(__file__).resolve().parents[1]
    inp = str(repo / "Candidates" / "inventory recon" / "in.xlsx")
    out = str(repo / "Candidates" / "inventory recon" / "out.xlsx")
    with pytest.raises(SourcePathWriteForbiddenError):
        assert_output_path_allowed(inp, out)


def test_rejects_output_equals_input(tmp_path):
    p = tmp_path / "book.xlsx"
    p.write_bytes(b"x")
    with pytest.raises(SourcePathWriteForbiddenError):
        assert_output_path_allowed(str(p), str(p))


def test_generate_refuses_multi_sheet_integrated(tmp_path):
    src = fx.make_stale_recon(str(tmp_path / "integrated.xlsx"))
    with pytest.raises(IntegratedWorkbookError):
        assert_generate_allowed(src)


def test_generate_allowed_on_two_sheet_fixture(tmp_path):
    src = fx.make_integrated_source(str(tmp_path / "mini.xlsx"))
    names = assert_generate_allowed(src)
    assert len(names) == 2


def test_relink_preserves_sheet_count(stale_input, tmp_path):
    from triage.one_marcus_recon import formula_relink as fr
    from triage.one_marcus_recon.package_cleanup import Package

    out = str(tmp_path / "out" / "relink.xlsx")
    before = fr.workbook_sheet_names(Package.from_path(stale_input).text("xl/workbook.xml"))
    result = run_recon(stale_input, output_path=out, cli_date="auto")
    after = fr.workbook_sheet_names(Package.from_path(out).text("xl/workbook.xml"))
    assert len(after) == len(before)
    assert result.report.baseline_compare_pass is True


def test_baseline_gate_fails_when_sheets_deleted(tmp_path):
    base = fx.make_stale_recon(str(tmp_path / "base.xlsx"))
    # Two-sheet stub simulates generator amputation.
    stub = fx.make_integrated_source(str(tmp_path / "stub.xlsx"))
    gate = run_baseline_gate(base, stub)
    assert gate.sheets_deleted
    assert gate.baseline_compare_pass is False


def test_cli_rejects_candidates_output():
    repo = Path(__file__).resolve().parents[1]
    inp = str(repo / "Outputs" / "_test_guard_in.xlsx")
    out = str(repo / "Candidates" / "inventory recon" / "_test_guard_out.xlsx")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "triage.one_marcus_recon.cli",
            "relink",
            "--input",
            inp,
            "--output",
            out,
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["error"] == "source_path_write_forbidden"


@pytest.fixture
def stale_input(tmp_path):
    src = tmp_path / "1 Marcus Recon Integrated 5-28-2026.xlsx"
    return fx.make_stale_recon(str(src))
