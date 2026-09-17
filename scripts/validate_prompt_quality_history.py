#!/usr/bin/env python3
"""Fail-closed Prompt Kit quality-history and effective-identity validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_prompt_kit_registry as builder  # noqa: E402

CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-quality-history.v1.json"


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
    return payload


def _load_migrations(contract: dict[str, Any]) -> list[dict[str, Any]]:
    path = ROOT / str(contract["semantic_migrations"])
    payload = _json(path)
    if payload.get("schema_version") != "prompt-semantic-migrations/v1":
        raise ValueError("unsupported prompt semantic migration schema")
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
        "rationale",
        "focused_tests",
    }
    for item in migrations:
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError(f"invalid semantic migration record: {item!r}")
        if item["change_kind"] not in {
            "strengthening",
            "restoration",
            "intentional_semantic_change",
        }:
            raise ValueError(f"unsupported migration change_kind: {item['change_kind']}")
        for field in ("affected_prompt_ids", "focused_tests"):
            if not isinstance(item[field], list) or not item[field]:
                raise ValueError(f"migration {item['migration_id']} requires {field}")
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


def audit_effective_identity(contract: dict[str, Any]) -> list[str]:
    canonical = {p["id"]: p for p in builder.load_prompt_registry()}
    effective = {p["id"]: p for p in builder.load_prompt_kit_registry()}
    exceptions = {
        item["prompt_id"]
        for item in contract["effective_identity"].get("temporary_exceptions", [])
    }
    errors: list[str] = []

    missing = sorted(set(canonical) - set(effective))
    if missing:
        errors.append(
            f"PQH003: canonical prompts missing from effective registry: {missing}"
        )

    for prompt_id in sorted(set(canonical) & set(effective)):
        canonical_text = canonical[prompt_id]["copyContent"]
        effective_text = effective[prompt_id]["copyContent"]
        if effective_text != canonical_text:
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
            if canonical_text not in text and prompt_id not in exceptions:
                errors.append(
                    f"PQH003: {prompt_id}/{profile} replaces or omits the canonical prompt"
                )
    return errors


def validate() -> list[str]:
    contract = _load_contract()
    migrations = _load_migrations(contract)
    return audit_source_history(contract, migrations) + audit_effective_identity(contract)


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
