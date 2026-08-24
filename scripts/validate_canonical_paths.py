#!/usr/bin/env python3
"""Fail-closed validation for the repository canonical path/profile contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "canonical-paths.v1.json"
REPOSITORY = "EndeavorEverlasting/web-excel-repair-triage"
REMOTE = "https://github.com/EndeavorEverlasting/web-excel-repair-triage.git"
EXPECTED_PROFILES = {
    "repository-development",
    "public-web",
    "windows-portable",
    "phone-tablet-pwa",
}
EXPECTED_PROOF_STATES = [
    "remote_main_contains_sha",
    "canonical_development_checkout_current",
    "production_use_path_current",
    "operator_entrypoint_observes_current",
]
WINDOWS_PERSON_PATH = re.compile(r"(?i)[A-Z]:[\\/]Users[\\/](?!<|%|\$)[^\\/]+")
UNIX_PERSON_PATH = re.compile(r"/(?:home|Users)/(?!<|%|\$)[^/]+")


class CanonicalPathValidationError(ValueError):
    """Raised when the canonical path contract is missing or malformed."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CanonicalPathValidationError(f"missing canonical path contract: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CanonicalPathValidationError(f"invalid canonical path JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise CanonicalPathValidationError("canonical path contract root must be an object")
    return payload


def _all_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)


def validate_contract(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != "web-excel-canonical-paths/v1":
        errors.append("unsupported schema_version")
    if payload.get("repository") != REPOSITORY:
        errors.append("repository identity is not canonical")
    if payload.get("canonical_remote") != REMOTE:
        errors.append("canonical_remote drifted")
    if payload.get("default_branch") != "main":
        errors.append("default_branch must be main")

    owner = payload.get("deep_repair_owner")
    if not isinstance(owner, dict) or owner.get("prompt_id") != "P92":
        errors.append("P92 must remain the deep canonical-path repair owner")

    policy = payload.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        expected = {
            "path_authority": "harness/canonical-paths.v1.json",
            "model_chosen_paths": False,
            "second_mutable_clone_allowed": False,
            "parallel_writer_strategy": "git-worktree",
            "temporary_worktree_root_strategy": "sibling-under-canonical-parent",
            "proof_implication": "none",
        }
        for field, value in expected.items():
            if policy.get(field) != value:
                errors.append(f"policy.{field} must equal {value!r}")

    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        errors.append("profiles must be a list")
        profiles = []
    ids = [item.get("id") for item in profiles if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("profile IDs must be unique")
    if set(ids) != EXPECTED_PROFILES:
        errors.append(f"profile IDs drifted: {sorted(str(item) for item in ids)}")
    by_id = {
        item["id"]: item
        for item in profiles
        if isinstance(item, dict) and item.get("id")
    }
    for profile_id, profile in by_id.items():
        for field in (
            "purpose",
            "supported_machines",
            "canonical_development_checkout",
            "production_use_path",
            "temporary_worktree_root",
            "operator_entrypoint",
        ):
            if field not in profile:
                errors.append(f"profile {profile_id} missing {field}")
        for field in (
            "canonical_development_checkout",
            "production_use_path",
            "temporary_worktree_root",
        ):
            item = profile.get(field)
            if not isinstance(item, dict) or not isinstance(item.get("applicable"), bool):
                errors.append(
                    f"profile {profile_id}.{field} must declare applicable true/false"
                )
        entrypoint = profile.get("operator_entrypoint")
        if (
            not isinstance(entrypoint, dict)
            or not entrypoint.get("kind")
            or not entrypoint.get("value")
        ):
            errors.append(f"profile {profile_id} must declare the real operator entrypoint")

    dev = by_id.get("repository-development", {})
    dev_checkout = dev.get("canonical_development_checkout", {}) if isinstance(dev, dict) else {}
    if dev_checkout.get("resolver") != "git rev-parse --show-toplevel":
        errors.append("repository-development must runtime-resolve the Git root")
    if dev_checkout.get("required_remote") != REMOTE:
        errors.append("repository-development must require canonical origin")
    if dev_checkout.get("hardcoded_absolute_path") is not False:
        errors.append("repository-development must forbid a hard-coded absolute checkout path")
    if dev_checkout.get("allow_isolated_feature_worktree") is not True:
        errors.append("repository-development must allow isolated feature worktrees")
    dev_worktree = dev.get("temporary_worktree_root", {}) if isinstance(dev, dict) else {}
    if dev_worktree.get("second_mutable_clone_allowed") is not False:
        errors.append("temporary writer isolation must forbid a second mutable clone")
    if ".worktrees/web-excel-repair-triage/" not in str(dev_worktree.get("template", "")):
        errors.append("temporary worktree root must use the canonical .worktrees family")

    public = by_id.get("public-web", {})
    if public.get("production_use_path", {}).get("value") != (
        "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
    ):
        errors.append("public-web production/use URL drifted")
    if public.get("operator_entrypoint", {}).get("value") != (
        "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
    ):
        errors.append("public-web operator entrypoint drifted")

    windows = by_id.get("windows-portable", {})
    if windows.get("production_use_path", {}).get("value") != (
        "Outputs/prompt-kit-portable/index.html"
    ):
        errors.append("windows-portable production/use artifact drifted")
    if windows.get("production_use_path", {}).get("served_at") != "http://127.0.0.1:8765/":
        errors.append("windows-portable served_at drifted")
    if windows.get("operator_entrypoint", {}).get("value") != "Open-Latest-PromptKit.cmd":
        errors.append("windows-portable operator entrypoint drifted")

    mobile = by_id.get("phone-tablet-pwa", {})
    if mobile.get("production_use_path", {}).get("value") != (
        "https://endeavoreverlasting.github.io/web-excel-repair-triage/"
    ):
        errors.append("phone-tablet-pwa production/use URL drifted")

    states = payload.get("proof_states")
    if not isinstance(states, list):
        errors.append("proof_states must be a list")
        states = []
    state_ids = [item.get("id") for item in states if isinstance(item, dict)]
    if state_ids != EXPECTED_PROOF_STATES:
        errors.append(f"proof state order drifted: {state_ids}")
    for index, state in enumerate(states):
        if not isinstance(state, dict):
            errors.append("proof state entries must be objects")
            continue
        required = state.get("requires")
        if not isinstance(required, list) or not required:
            errors.append(f"proof state {state.get('id')} must declare evidence requirements")
        forbidden = state.get("does_not_prove")
        if not isinstance(forbidden, list):
            errors.append(f"proof state {state.get('id')} must declare does_not_prove")
            continue
        expected_later = EXPECTED_PROOF_STATES[index + 1 :]
        missing = [item for item in expected_later if item not in forbidden]
        if missing:
            errors.append(
                f"proof state {state.get('id')} improperly promotes evidence; "
                f"missing does_not_prove={missing}"
            )

    for text in _all_strings(payload):
        if WINDOWS_PERSON_PATH.search(text) or UNIX_PERSON_PATH.search(text):
            errors.append(f"hard-coded person-specific absolute path is forbidden: {text!r}")
            break
    return errors


def require_valid_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = load_contract(path)
    errors = validate_contract(payload)
    if errors:
        raise CanonicalPathValidationError("; ".join(errors))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the canonical path/profile contract.")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = require_valid_contract()
    except CanonicalPathValidationError as exc:
        print(f"Canonical path contract: FAIL - {exc}")
        return 1
    if args.summary:
        print(
            "Canonical path contract: PASS "
            f"({len(payload['profiles'])} profiles, "
            f"{len(payload['proof_states'])} independent proof states)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
