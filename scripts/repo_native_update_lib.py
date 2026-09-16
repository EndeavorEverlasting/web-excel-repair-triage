#!/usr/bin/env python3
"""Shared helpers for the repository-native update generator harness."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "harness" / "repo-native-update"
CONTRACT_PATH = DOMAIN / "contracts" / "repo-native-update.v1.json"
GENERATOR_PATH = Path("scripts/run_repo_native_update.py")
DEFAULT_RECEIPT_PATH = Path("Outputs/repo-native-update/receipt.json")
RECEIPT_SCHEMA = "repo-native-update-receipt/v1"
CONTRACT_SCHEMA = "repo-native-update-contract/v1"
CANARY_INPUT_SCHEMA = "canary-constants-input/v1"


class RepoNativeUpdateError(RuntimeError):
    """Fail-closed generator or validation error."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepoNativeUpdateError(
            f"cannot read {path.relative_to(ROOT)}: {exc}"
        ) from exc


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def load_contract(path: Path | None = None) -> dict[str, Any]:
    contract = load_json(path or CONTRACT_PATH)
    if not isinstance(contract, dict):
        raise RepoNativeUpdateError("contract root must be an object")
    if contract.get("schema_version") != CONTRACT_SCHEMA:
        raise RepoNativeUpdateError("unexpected repo-native-update contract schema")
    surfaces = contract.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise RepoNativeUpdateError("contract must declare at least one surface")
    return contract


def resolve_surface(contract: dict[str, Any], surface_id: str) -> dict[str, Any]:
    for surface in contract.get("surfaces", []):
        if not isinstance(surface, dict):
            continue
        if str(surface.get("id", "")) == surface_id:
            return surface
    raise RepoNativeUpdateError(f"unknown surface: {surface_id}")


def validate_surface_shape(surface: dict[str, Any]) -> None:
    for key in ("id", "input_path", "owned_outputs", "trigger"):
        if key not in surface:
            raise RepoNativeUpdateError(f"surface missing field: {key}")
    owned = surface["owned_outputs"]
    if not isinstance(owned, list) or not owned:
        raise RepoNativeUpdateError("surface owned_outputs must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in owned):
        raise RepoNativeUpdateError("surface owned_outputs must be non-empty strings")
    if not isinstance(surface["input_path"], str) or not surface["input_path"].strip():
        raise RepoNativeUpdateError("surface input_path must be a non-empty string")
    if not isinstance(surface["trigger"], str) or not surface["trigger"].strip():
        raise RepoNativeUpdateError("surface trigger must be a non-empty string")


def assert_safe_relative_path(relative: str) -> str:
    raw = str(relative or "").strip().replace("\\", "/")
    if not raw:
        raise RepoNativeUpdateError("output path must be non-empty")
    if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":"):
        raise RepoNativeUpdateError(f"absolute output paths are forbidden: {raw}")
    parts = Path(raw).parts
    if ".." in parts:
        raise RepoNativeUpdateError(f"path traversal is forbidden: {raw}")
    return raw


def forbidden_prefixes(contract: dict[str, Any] | None = None) -> list[str]:
    if contract is None:
        try:
            contract = load_contract()
        except RepoNativeUpdateError:
            return [".github/", "AGENTS.md", "Candidates/", "Active/"]
    prefixes = contract.get("forbidden_output_prefixes", [])
    if not isinstance(prefixes, list):
        return []
    return [str(item).replace("\\", "/") for item in prefixes if str(item).strip()]


def assert_not_forbidden_output(relative: str, contract: dict[str, Any] | None = None) -> None:
    canonical = assert_safe_relative_path(relative)
    for prefix in forbidden_prefixes(contract):
        if prefix.endswith("/"):
            if canonical.startswith(prefix) or canonical == prefix.rstrip("/"):
                raise RepoNativeUpdateError(
                    f"output path hits forbidden prefix {prefix}: {canonical}"
                )
        elif canonical == prefix or canonical.startswith(prefix + "/"):
            raise RepoNativeUpdateError(
                f"output path hits forbidden prefix {prefix}: {canonical}"
            )


def resolve_owned_output(
    relative: str,
    surface: dict[str, Any],
    *,
    root: Path | None = None,
    contract: dict[str, Any] | None = None,
) -> Path:
    repo_root = root or ROOT
    canonical = assert_safe_relative_path(relative)
    assert_not_forbidden_output(canonical, contract)
    owned = {assert_safe_relative_path(item) for item in surface["owned_outputs"]}
    if canonical not in owned:
        raise RepoNativeUpdateError(
            f"output path is not declared for surface {surface['id']}: {canonical}"
        )
    resolved = (repo_root / canonical).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise RepoNativeUpdateError(
            f"output path escapes repository root: {canonical}"
        ) from exc
    if resolved.is_symlink():
        raise RepoNativeUpdateError(f"symlink outputs are forbidden: {canonical}")
    return resolved


def validate_canary_constants_input(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RepoNativeUpdateError("canary-constants input must be an object")
    if payload.get("schema_version") != CANARY_INPUT_SCHEMA:
        raise RepoNativeUpdateError("unexpected canary-constants input schema_version")
    constants = payload.get("constants")
    ordered_keys = payload.get("ordered_keys")
    if not isinstance(constants, dict) or not constants:
        raise RepoNativeUpdateError("canary-constants input requires non-empty constants")
    if not isinstance(ordered_keys, list) or not ordered_keys:
        raise RepoNativeUpdateError("canary-constants input requires ordered_keys")
    if any(not isinstance(key, str) or not key for key in ordered_keys):
        raise RepoNativeUpdateError("ordered_keys must be non-empty strings")
    if len(ordered_keys) != len(set(ordered_keys)):
        raise RepoNativeUpdateError("ordered_keys must not contain duplicates")
    constant_keys = set(constants.keys())
    ordered_set = set(ordered_keys)
    if constant_keys != ordered_set:
        raise RepoNativeUpdateError(
            "ordered_keys must match the constants key set exactly"
        )
    for key in ordered_keys:
        value = constants[key]
        if not isinstance(value, (bool, str, int, float)):
            raise RepoNativeUpdateError(
                f"unsupported constant type for {key}: {type(value).__name__}"
            )
    return payload


def render_constant_value(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, (int, float)):
        return repr(value)
    raise RepoNativeUpdateError(f"unsupported constant value type: {type(value).__name__}")


def build_canary_constants_module(
    payload: dict[str, Any],
    *,
    surface_id: str,
    input_relative: str,
) -> str:
    lines = [
        "# GENERATED by scripts/run_repo_native_update.py — DO NOT HAND-EDIT.",
        f"# Surface: {surface_id}",
        f"# Input: {input_relative}",
        "",
    ]
    constants = payload["constants"]
    for key in payload["ordered_keys"]:
        lines.append(f"{key} = {render_constant_value(constants[key])}")
    lines.append("")
    return "\n".join(lines)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def atomic_write_text(path: Path, text: str) -> None:
    normalized = normalize_newlines(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    try:
        temp_path.write_text(normalized, encoding="utf-8", newline="\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def build_receipt(
    *,
    contract: dict[str, Any],
    surface: dict[str, Any],
    input_path: Path,
    output_paths: list[str],
    output_sha256: dict[str, str],
    status: str,
) -> dict[str, Any]:
    return {
        "schema_version": RECEIPT_SCHEMA,
        "generator_id": str(contract.get("generator_id", "repo-native-update")),
        "generator_path": GENERATOR_PATH.as_posix(),
        "surface_id": str(surface["id"]),
        "input_path": input_path.relative_to(ROOT).as_posix(),
        "input_sha256": sha256_file(input_path),
        "output_paths": output_paths,
        "output_sha256": output_sha256,
        "status": status,
        "trigger": "cli",
        "recursion_guard": "no_auto_commit",
        "validation": "pass",
        "proof_ceiling": str(surface.get("proof_ceiling", "")),
        "actions_required": False,
    }


def write_receipt(receipt: dict[str, Any], receipt_path: Path) -> None:
    atomic_write_text(
        receipt_path,
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    )


def tracked(path: Path, *, root: Path | None = None) -> bool:
    repo_root = root or ROOT
    if not (repo_root / ".git").exists():
        return True
    rel = path.relative_to(repo_root).as_posix()
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def require_tracked_file(relative: str, *, root: Path | None = None) -> Path:
    repo_root = root or ROOT
    path = repo_root / relative
    if not path.is_file() or path.stat().st_size == 0:
        raise RepoNativeUpdateError(f"missing/empty harness component: {relative}")
    if not tracked(path, root=repo_root):
        raise RepoNativeUpdateError(f"untracked harness component: {relative}")
    return path
