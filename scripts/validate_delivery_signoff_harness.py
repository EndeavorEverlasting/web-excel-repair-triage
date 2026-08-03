#!/usr/bin/env python3
"""Validate delivery sign-off harness completeness and artifact manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "harness/delivery-signoff/registry.json"
REQUIRED = [
    "harness/delivery-signoff/CODEBASE_MAP.md",
    "harness/delivery-signoff/WORKFLOWS.md",
    "harness/delivery-signoff/ARTIFACT_REGISTRY.md",
    "harness/delivery-signoff/registry.json",
    "configs/delivery_signoff_layout_v1.json",
    "skills/delivery-signoff-generation/SKILL.md",
    "capabilities/delivery-signoff-generation.json",
    "triggers/delivery-signoff-generation.json",
    "scripts/validate_delivery_signoff_harness.py",
    ".githooks/pre-commit-delivery-signoff",
    ".github/workflows/delivery-signoff-harness.yml",
    "reports/harness/delivery-signoff-state.md",
]
COMPONENT_KEYS = {
    "codebase_map", "workflows", "artifact_registry", "layout_config", "skill",
    "capability", "trigger", "validator", "hook", "ci", "operator_report",
}
INK_SURFACES = {"asset_mark_cells", "field_annotation_box", "receiver_signature"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_harness(errors: list[str]) -> None:
    for rel in REQUIRED:
        check(errors, (ROOT / rel).is_file(), f"missing required harness component: {rel}")
    if not REGISTRY.is_file():
        return

    try:
        registry = read_json(REGISTRY)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid harness registry JSON: {exc}")
        return

    check(errors, registry.get("schema") == "triage-delivery-signoff-harness/v1", "wrong harness registry schema")
    components = registry.get("components", {})
    check(errors, set(components) == COMPONENT_KEYS, "harness component registry is incomplete or drifted")
    for key, rel in components.items():
        check(errors, isinstance(rel, str) and (ROOT / rel).is_file(), f"registered component missing: {key} -> {rel}")

    try:
        layout = read_json(ROOT / components.get("layout_config", ""))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid layout config: {exc}")
        layout = {}

    page = layout.get("page", {})
    typography = layout.get("typography", {})
    identity = layout.get("identity", {})
    equipment = layout.get("equipment", {})
    draw = layout.get("draw_surfaces", {})
    check(errors, page.get("target_count") == 1 and page.get("maximum_count") == 2, "layout page contract must be target 1 / maximum 2")
    check(errors, float(typography.get("minimum_body_points", 0)) >= 8.5, "minimum body font must be at least 8.5 pt")
    check(errors, float(typography.get("minimum_serial_points", 0)) >= 8.5, "minimum serial font must be at least 8.5 pt")
    check(errors, identity.get("priority") == ["serial_number", "mac_address", "asset_tag", "temporary_hostname"], "identity priority must be serial-first")
    check(errors, identity.get("temporary_hostname_in_primary_drawbox") is False, "temporary hostnames cannot be primary drawbox content")
    check(errors, equipment.get("one_row_per_distinct_physical_item") is True, "distinct equipment-row contract missing")
    check(errors, equipment.get("separate_cable_color_and_model_rows") is True, "distinct cable-row contract missing")
    check(errors, draw.get("document_protection") == "none", "document must remain unprotected")
    check(errors, draw.get("flattened_document_forbidden") is True, "flattened DOCX prohibition missing")
    check(errors, set(draw.get("required", [])) == INK_SURFACES, "required draw surfaces are incomplete")

    for rel, expected_schema in [
        (components.get("capability", ""), "triage-capability/v1"),
        (components.get("trigger", ""), "triage-trigger/v1"),
    ]:
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            payload = read_json(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"invalid JSON {rel}: {exc}")
            continue
        check(errors, payload.get("schema") == expected_schema, f"wrong schema in {rel}")

    trigger_path = ROOT / components.get("trigger", "")
    if trigger_path.is_file():
        trigger = read_json(trigger_path)
        route = trigger.get("route", {})
        check(errors, route.get("skill") == components.get("skill"), "trigger skill route drift")
        check(errors, route.get("capability") == components.get("capability"), "trigger capability route drift")
        check(errors, route.get("workflow") == components.get("workflows"), "trigger workflow route drift")
        check(errors, route.get("validator") == components.get("validator"), "trigger validator route drift")

    required_tokens = {
        "harness/delivery-signoff/WORKFLOWS.md": ["serial", "active-roster", "unprotected", "two-page", "manifest"],
        "skills/delivery-signoff-generation/SKILL.md": ["8.5", "draw", "temporary hostnames", "cable", "render"],
        "harness/delivery-signoff/ARTIFACT_REGISTRY.md": ["SERIAL_FIRST_INK_READY", "draw_ready_static", "operator_accepted"],
    }
    for rel, tokens in required_tokens.items():
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for token in tokens:
            check(errors, token.lower() in text, f"{rel} missing operational token: {token}")


def validate_manifest(path: Path, errors: list[str]) -> None:
    try:
        manifest = read_json(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid artifact manifest JSON: {exc}")
        return

    check(errors, manifest.get("schema") == "delivery-signoff-artifact-manifest/v1", "manifest schema must be delivery-signoff-artifact-manifest/v1")
    for key in [
        "input_spec", "docx", "preview", "page_count", "minimum_font_points",
        "serial_counts", "equipment_rows", "document_protection",
        "required_ink_surfaces", "draw_proof_level", "stale_content_scan", "proof_ceiling",
    ]:
        check(errors, key in manifest, f"manifest missing required field: {key}")

    check(errors, isinstance(manifest.get("page_count"), int) and 1 <= manifest.get("page_count", 0) <= 2, "page_count must be 1 or 2")
    try:
        font = float(manifest.get("minimum_font_points", 0))
    except (TypeError, ValueError):
        font = 0
    check(errors, font >= 8.5, "minimum_font_points must be at least 8.5")
    check(errors, manifest.get("document_protection") == "none", "DOCX must be unprotected")
    check(errors, INK_SURFACES.issubset(set(manifest.get("required_ink_surfaces", []))), "manifest lacks required ink surfaces")
    check(errors, manifest.get("draw_proof_level") in {"draw_ready_static", "draw_smoke_tested", "operator_accepted"}, "invalid draw proof level")

    serial_counts = manifest.get("serial_counts", {})
    check(errors, isinstance(serial_counts, dict) and bool(serial_counts), "serial_counts must be a non-empty object")
    for asset_type, counts in serial_counts.items():
        if not isinstance(counts, dict):
            errors.append(f"serial_counts.{asset_type} must be an object")
            continue
        check(errors, counts.get("declared") == counts.get("rendered"), f"serial count mismatch for {asset_type}")
        check(errors, counts.get("duplicates", 0) == 0, f"duplicate serials reported for {asset_type}")

    rows = manifest.get("equipment_rows", [])
    check(errors, isinstance(rows, list) and bool(rows), "equipment_rows must be a non-empty list")
    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f"equipment row {index} is not an object")
            continue
        key = (
            str(row.get("equipment_type", "")).casefold(),
            str(row.get("model_or_part", "")).casefold(),
            str(row.get("color_or_variant", "")).casefold(),
        )
        check(errors, key not in seen, f"duplicate/collapsed equipment row: {key}")
        seen.add(key)
        if "cable" in key[0] or "ethernet" in key[0]:
            check(errors, bool(key[1]) and bool(key[2]), f"cable row {index} must retain model and color/variant")

    stale = manifest.get("stale_content_scan", {})
    check(errors, stale.get("status") == "PASS", "stale content scan must PASS")
    check(errors, not stale.get("matches"), "stale content scan contains matches")

    for object_key in ["input_spec", "docx"]:
        item = manifest.get(object_key, {})
        file_path = item.get("path") if isinstance(item, dict) else None
        expected_hash = item.get("sha256") if isinstance(item, dict) else None
        if file_path:
            candidate = Path(file_path)
            if not candidate.is_absolute():
                candidate = ROOT / candidate
            check(errors, candidate.is_file(), f"manifest {object_key} path missing: {candidate}")
            if candidate.is_file() and expected_hash:
                check(errors, sha256(candidate) == expected_hash.lower(), f"manifest {object_key} SHA-256 mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, help="Optional delivery-signoff-artifact-manifest/v1 JSON")
    args = parser.parse_args()

    errors: list[str] = []
    validate_harness(errors)
    if args.manifest:
        validate_manifest(args.manifest.resolve(), errors)

    if errors:
        print("FAIL: delivery sign-off harness")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: delivery sign-off harness")
    print(f"- required components: {len(REQUIRED)}")
    print("- serial-first layout contract: PASS")
    print("- distinct equipment/cable contract: PASS")
    print("- editable ink-ready two-page contract: PASS")
    print("- capability and trigger wiring: PASS")
    if args.manifest:
        print(f"- validated manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
