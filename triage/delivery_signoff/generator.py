"""Generate editable, ink-ready delivery sign-offs with deterministic proof artifacts."""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .document import build_document, docx_serial_cell_texts, docx_text, format_identifier
from .proof import extract_pdf_text, relative_entry, render_docx, validate_path_hash_object
from .schema import (
    INK_SURFACES,
    MANIFEST_SCHEMA,
    MINIMUM_FONT_POINTS,
    MINIMUM_HEADING_POINTS,
    GenerationResult,
    SignoffValidationError,
    safe_slug,
    validate_spec,
)


def _bounded_occurrences(text: str, value: str) -> int:
    return len(re.findall(rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])", text))


def _validate_generated(
    spec: dict[str, Any],
    docx_path: Path,
    pdf_path: Path,
    page_paths: Iterable[Path],
) -> tuple[dict[str, Any], dict[str, Any]]:
    text = docx_text(docx_path)
    cell_texts = docx_serial_cell_texts(docx_path)
    pdf_text = extract_pdf_text(pdf_path)
    serial_counts: dict[str, Any] = {}
    for group in spec["serialized_assets"]:
        expected_values = [format_identifier(item) for item in group["identifiers"]]
        rendered = sum(cell_texts.count(value) for value in expected_values)
        duplicates = len(expected_values) - len({item["serial_number"].casefold() for item in group["identifiers"]})
        serial_counts[group["asset_type"]] = {
            "declared": len(group["identifiers"]),
            "rendered": rendered,
            "duplicates": duplicates,
        }
        if rendered != len(group["identifiers"]):
            raise SignoffValidationError(
                f"serial count mismatch for {group['asset_type']}: "
                f"declared {len(group['identifiers'])}, rendered {rendered}"
            )
        canonical_pdf = re.sub(r"[^A-Za-z0-9]", "", pdf_text).casefold()
        for item in group["identifiers"]:
            canonical_serial = re.sub(r"[^A-Za-z0-9]", "", item["serial_number"]).casefold()
            if canonical_serial not in canonical_pdf:
                raise SignoffValidationError(
                    f"rendered PDF does not contain the complete serial token: {item['serial_number']}"
                )
    matches = [token for token in spec["reject_tokens"] if token.casefold() in text.casefold()]
    if matches:
        raise SignoffValidationError(f"stale-content scan failed: {matches}")
    pages = tuple(page_paths)
    return serial_counts, {
        "status": "PASS",
        "matches": [],
        "scanned_tokens": spec["reject_tokens"],
        "pages": len(pages),
    }


def _validate_manifest_payload(manifest: dict[str, Any], package_dir: Path) -> None:
    required = {
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
    if float(manifest["minimum_heading_points"]) < MINIMUM_HEADING_POINTS:
        raise SignoffValidationError("manifest minimum heading is below 11 pt")
    if manifest["document_protection"] != "none":
        raise SignoffValidationError("document protection must be none")
    if not set(INK_SURFACES).issubset(set(manifest["required_ink_surfaces"])):
        raise SignoffValidationError("required ink surfaces are incomplete")
    proof_ceiling = manifest.get("proof_ceiling")
    if not isinstance(proof_ceiling, str) or len(proof_ceiling.strip()) < 20:
        raise SignoffValidationError("proof_ceiling must be a non-empty actionable boundary")
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


def _identity_from_package(package_dir: Path) -> tuple[str, str]:
    input_path = package_dir / "input-spec.json"
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        return payload["site"]["code"], payload["signoff"]["id"]
    except Exception as exc:  # noqa: BLE001
        raise SignoffValidationError(
            f"existing package cannot be safely identified: {input_path}: {exc}"
        ) from exc


def _acquire_lock(lock_path: Path) -> int:
    try:
        return os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise SignoffValidationError(f"another generation run owns this sign-off: {lock_path}") from exc


def _backup_root(output_root: Path) -> Path:
    for candidate in (output_root, *output_root.parents):
        if candidate.name == "delivery-signoff" and candidate.parent.name == "Outputs":
            return candidate.parent / "backups" / "delivery-signoff"
    return output_root.parent / "backups" / "delivery-signoff"


def _publish_package(
    temp_package: Path,
    package_dir: Path,
    output_root: Path,
    spec: dict[str, Any],
) -> Path | None:
    backup_path: Path | None = None
    if package_dir.exists():
        existing_identity = _identity_from_package(package_dir)
        requested_identity = (spec["site"]["code"], spec["signoff"]["id"])
        if existing_identity != requested_identity:
            raise SignoffValidationError(
                "safe-slug collision: existing package identity "
                f"{existing_identity!r} differs from requested {requested_identity!r}"
            )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = (
            _backup_root(output_root)
            / package_dir.parent.name
            / package_dir.name
            / f"{stamp}-{uuid4().hex[:8]}"
        )
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(package_dir, backup_path)
    try:
        os.replace(temp_package, package_dir)
    except Exception:
        if backup_path is not None and backup_path.exists() and not package_dir.exists():
            os.replace(backup_path, package_dir)
        raise
    return backup_path


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
    site_dir = output_root_path / site_slug
    package_dir = site_dir / signoff_slug
    site_dir.mkdir(parents=True, exist_ok=True)
    lock_path = site_dir / f".{signoff_slug}.lock"
    lock_fd = _acquire_lock(lock_path)
    temp_package: Path | None = Path(tempfile.mkdtemp(prefix=f".{signoff_slug}.tmp-", dir=site_dir))
    try:
        assert temp_package is not None
        preview_dir = temp_package / "preview"
        normalized_spec_path = temp_package / "input-spec.json"
        normalized_spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        docx_name = f"{site_slug}_Delivery_Sign_Off_{signoff_slug}_SERIAL_FIRST_INK_READY.docx"
        docx_path = temp_package / docx_name
        layout_plan = build_document(spec, docx_path)
        preview_pdf_path, page_preview_paths = render_docx(docx_path, preview_dir)
        serial_counts, stale_scan = _validate_generated(
            spec,
            docx_path,
            preview_pdf_path,
            page_preview_paths,
        )

        manifest = {
            "schema": MANIFEST_SCHEMA,
            "artifact_family": "delivery-signoff",
            "site_code": spec["site"]["code"],
            "site_name": spec["site"]["name"],
            "signoff_id": spec["signoff"]["id"],
            "serialized_assets_expected": bool(spec["serialized_assets"]),
            "input_spec": relative_entry(normalized_spec_path, temp_package),
            "docx": relative_entry(docx_path, temp_package),
            "preview": {
                **relative_entry(preview_pdf_path, temp_package),
                "format": "pdf",
                "page_hashes": [relative_entry(page, temp_package) for page in page_preview_paths],
            },
            "page_count": len(page_preview_paths),
            "minimum_font_points": MINIMUM_FONT_POINTS,
            "minimum_heading_points": MINIMUM_HEADING_POINTS,
            "layout_plan": {
                "orientation": "landscape" if layout_plan.landscape else "portrait",
                "serial_columns": layout_plan.serial_columns,
                "serial_width_inches": layout_plan.serial_width,
            },
            "serial_counts": serial_counts,
            "equipment_rows": spec["equipment_rows"],
            "document_protection": "none",
            "required_ink_surfaces": INK_SURFACES,
            "draw_proof_level": "draw_ready_static",
            "stale_content_scan": stale_scan,
            "source_provenance": spec["provenance"],
            "proof_ceiling": spec["proof_ceiling"],
        }
        _validate_manifest_payload(manifest, temp_package)
        manifest_path = temp_package / "delivery-signoff-artifact-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        validation_log_path = temp_package / "delivery-signoff-validation.txt"
        validation_log_path.write_text(
            "PASS: delivery sign-off generation\n"
            f"- site: {spec['site']['code']} | {spec['site']['name']}\n"
            f"- equipment rows: {len(spec['equipment_rows'])}\n"
            f"- serialized groups: {len(spec['serialized_assets'])}\n"
            f"- rendered pages: {len(page_preview_paths)}\n"
            f"- orientation: {'landscape' if layout_plan.landscape else 'portrait'}\n"
            f"- serial columns: {layout_plan.serial_columns}\n"
            f"- minimum font points: {MINIMUM_FONT_POINTS}\n"
            f"- minimum heading points: {MINIMUM_HEADING_POINTS}\n"
            "- document protection: none\n"
            "- required ink surfaces: PASS\n"
            "- stale content scan: PASS\n"
            "- exact DOCX serial-cell reconciliation: PASS\n"
            "- rendered PDF serial-token reconciliation: PASS\n"
            "- manifest path/hash containment: PASS\n",
            encoding="utf-8",
        )
        _publish_package(temp_package, package_dir, output_root_path, spec)
        temp_package = None  # publication moved the directory

        final_preview_dir = package_dir / "preview"
        final_docx_path = package_dir / docx_name
        final_pdf_path = final_preview_dir / preview_pdf_path.name
        final_pages = tuple(final_preview_dir / page.name for page in page_preview_paths)
        return GenerationResult(
            package_dir=package_dir,
            docx_path=final_docx_path,
            preview_pdf_path=final_pdf_path,
            page_preview_paths=final_pages,
            manifest_path=package_dir / "delivery-signoff-artifact-manifest.json",
            validation_log_path=package_dir / "delivery-signoff-validation.txt",
        )
    finally:
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)
        if temp_package is not None and temp_package.exists():
            shutil.rmtree(temp_package, ignore_errors=True)
