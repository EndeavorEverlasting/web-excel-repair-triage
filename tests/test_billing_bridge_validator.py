from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from triage import billing_bridge_validator as bbv
from triage import billing_workbook_profile as bwp


# ── helpers: synthetic OOXML ──

def _make_minimal_xlsx(
    sheet_names: list[str] | None = None,
    table_names: list[str] | None = None,
    formulas: list[str] | None = None,
    bad_rels_target: str | None = None,
) -> bytes:
    """Build a tiny .xlsx in memory for testing."""
    sheet_names = sheet_names or ["Sheet1"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml
        z.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'</Types>',
        )
        # xl/workbook.xml
        sheets_xml = "".join(
            f'<sheet name="{n}" sheetId="{i+1}" r:id="rId{i+1}"/>'
            for i, n in enumerate(sheet_names)
        )
        z.writestr(
            "xl/workbook.xml",
            (
                '<?xml version="1.0"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f'<sheets>{sheets_xml}</sheets></workbook>'
            ).encode("utf-8"),
        )
        # xl/_rels/workbook.xml.rels
        rels = ""
        for i, _ in enumerate(sheet_names):
            target = bad_rels_target or f"worksheets/sheet{i+1}.xml"
            rels += (
                f'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="{target}" Id="rId{i+1}"/>'
            )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            (
                '<?xml version="1.0"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'{rels}</Relationships>'
            ).encode("utf-8"),
        )
        # xl/worksheets/sheet*.xml
        formula_xml = ""
        if formulas:
            for f in formulas:
                formula_xml += f'<c r="A1" t="str"><f>{f}</f><v></v></c>'
        for i, _ in enumerate(sheet_names):
            z.writestr(
                f"xl/worksheets/sheet{i+1}.xml",
                (
                    '<?xml version="1.0"?>'
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    '<sheetData>'
                    f'<row r="1">{formula_xml}</row>'
                    '</sheetData></worksheet>'
                ).encode("utf-8"),
            )
        # xl/styles.xml
        z.writestr(
            "xl/styles.xml",
            b'<?xml version="1.0"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        )
        # xl/sharedStrings.xml
        z.writestr(
            "xl/sharedStrings.xml",
            b'<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1"><si><t>hello</t></si></sst>',
        )
        # xl/tables/table*.xml
        for i, tn in enumerate(table_names or []):
            z.writestr(
                f"xl/tables/table{i+1}.xml",
                (
                    '<?xml version="1.0"?>'
                    '<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    f'displayName="{tn}" id="{i+1}" ref="A1:B2">'
                    '<tableColumns><tableColumn id="1" name="ColA"/></tableColumns></table>'
                ).encode("utf-8"),
            )
    return buf.getvalue()


# ── profile tests ──

def test_profile_detects_billing_sheet_names(tmp_path: Path) -> None:
    p = tmp_path / "billing.xlsx"
    p.write_bytes(_make_minimal_xlsx(sheet_names=["Billing Summary", "Sheet2"]))
    result = bwp.profile_workbook(str(p))
    assert result.is_billing_workbook is True
    assert "Billing Summary" in result.matched_sheet_names


def test_profile_detects_billing_table_names(tmp_path: Path) -> None:
    p = tmp_path / "hours.xlsx"
    p.write_bytes(_make_minimal_xlsx(table_names=["Hours_Table"]))
    result = bwp.profile_workbook(str(p))
    assert result.is_billing_workbook is True
    assert "Hours_Table" in result.matched_table_names


def test_profile_low_confidence_for_generic_workbook(tmp_path: Path) -> None:
    p = tmp_path / "generic.xlsx"
    p.write_bytes(_make_minimal_xlsx(sheet_names=["Data"]))
    result = bwp.profile_workbook(str(p))
    assert result.is_billing_workbook is False
    assert result.confidence == "low"


# ── validator tests ──

def test_validator_passes_clean_workbook(tmp_path: Path) -> None:
    p = tmp_path / "clean.xlsx"
    p.write_bytes(_make_minimal_xlsx(sheet_names=["Billing Summary"]))
    rpt = bbv.validate_billing_workbook(
        str(p),
        run_id="billing-2026-04-001",
        month="2026-04",
        out_root=str(tmp_path / "runs"),
    )
    assert rpt.status in ("pass", "warn")
    assert rpt.checks["zip_scan"] == "pass"
    out_dir = tmp_path / "runs" / "2026-04" / "validation"
    assert (out_dir / "billing-2026-04-001_validation_report.json").exists()


def test_validator_fails_malformed_zip(tmp_path: Path) -> None:
    p = tmp_path / "broken.zip"
    p.write_text("not a zip")
    rpt = bbv.validate_billing_workbook(
        str(p),
        run_id="billing-2026-04-002",
        month="2026-04",
        out_root=str(tmp_path / "runs"),
    )
    assert rpt.status == "fail"
    assert "ZIP integrity" in rpt.failures[0]
    assert rpt.web_excel_safe is False


def test_validator_blocks_missing_relationship_target(tmp_path: Path) -> None:
    p = tmp_path / "bad_rels.xlsx"
    p.write_bytes(
        _make_minimal_xlsx(
            sheet_names=["Invoice"],
            bad_rels_target="worksheets/missing.xml",
        )
    )
    rpt = bbv.validate_billing_workbook(
        str(p),
        run_id="billing-2026-04-003",
        month="2026-04",
        out_root=str(tmp_path / "runs"),
    )
    assert rpt.checks["relationships"] == "fail"
    assert rpt.status == "fail"
    assert rpt.web_excel_safe is False


def test_validator_warns_on_stopship_formula(tmp_path: Path) -> None:
    p = tmp_path / "stopship.xlsx"
    p.write_bytes(
        _make_minimal_xlsx(
            sheet_names=["Billing"],
            formulas=["=_xlfn.LET(a,1,a+1)"],
        )
    )
    rpt = bbv.validate_billing_workbook(
        str(p),
        run_id="billing-2026-04-004",
        month="2026-04",
        out_root=str(tmp_path / "runs"),
    )
    assert rpt.checks["stop_ship_tokens"] == "fail"
    assert rpt.status == "fail"
    assert rpt.web_excel_safe is False


def test_cli_writes_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "candidate.xlsx"
    p.write_bytes(_make_minimal_xlsx(sheet_names=["Billing Bridge"]))
    out_root = tmp_path / "runs"
    monkeypatch.chdir(tmp_path)
    from triage.billing_bridge_validator import _cli
    monkeypatch.setattr(
        "sys.argv",
        [
            "billing_bridge_validator",
            str(p),
            "--run-id",
            "billing-2026-04-005",
            "--month",
            "2026-04",
            "--out-root",
            str(out_root),
            "--quiet",
        ],
    )
    # _cli prints the report path on success
    _cli()
    report_path = out_root / "2026-04" / "validation" / "billing-2026-04-005_validation_report.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["run_id"] == "billing-2026-04-005"
    assert "candidate_workbook" in data
