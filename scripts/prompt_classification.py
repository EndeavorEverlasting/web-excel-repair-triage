#!/usr/bin/env python3
"""Canonical Prompt Kit lifecycle classification policy and fail-closed hooks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "registry" / "prompts" / "prompt-classification.v1.json"


def load_policy() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "prompt-classification/v1":
        raise SystemExit(f"Unsupported prompt classification schema: {POLICY_PATH}")
    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        raise SystemExit("Prompt classification policy must define sections")
    seen_names: set[str] = set()
    seen_ids: set[str] = set()
    memberships: dict[str, str] = {}
    for section in sections:
        if not isinstance(section, dict):
            raise SystemExit("Prompt classification sections must be objects")
        for field in ("id", "name", "glow", "definition", "types"):
            if field not in section:
                raise SystemExit(f"Prompt classification section missing {field}")
        sid = str(section["id"]).strip()
        name = str(section["name"]).strip()
        if not sid or sid in seen_ids or not name or name in seen_names:
            raise SystemExit("Prompt classification section ids/names must be unique and non-empty")
        seen_ids.add(sid)
        seen_names.add(name)
        types = section["types"]
        if not isinstance(types, list) or not types:
            raise SystemExit(f"Prompt classification section {name} must define types")
        for value in types:
            prompt_type = str(value).strip()
            if not prompt_type:
                raise SystemExit(f"Prompt classification section {name} has an empty type")
            if prompt_type in memberships:
                raise SystemExit(f"Prompt type {prompt_type!r} maps to multiple lifecycle sections")
            memberships[prompt_type] = name
    return payload


def type_to_section() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for section in load_policy()["sections"]:
        for prompt_type in section["types"]:
            mapping[str(prompt_type).strip()] = str(section["name"]).strip()
    return mapping


def site_sections() -> list[dict[str, Any]]:
    return [
        {
            "name": str(section["name"]),
            "glow": str(section["glow"]),
            "types": list(section["types"]),
        }
        for section in load_policy()["sections"]
    ]


def require_known_prompt_type(prompt_type: str) -> str:
    value = str(prompt_type).strip()
    mapping = type_to_section()
    if value not in mapping:
        raise SystemExit(
            f"Unclassified prompt type {value!r}; classify it in "
            f"{POLICY_PATH.relative_to(REPO_ROOT)} before adding the prompt"
        )
    return mapping[value]


def validate_prompt_classification(
    prompts: list[dict[str, Any]], label: str = "Prompt Kit"
) -> None:
    mapping = type_to_section()
    unmapped: dict[str, list[str]] = {}
    for prompt in prompts:
        prompt_type = str(prompt.get("type", "")).strip()
        if prompt_type not in mapping:
            unmapped.setdefault(prompt_type or "<empty>", []).append(
                f"{prompt.get('id', '?')}:{prompt.get('name', '?')}"
            )
    if unmapped:
        raise SystemExit(
            f"{label} contains prompt types without lifecycle classification: {unmapped}"
        )


def classification_summary(prompts: list[dict[str, Any]]) -> dict[str, Any]:
    validate_prompt_classification(prompts)
    mapping = type_to_section()
    counts = {section["name"]: 0 for section in load_policy()["sections"]}
    used: set[str] = set()
    for prompt in prompts:
        prompt_type = str(prompt["type"]).strip()
        used.add(prompt_type)
        counts[mapping[prompt_type]] += 1
    return {
        "policy_id": load_policy()["policy_id"],
        "prompt_counts_by_section": counts,
        "unused_mapped_types": sorted(set(mapping) - used),
    }
