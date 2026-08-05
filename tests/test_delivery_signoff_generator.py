from __future__ import annotations

import json
from pathlib import Path

import pytest

from triage.delivery_signoff import SignoffValidationError, generate_signoff

FIXTURES = Path(__file__).parent / "fixtures" / "delivery_signoff"


@pytest.mark.parametrize(
    ("fixture", "expected_rows", "expected_poc"),
    [
        ("melville_3hq_20260805.json", 16, "Timothy W. Seeberger"),
        ("huntington_hospital_20260805.json", 3, "Morgan Mitchell"),
    ],
)
def test_generates_valid_equipment_only_signoff(tmp_path: Path, fixture: str, expected_rows: int, expected_poc: str) -> None:
    result = generate_signoff(FIXTURES / fixture, tmp_path)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert result.docx_path.is_file()
    assert result.preview_pdf_path.is_file()
    assert result.validation_log_path.read_text(encoding="utf-8").startswith("PASS")
    assert 1 <= manifest["page_count"] <= 2
    assert len(manifest["equipment_rows"]) == expected_rows
    assert manifest["serial_counts"] == {}
    assert manifest["serialized_assets_expected"] is False
    assert manifest["preview"]["page_hashes"]
    assert expected_poc in _docx_xml(result.docx_path)


def test_generates_serial_first_group_and_reconciles_counts(tmp_path: Path) -> None:
    payload = json.loads((FIXTURES / "huntington_hospital_20260805.json").read_text(encoding="utf-8"))
    payload["serialized_assets"] = [
        {
            "asset_type": "Neuron",
            "identifiers": [
                {"serial_number": "1100000001", "mac_address": "AA:BB:CC:00:00:01"},
                {"serial_number": "1100000002", "mac_address": "AA:BB:CC:00:00:02"},
                {"serial_number": "1100000003", "mac_address": ""}
            ]
        }
    ]
    source = tmp_path / "serial-signoff.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = generate_signoff(source, tmp_path / "out")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["serialized_assets_expected"] is True
    assert manifest["serial_counts"]["Neuron"] == {"declared": 3, "rendered": 3, "duplicates": 0}
    assert "1100000001 / AA:BB:CC:00:00:01" in _docx_xml(result.docx_path)


def test_rejects_invalid_quantity(tmp_path: Path) -> None:
    payload = json.loads((FIXTURES / "huntington_hospital_20260805.json").read_text(encoding="utf-8"))
    payload["equipment_rows"][0]["quantity"] = -1
    source = tmp_path / "bad.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SignoffValidationError, match="positive integer"):
        generate_signoff(source, tmp_path / "out")


def test_rejects_duplicate_serials(tmp_path: Path) -> None:
    payload = json.loads((FIXTURES / "huntington_hospital_20260805.json").read_text(encoding="utf-8"))
    payload["serialized_assets"] = [
        {
            "asset_type": "Neuron",
            "identifiers": [
                {"serial_number": "1100000001"},
                {"serial_number": "1100000001"}
            ]
        }
    ]
    source = tmp_path / "bad-serials.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SignoffValidationError, match="duplicate serial"):
        generate_signoff(source, tmp_path / "out")


def test_rejects_incomplete_cable_identity(tmp_path: Path) -> None:
    payload = json.loads((FIXTURES / "huntington_hospital_20260805.json").read_text(encoding="utf-8"))
    payload["equipment_rows"] = [
        {"equipment_type": "Ethernet Cable", "model_or_part": "CAT6", "color_or_variant": "", "quantity": 2}
    ]
    source = tmp_path / "bad-cable.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SignoffValidationError, match="require model_or_part and color_or_variant"):
        generate_signoff(source, tmp_path / "out")


def _docx_xml(path: Path) -> str:
    import zipfile

    with zipfile.ZipFile(path) as archive:
        return archive.read("word/document.xml").decode("utf-8")
