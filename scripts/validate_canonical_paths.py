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
EXPECTED_APPLICABILITY = {
    "repository-development": {
        "canonical_development_checkout": True,
        "production_use_path": False,
        "temporary_worktree_root": True,
    },
    "public-web": {
        "canonical_development_checkout": True,
        "production_use_path": True,
        "temporary_worktree_root": False,
    },
    "windows-portable": {
        "canonical_development_checkout": True,
        "production_use_path": True,
        "temporary_worktree_root": False,
    },
    "phone-tablet-pwa": {
        "canonical_development_checkout": True,
        "production_use_path": True,
        "temporary_worktree_root": False,
    },
}
EXPECTED_PROOF_STATES = [
    "remote_main_contains_sha",
    "canonical_development_checkout_current",
    "production_use_path_current",
    "operator_entrypoint_observes_current",
]
EXPECTED_REQUIRED_EVIDENCE = {
    "remote_main_contains_sha": [
        "provider_default_branch_ref",
        "commit_ancestry",
    ],
    "canonical_development_checkout_current": [
        "runtime_git_root",
        "canonical_remote",
        "worktree_state",
        "remote_containment",
    ],
    "production_use_path_current": [
        "profile_use_surface_identity",
        "source_commit_or_artifact_binding",
    ],
    "operator_entrypoint_observes_current": [
        "real_entrypoint_observation",
        "intended_artifact_or_path_binding",
    ],
}
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


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, field: str, errors: list[str]) -> list[str] | None:
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must be a non-empty string list")
        return None
    if not all(_nonempty_string(item) for item in value):
        errors.append(f"{field} must contain only non-empty strings")
        return None
    if len(value) != len(set(value)):
        errors.append(f"{field} must not contain duplicates")
        return None
    return value


def _object_field(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    nested = value.get(field)
    return nested if isinstance(nested, dict) else {}


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

    valid_profiles: list[dict[str, Any]] = []
    ids: list[str] = []
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            errors.append(f"profiles[{index}] must be an object")
            continue
        profile_id = profile.get("id")
        if not _nonempty_string(profile_id):
            errors.append(f"profiles[{index}].id must be a non-empty string")
            continue
        ids.append(profile_id)
        valid_profiles.append(profile)

    if len(ids) != len(set(ids)):
        errors.append("profile IDs must be unique")
    if set(ids) != EXPECTED_PROFILES:
        errors.append(f"profile IDs drifted: {sorted(ids)}")
    by_id = {profile["id"]: profile for profile in valid_profiles}

    for profile in valid_profiles:
        profile_id = profile["id"]
        if not _nonempty_string(profile.get("purpose")):
            errors.append(f"profile {profile_id}.purpose must be a non-empty string")
        _string_list(
            profile.get("supported_machines"),
            f"profile {profile_id}.supported_machines",
            errors,
        )

        for field in (
            "canonical_development_checkout",
            "production_use_path",
            "temporary_worktree_root",
        ):
            item = profile.get(field)
            if not isinstance(item, dict):
                errors.append(f"profile {profile_id}.{field} must be an object")
                continue
            applicable = item.get("applicable")
            if not isinstance(applicable, bool):
                errors.append(
                    f"profile {profile_id}.{field} must declare applicable true/false"
                )
                continue
            expected_applicable = EXPECTED_APPLICABILITY.get(profile_id, {}).get(field)
            if expected_applicable is not None and applicable is not expected_applicable:
                errors.append(
                    f"profile {profile_id}.{field}.applicable must be "
                    f"{str(expected_applicable).lower()}"
                )

        entrypoint = profile.get("operator_entrypoint")
        if not isinstance(entrypoint, dict):
            errors.append(f"profile {profile_id}.operator_entrypoint must be an object")
        else:
            for field in ("kind", "value"):
                if not _nonempty_string(entrypoint.get(field)):
                    errors.append(
                        f"profile {profile_id}.operator_entrypoint.{field} "
                        "must be a non-empty string"
                    )

    dev = by_id.get("repository-development", {})
    dev_checkout = _object_field(dev, "canonical_development_checkout")
    if dev_checkout.get("resolver") != "git rev-parse --show-toplevel":
        errors.append("repository-development must runtime-resolve the Git root")
    if dev_checkout.get("required_remote") != REMOTE:
        errors.append("repository-development must require canonical origin")
    if dev_checkout.get("hardcoded_absolute_path") is not False:
        errors.append("repository-development must forbid a hard-coded absolute checkout path")
    if dev_checkout.get("allow_isolated_feature_worktree") is not True:
        errors.append("repository-development must allow isolated feature worktrees")
    dev_worktree = _object_field(dev, "temporary_worktree_root")
    if dev_worktree.get("second_mutable_clone_allowed") is not False:
        errors.append("temporary writer isolation must forbid a second mutable clone")
    if ".worktrees/web-excel-repair-triage/" not in str(dev_worktree.get("template", "")):
        errors.append("temporary worktree root must use the canonical .worktrees family")

    public = by_id.get("public-web", {})
    public_use = _object_field(public, "production_use_path")
    public_entry = _object_field(public, "operator_entrypoint")
    public_url = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
    if public_use.get("value") != public_url:
        errors.append("public-web production/use URL drifted")
    if public_entry.get("value") != public_url:
        errors.append("public-web operator entrypoint drifted")

    windows = by_id.get("windows-portable", {})
    windows_use = _object_field(windows, "production_use_path")
    windows_entry = _object_field(windows, "operator_entrypoint")
    if windows_use.get("value") != "Outputs/prompt-kit-portable/index.html":
        errors.append("windows-portable production/use artifact drifted")
    if windows_use.get("served_at") != "http://127.0.0.1:8765/":
        errors.append("windows-portable served_at drifted")
    if windows_entry.get("value") != "Open-Latest-PromptKit.cmd":
        errors.append("windows-portable operator entrypoint drifted")

    mobile = by_id.get("phone-tablet-pwa", {})
    mobile_use = _object_field(mobile, "production_use_path")
    if mobile_use.get("value") != "https://endeavoreverlasting.github.io/web-excel-repair-triage/":
        errors.append("phone-tablet-pwa production/use URL drifted")

    states = payload.get("proof_states")
    if not isinstance(states, list):
        errors.append("proof_states must be a list")
        states = []
    state_ids = [
        state.get("id") if isinstance(state, dict) else None
        for state in states
    ]
    if state_ids != EXPECTED_PROOF_STATES:
        errors.append(f"proof state order drifted: {state_ids}")

    for index, state in enumerate(states):
        if not isinstance(state, dict):
            errors.append(f"proof_states[{index}] must be an object")
            continue
        state_id = state.get("id")
        if not _nonempty_string(state_id):
            errors.append(f"proof_states[{index}].id must be a non-empty string")
            continue
        required = _string_list(
            state.get("requires"),
            f"proof state {state_id}.requires",
            errors,
        )
        expected_required = EXPECTED_REQUIRED_EVIDENCE.get(state_id)
        if expected_required is not None and required is not None and required != expected_required:
            errors.append(
                f"proof state {state_id}.requires drifted: "
                f"expected={expected_required} actual={required}"
            )
        forbidden = state.get("does_not_prove")
        if not isinstance(forbidden, list) or not all(
            _nonempty_string(item) for item in forbidden
        ):
            errors.append(f"proof state {state_id}.does_not_prove must be a string list")
            continue
        expected_later = EXPECTED_PROOF_STATES[index + 1 :]
        if forbidden != expected_later:
            errors.append(
                f"proof state {state_id} improperly promotes evidence; "
                f"expected does_not_prove={expected_later} actual={forbidden}"
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
