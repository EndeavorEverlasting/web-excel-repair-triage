"""Input contracts and common types for delivery sign-off generation."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "delivery-signoff-spec/v1"
MANIFEST_SCHEMA = "delivery-signoff-artifact-manifest/v1"
MINIMUM_FONT_POINTS = 8.5
MINIMUM_HEADING_POINTS = 11.0
INK_SURFACES = ["asset_mark_cells", "field_annotation_box", "receiver_signature"]
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
MAX_IDENTIFIER_LENGTH = 64


class SignoffValidationError(ValueError):
    """Raised when a sign-off input or generated artifact violates its contract."""


@dataclass(frozen=True)
class GenerationResult:
    package_dir: Path
    docx_path: Path
    preview_pdf_path: Path
    page_preview_paths: tuple[Path, ...]
    manifest_path: Path
    validation_log_path: Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_slug(value: str, fallback: str) -> str:
    slug = SAFE_NAME_RE.sub("_", value.strip()).strip("._")
    return slug or fallback


def _require_text(
    value: Any,
    field: str,
    *,
    allow_blank: bool = False,
    maximum_length: int | None = None,
) -> str:
    if not isinstance(value, str):
        raise SignoffValidationError(f"{field} must be a string")
    cleaned = value.strip()
    if not allow_blank and not cleaned:
        raise SignoffValidationError(f"{field} must not be blank")
    if CONTROL_RE.search(cleaned):
        raise SignoffValidationError(f"{field} must not contain control characters")
    if maximum_length is not None and len(cleaned) > maximum_length:
        raise SignoffValidationError(f"{field} must be at most {maximum_length} characters")
    return cleaned


def _require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SignoffValidationError(f"{field} must be a positive integer")
    return value


def validate_spec(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SignoffValidationError("input spec must be a JSON object")
    if raw.get("schema") != SCHEMA:
        raise SignoffValidationError(f"schema must be {SCHEMA}")

    site = raw.get("site")
    if not isinstance(site, dict):
        raise SignoffValidationError("site must be an object")
    site_code = _require_text(site.get("code"), "site.code", maximum_length=96)
    site_name = _require_text(site.get("name"), "site.name", maximum_length=160)

    signoff = raw.get("signoff")
    if not isinstance(signoff, dict):
        raise SignoffValidationError("signoff must be an object")
    signoff_id = _require_text(signoff.get("id"), "signoff.id", maximum_length=128)
    title = _require_text(signoff.get("title", "Delivery Sign-Off"), "signoff.title", maximum_length=160)
    delivery_date = _require_text(
        signoff.get("delivery_date", ""),
        "signoff.delivery_date",
        allow_blank=True,
        maximum_length=40,
    )

    recipient = raw.get("recipient", {})
    if not isinstance(recipient, dict):
        raise SignoffValidationError("recipient must be an object")
    recipient_norm = {
        field: _require_text(
            recipient.get(field, ""),
            f"recipient.{field}",
            allow_blank=True,
            maximum_length=160,
        )
        for field in ("name", "title", "building_room", "phone")
    }

    equipment = raw.get("equipment_rows")
    if not isinstance(equipment, list) or not equipment:
        raise SignoffValidationError("equipment_rows must be a non-empty list")
    equipment_norm: list[dict[str, Any]] = []
    seen_rows: set[tuple[str, str, str]] = set()
    equipment_by_type: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(equipment, 1):
        if not isinstance(row, dict):
            raise SignoffValidationError(f"equipment_rows[{index}] must be an object")
        equipment_type = _require_text(
            row.get("equipment_type"),
            f"equipment_rows[{index}].equipment_type",
            maximum_length=128,
        )
        model = _require_text(
            row.get("model_or_part", ""),
            f"equipment_rows[{index}].model_or_part",
            allow_blank=True,
            maximum_length=128,
        )
        variant = _require_text(
            row.get("color_or_variant", ""),
            f"equipment_rows[{index}].color_or_variant",
            allow_blank=True,
            maximum_length=128,
        )
        quantity = _require_positive_int(row.get("quantity"), f"equipment_rows[{index}].quantity")
        key = (equipment_type.casefold(), model.casefold(), variant.casefold())
        if key in seen_rows:
            raise SignoffValidationError(f"duplicate equipment row: {key}")
        seen_rows.add(key)
        if ("cable" in key[0] or "ethernet" in key[0]) and (not model or not variant):
            raise SignoffValidationError(
                f"equipment_rows[{index}] cable rows require model_or_part and color_or_variant"
            )
        normalized_row = {
            "equipment_type": equipment_type,
            "model_or_part": model,
            "color_or_variant": variant,
            "quantity": quantity,
        }
        equipment_norm.append(normalized_row)
        equipment_by_type.setdefault(equipment_type.casefold(), []).append(normalized_row)

    groups = raw.get("serialized_assets", [])
    if not isinstance(groups, list):
        raise SignoffValidationError("serialized_assets must be a list")
    groups_norm: list[dict[str, Any]] = []
    all_identifiers: set[str] = set()
    seen_asset_types: set[str] = set()
    for group_index, group in enumerate(groups, 1):
        if not isinstance(group, dict):
            raise SignoffValidationError(f"serialized_assets[{group_index}] must be an object")
        asset_type = _require_text(
            group.get("asset_type"),
            f"serialized_assets[{group_index}].asset_type",
            maximum_length=128,
        )
        asset_type_key = asset_type.casefold()
        if asset_type_key in seen_asset_types:
            raise SignoffValidationError(f"duplicate serialized asset type: {asset_type}")
        seen_asset_types.add(asset_type_key)
        identifiers = group.get("identifiers")
        if not isinstance(identifiers, list) or not identifiers:
            raise SignoffValidationError(
                f"serialized_assets[{group_index}].identifiers must be a non-empty list"
            )
        normalized: list[dict[str, str]] = []
        for item_index, item in enumerate(identifiers, 1):
            if not isinstance(item, dict):
                raise SignoffValidationError(
                    f"serialized_assets[{group_index}].identifiers[{item_index}] must be an object"
                )
            serial = _require_text(
                item.get("serial_number"),
                f"serialized_assets[{group_index}].identifiers[{item_index}].serial_number",
                maximum_length=MAX_IDENTIFIER_LENGTH,
            )
            mac = _require_text(
                item.get("mac_address", ""),
                f"serialized_assets[{group_index}].identifiers[{item_index}].mac_address",
                allow_blank=True,
                maximum_length=MAX_IDENTIFIER_LENGTH,
            )
            serial_key = serial.casefold()
            if serial_key in all_identifiers:
                raise SignoffValidationError(f"duplicate serial number: {serial}")
            all_identifiers.add(serial_key)
            normalized.append({"serial_number": serial, "mac_address": mac})

        matching_rows = equipment_by_type.get(asset_type_key, [])
        if len(matching_rows) != 1:
            raise SignoffValidationError(
                f"serialized asset type {asset_type!r} must match exactly one equipment row"
            )
        declared_quantity = matching_rows[0]["quantity"]
        if declared_quantity != len(normalized):
            raise SignoffValidationError(
                f"serialized asset quantity mismatch for {asset_type}: "
                f"equipment declares {declared_quantity}, identifiers provide {len(normalized)}"
            )
        groups_norm.append({"asset_type": asset_type, "identifiers": normalized})

    reject_tokens = raw.get("reject_tokens", [])
    if not isinstance(reject_tokens, list) or any(not isinstance(token, str) for token in reject_tokens):
        raise SignoffValidationError("reject_tokens must be a list of strings")
    provenance = raw.get("provenance", {})
    if not isinstance(provenance, dict):
        raise SignoffValidationError("provenance must be an object")
    proof_ceiling = _require_text(
        raw.get(
            "proof_ceiling",
            "Static render and package validation do not prove operator Word pen acceptance.",
        ),
        "proof_ceiling",
        maximum_length=500,
    )

    return {
        "schema": SCHEMA,
        "site": {"code": site_code, "name": site_name},
        "signoff": {
            "id": signoff_id,
            "title": title,
            "delivery_date": delivery_date,
            "subtitle": _require_text(
                signoff.get("subtitle", ""),
                "signoff.subtitle",
                allow_blank=True,
                maximum_length=160,
            ),
        },
        "recipient": recipient_norm,
        "equipment_rows": equipment_norm,
        "serialized_assets": groups_norm,
        "reject_tokens": [token.strip() for token in reject_tokens if token.strip()],
        "provenance": provenance,
        "proof_ceiling": proof_ceiling,
    }
