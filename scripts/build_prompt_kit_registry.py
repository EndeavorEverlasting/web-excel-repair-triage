#!/usr/bin/env python3
"""Build the Prompt Kit website from the base registry plus tracked extensions."""
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


def load_prompt_registry() -> list[dict[str, Any]]:
    """Load, validate, and merge the canonical registry and extensions."""
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

    seen_ids: set[str] = set()
    seen_sequences: set[str] = set()
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

    return sorted(prompts, key=lambda prompt: int(str(prompt["seq"])))


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
        description="Build the Prompt Kit website with skill-development registry extensions."
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
