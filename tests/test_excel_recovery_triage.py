from __future__ import annotations

import json
import zipfile

from triage.excel_recovery_triage import (
    build_report,
    main,
    parse_recovery_log_text,
    render_markdown,
)

RECOVERY_LOG = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<recoveryLog xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <logFileName>error588520_01.xml</logFileName>
  <summary>Errors were detected in file 'roster_review_blank.xlsx'</summary>
  <removedParts>
    <removedPart>Removed Part: /xl/styles.xml part with XML error. (Styles) Load error. Line 1, column 0.</removedPart>
  </removedParts>
  <removedRecords>
    <removedRecord>Removed Records: Cell information from /xl/worksheets/sheet1.xml part</removedRecord>
    <removedRecord>Removed Records: Cell information from /xl/worksheets/sheet2.xml part</removedRecord>
  </removedRecords>
  <repairedRecords>
    <repairedRecord>Repaired Records: Conditional formatting from /xl/worksheets/sheet2.xml part</repairedRecord>
  </repairedRecords>
</recoveryLog>'''


def _write_xlsx(path, parts):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in parts.items():
            zf.writestr(name, content)


def _valid_parts():
    return {
        "[Content_Types].xml": '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        "xl/styles.xml": '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dxfs count="1"><dxf/></dxfs></styleSheet>',
        "xl/worksheets/sheet1.xml": '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>',
        "xl/worksheets/sheet2.xml": '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/><conditionalFormatting sqref="A1"><cfRule type="expression" dxfId="0" priority="1"><formula>1=1</formula></cfRule></conditionalFormatting></worksheet>',
    }


def test_parses_recovery_log_and_normalizes_parts():
    parsed = parse_recovery_log_text(RECOVERY_LOG)

    assert parsed["parsed"] is True
    assert parsed["log_file_name"] == "error588520_01.xml"
    assert [entry["action"] for entry in parsed["entries"]] == [
        "removed_part",
        "removed_record",
        "removed_record",
        "repaired_record",
    ]
    assert parsed["entries"][0]["part"] == "xl/styles.xml"
    assert parsed["entries"][-1]["part"] == "xl/worksheets/sheet2.xml"


def test_exact_failure_class_is_stop_ship_and_correlated(tmp_path):
    workbook = tmp_path / "broken.xlsx"
    parts = _valid_parts()
    parts["xl/styles.xml"] = b""
    _write_xlsx(workbook, parts)
    log = tmp_path / "error.xml"
    log.write_text(RECOVERY_LOG, encoding="utf-8")

    report = build_report(workbook, [log])

    assert report["verdict"] == "STOP_SHIP"
    assert "excel_recovery_actions_observed" in report["stop_ship_reasons"]
    assert "xml_part_parse_failure" in report["stop_ship_reasons"]
    assert {item["part"] for item in report["workbook"]["xml_parse_failures"]} == {"xl/styles.xml"}
    assert {item["code"] for item in report["root_cause_candidates"]} >= {
        "STYLES_XML_UNREADABLE",
        "STYLE_TABLE_FAILURE_CASCADES_TO_CELLS",
        "CONDITIONAL_FORMATTING_REPAIRED",
    }


def test_out_of_range_conditional_format_reference_is_stop_ship(tmp_path):
    workbook = tmp_path / "bad_dxf.xlsx"
    parts = _valid_parts()
    parts["xl/worksheets/sheet2.xml"] = parts["xl/worksheets/sheet2.xml"].replace('dxfId="0"', 'dxfId="5"')
    _write_xlsx(workbook, parts)

    report = build_report(workbook)

    assert report["verdict"] == "STOP_SHIP"
    assert "conditional_formatting_dxf_reference_invalid" in report["stop_ship_reasons"]
    assert report["workbook"]["styles_and_cf"]["out_of_range_dxf_references"][0]["dxf_id"] == 5


def test_valid_static_package_passes_without_claiming_desktop_proof(tmp_path):
    workbook = tmp_path / "ok.xlsx"
    _write_xlsx(workbook, _valid_parts())

    report = build_report(workbook)

    assert report["verdict"] == "STATIC_PACKAGE_PASS"
    assert report["achieved_proof"] == "static_package_inspection"
    assert "no Desktop Excel" in report["proof_ceiling"]
    assert report["workbook"]["xml_parse_failures"] == []


def test_cli_writes_json_and_markdown(tmp_path):
    workbook = tmp_path / "broken.xlsx"
    parts = _valid_parts()
    parts["xl/styles.xml"] = b""
    _write_xlsx(workbook, parts)
    log = tmp_path / "error.xml"
    log.write_text(RECOVERY_LOG, encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    rc = main([
        str(workbook),
        "--recovery-log",
        str(log),
        "--json-out",
        str(json_out),
        "--markdown-out",
        str(markdown_out),
    ])

    assert rc == 1
    assert json.loads(json_out.read_text(encoding="utf-8"))["verdict"] == "STOP_SHIP"
    rendered = markdown_out.read_text(encoding="utf-8")
    assert "STYLES_XML_UNREADABLE" in rendered
    assert "xl/styles.xml" in rendered
    assert render_markdown(build_report(workbook, [log])).startswith("# Excel Recovery Triage")
