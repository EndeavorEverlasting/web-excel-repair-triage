from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / ".ai"

STATUSES = {"PASS", "FAIL", "NOT_RUN", "NOT_APPLICABLE", "BLOCKED"}
PROOF_LEVELS = {
    "contract",
    "harness",
    "static_test",
    "build",
    "package",
    "render",
    "launcher",
    "command_ack",
    "behavior_observed",
    "browser",
    "live_runtime",
    "operator_acceptance",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_validator_registry_has_one_owner_per_module() -> None:
    registry = load(AI / "validator-registry.json")
    validators = registry["validators"]
    modules = [item["canonical_module"] for item in validators.values()]
    assert len(modules) == len(set(modules))
    assert set(registry["validation_statuses"]) == STATUSES
    assert set(registry["proof_levels"]) == PROOF_LEVELS
    assert set(registry["composition_order"]) == set(validators)
    assert registry["rules"]["no_duplicate_authority"] is True
    assert registry["rules"]["no_proof_promotion"] is True


def test_prompt_kit_validator_ownership_is_explicit() -> None:
    validators = load(AI / "validator-registry.json")["validators"]
    assert validators["web_excel_compatibility"]["owner_pr"] == 57
    assert 53 in validators["web_excel_compatibility"]["absorbs_prs"]
    assert validators["prompt_kit_operability"]["owner_pr"] == 61
    assert validators["excel_desktop_recovery_triage"]["owner_pr"] == 60
    assert validators["excel_desktop_recovery_triage"]["proof_ceiling"] == "launcher"


def test_prompt_kit_artifacts_are_registered_and_untracked_by_contract() -> None:
    artifacts = load(AI / "artifact-registry.json")["artifacts"]
    workbook = artifacts["prompt_kit_workbook"]
    assert workbook["delivery"] is True
    assert workbook["proof_ceiling"] == "operator_acceptance"
    assert "Workbook binaries remain untracked" in workbook["description"]
    assert artifacts["excel_recovery_triage_report"]["proof_ceiling"] == "launcher"


def test_prompt_kit_workflows_keep_desktop_and_web_proof_separate() -> None:
    workflows = load(AI / "workflow-registry.json")["workflows"]
    package = workflows["prompt-kit-package-validation"]
    desktop = workflows["excel-desktop-recovery-triage"]
    field = workflows["prompt-kit-field-acceptance"]
    assert package["proof_ceiling"] == "package"
    assert desktop["proof_ceiling"] == "launcher"
    assert desktop["engine_source_pr"] == 60
    assert field["proof_ceiling"] == "operator_acceptance"
    assert package["artifact_id"] != desktop["artifact_id"]


def test_acceptance_schemas_use_canonical_statuses() -> None:
    acceptance = load(AI / "schemas" / "prompt-kit-acceptance-state.json")
    field = load(AI / "schemas" / "prompt-kit-field-acceptance-record.json")
    gate_statuses = set(acceptance["$defs"]["gate"]["properties"]["status"]["enum"])
    field_statuses = set(field["properties"]["checks"]["items"]["properties"]["status"]["enum"])
    assert gate_statuses == STATUSES
    assert field_statuses == STATUSES
    required_gates = set(acceptance["properties"]["gates"]["required"])
    assert {"desktop_excel", "excel_for_web", "mouse_navigation", "clipboard", "operator_acceptance"} <= required_gates
