"""
tests/test_dv_engine.py
-----------------------
Unit tests for triage.dv_engine.

Test matrix
-----------
  T1  DVRule.to_xml — header_row protection rule renders correct attributes
  T2  DVRule.to_xml — list rule renders formula1 child element
  T3  DVSpec.to_json / from_json — lossless round-trip
  T4  extract_dv_spec — finds all DV rules in a synthetic workbook
  T5  apply_dv_spec   — inserts a <dataValidations> block when none present
  T6  apply_dv_spec   — replaces an existing <dataValidations> block
  T7  _categorise     — all three protection title strings → correct category
  T8  make_header_protection / make_formula_protection / make_automated_protection
  T9  make_list_validation
  T10 DVSpec.rules_for_sheet — filters by part path
"""
from __future__ import annotations
import io
import json
import zipfile

import pytest

from triage.dv_engine import (
    DVRule, DVSpec,
    HEADER_ROW_TITLE, FORMULA_CELL_TITLE, AUTOMATED_TITLE, AUTOMATED_ERROR,
    extract_dv_spec, apply_dv_spec,
    make_header_protection, make_formula_protection,
    make_automated_protection, make_list_validation,
    _categorise,
)


# ─────────────────────────── helpers ────────────────────────────────────────

_WORKBOOK_XML = b"""<?xml version="1.0"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

_WORKBOOK_RELS = b"""<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet1.xml"/>
</Relationships>"""

_CONTENT_TYPES = b"""<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

_SHEET_NO_DV = b"""<?xml version="1.0"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
</worksheet>"""

_SHEET_WITH_DV = b"""<?xml version="1.0"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:xr="http://schemas.microsoft.com/office/spreadsheetml/2014/revision">
  <sheetData/>
  <dataValidations count="1">
    <dataValidation type="list" allowBlank="1" showErrorMessage="1"
                    sqref="B2:B100" xr:uid="{AAA-001}">
      <formula1>"Yes,No"</formula1>
    </dataValidation>
  </dataValidations>
</worksheet>"""


def _make_xlsx(sheet_xml: bytes = _SHEET_NO_DV) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("xl/workbook.xml", _WORKBOOK_XML)
        z.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buf.getvalue()


def _read_sheet(patched: bytes, part: str = "xl/worksheets/sheet1.xml") -> str:
    with zipfile.ZipFile(io.BytesIO(patched), "r") as z:
        return z.read(part).decode("utf-8")


# ─── shared fixture ──────────────────────────────────────────────────────────
_PART = "xl/worksheets/sheet1.xml"

# ─────────────────────────── T1 DVRule.to_xml header ───────────────────────
def test_t1_header_rule_xml():
    rule = make_header_protection(_PART, "1:1", "Sheet1")
    xml = rule.to_xml()
    assert 'type="custom"' in xml
    assert "FALSE" in xml
    assert "header" in xml.lower() or HEADER_ROW_TITLE in xml
    assert 'sqref="1:1"' in xml
    assert "xr:uid=" in xml


# ─────────────────────────── T2 DVRule.to_xml list ─────────────────────────
def test_t2_list_rule_xml():
    rule = make_list_validation(_PART, "B2:B100", ["Yes", "No"], "Sheet1")
    xml = rule.to_xml()
    assert 'type="list"' in xml
    assert "<formula1>" in xml
    assert "Yes,No" in xml


# ─────────────────────────── T3 JSON round-trip ────────────────────────────
def test_t3_json_roundtrip():
    spec = DVSpec(source_file="test.xlsx", rules=[
        make_header_protection(_PART, "1:1", "Sheet1"),
        make_list_validation(_PART, "B2", ["Yes", "No"], "Sheet1"),
    ])
    blob = spec.to_json()
    reloaded = DVSpec.from_json(blob)
    assert len(reloaded.rules) == 2
    assert reloaded.source_file == "test.xlsx"
    assert reloaded.rules[0].category == "header_row"
    assert reloaded.rules[1].category == "list"
    # Idempotent second round-trip
    assert json.loads(reloaded.to_json()) == json.loads(blob)


# ─────────────────────────── T4 extract_dv_spec ────────────────────────────
def test_t4_extract_dv_spec(tmp_path):
    p = tmp_path / "test.xlsx"
    p.write_bytes(_make_xlsx(_SHEET_WITH_DV))
    spec = extract_dv_spec(str(p))
    assert len(spec.rules) == 1
    r = spec.rules[0]
    assert r.dv_type == "list"
    assert r.sqref == "B2:B100"
    assert r.category == "list"


# ─────────────────────────── T5 apply — no existing DV ─────────────────────
def test_t5_apply_inserts_dv_block(tmp_path):
    spec = DVSpec(source_file="", rules=[
        make_header_protection(_PART, "1:1", "Sheet1"),
    ])
    patched = apply_dv_spec(_make_xlsx(_SHEET_NO_DV), spec)
    sheet = _read_sheet(patched)
    assert "<dataValidations" in sheet
    assert "<dataValidation" in sheet
    assert "FALSE" in sheet


# ─────────────────────────── T6 apply — replaces existing DV ───────────────
def test_t6_apply_replaces_existing_dv(tmp_path):
    spec = DVSpec(source_file="", rules=[
        make_header_protection(_PART, "1:1", "Sheet1"),
    ])
    patched = apply_dv_spec(_make_xlsx(_SHEET_WITH_DV), spec)
    sheet = _read_sheet(patched)
    # Old list rule should be gone; header protection should be in
    assert "Yes,No" not in sheet
    assert "header" in sheet.lower() or HEADER_ROW_TITLE in sheet


# ─────────────────────────── T7 _categorise ────────────────────────────────
@pytest.mark.parametrize("title,dv_type,formula1,expected", [
    (HEADER_ROW_TITLE,   "custom", "FALSE",    "header_row"),
    (FORMULA_CELL_TITLE, "custom", "FALSE",    "formula_cell"),
    (AUTOMATED_TITLE,    "custom", "FALSE",    "automated"),
    ("",                 "custom", "FALSE",    "protected"),
    ("",                 "list",   '"Yes,No"', "list"),
])
def test_t7_categorise(title, dv_type, formula1, expected):
    rule = DVRule(dv_type=dv_type, formula1=formula1, error_title=title)
    assert _categorise(rule) == expected


# ─────────────────────────── T8 builder functions ──────────────────────────
def test_t8_builders():
    h = make_header_protection(_PART, "1:1", "Sheet1")
    assert h.category == "header_row"
    assert h.dv_type == "custom"
    assert h.formula1 == "FALSE"
    assert h.show_error is True
    assert h.sheet_part == _PART

    f = make_formula_protection(_PART, "A1", "Sheet1")
    assert f.category == "formula_cell"
    assert f.formula1 == "FALSE"

    a = make_automated_protection(_PART, "C1", "Sheet1")
    assert a.category == "automated"
    assert AUTOMATED_ERROR in a.error_msg or "overwrite" in a.error_msg


# ─────────────────────────── T9 make_list_validation ───────────────────────
def test_t9_list_validation():
    r = make_list_validation(_PART, "D2:D50", ["A", "B", "C"], "Sheet1")
    assert r.category == "list"
    assert r.dv_type == "list"
    assert r.formula1 == '"A,B,C"'
    assert r.sqref == "D2:D50"
    assert r.sheet_part == _PART


# ─────────────────────────── T10 rules_for_sheet ───────────────────────────
def test_t10_rules_for_sheet():
    _P1 = "xl/worksheets/sheet1.xml"
    _P2 = "xl/worksheets/sheet2.xml"
    spec = DVSpec(rules=[
        make_header_protection(_P1, "1:1", "S1"),
        make_header_protection(_P2, "1:1", "S2"),
        make_list_validation(_P1, "B2", ["X"], "S1"),
    ])
    s1 = spec.rules_for_sheet(_P1)
    s2 = spec.rules_for_sheet(_P2)
    assert len(s1) == 2
    assert len(s2) == 1
    assert all(r.sheet_part == _P2 for r in s2)

