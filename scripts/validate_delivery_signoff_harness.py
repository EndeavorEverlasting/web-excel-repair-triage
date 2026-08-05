#!/usr/bin/env python3
"""Validate delivery sign-off harness completeness and artifact manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
    check(errors, _safe_float(typography.get("minimum_body_points")) >= 8.5, "minimum body font must be at least 8.5 pt")
    check(errors, _safe_float(typography.get("minimum_serial_points")) >= 8.5, "minimum serial font must be at least 8.5 pt")
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


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _valid_non_negative_int(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _resolve_package_path(
    manifest_dir: Path,
    raw_path: Any,
    errors: list[str],
    label: str,
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"{label}.path must be a non-empty string")
        return None
    relative = Path(raw_path)
    if relative.is_absolute():
        errors.append(f"{label}.path must be relative to the manifest package")
        return None
    package_root = manifest_dir.resolve()
    candidate = (package_root / relative).resolve()
    try:
        candidate.relative_to(package_root)
    except ValueError:
        errors.append(f"{label}.path escapes the manifest package: {raw_path}")
        return None
    return candidate


def _validate_path_hash_object(
    manifest_dir: Path,
    item: Any,
    errors: list[str],
    label: str,
) -> None:
    if not isinstance(item, dict):
        errors.append(f"manifest {label} must be an object")
        return
    candidate = _resolve_package_path(manifest_dir, item.get("path"), errors, label)
    expected_hash = item.get("sha256")
    hash_valid = isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash.lower()) is not None
    check(errors, hash_valid, f"{label}.sha256 must be a 64-character hexadecimal digest")
    if candidate is None:
        return
    check(errors, candidate.is_file(), f"manifest {label} path missing: {candidate}")
    if candidate.is_file() and hash_valid:
        check(errors, sha256(candidate) == expected_hash.lower(), f"manifest {label} SHA-256 mismatch")


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
        "serialized_assets_expected",
    ]:
        check(errors, key in manifest, f"manifest missing required field: {key}")

    check(errors, isinstance(manifest.get("page_count"), int) and not isinstance(manifest.get("page_count"), bool) and 1 <= manifest.get("page_count", 0) <= 2, "page_count must be 1 or 2")
    check(errors, _safe_float(manifest.get("minimum_font_points")) >= 8.5, "minimum_font_points must be at least 8.5")
    check(errors, manifest.get("document_protection") == "none", "DOCX must be unprotected")
    ink_surfaces = manifest.get("required_ink_surfaces", [])
    check(errors, isinstance(ink_surfaces, list) and INK_SURFACES.issubset(set(ink_surfaces)), "manifest lacks required ink surfaces")
    check(errors, manifest.get("draw_proof_level") in {"draw_ready_static", "draw_smoke_tested", "operator_accepted"}, "invalid draw proof level")

    serialized_assets_expected = manifest.get("serialized_assets_expected")
    check(errors, isinstance(serialized_assets_expected, bool), "serialized_assets_expected must be boolean")
    serial_counts = manifest.get("serial_counts", {})
    check(errors, isinstance(serial_counts, dict), "serial_counts must be an object")
    if isinstance(serial_counts, dict):
        if serialized_assets_expected is True:
            check(errors, bool(serial_counts), "serial_counts must be non-empty when serialized assets are expected")
        for asset_type, counts in serial_counts.items():
            if not isinstance(asset_type, str) or not asset_type.strip():
                errors.append("serial_counts asset type must be a non-empty string")
            if not isinstance(counts, dict):
                errors.append(f"serial_counts.{asset_type} must be an object")
                continue
            for count_name in ("declared", "rendered", "duplicates"):
                value = counts.get(count_name)
                check(
                    errors,
                    _valid_non_negative_int(value),
                    f"serial_counts.{asset_type}.{count_name} must be a non-negative integer",
                )
            if all(_valid_non_negative_int(counts.get(name)) for name in ("declared", "rendered", "duplicates")):
                check(errors, counts["declared"] == counts["rendered"], f"serial count mismatch for {asset_type}")
                check(errors, counts["duplicates"] == 0, f"duplicate serials reported for {asset_type}")

    rows = manifest.get("equipment_rows", [])
    check(errors, isinstance(rows, list) and bool(rows), "equipment_rows must be a non-empty list")
    seen: set[tuple[str, str, str]] = set()
    if isinstance(rows, list):
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict):
                errors.append(f"equipment row {index} is not an object")
                continue
            equipment_type = row.get("equipment_type")
            model = row.get("model_or_part", "")
            variant = row.get("color_or_variant", "")
            quantity = row.get("quantity")
            check(errors, isinstance(equipment_type, str) and bool(equipment_type.strip()), f"equipment row {index} equipment_type must be non-empty")
            check(errors, isinstance(model, str), f"equipment row {index} model_or_part must be a string")
            check(errors, isinstance(variant, str), f"equipment row {index} color_or_variant must be a string")
            check(errors, _valid_non_negative_int(quantity) and quantity > 0, f"equipment row {index} quantity must be a positive integer")
            key = (
                equipment_type.strip().casefold() if isinstance(equipment_type, str) else "",
                model.strip().casefold() if isinstance(model, str) else "",
                variant.strip().casefold() if isinstance(variant, str) else "",
            )
            check(errors, key not in seen, f"duplicate/collapsed equipment row: {key}")
            seen.add(key)
            if "cable" in key[0] or "ethernet" in key[0]:
                check(errors, bool(key[1]) and bool(key[2]), f"cable row {index} must retain model and color/variant")

    stale = manifest.get("stale_content_scan", {})
    check(errors, isinstance(stale, dict), "stale_content_scan must be an object")
    if isinstance(stale, dict):
        check(errors, stale.get("status") == "PASS", "stale content scan must PASS")
        check(errors, isinstance(stale.get("matches", []), list) and not stale.get("matches"), "stale content scan contains matches")

    manifest_dir = path.resolve().parent
    for object_key in ["input_spec", "docx"]:
        _validate_path_hash_object(manifest_dir, manifest.get(object_key), errors, object_key)

    preview = manifest.get("preview")
    _validate_path_hash_object(manifest_dir, preview, errors, "preview")
    if isinstance(preview, dict):
        page_hashes = preview.get("page_hashes")
        check(errors, isinstance(page_hashes, list) and bool(page_hashes), "preview.page_hashes must be a non-empty list")
        if isinstance(page_hashes, list):
            for index, page in enumerate(page_hashes, 1):
                _validate_path_hash_object(manifest_dir, page, errors, f"preview.page_hashes[{index}]")
            if isinstance(manifest.get("page_count"), int) and not isinstance(manifest.get("page_count"), bool):
                check(errors, len(page_hashes) == manifest["page_count"], "preview.page_hashes count must equal page_count")


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
