"""tests/test_harness_cli.py
---------------------------
Synthetic tests for the harness spine CLI: doctor, workflows, explain, run, validate.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from triage.harness.cli import main as cli_main
from triage.harness.doctor import run_doctor
from triage.harness.context import (
    create_run_context,
    complete_run_context,
    load_run_context,
    PROOF_LEVELS,
    PROOF_RANK,
    proof_level_gte,
)
from triage.harness.validate import run_validation
from triage.harness.output_policy import (
    is_source_path,
    is_output_path,
    validate_output_allocation,
    refuse_source_writes,
)
from triage.harness.registry import (
    load_artifact_registry,
    load_workflow_registry,
    get_workflow,
    get_artifact,
    list_workflows,
    list_artifacts,
)
from triage.path_policy import repo_root


# ── Registry tests ────────────────────────────────────────────────


class TestArtifactRegistry:
    def test_loads(self):
        reg = load_artifact_registry()
        assert "artifacts" in reg
        assert "version" in reg

    def test_has_known_artifacts(self):
        reg = load_artifact_registry()
        arts = reg["artifacts"]
        assert "bonita_neuron_track_hours" in arts
        assert "blank_shell_workbook" in arts
        assert "validation_report" in arts
        assert "manifest" in arts

    def test_get_artifact(self):
        art = get_artifact("bonita_neuron_track_hours")
        assert art is not None
        assert art["type"] == "workbook"
        assert art["delivery"] is True
        assert "manifest.json" in art["required_sidecars"]

    def test_list_artifacts(self):
        arts = list_artifacts()
        assert len(arts) >= 6


class TestWorkflowRegistry:
    def test_loads(self):
        reg = load_workflow_registry()
        assert "workflows" in reg
        assert "version" in reg

    def test_has_known_workflows(self):
        wfs = list_workflows()
        assert "roster-review-blank" in wfs
        assert "bonita-neuron-track-hours" in wfs
        assert "roster-diagnostic" in wfs

    def test_get_workflow(self):
        wf = get_workflow("roster-review-blank")
        assert wf is not None
        assert wf["direction"] == "roster_to_admin"
        assert wf["proof_ceiling"] == "package"

    def test_unknown_workflow_returns_none(self):
        assert get_workflow("nonexistent") is None


# ── Run context tests ─────────────────────────────────────────────


class TestRunContext:
    def test_create_and_load(self):
        ctx = create_run_context(
            workflow_id="roster-review-blank",
            input_paths=[],
            requested_proof_level="harness",
            metadata={"months": ["2026-04", "2026-05"], "synthetic": True},
        )
        assert "run_id" in ctx
        assert len(ctx["run_id"]) == 8
        assert ctx["workflow_id"] == "roster-review-blank"
        assert ctx["requested_proof_level"] == "harness"
        assert ctx["branch"] != ""
        assert ctx["commit_sha"] != ""
        assert isinstance(ctx["dirty"], bool)

        # Verify file was written
        run_dir = repo_root() / ctx["output_dir"]
        assert (run_dir / "run-context.json").exists()

        # Verify round-trip
        loaded = load_run_context(ctx["run_id"])
        assert loaded is not None
        assert loaded["run_id"] == ctx["run_id"]

        # Cleanup
        shutil.rmtree(run_dir, ignore_errors=True)

    def test_complete_run_context(self):
        ctx = create_run_context(
            workflow_id="roster-review-blank",
            input_paths=[],
            requested_proof_level="harness",
        )
        ctx = complete_run_context(ctx, "build")
        assert ctx["completed_at"] is not None
        assert ctx["achieved_proof_level"] == "build"

        loaded = load_run_context(ctx["run_id"])
        assert loaded is not None
        assert loaded["achieved_proof_level"] == "build"

        # Cleanup
        shutil.rmtree(repo_root() / ctx["output_dir"], ignore_errors=True)

    def test_invalid_proof_level_raises(self):
        with pytest.raises(ValueError, match="Unknown proof level"):
            create_run_context(
                workflow_id="test",
                input_paths=[],
                requested_proof_level="nonexistent",
            )


class TestProofLevels:
    def test_all_levels_defined(self):
        assert len(PROOF_LEVELS) == 12
        assert PROOF_LEVELS[0] == "contract"
        assert PROOF_LEVELS[-1] == "operator_acceptance"

    def test_rank_ordering(self):
        assert proof_level_gte("build", "harness")
        assert proof_level_gte("build", "build")
        assert not proof_level_gte("harness", "build")

    def test_rank_completeness(self):
        assert len(PROOF_RANK) == len(PROOF_LEVELS)


# ── Output policy tests ───────────────────────────────────────────


class TestOutputPolicy:
    def test_is_output_path(self):
        assert is_output_path("Outputs/runs/abc12345")
        assert is_output_path(repo_root() / "Outputs" / "runs" / "abc12345")
        assert not is_output_path("Candidates/something")

    def test_is_source_path(self):
        assert is_source_path("Candidates/something.xlsx")
        assert is_source_path("Active/roster.xlsx")
        assert is_source_path("References/template.xlsx")
        assert not is_source_path("Outputs/something.xlsx")

    def test_validate_output_allocation_pass(self):
        violations = validate_output_allocation(
            "Outputs/runs/abc12345",
            input_paths=["Active/roster.xlsx"],
        )
        assert violations == []

    def test_validate_output_allocation_fail_not_under_outputs(self):
        violations = validate_output_allocation("temp/something")
        assert len(violations) == 1
        assert "not under Outputs" in violations[0]

    def test_validate_output_allocation_fail_equals_input(self):
        violations = validate_output_allocation(
            "Outputs/runs/test",
            input_paths=["Outputs/runs/test"],
        )
        assert any("equals input" in v for v in violations)

    def test_refuse_source_writes(self):
        violations = refuse_source_writes(["Candidates/output.xlsx"])
        assert len(violations) == 1
        assert "refusing" in violations[0]

    def test_refuse_source_writes_clean(self):
        violations = refuse_source_writes(["Outputs/clean.xlsx"])
        assert violations == []


# ── Doctor tests ──────────────────────────────────────────────────


class TestDoctor:
    def test_doctor_passes(self):
        result = run_doctor()
        assert result["status"] == "OK"
        assert len(result["checks"]) >= 6
        for check in result["checks"]:
            assert check["status"] in ("PASS", "WARN"), f"Doctor check failed: {check['name']}: {check['message']}"


# ── CLI command tests ─────────────────────────────────────────────


class TestCLIDoctor:
    def test_doctor_command(self):
        assert cli_main(["doctor"]) == 0


class TestCLIWorkflows:
    def test_workflows_command(self, capsys):
        assert cli_main(["workflows"]) == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "roster-review-blank" in data
        assert "bonita-neuron-track-hours" in data


class TestCLIExplain:
    def test_explain_known(self, capsys):
        assert cli_main(["explain", "roster-review-blank"]) == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["workflow_id"] == "roster-review-blank"
        assert data["proof_ceiling"] == "package"
        assert "artifact" in data

    def test_explain_unknown(self, capsys):
        assert cli_main(["explain", "nonexistent"]) == 1


class TestCLIRun:
    def test_run_synthetic(self, capsys):
        rc = cli_main(["run", "roster-review-blank", "--months", "2026-04", "2026-05"])
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "run_id" in data
        assert data["workflow_id"] == "roster-review-blank"
        assert data["achieved_proof_level"] == "build"

        # Verify manifest written
        run_dir = repo_root() / data["output_dir"]
        assert (run_dir / "synthetic-manifest.json").exists()
        assert (run_dir / "run-context.json").exists()

        # Cleanup
        shutil.rmtree(run_dir, ignore_errors=True)

    def test_run_unknown_workflow(self):
        assert cli_main(["run", "nonexistent"]) == 1


class TestCLIValidate:
    def test_validate_synthetic_run(self, capsys):
        # First create a run
        rc = cli_main(["run", "roster-review-blank"])
        assert rc == 0

        # Find the run we just created
        runs_dir = repo_root() / "Outputs" / "runs"
        run_ids = sorted(
            [d.name for d in runs_dir.iterdir() if d.is_dir()],
            key=lambda x: (runs_dir / x).stat().st_mtime,
            reverse=True,
        )
        assert run_ids, "No run directories found"
        latest_run_id = run_ids[0]

        # Validate it (capsys accumulates all output, so read from file)
        rc = cli_main(["validate", latest_run_id])
        assert rc == 0

        report_path = runs_dir / latest_run_id / "validation-report.json"
        assert report_path.exists()
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["overall_status"] == "PASS"
        assert data["run_id"] == latest_run_id
        assert data["summary"]["fail"] == 0
        assert data["summary"]["total"] >= 5

        # Cleanup
        shutil.rmtree(runs_dir / latest_run_id, ignore_errors=True)
