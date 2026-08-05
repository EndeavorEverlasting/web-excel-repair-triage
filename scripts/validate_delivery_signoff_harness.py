#!/usr/bin/env python3
"""Validate delivery sign-off harness completeness and generated artifact manifests."""
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
    "scripts/evaluate_delivery_signoff_trigger.py",
    "scripts/validate_delivery_signoff_harness.py",
    ".githooks/pre-commit-delivery-signoff",
    ".github/workflows/delivery-signoff-harness.yml",
    "reports/harness/delivery-signoff-state.md",
]
COMPONENT_KEYS = {
    "codebase_map",
    "workflows",
    "artifact_registry",
    "layout_config",
    "skill",
    "capability",
    "trigger",
    "validator",
    "hook",
    "ci",
    "operator_report",
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


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _valid_non_negative_int(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


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
    check(errors, isinstance(components, dict) and set(components) == COMPONENT_KEYS, "harness component registry is incomplete or drifted")
    if isinstance(components, dict):
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
    layout_policy = layout.get("layout", {})
    contamination = layout.get("contamination_checks", {})
    check(errors, layout.get("schema") == "delivery-signoff-layout/v1", "wrong layout schema")
    check(errors, page.get("target_count") == 1 and page.get("maximum_count") == 2, "layout page contract must be target 1 / maximum 2")
    check(errors, page.get("orientation_strategy") == "choose_portrait_or_landscape_from_serial_density", "layout orientation must be density based")
    check(errors, _safe_float(page.get("minimum_margin_inches")) >= 0.35, "layout minimum margin must be at least 0.35 inches")
    check(errors, 0 < _safe_float(page.get("maximum_unused_page_fraction")) <= 0.22, "layout unused-page ceiling must be at most 0.22")
    check(errors, _safe_float(typography.get("minimum_body_points")) >= 8.5, "minimum body font must be at least 8.5 pt")
    check(errors, _safe_float(typography.get("minimum_serial_points")) >= 8.5, "minimum serial font must be at least 8.5 pt")
    check(errors, _safe_float(typography.get("minimum_heading_points")) >= 11, "minimum heading font must be at least 11 pt")
    check(errors, typography.get("prefer_condensed_spacing_before_smaller_font") is True, "condensed spacing must be preferred before smaller text")
    check(errors, identity.get("priority") == ["serial_number", "mac_address", "asset_tag", "temporary_hostname"], "identity priority must be serial-first")
    check(errors, identity.get("temporary_hostname_in_primary_drawbox") is False, "temporary hostnames cannot be primary drawbox content")
    check(errors, identity.get("neuron_pair_format") == "serial_number / mac_address", "Neuron serial/MAC pair format drift")
    check(errors, identity.get("duplicate_identifiers_forbidden") is True, "duplicate identifiers must be forbidden")
    check(errors, equipment.get("one_row_per_distinct_physical_item") is True, "distinct equipment-row contract missing")
    check(errors, equipment.get("separate_cable_color_and_model_rows") is True, "distinct cable-row contract missing")
    check(errors, equipment.get("quantity_must_be_evidence_backed") is True, "equipment quantities must remain evidence backed")
    check(errors, equipment.get("initials_column_required") is True, "equipment initials column must be required")
    check(errors, draw.get("document_protection") == "none", "document must remain unprotected")
    check(errors, draw.get("flattened_document_forbidden") is True, "flattened DOCX prohibition missing")
    check(errors, set(draw.get("required", [])) == INK_SURFACES, "required draw surfaces are incomplete")
    check(errors, draw.get("static_proof_label") == "draw_ready_static", "static draw proof label drift")
    check(errors, draw.get("operator_smoke_test_label") == "draw_smoke_tested", "operator draw proof label drift")
    check(errors, layout_policy.get("serial_drawbox") == "dominant_content_region", "serial drawbox policy drift")
    check(errors, layout_policy.get("acceptance_block") == "must_not_be_stranded_on_extra_page", "acceptance block policy drift")
    check(errors, layout_policy.get("reject_large_dead_space_beside_overflow") is True, "dead-space rejection must remain enabled")
    check(errors, layout_policy.get("reject_clipping_or_truncation") is True, "clipping/truncation rejection must remain enabled")
    for key in ("reject_stale_site_name", "reject_stale_recipient", "reject_stale_asset_range", "reject_stale_source_footer"):
        check(errors, contamination.get(key) is True, f"contamination check must remain enabled: {key}")

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
        try:
            trigger = read_json(trigger_path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"invalid trigger JSON: {exc}")
            trigger = {}
        evaluation = trigger.get("evaluation", {})
        routes = trigger.get("routes", {})
        generation = routes.get("generation", {}) if isinstance(routes, dict) else {}
        check(errors, evaluation.get("deny_precedence") is True, "trigger deny rules must take precedence")
        check(errors, evaluation.get("predicate_schema") == "triage-trigger-predicate/v1", "trigger predicate schema drift")
        check(errors, isinstance(trigger.get("allow_rules"), list) and bool(trigger.get("allow_rules")), "trigger allow rules must be typed and non-empty")
        check(errors, isinstance(trigger.get("deny_rules"), list) and bool(trigger.get("deny_rules")), "trigger deny rules must be typed and non-empty")
        check(errors, generation.get("skill") == components.get("skill"), "trigger skill route drift")
        check(errors, generation.get("capability") == components.get("capability"), "trigger capability route drift")
        check(errors, generation.get("workflow") == components.get("workflows"), "trigger workflow route drift")
        check(errors, generation.get("validator") == components.get("validator"), "trigger validator route drift")
        check(errors, routes.get("evidence_authority") == "EndeavorEverlasting/FUN", "evidence-only trigger route must point to FUN")

    required_tokens = {
        "harness/delivery-signoff/WORKFLOWS.md": [
            "serial",
            "active-roster",
            "unprotected",
            "two-page",
            "manifest",
            "one-writer",
            "mutation authority",
        ],
        "skills/delivery-signoff-generation/SKILL.md": [
            "8.5",
            "draw",
            "temporary hostnames",
            "cable",
            "render",
            "outputs/delivery-signoff",
            "proof ceiling",
        ],
        "harness/delivery-signoff/ARTIFACT_REGISTRY.md": ["SERIAL_FIRST_INK_READY", "draw_ready_static", "operator_accepted"],
    }
    for rel, tokens in required_tokens.items():
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for token in tokens:
            check(errors, token.lower() in text, f"{rel} missing operational token: {token}")


def _resolve_package_path(manifest_dir: Path, raw_path: Any, errors: list[str], label: str) -> Path | None:
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


def _validate_path_hash_object(manifest_dir: Path, item: Any, errors: list[str], label: str) -> Path | None:
    if not isinstance(item, dict):
        errors.append(f"manifest {label} must be an object")
        return None
    candidate = _resolve_package_path(manifest_dir, item.get("path"), errors, label)
    expected_hash = item.get("sha256")
    hash_valid = isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash.lower()) is not None
    check(errors, hash_valid, f"{label}.sha256 must be a 64-character hexadecimal digest")
    if candidate is None:
        return None
    check(errors, candidate.is_file(), f"manifest {label} path missing: {candidate}")
    if candidate.is_file() and hash_valid:
        check(errors, sha256(candidate) == expected_hash.lower(), f"manifest {label} SHA-256 mismatch")
    return candidate if candidate.is_file() else None


def _normalize_equipment_rows(rows: Any, errors: list[str], label: str) -> list[dict[str, Any]]:
    check(errors, isinstance(rows, list) and bool(rows), f"{label} must be a non-empty list")
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f"{label} row {index} is not an object")
            continue
        equipment_type = row.get("equipment_type")
        model = row.get("model_or_part", "")
        variant = row.get("color_or_variant", "")
        quantity = row.get("quantity")
        check(errors, isinstance(equipment_type, str) and bool(equipment_type.strip()), f"{label} row {index} equipment_type must be non-empty")
        check(errors, isinstance(model, str), f"{label} row {index} model_or_part must be a string")
        check(errors, isinstance(variant, str), f"{label} row {index} color_or_variant must be a string")
        check(errors, _valid_non_negative_int(quantity) and quantity > 0, f"{label} row {index} quantity must be a positive integer")
        key = (
            equipment_type.strip().casefold() if isinstance(equipment_type, str) else "",
            model.strip().casefold() if isinstance(model, str) else "",
            variant.strip().casefold() if isinstance(variant, str) else "",
        )
        check(errors, key not in seen, f"duplicate/collapsed {label} row: {key}")
        seen.add(key)
        if "cable" in key[0] or "ethernet" in key[0]:
            check(errors, bool(key[1]) and bool(key[2]), f"{label} cable row {index} must retain model and color/variant")
        normalized.append(
            {
                "equipment_type": equipment_type.strip() if isinstance(equipment_type, str) else equipment_type,
                "model_or_part": model.strip() if isinstance(model, str) else model,
                "color_or_variant": variant.strip() if isinstance(variant, str) else variant,
                "quantity": quantity,
            }
        )
    return normalized


def _validate_input_spec(spec_path: Path | None, manifest: dict[str, Any], errors: list[str]) -> None:
    if spec_path is None:
        return
    try:
        spec = read_json(spec_path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"input_spec is not valid JSON: {exc}")
        return
    check(errors, spec.get("schema") == "delivery-signoff-spec/v1", "input_spec schema must be delivery-signoff-spec/v1")
    site = spec.get("site", {})
    signoff = spec.get("signoff", {})
    check(errors, isinstance(site, dict) and isinstance(site.get("code"), str) and bool(site.get("code", "").strip()), "input_spec site.code must be non-empty")
    check(errors, isinstance(signoff, dict) and isinstance(signoff.get("id"), str) and bool(signoff.get("id", "").strip()), "input_spec signoff.id must be non-empty")
    if isinstance(site, dict):
        check(errors, manifest.get("site_code") == site.get("code"), "manifest site_code does not match input_spec")
        if "site_name" in manifest:
            check(errors, manifest.get("site_name") == site.get("name"), "manifest site_name does not match input_spec")
    if isinstance(signoff, dict):
        check(errors, manifest.get("signoff_id") == signoff.get("id"), "manifest signoff_id does not match input_spec")

    spec_rows = _normalize_equipment_rows(spec.get("equipment_rows"), errors, "input_spec equipment_rows")
    manifest_rows = _normalize_equipment_rows(manifest.get("equipment_rows"), errors, "manifest equipment_rows")
    check(errors, manifest_rows == spec_rows, "manifest equipment_rows do not match input_spec")

    groups = spec.get("serialized_assets", [])
    check(errors, isinstance(groups, list), "input_spec serialized_assets must be a list")
    expected_counts: dict[str, dict[str, int]] = {}
    equipment_by_type = {
        row["equipment_type"].casefold(): row
        for row in spec_rows
        if isinstance(row.get("equipment_type"), str)
    }
    seen_types: set[str] = set()
    seen_serials: set[str] = set()
    if isinstance(groups, list):
        for index, group in enumerate(groups, 1):
            if not isinstance(group, dict):
                errors.append(f"input_spec serialized_assets[{index}] must be an object")
                continue
            asset_type = group.get("asset_type")
            identifiers = group.get("identifiers")
            check(errors, isinstance(asset_type, str) and bool(asset_type.strip()), f"input_spec serialized_assets[{index}].asset_type must be non-empty")
            check(errors, isinstance(identifiers, list) and bool(identifiers), f"input_spec serialized_assets[{index}].identifiers must be non-empty")
            if not isinstance(asset_type, str) or not isinstance(identifiers, list):
                continue
            key = asset_type.strip().casefold()
            check(errors, key not in seen_types, f"duplicate input_spec serialized asset type: {asset_type}")
            seen_types.add(key)
            valid_serials: list[str] = []
            for item_index, item in enumerate(identifiers, 1):
                serial = item.get("serial_number") if isinstance(item, dict) else None
                check(errors, isinstance(serial, str) and bool(serial.strip()), f"input_spec serialized_assets[{index}].identifiers[{item_index}].serial_number must be non-empty")
                if isinstance(serial, str) and serial.strip():
                    serial_key = serial.strip().casefold()
                    check(errors, serial_key not in seen_serials, f"duplicate input_spec serial number: {serial}")
                    seen_serials.add(serial_key)
                    valid_serials.append(serial.strip())
            equipment_row = equipment_by_type.get(key)
            check(errors, equipment_row is not None, f"serialized asset type {asset_type} lacks matching equipment row")
            if equipment_row is not None:
                check(errors, equipment_row.get("quantity") == len(valid_serials), f"serialized asset quantity mismatch for {asset_type}")
            expected_counts[asset_type.strip()] = {
                "declared": len(valid_serials),
                "rendered": len(valid_serials),
                "duplicates": 0,
            }
    check(errors, manifest.get("serialized_assets_expected") is bool(groups), "serialized_assets_expected does not match input_spec")
    check(errors, manifest.get("serial_counts") == expected_counts, "manifest serial_counts do not reconcile with input_spec")


def validate_manifest(path: Path, errors: list[str]) -> None:
    try:
        manifest = read_json(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid artifact manifest JSON: {exc}")
        return

    check(errors, manifest.get("schema") == "delivery-signoff-artifact-manifest/v1", "manifest schema must be delivery-signoff-artifact-manifest/v1")
    for key in [
        "site_code",
        "signoff_id",
        "input_spec",
        "docx",
        "preview",
        "page_count",
        "minimum_font_points",
        "minimum_heading_points",
        "serial_counts",
        "equipment_rows",
        "document_protection",
        "required_ink_surfaces",
        "draw_proof_level",
        "stale_content_scan",
        "proof_ceiling",
        "serialized_assets_expected",
    ]:
        check(errors, key in manifest, f"manifest missing required field: {key}")

    check(errors, isinstance(manifest.get("page_count"), int) and not isinstance(manifest.get("page_count"), bool) and 1 <= manifest.get("page_count", 0) <= 2, "page_count must be 1 or 2")
    check(errors, _safe_float(manifest.get("minimum_font_points")) >= 8.5, "minimum_font_points must be at least 8.5")
    check(errors, _safe_float(manifest.get("minimum_heading_points")) >= 11, "minimum_heading_points must be at least 11")
    check(errors, manifest.get("document_protection") == "none", "DOCX must be unprotected")
    proof_ceiling = manifest.get("proof_ceiling")
    check(errors, isinstance(proof_ceiling, str) and len(proof_ceiling.strip()) >= 20, "proof_ceiling must be a non-empty actionable boundary")
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
            check(errors, isinstance(asset_type, str) and bool(asset_type.strip()), "serial_counts asset type must be a non-empty string")
            if not isinstance(counts, dict):
                errors.append(f"serial_counts.{asset_type} must be an object")
                continue
            for count_name in ("declared", "rendered", "duplicates"):
                check(errors, _valid_non_negative_int(counts.get(count_name)), f"serial_counts.{asset_type}.{count_name} must be a non-negative integer")
            if all(_valid_non_negative_int(counts.get(name)) for name in ("declared", "rendered", "duplicates")):
                check(errors, counts["declared"] == counts["rendered"], f"serial count mismatch for {asset_type}")
                check(errors, counts["duplicates"] == 0, f"duplicate serials reported for {asset_type}")

    _normalize_equipment_rows(manifest.get("equipment_rows"), errors, "manifest equipment_rows")
    stale = manifest.get("stale_content_scan", {})
    check(errors, isinstance(stale, dict), "stale_content_scan must be an object")
    if isinstance(stale, dict):
        check(errors, stale.get("status") == "PASS", "stale content scan must PASS")
        check(errors, isinstance(stale.get("matches", []), list) and not stale.get("matches"), "stale content scan contains matches")

    manifest_dir = path.resolve().parent
    input_spec_path = _validate_path_hash_object(manifest_dir, manifest.get("input_spec"), errors, "input_spec")
    _validate_path_hash_object(manifest_dir, manifest.get("docx"), errors, "docx")
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
    _validate_input_spec(input_spec_path, manifest, errors)


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
    print("- complete serial-first layout contract: PASS")
    print("- input-spec/manifest evidence reconciliation: PASS")
    print("- editable ink-ready two-page contract: PASS")
    print("- typed trigger wiring and deny precedence: PASS")
    if args.manifest:
        print(f"- validated manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
