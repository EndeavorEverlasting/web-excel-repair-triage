from __future__ import annotations

import copy
import json

from triage.prompt_kit_v33_prompt_contract import (
    DEFAULT_SPEC_PATH,
    EXPECTED_SEMANTICS,
    REQUIRED_PROMPTS,
    validate_prompt_contract,
    validate_prompt_contract_data,
)


def _source() -> dict:
    return json.loads(DEFAULT_SPEC_PATH.read_text(encoding="utf-8"))


def test_p02_and_p45_p49_source_contract_passes() -> None:
    result = validate_prompt_contract()
    assert result.passed, result.findings
    assert result.prompt_ids == REQUIRED_PROMPTS


def test_descriptive_only_p02_is_rejected() -> None:
    source = copy.deepcopy(_source())
    p02 = next(prompt for prompt in source["prompts"] if prompt["prompt_id"] == "P02")
    p02["lines"] = [
        "Describe the repository harness.",
        "Map the current components and recommend future work.",
        "Return a plan only.",
    ]
    result = validate_prompt_contract_data(source)
    assert not result.passed
    assert any(finding.startswith("P02 missing executable contract phrase") for finding in result.findings)


def test_compile_run_and_configure_semantics_are_distinct() -> None:
    source = _source()
    prompts = {prompt["prompt_id"]: prompt for prompt in source["prompts"]}
    assert {prompts[prompt_id]["execution_semantics"] for prompt_id in REQUIRED_PROMPTS} == set(
        EXPECTED_SEMANTICS.values()
    )
    assert prompts["P45"]["prompt_type"] == "COMPILE ONLY"
    assert prompts["P46"]["lines"][0] == "gnhf `"
    assert prompts["P47"]["lines"][0] == "gnhf `"
    assert prompts["P48"]["prompt_type"] == "DESKTOP + EXECUTE"
    assert "Do not promise unconditional failed-worktree preservation" in "\n".join(prompts["P48"]["lines"])
    assert prompts["P49"]["prompt_type"] == "ENVIRONMENT + CONFIGURE"


def test_agent_switchboard_v1_authority_is_versioned_and_repo_relative() -> None:
    authority = _source()["contract_authority"]
    assert authority["repository"] == "EndeavorEverlasting/AgentSwitchboard"
    assert authority["pull_request"] == 17
    assert len(authority["verified_head"]) == 40
    for key, value in authority.items():
        if key.endswith("schema") or key.endswith("entrypoint"):
            assert not value.startswith(("/", "\\"))
            assert ":" not in value
