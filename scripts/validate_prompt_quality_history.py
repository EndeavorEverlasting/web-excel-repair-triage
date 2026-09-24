#!/usr/bin/env python3
"""Fail-closed Prompt Kit quality-history and effective-identity validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_prompt_kit_registry as builder  # noqa: E402
from scripts import prompt_registry_product_boundaries as boundaries  # noqa: E402

CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-quality-history.v1.json"
PROMPT_ID_RE = re.compile(r"^P\d{2,4}$")
EFFECTIVE_IDENTITY_CHANGE_VALUES = {
    "preserve_canonical",
    "replacement_authorized",
}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _load_contract() -> dict[str, Any]:
    payload = _json(CONTRACT_PATH)
    if payload.get("schema_version") != "prompt-quality-history/v1":
        raise ValueError("unsupported prompt quality history schema")
    sources = payload.get("canonical_body_sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("canonical_body_sources must be a non-empty list")

    effective_identity = payload.get("effective_identity")
    if not isinstance(effective_identity, dict):
        raise ValueError("effective_identity must be an object")
    exceptions = effective_identity.get("temporary_exceptions", [])
    if not isinstance(exceptions, list):
        raise ValueError("temporary_exceptions must be a list")
    seen_exception_ids: set[str] = set()
    for item in exceptions:
        if not isinstance(item, dict):
            raise ValueError("temporary exception must be an object")
        for field in ("prompt_id", "reason", "owner_pr", "remove_when"):
            if field not in item:
                raise ValueError(f"temporary exception is missing {field}: {item!r}")
        prompt_id = str(item["prompt_id"])
        if not PROMPT_ID_RE.fullmatch(prompt_id):
            raise ValueError(f"invalid temporary-exception prompt ID: {prompt_id}")
        if prompt_id in seen_exception_ids:
            raise ValueError(f"duplicate temporary exception: {prompt_id}")
        seen_exception_ids.add(prompt_id)
        if not isinstance(item["owner_pr"], int) or item["owner_pr"] < 1:
            raise ValueError(f"temporary exception owner_pr must be positive: {prompt_id}")
        for field in ("reason", "remove_when"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"temporary exception {prompt_id} requires {field}")
    return payload


def _load_migrations(contract: dict[str, Any]) -> list[dict[str, Any]]:
    path = ROOT / str(contract["semantic_migrations"])
    payload = _json(path)
    if payload.get("schema_version") != "prompt-semantic-migrations/v1":
        raise ValueError("unsupported prompt semantic migration schema")
    declared_values = payload.get("effective_identity_change_values")
    if set(declared_values or []) != EFFECTIVE_IDENTITY_CHANGE_VALUES:
        raise ValueError("effective identity migration values drifted")
    migrations = payload.get("migrations")
    if not isinstance(migrations, list):
        raise ValueError("migrations must be a list")
    required = {
        "migration_id",
        "path",
        "from_git_blob_sha1",
        "to_git_blob_sha1",
        "affected_prompt_ids",
        "change_kind",
        "effective_identity_change",
        "rationale",
        "focused_tests",
    }
    seen_ids: set[str] = set()
    for item in migrations:
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError(f"invalid semantic migration record: {item!r}")
        migration_id = str(item["migration_id"])
        if not migration_id or migration_id in seen_ids:
            raise ValueError(f"duplicate or empty migration ID: {migration_id}")
        seen_ids.add(migration_id)
        if item["change_kind"] not in {
            "strengthening",
            "restoration",
            "intentional_semantic_change",
        }:
            raise ValueError(f"unsupported migration change_kind: {item['change_kind']}")
        if item["effective_identity_change"] not in EFFECTIVE_IDENTITY_CHANGE_VALUES:
            raise ValueError(
                "unsupported migration effective_identity_change: "
                f"{item['effective_identity_change']}"
            )
        if not isinstance(item["rationale"], str) or not item["rationale"].strip():
            raise ValueError(f"migration {migration_id} requires rationale")
        for field in ("affected_prompt_ids", "focused_tests"):
            if not isinstance(item[field], list) or not item[field]:
                raise ValueError(f"migration {migration_id} requires {field}")
        for prompt_id in item["affected_prompt_ids"]:
            if not isinstance(prompt_id, str) or not PROMPT_ID_RE.fullmatch(prompt_id):
                raise ValueError(f"migration {migration_id} has invalid prompt ID: {prompt_id}")
        for test_path in item["focused_tests"]:
            if not isinstance(test_path, str) or not test_path.strip():
                raise ValueError(f"migration {migration_id} has invalid focused test path")
            if not (ROOT / test_path).is_file():
                raise ValueError(
                    f"migration {migration_id} focused test does not exist: {test_path}"
                )
    return migrations


def _accepted_source_heads(
    contract: dict[str, Any], migrations: list[dict[str, Any]]
) -> tuple[dict[str, str], list[str]]:
    accepted = {
        item["path"]: item["git_blob_sha1"]
        for item in contract["canonical_body_sources"]
    }
    errors: list[str] = []
    for migration in migrations:
        path = migration["path"]
        if path not in accepted:
            errors.append(
                f"{migration['migration_id']}: migration path is not a canonical body source: {path}"
            )
            continue
        if migration["from_git_blob_sha1"] != accepted[path]:
            errors.append(
                f"{migration['migration_id']}: migration chain for {path} starts at "
                f"{migration['from_git_blob_sha1']} but accepted head is {accepted[path]}"
            )
            continue
        accepted[path] = migration["to_git_blob_sha1"]
    return accepted, errors


def _replacement_authorized_prompt_ids(
    migrations: list[dict[str, Any]],
) -> set[str]:
    return {
        prompt_id
        for migration in migrations
        if migration["effective_identity_change"] == "replacement_authorized"
        for prompt_id in migration["affected_prompt_ids"]
    }


def audit_source_history(
    contract: dict[str, Any], migrations: list[dict[str, Any]]
) -> list[str]:
    accepted, errors = _accepted_source_heads(contract, migrations)
    baselines = {
        item["path"]: item for item in contract["canonical_body_sources"]
    }
    for path, accepted_sha in accepted.items():
        full = ROOT / path
        if not full.is_file():
            errors.append(f"PQH001: canonical body source missing: {path}")
            continue
        data = full.read_bytes()
        actual_sha = _git_blob_sha1(data)
        if actual_sha != accepted_sha:
            errors.append(
                f"PQH001: {path} is {actual_sha}, expected accepted history head {accepted_sha}; "
                "add a reviewed semantic migration instead of silently resetting the baseline"
            )
        baseline_size = int(baselines[path]["baseline_size_bytes"])
        if len(data) < baseline_size and not any(m["path"] == path for m in migrations):
            errors.append(
                f"PQH002: {path} shrank from baseline {baseline_size} bytes to {len(data)} "
                "without a semantic migration"
            )
    return errors


def audit_effective_identity(
    contract: dict[str, Any], migrations: list[dict[str, Any]]
) -> list[str]:
    canonical = {p["id"]: p for p in builder.load_prompt_registry()}
    effective = {p["id"]: p for p in builder.load_prompt_kit_registry()}
    exception_records = contract["effective_identity"].get("temporary_exceptions", [])
    exceptions = {item["prompt_id"] for item in exception_records}
    replacement_authorized = _replacement_authorized_prompt_ids(migrations)
    used_exceptions: set[str] = set()
    errors: list[str] = []

    unknown_authorizations = sorted(replacement_authorized - set(canonical))
    if unknown_authorizations:
        errors.append(
            "PQH003: replacement-authorizing migrations reference unknown canonical prompts: "
            f"{unknown_authorizations}"
        )

    missing = sorted(set(canonical) - set(effective))
    if missing:
        errors.append(
            f"PQH003: canonical prompts missing from effective registry: {missing}"
        )

    for prompt_id in sorted(set(canonical) & set(effective)):
        canonical_text = canonical[prompt_id]["copyContent"]
        effective_text = effective[prompt_id]["copyContent"]
        if effective_text != canonical_text and prompt_id not in replacement_authorized:
            errors.append(
                f"PQH003: {prompt_id} effective copyContent diverges from canonical copyContent"
            )

        compiled = effective[prompt_id].get("compiledEffectivePrompts")
        if compiled is None:
            continue
        if not isinstance(compiled, dict) or not compiled:
            errors.append(f"PQH003: {prompt_id} compiledEffectivePrompts is empty or invalid")
            continue
        for profile, text in compiled.items():
            if not isinstance(text, str) or not text.strip():
                errors.append(
                    f"PQH003: {prompt_id}/{profile} compiled effective prompt is empty"
                )
                continue
            if canonical_text in text or prompt_id in replacement_authorized:
                continue
            if prompt_id in exceptions:
                used_exceptions.add(prompt_id)
                continue
            errors.append(
                f"PQH003: {prompt_id}/{profile} replaces or omits the canonical prompt"
            )

    unknown_exceptions = sorted(exceptions - set(canonical))
    if unknown_exceptions:
        errors.append(f"PQH006: temporary exceptions reference unknown prompts: {unknown_exceptions}")
    stale_exceptions = sorted(exceptions - used_exceptions - set(unknown_exceptions))
    if stale_exceptions:
        errors.append(
            "PQH006: temporary exceptions are no longer needed and must be removed: "
            f"{stale_exceptions}"
        )
    return errors


def _derive_canonical_prompt_sources() -> set[str]:
    """Derive the complete canonical prompt source set from product boundaries and builder."""
    product_contract = boundaries.load_contract()
    sources: set[str] = set()
    
    # Base registry
    base_path = boundaries.base_registry(product_contract)
    sources.add(base_path.relative_to(ROOT).as_posix())
    
    # Content registries
    for path in boundaries.content_registries(product_contract):
        sources.add(path.relative_to(ROOT).as_posix())
    
    # Legacy extension registries (composed from products)
    for path in boundaries.legacy_extension_registries(product_contract):
        sources.add(path.relative_to(ROOT).as_posix())
    
    # Prompt overrides
    sources.add("registry/prompts/prompt-overrides.v1.json")
    
    return sources


def audit_source_set_parity(contract: dict[str, Any]) -> list[str]:
    """Enforce PSC013: source-history set parity is exact."""
    errors: list[str] = []
    
    try:
        canonical_sources = _derive_canonical_prompt_sources()
    except Exception as exc:
        errors.append(
            f"PSC013: failed to derive canonical prompt source set: {exc}"
        )
        return errors
    
    protected_sources = {item["path"] for item in contract["canonical_body_sources"]}
    
    missing_from_history = sorted(canonical_sources - protected_sources)
    if missing_from_history:
        errors.append(
            f"PSC013: canonical prompt sources are missing from history protection: {missing_from_history}"
        )
    
    extra_in_history = sorted(protected_sources - canonical_sources)
    if extra_in_history:
        errors.append(
            f"PSC013: history contract includes sources that are not canonical prompt sources: {extra_in_history}"
        )
    
    return errors


def validate() -> list[str]:
    contract = _load_contract()
    migrations = _load_migrations(contract)
    return (
        audit_source_set_parity(contract)
        + audit_source_history(contract, migrations)
        + audit_effective_identity(contract, migrations)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        errors = validate()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"PROMPT QUALITY HISTORY: FAIL: {exc}")
        return 1

    if errors:
        print("PROMPT QUALITY HISTORY: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.summary:
        contract = _load_contract()
        canonical_count = len(builder.load_prompt_registry())
        print(
            "PROMPT QUALITY HISTORY: PASS | "
            f"canonical_prompts={canonical_count} | "
            f"body_sources={len(contract['canonical_body_sources'])}"
        )
    else:
        print("PROMPT QUALITY HISTORY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
