#!/usr/bin/env python3
"""Static completeness validator for the repository-native update harness."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import repo_native_update_lib as lib

MANIFEST = lib.DOMAIN / "manifest.v1.json"
MANIFEST_SCHEMA = "web-excel-repo-native-update-harness/v1"


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError(f"JSON root must be an object: {path}")
    return payload


def validate_contract_shape(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != lib.CONTRACT_SCHEMA:
        raise ValidationError("unexpected repo-native-update contract schema")
    if not isinstance(contract.get("generator_id"), str) or not contract["generator_id"]:
        raise ValidationError("contract generator_id must be a non-empty string")
    surfaces = contract.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValidationError("contract must declare at least one surface")
    seen: set[str] = set()
    for surface in surfaces:
        if not isinstance(surface, dict):
            raise ValidationError("each surface must be an object")
        try:
            lib.validate_surface_shape(surface)
        except lib.RepoNativeUpdateError as exc:
            raise ValidationError(str(exc)) from exc
        surface_id = str(surface["id"])
        if surface_id in seen:
            raise ValidationError(f"duplicate surface id: {surface_id}")
        seen.add(surface_id)
        for relative in surface["owned_outputs"]:
            try:
                lib.assert_safe_relative_path(str(relative))
            except lib.RepoNativeUpdateError as exc:
                raise ValidationError(str(exc)) from exc


def validate_static_harness() -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise ValidationError("unexpected repo-native-update manifest schema")
    components = manifest.get("components")
    required_keys = manifest.get("required_component_keys")
    if not isinstance(required_keys, list) or not required_keys:
        required_keys = [
            "contract",
            "generator",
            "validator",
            "tests",
            "canary_input",
            "launcher",
        ]
    required = {str(item) for item in required_keys}
    if not isinstance(components, dict) or not required.issubset(set(components)):
        raise ValidationError("repo-native-update component registry drifted")
    for relative in components.values():
        lib.require_tracked_file(str(relative))

    contract = load_json(ROOT / str(components["contract"]))
    validate_contract_shape(contract)
    canary = None
    for surface in contract.get("surfaces", []):
        if isinstance(surface, dict) and surface.get("id") == "canary-constants":
            canary = surface
            break
    if canary is None:
        raise ValidationError("canary-constants surface is missing from contract")
    owned = canary.get("owned_outputs") or []
    expected = "harness/repo-native-update/generated/canary_constants.py"
    if expected not in owned:
        raise ValidationError(
            "canary-constants must own harness/repo-native-update/generated/canary_constants.py"
        )
    return {"status": "PASS", "components": sorted(components)}


def resolve_report(raw: str) -> Path:
    target = Path(raw)
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    outputs = (ROOT / "Outputs").resolve()
    try:
        target.relative_to(outputs)
    except ValueError as exc:
        raise ValidationError("output report must stay under Outputs/") from exc
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()
    try:
        report = validate_static_harness()
        if args.report:
            destination = resolve_report(args.report)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        if args.summary:
            print("PASS: repository-native update harness")
            print("- contract surfaces declare owned outputs and triggers")
            print("- generator entrypoint is tracked and present")
            print("- canary input and focused tests are tracked")
            print("- owned output paths reject traversal and undeclared writes")
        return 0
    except (ValidationError, lib.RepoNativeUpdateError) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
