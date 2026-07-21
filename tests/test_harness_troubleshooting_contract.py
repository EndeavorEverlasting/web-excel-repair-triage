from __future__ import annotations

import copy
import json
from pathlib import Path

from triage import _prompt_kit_v39_generator_legacy as legacy
from triage import harness_troubleshooting_contract as contract
from triage import prompt_kit_v39_live_context_generator as live_generator


def test_live_evidence_troubleshooting_policy_and_prompt_are_valid() -> None:
    assert contract.validate_all() == ()


def test_live_context_generator_replaces_only_p54_and_preserves_prompt_order(tmp_path: Path) -> None:
    payload = live_generator.build_live_standard_spec()
    assert tuple(payload["section"]["prompt_ids"]) == live_generator.base.STANDARD_AI_EXTENSION_IDS
    assert tuple(item["prompt_id"] for item in payload["prompts"]) == live_generator.base.STANDARD_AI_EXTENSION_IDS
    prompt = payload["prompts"][4]
    assert prompt["prompt_id"] == "P54"
    text = "\n".join(prompt["lines"])
    assert "LATEST TRUSTWORTHY CONTEXT" in text
    assert "validated local runtime evidence" in text.lower()
    assert "first confirmed divergence" in text.lower()
    assert "smallest diagnostic action" in text.lower()
    assert "Do not freeze repository-specific filenames, commands, or paths into this prompt." in text
    assert "ACTION COMMITMENT" in text

    merged = tmp_path / "standard-ai.live.json"
    merged.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _, _, prompts = legacy._load_prompt_contracts(merged, live_generator.DEFAULT_GNHF_SPEC)
    assert [item["prompt_id"] for item in prompts[:8]] == list(live_generator.base.STANDARD_AI_EXTENSION_IDS)


def test_prompt_contract_rejects_acknowledgment_only_or_missing_action_commitment() -> None:
    payload = copy.deepcopy(contract.load_prompt_contract())
    payload["prompt"]["lines"] = [
        line for line in payload["prompt"]["lines"] if line != "ACTION COMMITMENT"
    ]
    issues = contract.validate_prompt_contract(payload)
    assert any("ACTION COMMITMENT" in issue for issue in issues)


def test_prompt_contract_rejects_frozen_repository_commands_and_paths() -> None:
    payload = copy.deepcopy(contract.load_prompt_contract())
    payload["prompt"]["lines"].append("Run pytest tests/test_specific_repository_file.py from C:\\repo.")
    issues = contract.validate_prompt_contract(payload)
    assert any("pytest" in issue for issue in issues)
    assert any("absolute path" in issue for issue in issues)


def test_policy_rejects_conversation_memory_over_current_evidence() -> None:
    payload = copy.deepcopy(contract.load_policy())
    payload["troubleshooting_contract"]["live_contract_resolution"][
        "conversation_memory_cannot_override_newer_evidence"
    ] = False
    issues = contract.validate_policy_contract(payload)
    assert any("conversation_memory_cannot_override_newer_evidence" in issue for issue in issues)


def test_artifact_registry_rejects_the_legacy_v39_generator() -> None:
    payload = copy.deepcopy(contract.load_artifact_registry())
    artifact = next(item for item in payload["artifacts"] if item["id"] == "ai-harness-prompt-kit-v39")
    artifact["generator"] = "python -m triage.prompt_kit_v39_generator"
    issues = contract.validate_artifact_registry(payload)
    assert "V39 artifact registry must use the live-context generator" in issues
