#!/usr/bin/env python3
"""Prompt Kit Compute Mode product projection.

This module bridges the Prompt Compilation execution-profile authority into the
browser product without turning the browser into a second policy engine.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts import prompt_context_engine as context_engine
from scripts import prompt_language_compiler as compiler

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "registry" / "prompts" / "prompt-compute-mode.v1.json"


class ComputeModeError(ValueError):
    """Raised when the product Compute Mode contract fails closed."""


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ComputeModeError(f"Compute Mode policy is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ComputeModeError(f"Compute Mode policy is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "prompt-compute-mode/v1":
        raise ComputeModeError("Compute Mode policy must use prompt-compute-mode/v1")
    if payload.get("product_default") != context_engine.PRODUCT_DEFAULT_PROFILE:
        raise ComputeModeError("Compute Mode product default must match Context Engine authority")
    profiles = payload.get("profiles")
    if profiles != ["exhaustive", "efficient"]:
        raise ComputeModeError("Compute Mode profiles must be exhaustive then efficient")
    if payload.get("profile_precedence") != list(context_engine.PROFILE_PRECEDENCE):
        raise ComputeModeError("Compute Mode precedence must match Context Engine authority")
    legacy = payload.get("legacy_exhaustive_section")
    if not isinstance(legacy, dict) or not legacy.get("start_marker") or not legacy.get("end_marker"):
        raise ComputeModeError("Compute Mode policy must bind the legacy exhaustive section")
    semantic = payload.get("semantic_overlay")
    if not isinstance(semantic, dict):
        raise ComputeModeError("Compute Mode policy must define semantic_overlay")
    for key in ("goal_template", "obligation", "invariants"):
        if key not in semantic:
            raise ComputeModeError(f"semantic_overlay missing {key}")
    return payload


def semantic_overlay_for_prompt(prompt_id: str, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Materialize the bounded execution-overlay semantics for one prompt identity."""
    policy = policy or load_policy()
    prompt_id = str(prompt_id).strip().upper()
    semantic = policy["semantic_overlay"]
    result = {
        "schema_version": "prompt-semantics/v1",
        "prompt_id": prompt_id,
        "goal": str(semantic["goal_template"]).format(prompt_id=prompt_id),
        "obligations": [dict(semantic["obligation"])],
        "invariants": list(semantic["invariants"]),
    }
    return compiler.validate_semantics(result)


def build_product_manifest(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build deterministic browser data from compiler-owned profile definitions."""
    policy = policy or load_policy()
    profiles: dict[str, Any] = {}
    for profile_name in policy["profiles"]:
        resolved = context_engine.resolve_execution_profile(explicit_run_override=profile_name)
        profile = resolved["profile"]
        overlay = compiler.render_execution_profile_overlay(profile)
        profiles[profile_name] = {
            "overlay": overlay,
            "profile_sha256": compiler.canonical_sha256(profile),
            "language_engine_revision": compiler.load_policy()["language_engine_revision"],
        }
    return {
        "schema_version": "prompt-compute-mode-product/v1",
        "product_default": policy["product_default"],
        "profile_precedence": list(policy["profile_precedence"]),
        "eligible_actionability_policy": policy["eligible_actionability_policy"],
        "compiled_overlay_marker": policy["compiled_overlay_marker"],
        "legacy_exhaustive_section": dict(policy["legacy_exhaustive_section"]),
        "profiles": profiles,
    }


def _remove_legacy_exhaustive_section(text: str, policy: dict[str, Any]) -> str:
    legacy = policy["legacy_exhaustive_section"]
    start_marker = str(legacy["start_marker"])
    end_marker = str(legacy["end_marker"])
    start = text.find(start_marker)
    if start < 0:
        raise ComputeModeError("canonical prompt is missing the exhaustive compute section")
    end = text.find(end_marker, start)
    if end < 0:
        raise ComputeModeError("canonical prompt is missing the post-exhaustive section boundary")
    if text.find(start_marker, start + len(start_marker)) >= 0:
        raise ComputeModeError("canonical prompt contains duplicate exhaustive compute sections")
    before = text[:start].rstrip()
    after = text[end:].lstrip()
    return f"{before}\n\n{after}" if before else after


def compose_effective_prompt(
    canonical_prompt: str,
    profile_name: str,
    *,
    policy: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> str:
    """Compose canonical prompt prose with one compiler-owned execution overlay."""
    policy = policy or load_policy()
    manifest = manifest or build_product_manifest(policy)
    canonical_prompt = str(canonical_prompt).rstrip()
    if not canonical_prompt:
        raise ComputeModeError("canonical prompt must not be empty")
    profile_name = str(profile_name).strip().lower()
    if profile_name not in manifest["profiles"]:
        raise ComputeModeError(f"unknown Compute Mode profile: {profile_name}")
    base = canonical_prompt
    if profile_name == "efficient":
        base = _remove_legacy_exhaustive_section(base, policy)
    overlay = str(manifest["profiles"][profile_name]["overlay"]).strip()
    marker = str(policy["compiled_overlay_marker"])
    if marker not in overlay:
        raise ComputeModeError("compiler overlay is missing the declared marker")
    return f"{base.rstrip()}\n\n{overlay}\n"


def is_eligible_prompt(prompt: dict[str, Any], policy: dict[str, Any] | None = None) -> bool:
    policy = policy or load_policy()
    return str(prompt.get("actionabilityPolicy", "")) == str(policy["eligible_actionability_policy"])
