#!/usr/bin/env python3
"""Build the Prompt Kit website from canonical registries and shared policies."""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import build_prompt_kit  # noqa: E402

BASE_REGISTRY = REPO_ROOT / "docs" / "prompts.json"
EXTENSION_REGISTRIES = (
    REPO_ROOT / "registry" / "prompts" / "skill-development-prompts.v1.json",
    REPO_ROOT / "registry" / "prompts" / "tutorial-discovery-prompts.v1.json",
    REPO_ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json",
    REPO_ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json",
    REPO_ROOT / "registry" / "prompts" / "management-operations-prompts.v1.json",
    REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json",
)
CONTENT_REGISTRIES = (
    REPO_ROOT / "registry" / "prompts" / "correspondence-prompts.v1.json",
)
PROMPT_OVERRIDES = REPO_ROOT / "registry" / "prompts" / "prompt-overrides.v1.json"
DISPLAY_ORDER_POLICY = (
    REPO_ROOT / "registry" / "prompts" / "prompt-display-order.v1.json"
)
GUIDED_RECOMMENDATIONS = REPO_ROOT / "docs" / "prompt-kit-guided-recommendations.js"
PROMPT_JOURNEY_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-journey.js"
POLISH_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-polish.js"
CORRESPONDENCE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-correspondence.js"
MANAGEMENT_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-management.js"
SPEC_ARCHITECTURE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-spec-architecture.js"
ACTIONABILITY_POLICY = (
    REPO_ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
)
REFERENCE = REPO_ROOT / "docs" / "reference.json"
DEFAULT_OUTPUT = REPO_ROOT / "web" / "prompt-kit" / "index.html"
PROTECTED_OUTPUT_ROOTS = (
    REPO_ROOT / "Candidates",
    REPO_ROOT / "Active",
)
REQUIRED_PROMPT_FIELDS = {
    "id",
    "seq",
    "name",
    "type",
    "class",
    "sprintRole",
    "progress",
    "useWhen",
    "inspectFirst",
    "expectedOutput",
    "nextStep",
    "proofGate",
    "color",
    "copySheet",
    "category",
    "copyContent",
    "keywords",
}
REQUIRED_ACTIONABILITY_POLICY_FIELDS = {
    "schema_version",
    "policy_id",
    "marker",
    "integration_marker",
    "integration_target",
    "applies_to",
    "next_step_suffix",
    "allowed_none_value",
    "green_merge_conditions",
    "merge_exceptions",
    "existing_work_reuse",
    "forbidden_solo_actions",
    "copy_content_appendix",
}
REQUIRED_DISPLAY_ORDER_FIELDS = {
    "schema_version",
    "policy_id",
    "promoted_prompt_ids",
    "fallback",
    "rationale",
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Required registry file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def validate_output_path(output: Path) -> Path:
    """Return a resolved output path or reject read-only operator input roots."""
    resolved = output.expanduser().resolve()
    for protected_root in PROTECTED_OUTPUT_ROOTS:
        try:
            resolved.relative_to(protected_root.resolve())
        except ValueError:
            continue
        raise ValueError(
            "Output path is inside a protected operator input directory: "
            f"{protected_root}"
        )
    return resolved


def load_actionability_policy() -> dict[str, Any]:
    """Load and fail closed on the shared next-command and next-step policy."""
    payload = _load_json(ACTIONABILITY_POLICY)
    if not isinstance(payload, dict):
        raise SystemExit(
            f"Actionability policy must be a JSON object: {ACTIONABILITY_POLICY}"
        )
    if payload.get("schema_version") != "prompt-next-action-policy/v1":
        raise SystemExit(
            f"Unsupported actionability policy schema in {ACTIONABILITY_POLICY}"
        )

    missing = sorted(REQUIRED_ACTIONABILITY_POLICY_FIELDS - set(payload))
    if missing:
        raise SystemExit(f"Actionability policy is missing fields: {missing}")

    for field in (
        "policy_id",
        "marker",
        "integration_marker",
        "integration_target",
        "applies_to",
        "next_step_suffix",
        "allowed_none_value",
        "copy_content_appendix",
    ):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"Actionability policy field must be non-empty: {field}")

    forbidden = payload.get("forbidden_solo_actions")
    if not isinstance(forbidden, list) or not forbidden:
        raise SystemExit("Actionability policy must define forbidden_solo_actions")
    if any(not isinstance(item, str) or not item.strip() for item in forbidden):
        raise SystemExit("Every forbidden solo action must be a non-empty string")

    for field in ("green_merge_conditions", "merge_exceptions"):
        values = payload.get(field)
        if not isinstance(values, list) or not values:
            raise SystemExit(
                f"Actionability policy field must define a non-empty list: {field}"
            )
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise SystemExit(
                f"Every actionability policy entry must be a non-empty string: {field}"
            )
        if len(values) != len(set(values)):
            raise SystemExit(
                f"Actionability policy list must not contain duplicates: {field}"
            )

    reuse = payload.get("existing_work_reuse")
    if not isinstance(reuse, dict):
        raise SystemExit("Actionability policy must define existing_work_reuse")
    for field in ("rule", "preservation_rule", "disposition_evidence"):
        value = reuse.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(
                f"Actionability existing-work field must be non-empty: {field}"
            )
    allowed = reuse.get("new_pr_allowed_when")
    if not isinstance(allowed, list) or not allowed:
        raise SystemExit(
            "Actionability existing-work policy must define new_pr_allowed_when"
        )
    if any(not isinstance(item, str) or not item.strip() for item in allowed):
        raise SystemExit(
            "Every new-PR allowance must be a non-empty string"
        )
    marker = str(payload["marker"])
    appendix = str(payload["copy_content_appendix"])
    if marker not in appendix:
        raise SystemExit("Actionability appendix must include its declared marker")
    integration_marker = str(payload["integration_marker"])
    if integration_marker not in appendix:
        raise SystemExit("Actionability appendix must include its integration marker")
    return payload


def load_display_order_policy() -> dict[str, Any]:
    """Load recommendation discovery metadata without changing stable identity."""
    payload = _load_json(DISPLAY_ORDER_POLICY)
    if not isinstance(payload, dict):
        raise SystemExit(
            f"Display order policy must be a JSON object: {DISPLAY_ORDER_POLICY}"
        )
    if payload.get("schema_version") != "prompt-display-order/v1":
        raise SystemExit(
            f"Unsupported display order schema in {DISPLAY_ORDER_POLICY}"
        )
    missing = sorted(REQUIRED_DISPLAY_ORDER_FIELDS - set(payload))
    if missing:
        raise SystemExit(f"Display order policy is missing fields: {missing}")
    promoted = payload.get("promoted_prompt_ids")
    if not isinstance(promoted, list) or not promoted:
        raise SystemExit("Display order policy must define promoted_prompt_ids")
    if any(not isinstance(item, str) or not item.strip() for item in promoted):
        raise SystemExit("Every promoted prompt id must be a non-empty string")
    normalized = [item.strip().upper() for item in promoted]
    if len(normalized) != len(set(normalized)):
        raise SystemExit("Display order policy contains duplicate prompt ids")
    if payload.get("fallback") != "sequence_ascending":
        raise SystemExit("Display order fallback must be sequence_ascending")
    payload = dict(payload)
    payload["promoted_prompt_ids"] = normalized
    return payload


def apply_prompt_overrides(prompts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replace legacy prompt records through one explicit versioned override registry."""
    payload = _load_json(PROMPT_OVERRIDES)
    if not isinstance(payload, dict):
        raise SystemExit(f"Prompt override registry must be an object: {PROMPT_OVERRIDES}")
    if payload.get("schema_version") != "prompt-registry-overrides/v1":
        raise SystemExit(f"Unsupported prompt override schema in {PROMPT_OVERRIDES}")
    overrides = payload.get("overrides")
    if not isinstance(overrides, list):
        raise SystemExit("Prompt override registry must define an overrides array")

    positions: dict[str, int] = {}
    for index, prompt in enumerate(prompts):
        prompt_id = str(prompt.get("id", "")).upper()
        if not prompt_id:
            raise SystemExit(f"Prompt record {index} has no id before overrides")
        if prompt_id in positions:
            raise SystemExit(f"Duplicate prompt id before overrides: {prompt_id}")
        positions[prompt_id] = index

    seen: set[str] = set()
    result = [dict(prompt) for prompt in prompts]
    for index, override in enumerate(overrides):
        if not isinstance(override, dict):
            raise SystemExit(f"Prompt override {index} is not an object")
        missing = sorted(REQUIRED_PROMPT_FIELDS - set(override))
        if missing:
            raise SystemExit(
                f"Prompt override {override.get('id', index)} is missing fields: {missing}"
            )
        override_id = str(override["id"])
        prompt_id = override_id.upper()
        if prompt_id in seen:
            raise SystemExit(f"Duplicate prompt override id: {prompt_id}")
        seen.add(prompt_id)
        if prompt_id not in positions:
            raise SystemExit(f"Prompt override references unknown prompt id: {prompt_id}")
        current = result[positions[prompt_id]]
        canonical_id = str(current.get("id", ""))
        if override_id != canonical_id:
            raise SystemExit(
                "Prompt override id must exactly match canonical identity: "
                f"{override_id} != {canonical_id}"
            )
        if str(override["seq"]) != str(current.get("seq")):
            raise SystemExit(
                f"Prompt override may not change stable sequence: {prompt_id} "
                f"{current.get('seq')} -> {override['seq']}"
            )
        result[positions[prompt_id]] = dict(override)
    return result


def apply_actionability_policy(
    prompt: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    """Return one operational prompt strengthened by the shared actionability contract."""
    prompt_id = str(prompt.get("id", "unknown"))
    next_step = str(prompt.get("nextStep", "")).strip()
    if not next_step:
        raise SystemExit(f"Prompt {prompt_id} has an empty nextStep")

    copy_content = str(prompt.get("copyContent", "")).rstrip()
    if not copy_content:
        raise SystemExit(f"Prompt {prompt_id} has empty copyContent")

    strengthened = dict(prompt)
    suffix = str(policy["next_step_suffix"]).strip()
    if suffix not in next_step:
        strengthened["nextStep"] = f"{next_step} {suffix}"

    marker = str(policy["marker"])
    appendix = str(policy["copy_content_appendix"]).strip()
    integration_marker = str(policy.get("integration_marker", "")).strip()
    has_current_integration = not integration_marker or integration_marker in copy_content
    if marker not in copy_content:
        strengthened["copyContent"] = f"{copy_content}\n\n{appendix}"
    elif not has_current_integration:
        legacy_prefix = f"{marker}\n- Do not leave NEXT COMMAND"
        legacy_start = copy_content.rfind(legacy_prefix)
        if legacy_start >= 0:
            base_content = copy_content[:legacy_start].rstrip()
            strengthened["copyContent"] = (
                f"{base_content}\n\n{appendix}" if base_content else appendix
            )
        else:
            strengthened["copyContent"] = f"{copy_content}\n\n{appendix}"
    strengthened["actionabilityPolicy"] = str(policy["policy_id"])
    return strengthened


def apply_display_order(
    prompts: list[dict[str, Any]], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    """Annotate recommendation discovery rank while preserving library chronology."""
    by_id = {str(prompt["id"]).upper(): prompt for prompt in prompts}
    promoted_ids = list(policy["promoted_prompt_ids"])
    missing = [prompt_id for prompt_id in promoted_ids if prompt_id not in by_id]
    if missing:
        raise SystemExit(f"Display order references unknown prompt ids: {missing}")

    promoted_rank = {prompt_id: index + 1 for index, prompt_id in enumerate(promoted_ids)}
    fallback_offset = len(promoted_ids) + 1000
    annotated: list[dict[str, Any]] = []
    for prompt in prompts:
        prompt_id = str(prompt["id"]).upper()
        ranked = dict(prompt)
        if prompt_id in promoted_rank:
            ranked["discoveryRank"] = promoted_rank[prompt_id]
            ranked["discoveryGroup"] = "promoted"
        else:
            ranked["discoveryRank"] = fallback_offset + int(str(prompt["seq"]))
            ranked["discoveryGroup"] = "sequence"
        ranked["displayOrderPolicy"] = str(policy["policy_id"])
        annotated.append(ranked)
    return annotated


def _validate_unique_prompt_identity(prompts: list[dict[str, Any]], label: str) -> None:
    seen_ids: set[str] = set()
    seen_sequences: set[str] = set()
    for index, prompt in enumerate(prompts):
        if not isinstance(prompt, dict):
            raise SystemExit(f"{label} prompt record {index} is not an object")
        missing = sorted(REQUIRED_PROMPT_FIELDS - set(prompt))
        if missing:
            raise SystemExit(
                f"{label} prompt {prompt.get('id', index)} is missing fields: {missing}"
            )
        prompt_id = str(prompt["id"])
        sequence = str(prompt["seq"])
        if prompt_id in seen_ids:
            raise SystemExit(f"Duplicate {label} prompt id: {prompt_id}")
        if sequence in seen_sequences:
            raise SystemExit(f"Duplicate {label} prompt sequence: {sequence}")
        seen_ids.add(prompt_id)
        seen_sequences.add(sequence)


def load_prompt_registry() -> list[dict[str, Any]]:
    """Load the canonical operational registry and apply its shared policies."""
    base = _load_json(BASE_REGISTRY)
    if not isinstance(base, list):
        raise SystemExit(f"Base prompt registry must be a JSON array: {BASE_REGISTRY}")

    prompts: list[dict[str, Any]] = list(base)
    for path in EXTENSION_REGISTRIES:
        payload = _load_json(path)
        if payload.get("schema_version") != "prompt-registry-extension/v1":
            raise SystemExit(f"Unsupported registry extension schema in {path}")
        extension_prompts = payload.get("prompts")
        if not isinstance(extension_prompts, list):
            raise SystemExit(f"Registry extension prompts must be an array: {path}")
        prompts.extend(extension_prompts)

    prompts = apply_prompt_overrides(prompts)
    _validate_unique_prompt_identity(prompts, "operational")
    actionability_policy = load_actionability_policy()
    strengthened_prompts = [
        apply_actionability_policy(prompt, actionability_policy) for prompt in prompts
    ]
    annotated_prompts = apply_display_order(
        strengthened_prompts, load_display_order_policy()
    )
    return sorted(
        annotated_prompts,
        key=lambda prompt: (int(str(prompt["seq"])), str(prompt["id"])),
    )


def load_content_prompt_registry() -> list[dict[str, Any]]:
    """Load content-only website prompts without injecting repo-execution policy text."""
    prompts: list[dict[str, Any]] = []
    for path in CONTENT_REGISTRIES:
        payload = _load_json(path)
        if not isinstance(payload, dict):
            raise SystemExit(f"Content registry must be a JSON object: {path}")
        if payload.get("schema_version") != "prompt-registry-extension/v1":
            raise SystemExit(f"Unsupported content registry schema in {path}")
        content_prompts = payload.get("prompts")
        if not isinstance(content_prompts, list):
            raise SystemExit(f"Content registry prompts must be an array: {path}")
        prompts.extend(content_prompts)

    _validate_unique_prompt_identity(prompts, "content")
    prepared: list[dict[str, Any]] = []
    for prompt in prompts:
        prompt_id = str(prompt["id"])
        if str(prompt.get("profile", "")).strip().lower() != "correspondence":
            raise SystemExit(
                f"Content prompt {prompt_id} must declare profile=correspondence"
            )
        if not str(prompt.get("nextStep", "")).strip():
            raise SystemExit(f"Content prompt {prompt_id} has an empty nextStep")
        if not str(prompt.get("copyContent", "")).strip():
            raise SystemExit(f"Content prompt {prompt_id} has empty copyContent")
        item = dict(prompt)
        item["actionabilityPolicy"] = "not-applicable:content-only"
        prepared.append(item)
    return prepared


def load_prompt_kit_registry() -> list[dict[str, Any]]:
    """Merge governed operational prompts with content-only website prompt profiles."""
    prompts = [dict(prompt) for prompt in load_prompt_registry()]
    prompts.extend(load_content_prompt_registry())
    _validate_unique_prompt_identity(prompts, "Prompt Kit")
    annotated_prompts = apply_display_order(prompts, load_display_order_policy())
    return sorted(
        annotated_prompts,
        key=lambda prompt: (int(str(prompt["seq"])), str(prompt["id"])),
    )


def _read_runtime(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"{label} is missing: {path}") from exc


def render() -> str:
    """Return the exact combined Prompt Kit HTML without writing it."""
    prompts = load_prompt_kit_registry()
    reference = _load_json(REFERENCE)
    html = build_prompt_kit.build_html(prompts, reference)
    guided_script = _read_runtime(GUIDED_RECOMMENDATIONS, "Guided recommendation behavior")
    journey_script = _read_runtime(PROMPT_JOURNEY_RUNTIME, "Guided next-step journey behavior")
    polish_script = _read_runtime(POLISH_RUNTIME, "Prompt Kit polish behavior")
    correspondence_script = _read_runtime(
        CORRESPONDENCE_RUNTIME, "Prompt Kit correspondence profile behavior"
    )
    management_script = _read_runtime(
        MANAGEMENT_RUNTIME, "Prompt Kit management profile behavior"
    )
    spec_architecture_script = _read_runtime(
        SPEC_ARCHITECTURE_RUNTIME, "Prompt Kit spec architecture profile behavior"
    )
    closing = "</body>"
    if closing not in html:
        raise SystemExit("Prompt Kit builder output is missing </body>")
    supplemental = (
        f"<script>\n{guided_script}\n</script>\n"
        f"<script>\n{journey_script}\n</script>\n"
        f"<script>\n{polish_script}\n</script>\n"
        f"<script>\n{correspondence_script}\n</script>\n"
        f"<script>\n{management_script}\n</script>\n"
        f"<script>\n{spec_architecture_script}\n</script>\n"
    )
    return html.replace(closing, supplemental + closing, 1)


def build(output: Path) -> str:
    output = validate_output_path(output)
    html = render()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the Prompt Kit website with registry extensions and policies."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the selected output is not the exact current generated website.",
    )
    parser.add_argument("--open", action="store_true", dest="open_after_build")
    args = parser.parse_args(argv)

    try:
        output = validate_output_path(args.output)
    except ValueError as exc:
        print(f"Prompt Kit output rejected: {exc}", file=sys.stderr)
        return 2

    prompts = load_prompt_kit_registry()
    expected = render()

    if args.check:
        if not output.exists():
            print(f"Prompt Kit check failed: output is missing: {output}", file=sys.stderr)
            return 1
        actual = output.read_text(encoding="utf-8")
        if actual != expected:
            print(f"Prompt Kit check failed: output is stale: {output}", file=sys.stderr)
            return 1
        print(f"Prompt Kit check passed: {output} ({len(prompts)} prompts)")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(f"Built {output} ({len(expected)} bytes, {len(prompts)} prompts)")
    if args.open_after_build:
        webbrowser.open(output.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
