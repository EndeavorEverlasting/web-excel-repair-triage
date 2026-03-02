"""
tests/test_cf_engine.py
-----------------------
Unit tests for triage.cf_engine.

Test matrix
-----------
  T1  CFDictionary.summary — counts blocks, rules, DXF styles correctly
  T2  CFDictionary.to_json / from_json — lossless round-trip
  T3  CFDictionary.add_rule — appends block and auto-assigns id
  T4  CFDictionary.blocks_for_sheet — filters by part path
  T5  extract_cf_dictionary — finds CF blocks in a synthetic workbook
  T6  _extract_dxf_list — extracts individual <dxf> elements from styles.xml
  T7  apply_cf_dictionary — injects CF blocks into a sheet with no existing CF
  T8  apply_cf_dictionary — replaces existing CF blocks in a sheet
  T9  apply_cf_dictionary — patches styles.xml DXF section
  T10 DXF reference integrity — dxf_id never exceeds len(dxf_styles)
"""
from __future__ import annotations
import io
import json
import zipfile

import pytest

from triage.cf_engine import (
    CFRule, CFBlock, CFDictionary,
    extract_cf_dictionary, apply_cf_dictionary,
    _extract_dxf_list,
)


# ─────────────────────────── helpers ────────────────────────────────────────

_STYLES_NO_DXF = b"""<?xml version="1.0"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font/></fonts>
  <dxfs count="0"/>
</styleSheet>"""

_STYLES_WITH_DXF = b"""<?xml version="1.0"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dxfs count="2">
    <dxf><fill><patternFill><bgColor rgb="FFFFC7CE"/></patternFill></fill></dxf>
    <dxf><fill><patternFill><bgColor rgb="FFC6EFCE"/></patternFill></fill></dxf>
  </dxfs>
</styleSheet>"""

_SHEET_NO_CF = b"""<?xml version="1.0"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
</worksheet>"""

_SHEET_WITH_CF = b"""<?xml version="1.0"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
  <conditionalFormatting sqref="A1:A10">
    <cfRule type="expression" dxfId="0" priority="1">
      <formula>A1&gt;0</formula>
    </cfRule>
  </conditionalFormatting>
</worksheet>"""

_WORKBOOK_XML = b"""<?xml version="1.0"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

_WORKBOOK_RELS = b"""<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
</Relationships>"""

_CONTENT_TYPES = b"""<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""


def _make_xlsx(sheet_xml: bytes = _SHEET_NO_CF,
               styles_xml: bytes = _STYLES_NO_DXF) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("xl/workbook.xml", _WORKBOOK_XML)
        z.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        z.writestr("xl/styles.xml", styles_xml)
    return buf.getvalue()


def _read_part(patched: bytes, part: str) -> str:
    with zipfile.ZipFile(io.BytesIO(patched), "r") as z:
        return z.read(part).decode("utf-8")


def _make_cfd_with_block(sqref: str = "B2:B10",
                          part: str = "xl/worksheets/sheet1.xml") -> CFDictionary:
    rule = CFRule(id="r01", rule_type="expression", dxf_id=0, priority=1,
                  formula="B2>0",
                  raw_xml='<cfRule type="expression" dxfId="0" priority="1"><formula>B2&gt;0</formula></cfRule>')
    block = CFBlock(id="b01", sheet_part=part, sheet_name="Sheet1",
                    sqref=sqref, rules=[rule],
                    raw_xml=f'<conditionalFormatting sqref="{sqref}">{rule.raw_xml}</conditionalFormatting>')
    dxf = "<dxf><fill><patternFill><bgColor rgb=\"FFFFC7CE\"/></patternFill></fill></dxf>"
    return CFDictionary(source_file="test.xlsx", dxf_styles=[dxf], blocks=[block])


# ─────────────────────────── T1 summary ────────────────────────────────────
def test_t1_summary():
    cfd = _make_cfd_with_block()
    s = cfd.summary
    assert s["total_blocks"] == 1
    assert s["total_rules"] == 1
    assert s["total_dxf_styles"] == 1
    assert "Sheet1" in s["per_sheet"]


# ─────────────────────────── T2 JSON round-trip ────────────────────────────
def test_t2_json_roundtrip():
    cfd = _make_cfd_with_block()
    blob = cfd.to_json()
    reloaded = CFDictionary.from_json(blob)
    assert reloaded.source_file == "test.xlsx"
    assert len(reloaded.blocks) == 1
    assert len(reloaded.dxf_styles) == 1
    assert reloaded.blocks[0].sqref == "B2:B10"
    assert reloaded.blocks[0].rules[0].formula == "B2>0"
    assert json.loads(reloaded.to_json()) == json.loads(blob)


# ─────────────────────────── T3 add_rule ───────────────────────────────────
def test_t3_add_rule():
    cfd = CFDictionary()
    block = CFBlock(sqref="C1:C10", sheet_part="xl/worksheets/sheet1.xml")
    cfd.add_rule(block)
    assert len(cfd.blocks) == 1
    assert cfd.blocks[0].id != ""   # auto-assigned


# ─────────────────────────── T4 blocks_for_sheet ───────────────────────────
def test_t4_blocks_for_sheet():
    cfd = CFDictionary(blocks=[
        CFBlock(id="a", sheet_part="xl/worksheets/sheet1.xml", sqref="A1"),
        CFBlock(id="b", sheet_part="xl/worksheets/sheet2.xml", sqref="A1"),
        CFBlock(id="c", sheet_part="xl/worksheets/sheet1.xml", sqref="B1"),
    ])
    assert len(cfd.blocks_for_sheet("xl/worksheets/sheet1.xml")) == 2
    assert len(cfd.blocks_for_sheet("xl/worksheets/sheet2.xml")) == 1
    assert len(cfd.blocks_for_sheet("xl/worksheets/sheet3.xml")) == 0


# ─────────────────────────── T5 extract_cf_dictionary ──────────────────────
def test_t5_extract_cf(tmp_path):
    p = tmp_path / "test.xlsx"
    p.write_bytes(_make_xlsx(_SHEET_WITH_CF, _STYLES_WITH_DXF))
    cfd = extract_cf_dictionary(str(p))
    assert len(cfd.blocks) == 1
    assert cfd.blocks[0].sqref == "A1:A10"
    assert len(cfd.blocks[0].rules) == 1
    assert cfd.blocks[0].rules[0].rule_type == "expression"
    assert len(cfd.dxf_styles) == 2


# ─────────────────────────── T6 _extract_dxf_list ──────────────────────────
def test_t6_extract_dxf_list():
    styles = _STYLES_WITH_DXF.decode("utf-8")
    dxfs = _extract_dxf_list(styles)
    assert len(dxfs) == 2
    assert "FFFFC7CE" in dxfs[0]
    assert "FFC6EFCE" in dxfs[1]


# ─────────────────────────── T7 apply — no CF present ──────────────────────
def test_t7_apply_inserts_cf_block():
    cfd = _make_cfd_with_block()
    patched = apply_cf_dictionary(_make_xlsx(_SHEET_NO_CF, _STYLES_NO_DXF), cfd)
    sheet = _read_part(patched, "xl/worksheets/sheet1.xml")
    assert "<conditionalFormatting" in sheet
    assert "<cfRule" in sheet


# ─────────────────────────── T8 apply — appends, preserves existing CF ────────
def test_t8_apply_appends_cf_block():
    """New CF blocks are APPENDED; existing CF in the sheet is preserved."""
    cfd = _make_cfd_with_block(sqref="B2:B10")
    patched = apply_cf_dictionary(_make_xlsx(_SHEET_WITH_CF, _STYLES_NO_DXF), cfd)
    sheet = _read_part(patched, "xl/worksheets/sheet1.xml")
    # New block is present
    assert "B2:B10" in sheet
    # Original block is NOT removed — non-destructive append
    assert "A1:A10" in sheet


# ─────────────────────────── T9 apply — patches styles DXF ─────────────────
def test_t9_apply_patches_styles_dxf():
    cfd = _make_cfd_with_block()
    patched = apply_cf_dictionary(_make_xlsx(_SHEET_NO_CF, _STYLES_NO_DXF), cfd)
    styles = _read_part(patched, "xl/styles.xml")
    assert "FFFFC7CE" in styles
    assert "<dxf>" in styles


# ─────────────────────────── T10 DXF reference integrity ───────────────────
def test_t10_dxf_reference_integrity():
    cfd = _make_cfd_with_block()
    n = len(cfd.dxf_styles)
    for block in cfd.blocks:
        for rule in block.rules:
            if rule.dxf_id is not None:
                assert rule.dxf_id < n, \
                    f"dxf_id {rule.dxf_id} out of range (have {n} DXF styles)"

