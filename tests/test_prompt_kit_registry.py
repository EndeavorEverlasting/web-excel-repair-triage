from __future__ import annotations

import json
from pathlib import Path

from triage.prompt_kit_registry import SCHEMA_VERSION, validate_registry
from triage.prompt_kit_registry_store import load_store

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "v38" / "prompt-registry.v1.json"
SCHEMA = ROOT / "registry" / "prompts" / "prompt-registry.v1.schema.json"
SHARD_SCHEMA = ROOT / "registry" / "prompts" / "prompt-record-shard.v1.schema.json"
OVERRIDES = ROOT / "configs" / "prompt_kit" / "v38_registry_variable_overrides.json"


def _payload() -> dict:
    return load_store(REGISTRY)


def test_v38_registry_is_complete_and_valid() -> None:
    payload = _payload()
    assert payload["schemaVersion"] == SCHEMA_VERSION
    assert payload["kitVersion"] == "v38"
    assert payload["source"]["promptCount"] == 45
    assert payload["source"]["promptIdRange"] == "P00-P44"
    assert [prompt["id"] for prompt in payload["prompts"]] == [f"P{number:02d}" for number in range(45)]
    assert validate_registry(payload) == []


def test_registry_preserves_execution_surface_boundaries() -> None:
    prompts = {prompt["id"]: prompt for prompt in _payload()["prompts"]}
    assert prompts["P02"]["executionSurface"] == "regular_ai_prompt"
    assert prompts["P07"]["executionSurface"] == "regular_ai_prompt"
    for prompt_id in ("P26", "P37", "P38", "P44"):
        assert prompts[prompt_id]["executionSurface"] == "gnhf_launch_artifact"
    assert prompts["P07"]["text"].startswith("EXECUTE THE REPO SPRINT")
    assert prompts["P38"]["text"].startswith("gnhf `")


def test_every_used_variable_has_machine_readable_metadata() -> None:
    payload = _payload()
    variables = {record["name"]: record for record in payload["variables"]}
    used = {name for prompt in payload["prompts"] for name in prompt["requiredVariables"]}
    assert used <= set(variables)
    for name in used:
        assert variables[name]["meaning"]
        assert variables[name]["origin"]


def test_registry_schema_and_override_documents_parse() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    shard_schema = json.loads(SHARD_SCHEMA.read_text(encoding="utf-8"))
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["properties"]["schemaVersion"]["const"] == SCHEMA_VERSION
    assert shard_schema["properties"]["schemaVersion"]["const"] == "ai-harness-prompt-record-shard/v1"
    assert overrides["schemaVersion"] == "ai-harness-prompt-variable-overrides/v1"
    assert len(overrides["variables"]) == 17


def test_validator_rejects_text_tampering() -> None:
    payload = _payload()
    payload["prompts"][7]["text"] += "\nchanged"
    errors = validate_registry(payload)
    assert "P07 textSha256 mismatch" in errors
