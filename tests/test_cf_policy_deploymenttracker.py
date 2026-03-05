from __future__ import annotations

import io
import zipfile

from triage.cf_policy_deploymenttracker import check_cf_policy_deploymenttracker


_CONTENT_TYPES = b"""<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/tables/table1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml"/>
</Types>"""


def _make_tracker_xlsx(include_cf: bool) -> bytes:
    wb = b"""<?xml version="1.0"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="12 - Device_Configuration" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    wb_rels = b"""<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

    sheet_rels = b"""<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table" Target="../tables/table1.xml"/>
</Relationships>"""

    styles = b"""<?xml version="1.0"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dxfs count="1">
    <dxf><fill><patternFill><bgColor rgb="FFFFC7CE"/></patternFill></fill></dxf>
  </dxfs>
</styleSheet>"""

    table = b"""<?xml version="1.0"?>
<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
       id="1" name="tblDeviceConfig" displayName="tblDeviceConfig" ref="A1:B10">
  <autoFilter ref="A1:B10"/>
  <tableColumns count="2">
    <tableColumn id="1" name="Deployed"/>
    <tableColumn id="2" name="PI Validated Date"/>
  </tableColumns>
</table>"""

    cf_block = b"""
  <conditionalFormatting sqref="B2:B10">
    <cfRule type="expression" dxfId="0" priority="1">
      <formula>AND(OR($A2=TRUE,UPPER($A2)="YES",$A2=1),$B2="")</formula>
    </cfRule>
  </conditionalFormatting>
"""

    sheet = (
        b"<?xml version=\"1.0\"?>\n"
        b"<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"\n"
        b"           xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">\n"
        b"  <sheetData/>\n"
        + (cf_block if include_cf else b"")
        + b"  <tableParts count=\"1\"><tablePart r:id=\"rId1\"/></tableParts>\n"
        + b"</worksheet>"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        z.writestr("xl/worksheets/_rels/sheet1.xml.rels", sheet_rels)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/tables/table1.xml", table)
    return buf.getvalue()


def test_cf_policy_deploymenttracker_passes_when_rule_present():
    data = _make_tracker_xlsx(include_cf=True)
    with zipfile.ZipFile(io.BytesIO(data), "r") as z:
        findings = check_cf_policy_deploymenttracker(z)
    assert findings == []


def test_cf_policy_deploymenttracker_reports_missing_rule():
    data = _make_tracker_xlsx(include_cf=False)
    with zipfile.ZipFile(io.BytesIO(data), "r") as z:
        findings = check_cf_policy_deploymenttracker(z)
    assert len(findings) == 1
    assert findings[0]["issue"] == "missing_rule"
    assert findings[0]["rule_id"].startswith("DT_CF_001")
