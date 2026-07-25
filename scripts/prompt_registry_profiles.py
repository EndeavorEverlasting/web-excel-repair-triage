#!/usr/bin/env python3
"""Build compact prompt execution profiles and passage audit reports."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import build_prompt_kit_registry as registry

from prompt_registry_harness_contracts import (
    PromptRegistryHarnessError,
    validate_domain_harness,
    validate_output_path,
)

IMPACT_CAPABILITY = {
    "inspect": "repository-inspection",
    "plan": "repository-inspection",
    "mutate": "bounded-repository-mutation",
    "mixed": "bounded-repository-mutation",
    "validate": "validation-proof-routing",
    "integrate": "integration-handoff",
}
IMPACT_CAPABILITY_SKILL = {
    "inspect": ".ai/skills/repository-inspection/SKILL.md",
    "plan": ".ai/skills/repository-inspection/SKILL.md",
    "mutate": ".ai/skills/bounded-repository-mutation/SKILL.md",
    "mixed": ".ai/skills/bounded-repository-mutation/SKILL.md",
    "validate": ".ai/skills/validation-proof-routing/SKILL.md",
    "integrate": ".ai/skills/integration-handoff/SKILL.md",
}
MUTATION_TERMS = (
    "build", "repair", "implement", "install", "configure", "cleanup",
    "maintain", "execute", "recover", "commit", "deploy", "operate",
    "enablement",
)
VALIDATION_TERMS = (
    "validate", "safety", "runtime proof", "test", "eval", "cert", "protect",
)
INTEGRATION_TERMS = (
    "integrate", "interop", "merge", "handoff", "closeout", "release",
)
PLAN_TERMS = (
    "plan", "discovery", "analyze", "opportunity", "directory",
    "compile only",
)


def prompt_blob(
    prompt: dict[str, Any],
    *,
    include_copy_content: bool = False,
) -> str:
    """Return normalized routing text without shared appendices by default."""
    values = [
        prompt.get("name", ""),
        prompt.get("type", ""),
        prompt.get("class", ""),
        prompt.get("sprintRole", ""),
        prompt.get("useWhen", ""),
        prompt.get("inspectFirst", ""),
        prompt.get("expectedOutput", ""),
        prompt.get("nextStep", ""),
        prompt.get("proofGate", ""),
        " ".join(
            prompt.get("keywords", [])
            if isinstance(prompt.get("keywords"), list)
            else []
        ),
    ]
    if include_copy_content:
        values.append(prompt.get("copyContent", ""))
    return " ".join(str(value) for value in values).lower()


def classify_impact(prompt: dict[str, Any]) -> str:
    text = prompt_blob(prompt)
    prompt_type = str(prompt.get("type", "")).lower()
    if any(term in text or term in prompt_type for term in INTEGRATION_TERMS):
        return "integrate"
    if any(term in text or term in prompt_type for term in VALIDATION_TERMS):
        if any(term in text or term in prompt_type for term in MUTATION_TERMS):
            return "mixed"
        return "validate"
    if any(term in text or term in prompt_type for term in MUTATION_TERMS):
        return "mutate"
    if any(term in text or term in prompt_type for term in PLAN_TERMS):
        return "plan"
    return "inspect"


def classify_context(prompt: dict[str, Any]) -> str:
    text = prompt_blob(prompt)
    repo_markers = (
        "repo", "repository", "branch", "worktree", "commit",
        "pull request", " pr ", "codebase", "git ", "artifact", "validator",
    )
    if any(marker in f" {text} " for marker in repo_markers):
        return "repository-required"
    if any(marker in text for marker in (
        "project", "file", "document", "workflow"
    )):
        return "repository-optional"
    return "non-repository"


def classify_proof(prompt: dict[str, Any]) -> str:
    text = str(prompt.get("proofGate", "")).lower() + " " + prompt_blob(prompt)
    if any(word in text for word in (
        "production", "live target", "deployed"
    )):
        return "production"
    if any(word in text for word in (
        "runtime", "browser", "gui", "live proof", "launch"
    )):
        return "runtime"
    if any(word in text for word in (
        "test", "validator", "ci", "schema", "lint", "static"
    )):
        return "deterministic"
    if any(word in text for word in (
        "inspect", "review", "evidence", "diff"
    )):
        return "inspection"
    return "declared"


def canary_present(prompt: dict[str, Any], canary: dict[str, Any]) -> bool:
    content = str(prompt.get("copyContent", ""))
    marker = str(canary["prompt_instruction_marker"])
    return (
        marker in content
        and "OBJECTIVE:" in content
        and "REPOS:" in content
    )


def profile_prompt(
    prompt: dict[str, Any],
    *,
    capabilities: dict[str, dict[str, Any]],
    canary: dict[str, Any],
    profile_schema: dict[str, Any],
) -> dict[str, Any]:
    impact = classify_impact(prompt)
    capability_id = IMPACT_CAPABILITY[impact]
    capability = capabilities[capability_id]
    content = str(prompt.get("copyContent", ""))
    shared_refs = [
        "harness/contracts/conversation-canary.v1.json",
        str(capability["skill"]),
        "registry/prompts/actionable-next-step-policy.v1.json",
        "harness/prompt-registry/WORKFLOW.md",
    ]
    profile = {
        "prompt_id": str(prompt["id"]),
        "sequence": int(str(prompt["seq"])),
        "name": str(prompt["name"]),
        "prompt_type": str(prompt["type"]),
        "primary_capability": capability_id,
        "primary_skill": str(capability["skill"]),
        "impact_class": impact,
        "context_class": classify_context(prompt),
        "proof_class": classify_proof(prompt),
        "canary_contract": {
            "contract_id": str(canary["contract_id"]),
            "present": canary_present(prompt, canary),
        },
        "shared_instruction_refs": shared_refs,
        "canonical_source": str(
            prompt.get("_source", "effective-registry")
        ),
        "token_metrics": {
            "source_copy_content_characters": len(content),
            "compact_profile_characters": 0,
            "shared_reference_count": len(shared_refs),
        },
    }
    compact = json.dumps(
        profile,
        sort_keys=True,
        separators=(",", ":"),
    )
    profile["token_metrics"]["compact_profile_characters"] = len(compact)

    required = set(profile_schema.get("required_fields", []))
    missing = required - set(profile)
    if missing:
        raise PromptRegistryHarnessError(
            f"profile is missing required fields: {sorted(missing)}"
        )
    forbidden = set(profile_schema.get("forbidden_fields", []))
    leaked = forbidden & set(profile)
    if leaked:
        raise PromptRegistryHarnessError(
            "profile contains forbidden full-prompt fields: "
            f"{sorted(leaked)}"
        )
    enums = profile_schema["enums"]
    for field in ("impact_class", "context_class", "proof_class"):
        if profile[field] not in enums[field]:
            raise PromptRegistryHarnessError(
                "profile field is outside declared enum: "
                f"{field}={profile[field]}"
            )
    if profile["primary_skill"] != IMPACT_CAPABILITY_SKILL[impact]:
        raise PromptRegistryHarnessError(
            "impact/skill routing drifted: "
            f"{impact} -> {profile['primary_skill']}"
        )
    return profile


def build_report(
    *,
    prompt_id: str | None = None,
    strict_canary: bool = False,
) -> dict[str, Any]:
    harness = validate_domain_harness()
    prompts = registry.load_prompt_registry()
    profiles = [
        profile_prompt(
            prompt,
            capabilities=harness["capabilities"],
            canary=harness["canary"],
            profile_schema=harness["profile_schema"],
        )
        for prompt in prompts
    ]
    profiles.sort(key=lambda item: item["sequence"])
    if prompt_id:
        wanted = prompt_id.upper()
        profiles = [
            item
            for item in profiles
            if item["prompt_id"].upper() == wanted
        ]
        if not profiles:
            raise PromptRegistryHarnessError(
                f"unknown prompt ID: {prompt_id}"
            )

    canary_missing = [
        item["prompt_id"]
        for item in profiles
        if not item["canary_contract"]["present"]
    ]
    source_characters = sum(
        int(item["token_metrics"]["source_copy_content_characters"])
        for item in profiles
    )
    compact_characters = sum(
        int(item["token_metrics"]["compact_profile_characters"])
        for item in profiles
    )
    capability_counts = Counter(
        item["primary_capability"] for item in profiles
    )
    coverage_complete = len(profiles) == (
        1 if prompt_id else len(prompts)
    )
    findings = (
        [
            {
                "id": "canary-missing",
                "severity": "error" if strict_canary else "warning",
                "prompt_ids": canary_missing,
                "message": (
                    "Effective prompts missing the objective/repository "
                    "canary contract."
                ),
            }
        ]
        if canary_missing
        else []
    )

    return {
        "schema_version": "prompt-registry-harness-audit-result/v1",
        "strict_canary": strict_canary,
        "prompt_filter": prompt_id,
        "prompt_count": len(prompts),
        "profile_count": len(profiles),
        "coverage_complete": coverage_complete,
        "canary_coverage_count": len(profiles) - len(canary_missing),
        "canary_missing_count": len(canary_missing),
        "canary_ready": not canary_missing,
        "capability_counts": dict(sorted(capability_counts.items())),
        "passage_order": [item["prompt_id"] for item in profiles],
        "token_metrics": {
            "source_copy_content_characters": source_characters,
            "compact_profile_characters": compact_characters,
            "estimated_passage_character_reduction": max(
                0,
                source_characters - compact_characters,
            ),
        },
        "profiles": profiles,
        "findings": findings,
        "proof_ceiling": (
            "Exhaustive deterministic effective-registry/profile coverage "
            "and static canary inclusion only; no provider/model adherence "
            "proof."
        ),
    }


def write_report(report: dict[str, Any], output: Path) -> Path:
    resolved = validate_output_path(output)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return resolved


def print_summary(
    report: dict[str, Any],
    output: Path | None = None,
) -> None:
    print("Prompt Registry Harness Audit")
    print("=" * 31)
    print(f"Profiles: {report['profile_count']} / {report['prompt_count']}")
    print(f"Coverage complete: {report['coverage_complete']}")
    print(
        "Canary coverage: "
        f"{report['canary_coverage_count']} / "
        f"{report['profile_count']}"
    )
    print(f"Strict canary: {report['strict_canary']}")
    print(
        "Estimated passage characters reduced: "
        f"{report['token_metrics']['estimated_passage_character_reduction']}"
    )
    print("Capability counts:")
    for capability_id, count in report["capability_counts"].items():
        print(f"- {capability_id}: {count}")
    if output:
        print(f"Report: {output}")
