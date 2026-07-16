"""Validate the declarative P02 and P45-P49 V33 prompt-source contract."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

DEFAULT_SPEC_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "prompt_kit"
    / "v33_gnhf_harness_prompts.json"
)
REQUIRED_PROMPTS = ("P02", "P45", "P46", "P47", "P48", "P49")
EXPECTED_SEMANTICS = {
    "P02": "assign executable repository harness construction",
    "P45": "compile a regular sprint request without executing it",
    "P46": "run GNHF to build or repair a repository harness",
    "P47": "run one registered repository harness workflow",
    "P48": "have ChatGPT Desktop Codex compile and execute through AgentSwitchboard",
    "P49": "plan and explicitly apply AgentSwitchboard workstation configuration",
}
AUTHORITY_PATHS = {
    "regular_request_schema": "tooling/gnhf/schemas/regular-sprint-request.v1.schema.json",
    "compiled_prompt_schema": "tooling/gnhf/schemas/compiled-gnhf-prompt-result.v1.schema.json",
    "desktop_runtime_entrypoint": "tooling/gnhf/Invoke-ChatGPTDesktopGnhfSprint.ps1",
    "environment_setup_entrypoint": "tooling/wsl/Start-TmuxGnhfWorkspaceSetup.ps1",
}


@dataclass(frozen=True)
class PromptSourceContractResult:
    spec: str
    prompt_ids: tuple[str, ...]
    findings: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict:
        return {
            "spec": self.spec,
            "status": "PASS" if self.passed else "FAIL",
            "prompt_ids": list(self.prompt_ids),
            "findings": list(self.findings),
            "proof_ceiling": (
                "declarative source shape and executable prompt semantics; agent spawn, "
                "desktop runtime, environment Apply, and operator acceptance remain runtime gates"
            ),
        }


def _payload(prompt: Mapping[str, object]) -> str:
    lines = prompt.get("lines")
    if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
        return ""
    return "\n".join(lines)


def _require_phrases(
    prompt_id: str,
    payload: str,
    phrases: Sequence[str],
    findings: list[str],
) -> None:
    lowered = payload.lower()
    for phrase in phrases:
        if phrase.lower() not in lowered:
            findings.append(f"{prompt_id} missing executable contract phrase: {phrase}")


def validate_prompt_contract_data(data: Mapping[str, object], *, spec: str = "<memory>") -> PromptSourceContractResult:
    findings: list[str] = []
    if data.get("schema_version") != 1:
        findings.append("schema_version must equal 1")

    authority = data.get("contract_authority")
    if not isinstance(authority, Mapping):
        findings.append("contract_authority must be an object")
        authority = {}
    if authority.get("repository") != "EndeavorEverlasting/AgentSwitchboard":
        findings.append("contract_authority.repository must be EndeavorEverlasting/AgentSwitchboard")
    if authority.get("pull_request") != 17:
        findings.append("contract_authority.pull_request must equal 17")
    verified_head = str(authority.get("verified_head", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", verified_head):
        findings.append("contract_authority.verified_head must be a full commit SHA")
    for key, expected in AUTHORITY_PATHS.items():
        if authority.get(key) != expected:
            findings.append(f"contract_authority.{key} must equal {expected}")

    order = data.get("sheet_order")
    if not isinstance(order, list) or not all(isinstance(name, str) for name in order):
        findings.append("sheet_order must be a list of strings")
        order = []
    prompt_order = [name[:3] for name in order if re.fullmatch(r"P\d{2}_COPY_SAFE", name)]
    expected_order = [f"P{number:02d}" for number in range(50)]
    if prompt_order != expected_order:
        findings.append("sheet_order must contain P00 through P49 exactly once in numeric order")

    editable_ranges = data.get("editable_ranges")
    if editable_ranges != {"Opportunity_Discovery": "A1:R100"}:
        findings.append("only Opportunity_Discovery!A1:R100 may be editable")

    raw_prompts = data.get("prompts")
    if not isinstance(raw_prompts, list):
        findings.append("prompts must be a list")
        raw_prompts = []
    prompts = {
        str(prompt.get("prompt_id")): prompt
        for prompt in raw_prompts
        if isinstance(prompt, Mapping) and prompt.get("prompt_id")
    }
    prompt_ids = tuple(prompts)
    if prompt_ids != REQUIRED_PROMPTS:
        findings.append(f"prompt source order must be {', '.join(REQUIRED_PROMPTS)}")

    semantics: list[str] = []
    for prompt_id in REQUIRED_PROMPTS:
        prompt = prompts.get(prompt_id)
        if prompt is None:
            findings.append(f"missing prompt source: {prompt_id}")
            continue
        expected_sheet = f"{prompt_id}_COPY_SAFE"
        if prompt.get("sheet_name") != expected_sheet:
            findings.append(f"{prompt_id} sheet_name must equal {expected_sheet}")
        semantic = str(prompt.get("execution_semantics", ""))
        semantics.append(semantic)
        if semantic != EXPECTED_SEMANTICS[prompt_id]:
            findings.append(f"{prompt_id} execution_semantics is not canonical")
        if not _payload(prompt):
            findings.append(f"{prompt_id} lines must be a non-empty list of strings")
    if len(semantics) != len(set(semantics)):
        findings.append("P02 and P45-P49 execution semantics must be distinct")

    p02 = _payload(prompts.get("P02", {}))
    _require_phrases(
        "P02",
        p02,
        (
            "inspect the current repository",
            "creating or repairing",
            "schemas, fixtures, validators, skills, capabilities, deterministic triggers, registered workflows, and integration seams",
            "modify tracked files",
            "validate",
            "commit",
            "push",
            "open or update the intended pull request",
            "descriptive-only",
        ),
        findings,
    )

    p45 = _payload(prompts.get("P45", {}))
    _require_phrases(
        "P45",
        p45,
        (
            "compile only",
            "do not execute the sprint",
            "regular-sprint-request v1",
            "compiled-gnhf-prompt-result v1",
            "schemaVersion to 1",
            "gitExecution",
            "agentRoute",
            "maxIterations",
            "maxTokens",
            "preventSleep",
            "timeoutSeconds",
            "commitContract.required must be true",
            "pushContract.mode",
            "proofCeiling",
            "finalResponseContract",
            "nextCommand",
        ),
        findings,
    )

    p46 = _payload(prompts.get("P46", {}))
    if not p46.startswith("gnhf `"):
        findings.append("P46 must be a direct GNHF command")
    _require_phrases(
        "P46",
        p46,
        ("build or repair", "schemas, fixtures, validators, skills, capabilities, triggers", "commit", "plan-only response is failure"),
        findings,
    )

    p47 = _payload(prompts.get("P47", {}))
    if not p47.startswith("gnhf `"):
        findings.append("P47 must be a direct GNHF command")
    _require_phrases(
        "P47",
        p47,
        ("registered workflow", "required artifact and commit", "process exit without the required artifact and commit is failure"),
        findings,
    )

    p48 = _payload(prompts.get("P48", {}))
    _require_phrases(
        "P48",
        p48,
        (
            "ChatGPT Desktop Codex",
            "regular-sprint-request v1",
            "compiled-gnhf-prompt-result v1",
            "Invoke-ChatGPTDesktopGnhfSprint.ps1",
            "-RequestPath",
            "-CompiledPromptPath",
            "-TargetRepo",
            "-Run",
            "print the entire compiled prompt",
            "script does not control the ChatGPT Desktop UI",
            "process exit alone is failure",
            "proof ceiling",
        ),
        findings,
    )

    p49 = _payload(prompts.get("P49", {}))
    _require_phrases(
        "P49",
        p49,
        (
            "Start-TmuxGnhfWorkspaceSetup.ps1",
            "-Mode Plan",
            "-Mode Apply",
            "explicitly authorizes",
            "PowerShell 7",
            "WSL Ubuntu",
            "WezTerm GUI",
            "tmux",
            "Node",
            "GNHF",
            "OpenCode",
            "AGY",
            "Goose",
            "preserve unmanaged or user-owned configuration",
            "Do not automate provider authentication",
            "reboot and resume checkpoints",
            "rollback",
        ),
        findings,
    )

    tracked_text = json.dumps(data, ensure_ascii=False)
    if re.search(r"[A-Za-z]:\\Users\\", tracked_text, re.IGNORECASE):
        findings.append("prompt source contains a machine-local user-profile path")

    return PromptSourceContractResult(spec=spec, prompt_ids=prompt_ids, findings=tuple(findings))


def validate_prompt_contract(path: Path = DEFAULT_SPEC_PATH) -> PromptSourceContractResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        return PromptSourceContractResult(str(path), (), ("prompt source root must be an object",))
    return validate_prompt_contract_data(data, spec=str(path))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", nargs="?", type=Path, default=DEFAULT_SPEC_PATH)
    args = parser.parse_args(argv)
    result = validate_prompt_contract(args.spec)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
