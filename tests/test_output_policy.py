"""Shared output path policy tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from triage.output_policy import (
    SourcePathWriteForbiddenError,
    allocate_run_dir,
    assert_out_dir_allowed,
    assert_output_path_allowed,
    run_id_from_dir,
)


def test_rejects_output_under_candidates():
    repo = Path(__file__).resolve().parents[1]
    inp = str(repo / "Candidates" / "in.xlsx")
    out = str(repo / "Candidates" / "out.xlsx")
    with pytest.raises(SourcePathWriteForbiddenError):
        assert_output_path_allowed(inp, output_path=out)


def test_rejects_output_under_artifact_intake():
    repo = Path(__file__).resolve().parents[1]
    inp = str(repo / "ArtifactIntake" / "2026-06-02" / "in.xlsx")
    out = str(repo / "ArtifactIntake" / "2026-06-02" / "out.xlsx")
    with pytest.raises(SourcePathWriteForbiddenError):
        assert_output_path_allowed(inp, output_path=out)


def test_rejects_output_under_references():
    repo = Path(__file__).resolve().parents[1]
    out = str(repo / "References" / "approved" / "out.xlsx")
    with pytest.raises(SourcePathWriteForbiddenError):
        assert_output_path_allowed(output_path=out)


def test_rejects_output_equals_input(tmp_path):
    p = tmp_path / "book.xlsx"
    p.write_bytes(b"x")
    with pytest.raises(SourcePathWriteForbiddenError):
        assert_output_path_allowed(str(p), output_path=str(p))


def test_accepts_outputs_subpath(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    out = tmp_path / "Outputs" / "engine" / "2026-06-04_run" / "delivery.xlsx"
    out.parent.mkdir(parents=True)
    assert_output_path_allowed(output_path=str(out))
    assert_out_dir_allowed(out.parent)


def test_accepts_artifacts_subpath(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    out_dir = tmp_path / "artifacts" / "roster_log_compare" / "2026-06-04_run"
    out_dir.mkdir(parents=True)
    assert_out_dir_allowed(out_dir)


def test_rejects_out_dir_outside_writable_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    bad = tmp_path / "Candidates" / "run"
    bad.mkdir(parents=True)
    with pytest.raises(SourcePathWriteForbiddenError):
        assert_out_dir_allowed(bad)


def test_allocate_run_dir_creates_expected_path(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    run = allocate_run_dir("admin_billing_summary", "proof")
    assert run.is_dir()
    assert run.parts[-2] == "admin_billing_summary"
    assert run.name.endswith("_proof")
    assert run_id_from_dir(run) == run.name
