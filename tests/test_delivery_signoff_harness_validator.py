from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.validate_delivery_signoff_harness import validate_manifest


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_manifest(tmp_path: Path) -> tuple[Path, dict]:
    spec = {
        "schema": "delivery-signoff-spec/v1",
        "site": {"code": "SITE", "name": "Site Name"},
        "signoff": {"id": "SIGNOFF", "title": "Delivery Sign-Off", "delivery_date": ""},
        "recipient": {},
        "equipment_rows": [
            {"equipment_type": "Arm", "model_or_part": "FLP-1", "color_or_variant": "", "quantity": 1}
        ],
        "serialized_assets": [],
        "proof_ceiling": "Static validation does not prove operator acceptance."
    }
    (tmp_path / "input-spec.json").write_text(json.dumps(spec), encoding="utf-8")
    for name in ("signoff.docx", "preview.pdf", "page-1.png"):
        (tmp_path / name).write_bytes(name.encode())
    manifest = {
        "schema": "delivery-signoff-artifact-manifest/v1",
        "site_code": "SITE",
        "site_name": "Site Name",
        "signoff_id": "SIGNOFF",
        "serialized_assets_expected": False,
        "input_spec": {"path": "input-spec.json", "sha256": _sha(tmp_path / "input-spec.json")},
        "docx": {"path": "signoff.docx", "sha256": _sha(tmp_path / "signoff.docx")},
        "preview": {
            "path": "preview.pdf",
            "sha256": _sha(tmp_path / "preview.pdf"),
            "page_hashes": [{"path": "page-1.png", "sha256": _sha(tmp_path / "page-1.png")}]
        },
        "page_count": 1,
        "minimum_font_points": 8.5,
        "minimum_heading_points": 11,
        "serial_counts": {},
        "equipment_rows": spec["equipment_rows"],
        "document_protection": "none",
        "required_ink_surfaces": ["asset_mark_cells", "field_annotation_box", "receiver_signature"],
        "draw_proof_level": "draw_ready_static",
        "stale_content_scan": {"status": "PASS", "matches": []},
        "proof_ceiling": spec["proof_ceiling"]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, manifest


def _validate(path: Path) -> list[str]:
    errors: list[str] = []
    validate_manifest(path, errors)
    return errors


def _write(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_valid_manifest_passes(tmp_path: Path) -> None:
    path, _ = _valid_manifest(tmp_path)
    assert _validate(path) == []


def test_empty_preview_evidence_fails(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    manifest["preview"] = {}
    _write(path, manifest)
    errors = _validate(path)
    assert any("preview.path" in error for error in errors)
    assert any("page_hashes" in error for error in errors)


def test_negative_serial_count_fails(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    manifest["serialized_assets_expected"] = True
    manifest["serial_counts"] = {"Neuron": {"declared": -1, "rendered": -1, "duplicates": 0}}
    _write(path, manifest)
    assert any("non-negative integer" in error for error in _validate(path))


def test_malformed_equipment_row_fails(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    manifest["equipment_rows"] = [{"equipment_type": "", "quantity": "1"}]
    _write(path, manifest)
    errors = _validate(path)
    assert any("equipment_type" in error for error in errors)
    assert any("quantity" in error for error in errors)


def test_absolute_and_escape_paths_fail(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    manifest["docx"]["path"] = str((tmp_path / "signoff.docx").resolve())
    manifest["input_spec"]["path"] = "../outside.json"
    _write(path, manifest)
    errors = _validate(path)
    assert any("docx.path must be relative" in error for error in errors)
    assert any("input_spec.path escapes" in error for error in errors)


def test_blank_proof_ceiling_fails(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    manifest["proof_ceiling"] = ""
    _write(path, manifest)
    assert any("proof_ceiling" in error for error in _validate(path))


def test_input_spec_schema_is_bound_to_manifest(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    spec_path = tmp_path / "input-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["schema"] = "not-a-signoff"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    manifest["input_spec"]["sha256"] = _sha(spec_path)
    _write(path, manifest)
    assert any("input_spec schema" in error for error in _validate(path))


def test_manifest_equipment_must_match_input_spec(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    manifest["equipment_rows"][0]["quantity"] = 2
    _write(path, manifest)
    assert any("do not match input_spec" in error for error in _validate(path))


def test_manifest_serial_counts_must_match_input_spec(tmp_path: Path) -> None:
    path, manifest = _valid_manifest(tmp_path)
    spec_path = tmp_path / "input-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["equipment_rows"] = [
        {"equipment_type": "Neuron", "model_or_part": "", "color_or_variant": "", "quantity": 2}
    ]
    spec["serialized_assets"] = [
        {"asset_type": "Neuron", "identifiers": [{"serial_number": "1"}, {"serial_number": "2"}]}
    ]
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    manifest["input_spec"]["sha256"] = _sha(spec_path)
    manifest["equipment_rows"] = spec["equipment_rows"]
    manifest["serialized_assets_expected"] = True
    manifest["serial_counts"] = {"Neuron": {"declared": 1, "rendered": 1, "duplicates": 0}}
    _write(path, manifest)
    assert any("serial_counts do not reconcile" in error for error in _validate(path))
