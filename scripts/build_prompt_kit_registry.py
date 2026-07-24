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
)
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
    "applies_to",
    "next_step_suffix",
    "allowed_none_value",
    "forbidden_solo_actions",
    "copy_content_appendix",
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

    marker = str(payload["marker"])
    if marker not in str(payload["copy_content_appendix"]):
        raise SystemExit("Actionability appendix must include its declared marker")
    return payload


def apply_actionability_policy(
    prompt: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    """Return one prompt strengthened by the repository-wide actionability contract."""
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
    if marker not in copy_content:
        strengthened["copyContent"] = f"{copy_content}\n\n{appendix}"

    strengthened["actionabilityPolicy"] = str(policy["policy_id"])
    return strengthened


def load_prompt_registry() -> list[dict[str, Any]]:
    """Load, validate, strengthen, and merge canonical prompts and extensions."""
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

    policy = load_actionability_policy()
    seen_ids: set[str] = set()
    seen_sequences: set[str] = set()
    strengthened_prompts: list[dict[str, Any]] = []
    for index, prompt in enumerate(prompts):
        if not isinstance(prompt, dict):
            raise SystemExit(f"Prompt record {index} is not an object")
        missing = sorted(REQUIRED_PROMPT_FIELDS - set(prompt))
        if missing:
            raise SystemExit(f"Prompt {prompt.get('id', index)} is missing fields: {missing}")
        prompt_id = str(prompt["id"])
        sequence = str(prompt["seq"])
        if prompt_id in seen_ids:
            raise SystemExit(f"Duplicate prompt id: {prompt_id}")
        if sequence in seen_sequences:
            raise SystemExit(f"Duplicate prompt sequence: {sequence}")
        seen_ids.add(prompt_id)
        seen_sequences.add(sequence)
        strengthened_prompts.append(apply_actionability_policy(prompt, policy))

    return sorted(strengthened_prompts, key=lambda prompt: int(str(prompt["seq"])))


def render() -> str:
    """Return the exact combined Prompt Kit HTML without writing it."""
    prompts = load_prompt_registry()
    reference = _load_json(REFERENCE)
    return build_prompt_kit.build_html(prompts, reference)


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

    prompts = load_prompt_registry()
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
