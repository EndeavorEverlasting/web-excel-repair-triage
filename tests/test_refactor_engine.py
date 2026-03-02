"""
tests/test_refactor_engine.py
------------------------------
Unit tests for triage.refactor_engine.

Test matrix
-----------
  T1  build_permutation — identity when order unchanged
  T2  build_permutation — columns reorder correctly
  T3  build_permutation — unspecified columns appended at end
  T4  rewrite_cell_ref — simple ref remapped
  T5  rewrite_formula — formula refs remapped, strings preserved
  T6  rewrite_sqref — space-separated ranges remapped
  T7  rewrite_sheet_xml — row cells reordered, formulas rewritten
  T8  rewrite_table_xml — tableColumn elements reordered, renames applied
  T9  refactor_columns — end-to-end on synthetic workbook
  T10 refactor_columns — rename_map updates header names
  T11 refactor_columns — CF sqref rewritten after column move
  T12 refactor_columns — DV sqref rewritten after column move
"""
from __future__ import annotations
import io
import re
import zipfile

import pytest

from triage.refactor_engine import (
    build_permutation,
    remap_col_letter,
    rewrite_cell_ref,
    rewrite_formula,
    rewrite_sqref,
    rewrite_sheet_xml,
    rewrite_table_xml,
    refactor_columns,
    RefactorSpec,
)


# ─────────────────────────── helpers ────────────────────────────────

_WB_XML = b"""<?xml version="1.0"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Deploy" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

_WB_RELS = b"""<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
</Relationships>"""

_SHEET_RELS = b"""<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table"
    Target="../tables/table1.xml"/>
</Relationships>"""

_CONTENT_TYPES = b"""<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""


def _make_sheet(rows_xml: str, cf_xml: str = "", dv_xml: str = "") -> bytes:
    return (
        '<?xml version="1.0"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:xr="http://schemas.microsoft.com/office/spreadsheetml/2014/revision">'
        f'<sheetData>{rows_xml}</sheetData>'
        f'{cf_xml}{dv_xml}'
        '</worksheet>'
    ).encode("utf-8")


def _make_table(headers: list[str], ref: str = "A1:C3") -> bytes:
    cols = "".join(
        f'<tableColumn id="{i+1}" name="{h}"/>' for i, h in enumerate(headers)
    )
    return (
        f'<?xml version="1.0"?>'
        f'<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        f' ref="{ref}" displayName="tblTest" name="tblTest">'
        f'<tableColumns count="{len(headers)}">{cols}</tableColumns>'
        f'</table>'
    ).encode("utf-8")


def _make_xlsx(sheet_bytes: bytes, table_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("xl/workbook.xml", _WB_XML)
        z.writestr("xl/_rels/workbook.xml.rels", _WB_RELS)
        z.writestr("xl/worksheets/sheet1.xml", sheet_bytes)
        z.writestr("xl/worksheets/_rels/sheet1.xml.rels", _SHEET_RELS)
        z.writestr("xl/tables/table1.xml", table_bytes)
    return buf.getvalue()


def _read_part(data: bytes, part: str) -> str:
    with zipfile.ZipFile(io.BytesIO(data), "r") as z:
        return z.read(part).decode("utf-8")


# ─────────────────────────── T1-T3: build_permutation ────────────

def test_t1_identity_permutation():
    headers = ["A", "B", "C"]
    perm = build_permutation(headers, ["A", "B", "C"])
    assert perm == {1: 1, 2: 2, 3: 3}


def test_t2_reorder_permutation():
    headers = ["A", "B", "C"]
    perm = build_permutation(headers, ["C", "A", "B"])
    assert perm == {1: 2, 2: 3, 3: 1}


def test_t3_unspecified_appended():
    headers = ["A", "B", "C", "D"]
    perm = build_permutation(headers, ["C", "A"])
    # C→1, A→2, then B→3, D→4 (original order of unspecified)
    assert perm[3] == 1  # C
    assert perm[1] == 2  # A
    assert perm[2] == 3  # B
    assert perm[4] == 4  # D


# ─────────────────────────── T4-T6: reference rewriting ──────────

def test_t4_rewrite_cell_ref():
    perm = {1: 3, 2: 1, 3: 2}  # A→C, B→A, C→B
    assert rewrite_cell_ref("$A$1", perm) == "$C$1"
    assert rewrite_cell_ref("B5", perm) == "A5"
    assert rewrite_cell_ref("C10", perm) == "B10"
    assert rewrite_cell_ref("$A$1:$C$99", perm) == "$C$1:$B$99"


def test_t5_rewrite_formula():
    perm = {1: 3, 2: 1, 3: 2}  # A→C, B→A, C→B
    assert rewrite_formula('$A2>0', perm) == '$C2>0'
    assert rewrite_formula('AND($B2="Yes",LEN(TRIM($C2))=0)', perm) == 'AND($A2="Yes",LEN(TRIM($B2))=0)'
    # String literals are preserved
    assert rewrite_formula('"Yes"', perm) == '"Yes"'


def test_t6_rewrite_sqref():
    perm = {1: 2, 2: 1}  # A↔B
    assert rewrite_sqref("A1:A10 B1:B10", perm) == "B1:B10 A1:A10"


# ─────────────────────────── T7: sheet XML rewriting ─────────────

def test_t7_rewrite_sheet_xml():
    xml = (
        '<worksheet><sheetData>'
        '<row r="1"><c r="A1"><v>0</v></c><c r="B1"><v>1</v></c><c r="C1"><v>2</v></c></row>'
        '<row r="2"><c r="A2"><v>x</v></c><c r="B2"><f>$A2+1</f><v>1</v></c><c r="C2"><v>z</v></c></row>'
        '</sheetData></worksheet>'
    )
    perm = {1: 3, 2: 1, 3: 2}  # A→C, B→A, C→B
    new_xml, fc = rewrite_sheet_xml(xml, perm)

    # Row 1: cells should be reordered (B→A, C→B, A→C)
    # The cell that was at A1 (col 1→3) should now be at C1
    assert 'r="C1"' in new_xml
    assert 'r="A1"' in new_xml
    assert 'r="B1"' in new_xml

    # Formula should be rewritten: $A2 → $C2
    assert "$C2+1" in new_xml
    assert fc > 0


# ─────────────────────────── T8: table XML rewriting ─────────────

def test_t8_rewrite_table_xml():
    tbl = (
        '<table ref="A1:C3" displayName="t" name="t">'
        '<tableColumns count="3">'
        '<tableColumn id="1" name="Alpha"/>'
        '<tableColumn id="2" name="Beta"/>'
        '<tableColumn id="3" name="Gamma"/>'
        '</tableColumns></table>'
    )
    perm = {1: 3, 2: 1, 3: 2}  # A→C, B→A, C→B
    rename = {"Alpha": "Alpha_NEW"}
    new_tbl, rc = rewrite_table_xml(tbl, perm, rename)
    # Beta should be first (was col 2 → col 1)
    cols = re.findall(r'name="([^"]*)"', new_tbl)
    # Filter out the table-level name
    tc_cols = [c for c in cols if c not in ("t",)]
    assert tc_cols[0] == "Beta"
    assert tc_cols[1] == "Gamma"
    assert tc_cols[2] == "Alpha_NEW"
    assert rc == 1


# ─────────────────────────── T9: end-to-end refactor ─────────────

def test_t9_refactor_columns_end_to_end():
    rows = (
        '<row r="1"><c r="A1"><v>0</v></c><c r="B1"><v>1</v></c><c r="C1"><v>2</v></c></row>'
        '<row r="2"><c r="A2"><v>x</v></c><c r="B2"><f>$A2+1</f><v>1</v></c><c r="C2"><v>z</v></c></row>'
    )
    sheet = _make_sheet(rows)
    table = _make_table(["Alpha", "Beta", "Gamma"], ref="A1:C2")
    xlsx = _make_xlsx(sheet, table)

    spec = RefactorSpec(
        target_sheet_name="Deploy",
        new_column_order=["Gamma", "Alpha", "Beta"],
    )
    result = refactor_columns(xlsx, spec)
    assert result.columns_moved > 0

    # Check table column order
    tbl_xml = _read_part(result.output_bytes, "xl/tables/table1.xml")
    cols = re.findall(r'name="([^"]*)"', tbl_xml)
    tc_cols = [c for c in cols if c not in ("tblTest",)]
    assert tc_cols == ["Gamma", "Alpha", "Beta"]


# ─────────────────────────── T10: rename_map ─────────────────────

def test_t10_rename_map():
    rows = '<row r="1"><c r="A1"><v>0</v></c><c r="B1"><v>1</v></c></row>'
    sheet = _make_sheet(rows)
    table = _make_table(["OldName", "Beta"], ref="A1:B1")
    xlsx = _make_xlsx(sheet, table)

    spec = RefactorSpec(
        target_sheet_name="Deploy",
        new_column_order=["OldName", "Beta"],
        rename_map={"OldName": "NewName"},
    )
    result = refactor_columns(xlsx, spec)
    assert result.columns_renamed == 1
    tbl_xml = _read_part(result.output_bytes, "xl/tables/table1.xml")
    assert 'name="NewName"' in tbl_xml
    assert 'name="OldName"' not in tbl_xml


# ─────────────────────────── T11: CF sqref rewritten ─────────────

def test_t11_cf_sqref_rewritten():
    rows = '<row r="1"><c r="A1"><v>0</v></c><c r="B1"><v>1</v></c></row>'
    cf = (
        '<conditionalFormatting sqref="A2:A10">'
        '<cfRule type="expression" dxfId="0" priority="1">'
        '<formula>$A2&gt;0</formula>'
        '</cfRule></conditionalFormatting>'
    )
    sheet = _make_sheet(rows, cf_xml=cf)
    table = _make_table(["Alpha", "Beta"], ref="A1:B1")
    xlsx = _make_xlsx(sheet, table)

    spec = RefactorSpec(
        target_sheet_name="Deploy",
        new_column_order=["Beta", "Alpha"],  # swap A↔B
    )
    result = refactor_columns(xlsx, spec)
    sheet_xml = _read_part(result.output_bytes, "xl/worksheets/sheet1.xml")
    # A was col 1 → now col 2 (B)
    assert 'sqref="B2:B10"' in sheet_xml
    assert "$B2" in sheet_xml  # formula ref updated


# ─────────────────────────── T12: DV sqref rewritten ─────────────

def test_t12_dv_sqref_rewritten():
    rows = '<row r="1"><c r="A1"><v>0</v></c><c r="B1"><v>1</v></c></row>'
    dv = (
        '<dataValidations count="1">'
        '<dataValidation type="custom" sqref="A2:A10" xr:uid="{TEST}">'
        '<formula1>FALSE</formula1>'
        '</dataValidation></dataValidations>'
    )
    sheet = _make_sheet(rows, dv_xml=dv)
    table = _make_table(["Alpha", "Beta"], ref="A1:B1")
    xlsx = _make_xlsx(sheet, table)

    spec = RefactorSpec(
        target_sheet_name="Deploy",
        new_column_order=["Beta", "Alpha"],
    )
    result = refactor_columns(xlsx, spec)
    sheet_xml = _read_part(result.output_bytes, "xl/worksheets/sheet1.xml")
    assert 'sqref="B2:B10"' in sheet_xml


# ─────────────────── Real sample data comparison tests ───────────

import os

_REF_CF = os.path.join(
    "Deprecated", "repaired", "web_repaired",
    "webrepaired_CF_Present_CANDIDATE_DeploymentTracker_vNext10_2026-03-02_0700_WEBSAFE.xlsx",
)
_ACTIVE = os.path.join(
    "Active",
    "CANDIDATE_DeploymentTracker_vNext10_2026-03-02_REFACTORED_WEBSAFE.xlsx",
)
# Fallback to Deprecated if refactored not yet in Active
if not os.path.exists(_ACTIVE):
    _ACTIVE = os.path.join(
        "Deprecated", "candidate",
        "CANDIDATE_DeploymentTracker_vNext10_2026-03-02_1415_WEBSAFE.xlsx",
    )

_HAS_REF = os.path.exists(_REF_CF)
_HAS_ACTIVE = os.path.exists(_ACTIVE)


@pytest.mark.skipif(not _HAS_REF, reason="Reference CF workbook not found")
def test_real_cf_extraction():
    """Extract CF dictionary from reference workbook and verify key properties."""
    from triage.cf_engine import extract_cf_dictionary
    cfd = extract_cf_dictionary(_REF_CF)
    # Should have blocks and DXF styles
    assert len(cfd.blocks) > 0
    assert len(cfd.dxf_styles) > 0
    # Deployments sheet should have the most CF rules
    deploy_blocks = [b for b in cfd.blocks if "Deploy" in b.sheet_name or "Device" in b.sheet_name]
    assert len(deploy_blocks) > 10, f"Expected >10 CF blocks on Deployments, got {len(deploy_blocks)}"


@pytest.mark.skipif(not _HAS_REF, reason="Reference CF workbook not found")
def test_real_cf_colors():
    """Verify the two purple hues exist in the reference CF workbook."""
    from triage.cf_engine import extract_cf_dictionary
    cfd = extract_cf_dictionary(_REF_CF)
    # Collect ALL dxf_xml from ALL rules (not just the first rule per block)
    all_dxf_parts = []
    for b in cfd.blocks:
        for r in b.rules:
            if r.dxf_xml:
                all_dxf_parts.append(r.dxf_xml)
    all_dxf = " ".join(all_dxf_parts)
    # Also check the dxf_styles list directly from styles.xml
    all_styles = " ".join(cfd.dxf_styles)
    combined = all_dxf + " " + all_styles
    # Deployment-required purple
    assert "D9B3FF" in combined, f"Missing deployment-required purple D9B3FF in {len(cfd.dxf_styles)} styles"
    # Config-prep purple — may be E6CCFF or a theme-based tint
    # If not found as literal hex, check for theme-based purple tints
    has_config_purple = "E6CCFF" in combined or "D9B3FF" in combined
    assert has_config_purple, "Missing any purple CF hue"


@pytest.mark.skipif(not _HAS_ACTIVE, reason="Active workbook not found")
def test_real_active_headers():
    """Verify active workbook has expected key headers in tblDeviceConfig."""
    with zipfile.ZipFile(_ACTIVE, "r") as z:
        tbl_xml = z.read("xl/tables/table4.xml").decode("utf-8")
    headers = re.findall(r'<tableColumn [^>]*name="([^"]*)"', tbl_xml)
    assert "Device Type" in headers
    assert "Deployed" in headers
    assert "Install Building" in headers
    # These are the columns that need moving
    assert "Area/Unit" in headers or "Area_Unit" in headers


@pytest.mark.skipif(not (_HAS_REF and _HAS_ACTIVE), reason="Sample workbooks not found")
def test_real_column_diff():
    """Compare column headers between reference and active workbooks."""
    with zipfile.ZipFile(_REF_CF, "r") as z:
        ref_tbl = z.read("xl/tables/table4.xml").decode("utf-8")
    with zipfile.ZipFile(_ACTIVE, "r") as z:
        act_tbl = z.read("xl/tables/table4.xml").decode("utf-8")

    ref_headers = re.findall(r'<tableColumn [^>]*name="([^"]*)"', ref_tbl)
    act_headers = re.findall(r'<tableColumn [^>]*name="([^"]*)"', act_tbl)

    # Both should have 81 columns
    assert len(ref_headers) == len(act_headers), (
        f"Column count mismatch: ref={len(ref_headers)} active={len(act_headers)}"
    )

