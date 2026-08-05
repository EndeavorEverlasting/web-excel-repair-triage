"""Generate editable, ink-ready delivery sign-offs with deterministic proof artifacts."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable

from .document import build_document, docx_text
from .proof import relative_entry, render_docx, validate_path_hash_object
from .schema import (
    INK_SURFACES,
    MANIFEST_SCHEMA,
    MINIMUM_FONT_POINTS,
    GenerationResult,
    SignoffValidationError,
    safe_slug,
    validate_spec,
)


def _validate_generated(spec: dict[str, Any], docx_path: Path, page_paths: Iterable[Path]) -> tuple[dict[str, Any], dict[str, Any]]:
    text = docx_text(docx_path)
    serial_counts: dict[str, Any] = {}
    for group in spec["serialized_assets"]:
        rendered = sum(text.count(item["serial_number"]) for item in group["identifiers"])
        duplicates = len(group["identifiers"]) - len({item["serial_number"].casefold() for item in group["identifiers"]})
        serial_counts[group["asset_type"]] = {
            "declared": len(group["identifiers"]),
            "rendered": rendered,
            "duplicates": duplicates,
        }
        if rendered != len(group["identifiers"]):
            raise SignoffValidationError(
                f"serial count mismatch for {group['asset_type']}: declared {len(group['identifiers'])}, rendered {rendered}"
            )
    matches = [token for token in spec["reject_tokens"] if token.casefold() in text.casefold()]
    if matches:
        raise SignoffValidationError(f"stale-content scan failed: {matches}")
    pages = tuple(page_paths)
    return serial_counts, {"status": "PASS", "matches": [], "scanned_tokens": spec["reject_tokens"], "pages": len(pages)}


def _validate_manifest_payload(manifest: dict[str, Any], package_dir: Path) -> None:
    required = {
        "input_spec", "docx", "preview", "page_count", "minimum_font_points", "serial_counts",
        "equipment_rows", "document_protection", "required_ink_surfaces", "draw_proof_level",
        "stale_content_scan", "proof_ceiling", "serialized_assets_expected",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise SignoffValidationError(f"manifest missing fields: {missing}")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise SignoffValidationError("invalid manifest schema")
    if not isinstance(manifest["page_count"], int) or not 1 <= manifest["page_count"] <= 2:
        raise SignoffValidationError("manifest page_count must be 1 or 2")
    if float(manifest["minimum_font_points"]) < MINIMUM_FONT_POINTS:
        raise SignoffValidationError("manifest minimum font is below 8.5 pt")
    if manifest["document_protection"] != "none":
        raise SignoffValidationError("document protection must be none")
    if not set(INK_SURFACES).issubset(set(manifest["required_ink_surfaces"])):
        raise SignoffValidationError("required ink surfaces are incomplete")
    counts = manifest["serial_counts"]
    if not isinstance(counts, dict):
        raise SignoffValidationError("serial_counts must be an object")
    if manifest["serialized_assets_expected"] and not counts:
        raise SignoffValidationError("serial_counts cannot be empty when serialized assets are expected")
    for asset_type, values in counts.items():
        if not isinstance(values, dict):
            raise SignoffValidationError(f"serial_counts.{asset_type} must be an object")
        for key in ("declared", "rendered", "duplicates"):
            value = values.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SignoffValidationError(f"serial_counts.{asset_type}.{key} must be a non-negative integer")
        if values["declared"] != values["rendered"] or values["duplicates"] != 0:
            raise SignoffValidationError(f"serial count reconciliation failed for {asset_type}")
    for object_key in ("input_spec", "docx"):
        validate_path_hash_object(manifest[object_key], package_dir, object_key)
    preview = manifest["preview"]
    validate_path_hash_object(preview, package_dir, "preview")
    page_hashes = preview.get("page_hashes")
    if not isinstance(page_hashes, list) or not page_hashes:
        raise SignoffValidationError("preview.page_hashes must be a non-empty list")
    if len(page_hashes) != manifest["page_count"]:
        raise SignoffValidationError("preview.page_hashes count must equal page_count")
    for index, page in enumerate(page_hashes, 1):
        validate_path_hash_object(page, package_dir, f"preview.page_hashes[{index}]")


def generate_signoff(spec_path: Path | str, output_root: Path | str) -> GenerationResult:
    """Generate a complete sign-off package from a validated JSON spec."""
    source_path = Path(spec_path).resolve()
    output_root_path = Path(output_root).resolve()
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise SignoffValidationError(f"cannot read input spec: {exc}") from exc
    spec = validate_spec(raw)

    site_slug = safe_slug(spec["site"]["code"], "SITE")
    signoff_slug = safe_slug(spec["signoff"]["id"], "SIGNOFF")
    package_dir = output_root_path / site_slug / signoff_slug
    if package_dir.exists():
        shutil.rmtree(package_dir)
    preview_dir = package_dir / "preview"
    package_dir.mkdir(parents=True, exist_ok=True)

    normalized_spec_path = package_dir / "input-spec.json"
    normalized_spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    docx_path = package_dir / f"{site_slug}_Delivery_Sign_Off_{signoff_slug}_SERIAL_FIRST_INK_READY.docx"
    build_document(spec, docx_path)
    preview_pdf_path, page_preview_paths = render_docx(docx_path, preview_dir)
    serial_counts, stale_scan = _validate_generated(spec, docx_path, page_preview_paths)

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "artifact_family": "delivery-signoff",
        "site_code": spec["site"]["code"],
        "site_name": spec["site"]["name"],
        "signoff_id": spec["signoff"]["id"],
        "serialized_assets_expected": bool(spec["serialized_assets"]),
        "input_spec": relative_entry(normalized_spec_path, package_dir),
        "docx": relative_entry(docx_path, package_dir),
        "preview": {
            **relative_entry(preview_pdf_path, package_dir),
            "format": "pdf",
            "page_hashes": [relative_entry(page, package_dir) for page in page_preview_paths],
        },
        "page_count": len(page_preview_paths),
        "minimum_font_points": MINIMUM_FONT_POINTS,
        "serial_counts": serial_counts,
        "equipment_rows": spec["equipment_rows"],
        "document_protection": "none",
        "required_ink_surfaces": INK_SURFACES,
        "draw_proof_level": "draw_ready_static",
        "stale_content_scan": stale_scan,
        "source_provenance": spec["provenance"],
        "proof_ceiling": spec["proof_ceiling"],
    }
    _validate_manifest_payload(manifest, package_dir)
    manifest_path = package_dir / "delivery-signoff-artifact-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    validation_log_path = package_dir / "delivery-signoff-validation.txt"
    validation_log_path.write_text(
        "PASS: delivery sign-off generation\n"
        f"- site: {spec['site']['code']} | {spec['site']['name']}\n"
        f"- equipment rows: {len(spec['equipment_rows'])}\n"
        f"- serialized groups: {len(spec['serialized_assets'])}\n"
        f"- rendered pages: {len(page_preview_paths)}\n"
        f"- minimum font points: {MINIMUM_FONT_POINTS}\n"
        "- document protection: none\n"
        "- required ink surfaces: PASS\n"
        "- stale content scan: PASS\n"
        "- manifest path/hash containment: PASS\n",
        encoding="utf-8",
    )
    return GenerationResult(
        package_dir=package_dir,
        docx_path=docx_path,
        preview_pdf_path=preview_pdf_path,
        page_preview_paths=page_preview_paths,
        manifest_path=manifest_path,
        validation_log_path=validation_log_path,
    )
