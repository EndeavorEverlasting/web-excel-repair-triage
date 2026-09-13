#!/usr/bin/env python3
"""Fail-closed validator for Prompt Kit privacy, storage, and deployment boundaries."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-cross-device-access.v1.json"
PAGES_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"
GUIDE_PATH = ROOT / "docs" / "PROMPT_KIT_PRIVACY_STORAGE.md"
GITIGNORE_PATH = ROOT / ".gitignore"

REQUIRED_PLANES = {"prompt_canon", "personal_state", "private_sync", "collective_learning"}
EXPECTED_OUTPUT_ALLOWLIST = {
    "schema_version",
    "canon_version",
    "prompt.prompt_id",
    "prompt.prompt_version",
    "behavior.action",
    "behavior.outcome",
    "behavior.correction_bucket",
    "behavior.retry_bucket",
    "behavior.duration_bucket",
    "transition.from_prompt",
    "transition.to_prompt",
    "count",
}
REQUIRED_FORBIDDEN_CLASSES = {
    "identity",
    "persistent_pseudonym",
    "private_sync",
    "device",
    "session",
    "project",
    "raw_text",
    "exact_time",
}
REQUIRED_SYNC_ALLOWED_FIELDS = {
    "schema_version",
    "canon_version",
    "favorites",
    "collections",
    "saved_variants",
    "preferences",
    "personal_tags",
    "explicitly_saved_notes",
    "saved_workflows",
}
EXPECTED_PAGES_BUNDLE = {
    ("/", "web/prompt-kit-mobile/", "launcher-pwa"),
    (
        "/afk-agent-flow/index.html",
        "scripts/build_prompt_kit_registry.py -> web/prompt-kit/index.html",
        "generated-canonical-app",
    ),
    (
        "/afk-agent-flow/resources.v1.json",
        "web/prompt-kit/resources.v1.json",
        "public-resource-index",
    ),
    (
        "/prompt-kit/index.html",
        "web/prompt-kit-legacy-redirect/index.html",
        "legacy-redirect",
    ),
    (
        "/operant/index.html",
        "web/operant-legacy-redirect/index.html",
        "legacy-redirect",
    ),
    ("/roster-log-v2/", "web/roster-log-v2/", "separate-static-app"),
}
PUBLIC_SOURCE_ROOTS = (
    "web/prompt-kit-mobile",
    "web/prompt-kit",
    "web/prompt-kit-legacy-redirect",
    "web/operant-legacy-redirect",
    "web/roster-log-v2",
)
REQUIRED_PAGES_WORKFLOW_FRAGMENTS = (
    'mkdir -p "$SITE_ROOT/afk-agent-flow"',
    'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/afk-agent-flow/index.html"',
    'cp web/prompt-kit/resources.v1.json "$SITE_ROOT/afk-agent-flow/resources.v1.json"',
    'cp -R web/prompt-kit-mobile/. "$SITE_ROOT/"',
    'cmp "$SITE_ROOT/afk-agent-flow/index.html" web/prompt-kit/index.html',
    'uses: actions/deploy-pages@v5',
)
REQUIRED_PRIVATE_IGNORE_PATTERNS = {
    ".promptkit/",
    "*.pkenc",
    "promptkit.db",
    "promptkit.local.db",
    "promptkit-journal*",
    "promptkit-reducer-buffer*",
    "*.promptkit-key",
    "*.promptkit-recovery",
    "*.pairing-secret",
}
FORBIDDEN_PUBLIC_BASENAMES = {
    "promptkit.db",
    "promptkit.local.db",
    "credentials.json",
    "credential.json",
    "secrets.json",
    "secret.json",
    "tokens.json",
    "token.json",
    "auth.json",
}
FORBIDDEN_PUBLIC_SUFFIXES = (
    ".pkenc",
    ".promptkit-key",
    ".promptkit-recovery",
    ".pairing-secret",
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".kdbx",
)
FORBIDDEN_PUBLIC_COMPONENTS = {".promptkit", "saves", "crash_dumps"}


class PrivacyStorageError(RuntimeError):
    """Raised when an owned privacy/storage contract invariant drifts."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PrivacyStorageError(f"missing required file: {path.relative_to(ROOT).as_posix()}") from exc
    except json.JSONDecodeError as exc:
        raise PrivacyStorageError(f"invalid JSON: {path.relative_to(ROOT).as_posix()}: {exc}") from exc
    if not isinstance(value, dict):
        raise PrivacyStorageError(f"JSON root must be an object: {path.relative_to(ROOT).as_posix()}")
    return value


def _require_nonempty_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise PrivacyStorageError(f"{field} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise PrivacyStorageError(f"{field} contains an empty or non-string item")
    if len(value) != len(set(value)):
        raise PrivacyStorageError(f"{field} contains duplicates")
    return value


def _require_substrings(values: list[str], required: tuple[str, ...], field: str) -> None:
    joined = "\n".join(values).lower()
    for fragment in required:
        if fragment.lower() not in joined:
            raise PrivacyStorageError(f"{field} is missing required privacy concept: {fragment}")


def is_forbidden_public_path(path: str) -> bool:
    """Return True when a tracked public-source path looks like private runtime/secret state."""
    normalized = PurePosixPath(path)
    parts = {part.lower() for part in normalized.parts}
    name = normalized.name.lower()
    if parts & FORBIDDEN_PUBLIC_COMPONENTS:
        return True
    if name in FORBIDDEN_PUBLIC_BASENAMES:
        return True
    if name == ".env" or name.startswith(".env."):
        return True
    if name.startswith("promptkit-journal") or name.startswith("promptkit-reducer-buffer"):
        return True
    return name.endswith(FORBIDDEN_PUBLIC_SUFFIXES)


def validate_public_tracked_paths(paths: list[str]) -> None:
    violations = sorted(path for path in paths if is_forbidden_public_path(path))
    if violations:
        raise PrivacyStorageError(
            "tracked private/secret-like artifacts exist under GitHub Pages source roots: "
            + ", ".join(violations)
        )


def tracked_public_files() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--", *PUBLIC_SOURCE_ROOTS],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise PrivacyStorageError(f"git ls-files failed while inspecting Pages sources: {stderr}")
    paths = [item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]
    if not paths:
        raise PrivacyStorageError("no tracked files found under canonical GitHub Pages source roots")
    return paths


def validate_contract(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("privacy_storage_guide") != "docs/PROMPT_KIT_PRIVACY_STORAGE.md":
        raise PrivacyStorageError("privacy storage guide ownership drifted")

    architecture = payload.get("data_plane_architecture")
    if not isinstance(architecture, dict):
        raise PrivacyStorageError("data_plane_architecture must be an object")
    invariant = str(architecture.get("invariant", ""))
    for phrase in ("GitHub contains product truth", "user's device contains personal truth", "No private user state"):
        if phrase not in invariant:
            raise PrivacyStorageError(f"data plane invariant is missing: {phrase}")
    planes = architecture.get("planes")
    if not isinstance(planes, dict) or set(planes) != REQUIRED_PLANES:
        raise PrivacyStorageError(f"data planes must be exactly {sorted(REQUIRED_PLANES)}")

    canon = planes["prompt_canon"]
    if not isinstance(canon, dict):
        raise PrivacyStorageError("prompt_canon plane must be an object")
    canon_forbidden = _require_nonempty_string_list(canon.get("must_never_receive"), "prompt_canon.must_never_receive")
    _require_substrings(
        canon_forbidden,
        ("user identity", "device", "session", "favorites", "project", "raw user"),
        "prompt_canon.must_never_receive",
    )

    personal = planes["personal_state"]
    if personal.get("authority") != "user-device" or personal.get("plaintext_location") != "device-only":
        raise PrivacyStorageError("personal_state must remain device-only plaintext authority")
    personal_egress = _require_nonempty_string_list(personal.get("egress"), "personal_state.egress")
    _require_substrings(personal_egress, ("encrypted", "PrivacyReducer"), "personal_state.egress")

    private_sync = planes["private_sync"]
    if private_sync.get("prompt_kit_owned_backend_required") is not False:
        raise PrivacyStorageError("private_sync v1 must not require a Prompt Kit-owned backend")
    if private_sync.get("v1_transport") != "user-selected storage or file transfer":
        raise PrivacyStorageError("private_sync v1 transport drifted")
    sync_plaintext_forbidden = _require_nonempty_string_list(
        private_sync.get("must_never_receive_plaintext"),
        "private_sync.must_never_receive_plaintext",
    )
    _require_substrings(
        sync_plaintext_forbidden,
        ("raw prompt", "local journal", "project", "user identity", "encryption keys"),
        "private_sync.must_never_receive_plaintext",
    )

    learning = planes["collective_learning"]
    if learning.get("v1_network_ingestion_required") is not False:
        raise PrivacyStorageError("collective_learning v1 network ingestion must remain optional/unimplemented")
    learning_forbidden = _require_nonempty_string_list(
        learning.get("must_never_receive"), "collective_learning.must_never_receive"
    )
    _require_substrings(
        learning_forbidden,
        ("persistent pseudonymous", "session", "project", "raw user", "exact activity"),
        "collective_learning.must_never_receive",
    )

    deployment = payload.get("deployment_surfaces")
    if not isinstance(deployment, dict) or set(deployment) != {"repository_authority", "github_pages", "user_device"}:
        raise PrivacyStorageError("deployment surfaces must be repository_authority, github_pages, and user_device")
    repository = deployment["repository_authority"]
    if repository.get("private_user_data_allowed") is not False:
        raise PrivacyStorageError("repository authority must reject private user data")
    github_pages = deployment["github_pages"]
    if github_pages.get("source_workflow") != ".github/workflows/prompt-kit-pages.yml":
        raise PrivacyStorageError("GitHub Pages workflow owner drifted")
    bundle = github_pages.get("bundle")
    if not isinstance(bundle, list):
        raise PrivacyStorageError("GitHub Pages bundle must be a list")
    actual_bundle = {
        (str(item.get("public_path")), str(item.get("source")), str(item.get("kind")))
        for item in bundle
        if isinstance(item, dict)
    }
    if actual_bundle != EXPECTED_PAGES_BUNDLE or len(bundle) != len(EXPECTED_PAGES_BUNDLE):
        raise PrivacyStorageError("GitHub Pages bundle mapping drifted from the canonical deployment layout")
    published_forbidden = _require_nonempty_string_list(
        github_pages.get("must_never_publish"), "github_pages.must_never_publish"
    )
    _require_substrings(
        published_forbidden,
        ("personal state", "local journal", "encrypted save", "device", "project", "encryption keys", "PrivacyReducer"),
        "github_pages.must_never_publish",
    )
    user_device = deployment["user_device"]
    stores = user_device.get("logical_stores")
    if not isinstance(stores, dict) or set(stores) != {
        "public_cache",
        "personal_state",
        "local_journal",
        "privacy_reducer_buffer",
        "sync_state",
        "secrets",
    }:
        raise PrivacyStorageError("user-device logical store ownership drifted")
    if user_device.get("portable_export") != "promptkit-save.pkenc":
        raise PrivacyStorageError("portable encrypted save filename drifted")

    capsule = payload.get("sync_capsule_contract")
    if not isinstance(capsule, dict):
        raise PrivacyStorageError("sync_capsule_contract must be an object")
    if capsule.get("schema") != "promptkit-sync-capsule/v1":
        raise PrivacyStorageError("sync capsule schema drifted")
    if capsule.get("serialization") != "positive-allowlist-only":
        raise PrivacyStorageError("sync capsule must remain positive-allowlist-only")
    if capsule.get("encryption_required_before_transport") is not True:
        raise PrivacyStorageError("sync capsule encryption must be required before transport")
    allowed_fields = set(_require_nonempty_string_list(capsule.get("allowed_fields"), "sync_capsule.allowed_fields"))
    if allowed_fields != REQUIRED_SYNC_ALLOWED_FIELDS:
        raise PrivacyStorageError("sync capsule allowed fields drifted")
    forbidden_pre_encryption = _require_nonempty_string_list(
        capsule.get("forbidden_pre_encryption"), "sync_capsule.forbidden_pre_encryption"
    )
    _require_substrings(
        forbidden_pre_encryption,
        ("raw prompt", "local journal", "repository", "session", "device", "PrivacyReducer", "encryption keys"),
        "sync_capsule.forbidden_pre_encryption",
    )

    reducer = payload.get("privacy_reducer_contract")
    if not isinstance(reducer, dict):
        raise PrivacyStorageError("privacy_reducer_contract must be an object")
    if reducer.get("schema") != "collective-evidence/v1":
        raise PrivacyStorageError("PrivacyReducer output schema drifted")
    if reducer.get("network_access") != "forbidden":
        raise PrivacyStorageError("PrivacyReducer itself must not have network access")
    output_allowlist = set(_require_nonempty_string_list(reducer.get("output_allowlist"), "privacy_reducer.output_allowlist"))
    if output_allowlist != EXPECTED_OUTPUT_ALLOWLIST:
        raise PrivacyStorageError("PrivacyReducer output allowlist drifted")
    forbidden_classes = reducer.get("forbidden_output_classes")
    if not isinstance(forbidden_classes, dict) or set(forbidden_classes) != REQUIRED_FORBIDDEN_CLASSES:
        raise PrivacyStorageError("PrivacyReducer forbidden output classes drifted")
    for class_name in REQUIRED_FORBIDDEN_CLASSES:
        _require_nonempty_string_list(forbidden_classes[class_name], f"privacy_reducer.{class_name}")
    forbidden_flat = {item.lower() for values in forbidden_classes.values() for item in values}
    for forbidden_name in ("user_id", "installation_id", "vault_id", "device_id", "session_id", "repository", "task_text", "timestamp"):
        if forbidden_name not in forbidden_flat:
            raise PrivacyStorageError(f"PrivacyReducer forbidden field missing: {forbidden_name}")
    if output_allowlist & forbidden_flat:
        raise PrivacyStorageError("PrivacyReducer allowlist overlaps forbidden fields")

    batching = reducer.get("batching")
    expected_batching = {
        "minimum_local_count": 5,
        "minimum_distinct_aggregates": 3,
        "minimum_batch_age_hours": 6,
        "randomized_flush_window_hours": [12, 24],
        "aggregate_buffer_max_days": 90,
    }
    if batching != expected_batching:
        raise PrivacyStorageError("PrivacyReducer local batching profile drifted")
    reducer_invariants = _require_nonempty_string_list(reducer.get("invariants"), "privacy_reducer.invariants")
    _require_substrings(
        reducer_invariants,
        ("Unknown output fields fail closed", "hashed", "identical collective evidence", "local aggregate buffer"),
        "privacy_reducer.invariants",
    )

    backend = payload.get("v1_backend_policy")
    if not isinstance(backend, dict) or backend.get("prompt_kit_owned_backend_required") is not False:
        raise PrivacyStorageError("v1 backend policy must remain no-Prompt-Kit-backend-required")
    if backend.get("required_remote_infrastructure") != ["GitHub repository", "GitHub Pages static hosting"]:
        raise PrivacyStorageError("v1 required remote infrastructure drifted")
    for status_field in ("future_hosted_sync_status", "future_collective_ingestion_status"):
        if backend.get(status_field) != "not implemented by this contract":
            raise PrivacyStorageError(f"{status_field} overclaims implementation")

    return {
        "planes": sorted(planes),
        "pages_bundle_count": len(bundle),
        "privacy_output_field_count": len(output_allowlist),
        "sync_allowed_field_count": len(allowed_fields),
    }


def validate_repository_surfaces() -> None:
    pages = PAGES_WORKFLOW_PATH.read_text(encoding="utf-8")
    for fragment in REQUIRED_PAGES_WORKFLOW_FRAGMENTS:
        if fragment not in pages:
            raise PrivacyStorageError(f"Pages workflow no longer proves deployment mapping: {fragment}")

    tracked = tracked_public_files()
    validate_public_tracked_paths(tracked)

    guide = GUIDE_PATH.read_text(encoding="utf-8")
    for phrase in (
        "Prompt Canon",
        "Personal State",
        "Private Sync",
        "Collective Learning",
        "promptkit-save.pkenc",
        "No Prompt Kit-owned backend is required for v1",
        "web/prompt-kit-mobile/",
        "/afk-agent-flow/index.html",
        "raw Local Journal history stays on the device",
        "git ls-files",
    ):
        if phrase not in guide:
            raise PrivacyStorageError(f"privacy/storage guide is missing required text: {phrase}")

    ignore_lines = {
        line.strip()
        for line in GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    missing = sorted(REQUIRED_PRIVATE_IGNORE_PATTERNS - ignore_lines)
    if missing:
        raise PrivacyStorageError(f".gitignore is missing Prompt Kit private-state patterns: {missing}")


def validate() -> dict[str, Any]:
    summary = validate_contract(_load_json(CONTRACT_PATH))
    validate_repository_surfaces()
    return {
        "schema_version": "prompt-kit-privacy-storage-validation/v1",
        "status": "PASS",
        **summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate()
    except (PrivacyStorageError, FileNotFoundError) as exc:
        print(f"prompt-kit-privacy-storage: FAIL: {exc}")
        return 1
    if args.summary:
        print(
            "prompt-kit-privacy-storage: PASS "
            f"({len(report['planes'])} planes, {report['pages_bundle_count']} Pages surfaces, "
            f"{report['sync_allowed_field_count']} sync fields, {report['privacy_output_field_count']} learning fields)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
