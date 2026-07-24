"""tests/test_ai_schemas.py
--------------------------
Validate that the .ai/schemas JSON documents are well-formed and internally consistent.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMA_DIR = Path(__file__).resolve().parent.parent / ".ai" / "schemas"
REGISTRY_DIR = Path(__file__).resolve().parent.parent / ".ai"


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


class TestSchemasExist:
    def test_run_context_schema(self):
        p = SCHEMA_DIR / "run-context.json"
        assert p.exists(), f"Missing: {p}"

    def test_validation_report_schema(self):
        p = SCHEMA_DIR / "validation-report.json"
        assert p.exists(), f"Missing: {p}"

    def test_roster_diagnostic_schema(self):
        p = SCHEMA_DIR / "roster-workbook-diagnostic-report.json"
        assert p.exists(), f"Missing: {p}"


class TestRunContextSchema:
    def test_loads(self):
        data = _load_json(SCHEMA_DIR / "run-context.json")
        assert data["$schema"].startswith("https://")
        assert "run_id" in data["required"]
        assert "workflow_id" in data["required"]

    def test_proof_levels_enum(self):
        data = _load_json(SCHEMA_DIR / "run-context.json")
        levels = data["$defs"]["proof_level"]["enum"]
        assert "contract" in levels
        assert "operator_acceptance" in levels
        assert len(levels) == 12

    def test_has_required_fields(self):
        data = _load_json(SCHEMA_DIR / "run-context.json")
        required = data["required"]
        assert "run_id" in required
        assert "workflow_id" in required
        assert "started_at" in required
        assert "branch" in required
        assert "commit_sha" in required
        assert "dirty" in required
        assert "input_paths" in required
        assert "output_dir" in required
        assert "requested_proof_level" in required
        assert "achieved_proof_level" in required
        assert "skipped_gates" in required


class TestValidationReportSchema:
    def test_loads(self):
        data = _load_json(SCHEMA_DIR / "validation-report.json")
        assert "run_id" in data["required"]
        assert "overall_status" in data["required"]
        assert "checks" in data["required"]

    def test_validation_states(self):
        data = _load_json(SCHEMA_DIR / "validation-report.json")
        states = data["$defs"]["validation_status"]["enum"]
        assert "PASS" in states
        assert "FAIL" in states
        assert "NOT_RUN" in states
        assert "NOT_APPLICABLE" in states
        assert "BLOCKED" in states

    def test_check_has_status(self):
        data = _load_json(SCHEMA_DIR / "validation-report.json")
        check = data["$defs"]["validation_check"]
        assert "name" in check["required"]
        assert "status" in check["required"]


class TestRosterDiagnosticSchema:
    def test_loads(self):
        data = _load_json(SCHEMA_DIR / "roster-workbook-diagnostic-report.json")
        assert "run_id" in data["required"]
        assert "tabs" in data["required"]
        assert "summary" in data["required"]

    def test_tab_detail(self):
        data = _load_json(SCHEMA_DIR / "roster-workbook-diagnostic-report.json")
        tab = data["$defs"]["tab_detail"]
        assert "name" in tab["required"]
        assert "row_count" in tab["required"]


class TestRegistries:
    def test_artifact_registry_loads(self):
        data = _load_json(REGISTRY_DIR / "artifact-registry.json")
        assert "artifacts" in data
        assert "version" in data

    def test_workflow_registry_loads(self):
        data = _load_json(REGISTRY_DIR / "workflow-registry.json")
        assert "workflows" in data
        assert "version" in data

    def test_workflow_refs_valid_artifact(self):
        wfs = _load_json(REGISTRY_DIR / "workflow-registry.json")["workflows"]
        arts = _load_json(REGISTRY_DIR / "artifact-registry.json")["artifacts"]
        for wf_id, wf in wfs.items():
            art_id = wf.get("artifact_id", "")
            if art_id:
                assert art_id in arts, f"Workflow {wf_id} references unknown artifact {art_id}"

    def test_no_ceremonial_empty_registries(self):
        for name in ["artifact-registry.json", "workflow-registry.json"]:
            data = _load_json(REGISTRY_DIR / name)
            assert len(data) > 1, f"{name} is ceremonial/empty"
