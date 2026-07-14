"""Harness diagnostics and pipeline execution tests."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from triage.path_policy import repo_root
from triage.harness.registry import load_workflows, get_workflow
from triage.harness.doctor import run_doctor
from triage.harness.runner import get_git_state
from triage.harness.cli import parse_remaining_args


def test_harness_registries_load_and_are_valid():
    wfs = load_workflows()
    assert len(wfs) > 0
    
    # Verify our wired workflow roster-review-blank is present
    blank_wf = get_workflow("roster-review-blank")
    assert blank_wf is not None
    assert blank_wf["id"] == "roster-review-blank"
    assert "months" in blank_wf["inputs"]
    assert "output" in blank_wf["outputs"]


def test_doctor_diagnostics_healthy():
    # The workspace should be healthy
    healthy = run_doctor()
    assert healthy is True


def test_git_state_retrieval():
    state = get_git_state()
    assert "commit" in state
    assert "branch" in state
    assert "dirty" in state
    assert isinstance(state["dirty"], bool)


def test_cli_remaining_args_parser():
    argv = ["--months", "2026-04", "2026-05", "--output", "Outputs/test.xlsx", "--dry-run"]
    params = parse_remaining_args(argv)
    
    assert params["months"] == ["2026-04", "2026-05"]
    assert params["output"] == "Outputs/test.xlsx"
    assert params["dry-run"] is True


def test_harness_workflow_run_e2e_fixture(tmp_path):
    from triage.harness.runner import run_workflow, validate_run, generate_report, generate_handoff
    
    test_out = tmp_path / "test_blank.xlsx"
    params = {
        "months": ["2026-04"],
        "output": str(test_out),
    }
    
    # Run the workflow via our runner
    run_dir = run_workflow("roster-review-blank", params)
    
    # Check that outputs and metadata files were generated
    assert test_out.is_file()
    assert run_dir.is_dir()
    assert (run_dir / "run-context.json").is_file()
    
    # Validate the run
    val_report = validate_run(run_dir)
    # openpyxl-generated blank sheets contain inlineStr and absolute target paths
    assert val_report["passed"] is False
    assert len(val_report["issues"]) > 0
    assert (run_dir / "validation-report.json").is_file()
    
    # Generate report
    report_file = generate_report(run_dir)
    assert report_file.is_file()
    assert "Execution Context" in report_file.read_text(encoding="utf-8")
    
    # Generate handoff
    handoff_file = generate_handoff(run_dir)
    assert handoff_file.is_file()
    assert "Session Handoff Digest" in handoff_file.read_text(encoding="utf-8")

