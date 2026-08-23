from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from triage.nth_qualitative_admin.builder import (
    MAIN_NS,
    PROFILE_PATH,
    QualitativeAdminError,
    build_package,
    build_workbook,
    derive_metrics,
    load_profile,
    validate_spec,
)
from triage.nth_qualitative_admin.validator import QualitativeAdminValidationError, validate_workbook
from triage.nth_qualitative_admin.style_template import canonical_styles_xml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "configs" / "examples"
NS = {"x": MAIN_NS}


def _load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _strings(path: Path, sheet_index: int) -> list[str]:
    with ZipFile(path) as zf:
        root = ET.fromstring(zf.read(f"xl/worksheets/sheet{sheet_index}.xml"))
    return [(node.text or "") for node in root.findall(".//x:c[@t='str']/x:v", NS)]


def test_reference_profile_is_machine_readable_and_current() -> None:
    profile = load_profile()
    assert profile["profile_id"] == "nth-qualitative-admin"
    assert {item["mode"] for item in profile["reference_fingerprints"]} == {
        "completed_month",
        "month_to_date",
    }
    assert len(profile["reference_fingerprints"]) == 2
    assert profile["authority"]["workbook_formula_policy"].startswith("forbidden")
    assert profile["package_contract"]["shared_strings"] == "present and empty"
    styles = profile["visual_contract"]["style_ids"]
    for name in ("title", "subtitle", "section_title", "kpi_value_yellow", "wrapped_date_total"):
        assert isinstance(styles[name], int)


def test_completed_month_build_derives_quantitative_controls_and_exact_structure(tmp_path: Path) -> None:
    spec = _load("nth_qualitative_admin_completed.synthetic.json")
    normalized = validate_spec(spec)
    metrics = derive_metrics(normalized)
    assert metrics["total_paid_hours"] == 32.5
    assert metrics["completed_shift_records"] == 4
    assert [item["paid_hours"] for item in metrics["technicians"]] == [16.0, 16.5]

    manifest = build_package(spec, tmp_path)
    workbook = Path(manifest["workbook"])
    assert workbook.name == "ADMIN_SHARE_NTH_June_2026_QUALITATIVE_CURRENT_2026-07-02.xlsx"
    assert manifest["validation_pass"] is True
    assert manifest["total_paid_hours"] == 32.5
    assert manifest["completed_shift_records"] == 4

    report = validate_workbook(workbook, normalized)
    assert report["status"] == "PASS"
    assert report["formula_count"] == 0
    assert report["sheet_count"] == 5

    with ZipFile(workbook) as zf:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        names = [item.attrib["name"] for item in wb.findall(".//x:sheets/x:sheet", NS)]
        assert names == [
            "Executive Dashboard",
            "Visual Summary",
            "June 2026 NTH Detail",
            "Operational Themes",
            "Billing Support Context",
        ]
        assert not any(name.startswith("xl/drawings/") for name in zf.namelist())
        assert "xl/calcChain.xml" not in zf.namelist()
        assert b"<f" not in b"".join(
            zf.read(f"xl/worksheets/sheet{idx}.xml") for idx in range(1, 6)
        )

    dashboard = "\n".join(_strings(workbook, 1))
    assert "RECORDED NTH" in dashboard
    assert "SHIFT RECORDS" in dashboard
    assert "PRIOR BASELINE" in dashboard
    assert "REVIEW — current NTH 32.5; prior baseline 31.5" in dashboard
    assert "Use paid hours by date/technician as the quantitative record." in dashboard


def test_mtd_build_preserves_zero_hour_tracked_tech_and_planned_boundary(tmp_path: Path) -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    normalized = validate_spec(spec)
    metrics = derive_metrics(normalized)
    assert metrics["total_paid_hours"] == 32.0
    assert metrics["completed_shift_records"] == 4
    assert metrics["technicians"][-1] == {
        "technician": "Gamma Tech",
        "paid_hours": 0.0,
        "shift_count": 0,
    }

    manifest = build_package(spec, tmp_path)
    workbook = Path(manifest["workbook"])
    assert workbook.name == "ADMIN_SHARE_NTH_August_2026_MTD_QUALITATIVE_CURRENT_2026-08-05.xlsx"
    assert manifest["validation_pass"] is True

    with ZipFile(workbook) as zf:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        names = [item.attrib["name"] for item in wb.findall(".//x:sheets/x:sheet", NS)]
        assert names == [
            "Executive Dashboard",
            "Visual Summary",
            "August 2026 NTH Detail",
            "Operational Themes",
            "Carryover & Planned Work",
            "Configuration & Inventory Context",
        ]
        shared = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        assert list(shared) == []

    dash = "\n".join(_strings(workbook, 1))
    assert "MTD PAID HOURS" in dash
    assert "COMPLETED SHIFTS" in dash
    assert "AUG 5" in dash
    assert "PLANNED — NOT POSTED" in dash
    assert "no task-hour split is inferred" in dash
    visual = "\n".join(_strings(workbook, 2))
    assert "Direct paid hours and completed shift records only. No percentage, peak, ranking, or inferred workstream-hour metrics." in visual


def test_mtd_planned_work_cannot_create_paid_hours() -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    spec["carryover_planned_work"][0]["paid_hours_posted"] = 1
    with pytest.raises(QualitativeAdminError, match="must keep paid_hours_posted at 0"):
        validate_spec(spec)


def test_detail_row_outside_target_month_fails_closed() -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    spec["detail_rows"][0]["date"] = "2026-07-31"
    with pytest.raises(QualitativeAdminError, match="outside target month"):
        validate_spec(spec)


def test_unsupported_percentage_or_rank_language_requires_direct_evidence() -> None:
    spec = _load("nth_qualitative_admin_completed.synthetic.json")
    spec["executive_readout"][0]["management_interpretation"] = "Configuration was 75% of the month and this was the peak day."
    with pytest.raises(QualitativeAdminError, match="percentage"):
        validate_spec(spec)
    spec["executive_readout"][0]["direct_quantitative_evidence"] = True
    validate_spec(spec)


def test_workstream_hour_allocation_language_requires_direct_task_time_evidence() -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    spec["detail_rows"][0]["qualitative_work_context"] = "4 hours configuration and validation."
    with pytest.raises(QualitativeAdminError, match="allocate hours to a workstream"):
        validate_spec(spec)
    spec["detail_rows"][0]["direct_task_time_evidence"] = True
    validate_spec(spec)


def test_committed_style_template_preserves_reference_font_palette_and_number_formats() -> None:
    profile = load_profile()
    style_bytes = canonical_styles_xml()
    root = ET.fromstring(style_bytes)
    fonts = root.find("x:fonts", NS)
    assert fonts is not None
    font_names = [node.attrib["val"] for node in fonts.findall(".//x:name", NS)]
    assert font_names and set(font_names) == {"Carlito"}
    xml = style_bytes.decode("utf-8")
    for color in ("173B5C", "DCEAF7", "DDEED9", "FFF1BF"):
        assert color in xml
    numfmts = {item.attrib["numFmtId"]: item.attrib["formatCode"] for item in root.findall(".//x:numFmts/x:numFmt", NS)}
    assert numfmts["200"] == "0.00"
    assert numfmts["201"] == "m/d/yyyy"
    cell_xfs = root.find("x:cellXfs", NS)
    assert cell_xfs is not None
    assert int(cell_xfs.attrib["count"]) >= 140


def test_manifest_records_reference_fingerprints_not_private_reference_paths(tmp_path: Path) -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    manifest = build_package(spec, tmp_path)
    payload = Path(manifest["manifest"]).read_text(encoding="utf-8")
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    for item in profile["reference_fingerprints"]:
        assert item["sha256"] in payload
    assert "ADMIN_SHARE_NTH_August_2026_MTD_QUALITATIVE_CURRENT_2026-08-19.xlsx" not in payload
    assert "ADMIN_SHARE_NTH_June_2026_QUALITATIVE_CURRENT_2026-08-19.xlsx" not in payload


def test_repository_local_output_is_restricted_to_outputs() -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    for forbidden in (ROOT / "Candidates" / "bad", ROOT / "Active" / "bad", ROOT / "bad-output"):
        with pytest.raises(QualitativeAdminError, match="must be written under Outputs"):
            build_package(spec, forbidden)
        assert not forbidden.exists()


def _rewrite_sheet_cell(workbook: Path, sheet_index: int, ref: str, new_value: str) -> None:
    with ZipFile(workbook, "r") as src:
        members = {name: src.read(name) for name in src.namelist()}
    member = f"xl/worksheets/sheet{sheet_index}.xml"
    root = ET.fromstring(members[member])
    cell = root.find(f".//x:c[@r='{ref}']", NS)
    assert cell is not None
    value = cell.find("x:v", NS)
    assert value is not None
    value.text = new_value
    ET.register_namespace("", MAIN_NS)
    members[member] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    replacement = workbook.with_suffix(".tampered.xlsx")
    with ZipFile(replacement, "w") as out:
        for name, data in members.items():
            out.writestr(name, data)
    replacement.replace(workbook)


def test_direct_build_workbook_preserves_protected_operator_inputs() -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    for forbidden in (
        ROOT / "Candidates" / "do-not-touch.xlsx",
        ROOT / "Active" / "do-not-touch.xlsx",
        ROOT / "do-not-touch.xlsx",
    ):
        with pytest.raises(QualitativeAdminError, match="must be written under Outputs"):
            build_workbook(spec, forbidden)
        assert not forbidden.exists()


def test_nonfinite_numeric_evidence_fails_closed() -> None:
    base = _load("nth_qualitative_admin_mtd.synthetic.json")
    for value in ("NaN", "Infinity", "-Infinity"):
        spec = deepcopy(base)
        spec["detail_rows"][0]["paid_hours"] = value
        with pytest.raises(QualitativeAdminError, match="must be finite"):
            validate_spec(spec)

    completed = _load("nth_qualitative_admin_completed.synthetic.json")
    completed["prior_baseline"] = "NaN"
    with pytest.raises(QualitativeAdminError, match="prior_baseline must be finite"):
        validate_spec(completed)

    carryover = deepcopy(base)
    carryover["carryover_planned_work"][0]["paid_hours_posted"] = "Infinity"
    with pytest.raises(QualitativeAdminError, match="paid_hours_posted must be finite"):
        validate_spec(carryover)


def test_evidence_flags_must_be_real_booleans() -> None:
    spec = _load("nth_qualitative_admin_completed.synthetic.json")
    spec["executive_readout"][0]["direct_quantitative_evidence"] = "false"
    with pytest.raises(QualitativeAdminError, match="direct_quantitative_evidence must be boolean"):
        validate_spec(spec)

    detail = _load("nth_qualitative_admin_mtd.synthetic.json")
    detail["detail_rows"][0]["direct_task_time_evidence"] = "false"
    with pytest.raises(QualitativeAdminError, match="direct_task_time_evidence must be boolean"):
        validate_spec(detail)


def test_case_variant_technician_identity_aggregates_to_canonical_tracked_name() -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    spec["detail_rows"][0]["technician"] = "alpha tech"
    normalized = validate_spec(spec)
    metrics = derive_metrics(normalized)
    alpha = [item for item in metrics["technicians"] if item["technician"] == "Alpha Tech"]
    assert alpha == [{"technician": "Alpha Tech", "paid_hours": 16.0, "shift_count": 2}]
    assert not any(item["technician"] == "alpha tech" for item in metrics["technicians"])


def test_validator_rejects_tampered_detail_evidence(tmp_path: Path) -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    normalized = validate_spec(spec)
    manifest = build_package(spec, tmp_path)
    workbook = Path(manifest["workbook"])
    _rewrite_sheet_cell(workbook, 3, "D5", "999")
    with pytest.raises(QualitativeAdminValidationError, match="paid_hours reconciliation failed"):
        validate_workbook(workbook, normalized)


def test_validator_rejects_tampered_dashboard_quantitative_control(tmp_path: Path) -> None:
    spec = _load("nth_qualitative_admin_mtd.synthetic.json")
    normalized = validate_spec(spec)
    manifest = build_package(spec, tmp_path)
    workbook = Path(manifest["workbook"])
    _rewrite_sheet_cell(workbook, 1, "A5", "999")
    with pytest.raises(QualitativeAdminValidationError, match="dashboard total paid hours reconciliation failed"):
        validate_workbook(workbook, normalized)


def test_theme_is_well_formed_and_profile_fingerprints_match_templates() -> None:
    profile = load_profile()
    theme = (ROOT / "triage" / "nth_qualitative_admin" / "templates" / "theme1.xml").read_bytes()
    ET.fromstring(theme)
    assert hashlib.sha256(theme).hexdigest() == profile["visual_contract"]["template_sha256"]["theme1.xml"]
    assert hashlib.sha256(canonical_styles_xml()).hexdigest() == profile["visual_contract"]["template_sha256"]["styles.xml"]
