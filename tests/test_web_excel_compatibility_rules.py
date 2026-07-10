from __future__ import annotations

import zipfile

from triage.web_excel_compatibility_rules import inspect_web_excel_package


def _write_xlsx(path, parts):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in parts.items():
            zf.writestr(name, content)


def _minimal_parts(content_types_extra="", drawings_chart_part=False):
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + content_types_extra +
            '</Types>'
        ),
        "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
    }
    if drawings_chart_part:
        parts["xl/drawings/charts/chart1.xml"] = '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"/>'
        parts["xl/drawings/_rels/drawing1.xml.rels"] = (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="charts/chart1.xml"/>'
            '</Relationships>'
        )
    else:
        parts["xl/charts/chart1.xml"] = '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"/>'
        parts["xl/drawings/_rels/drawing1.xml.rels"] = (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart1.xml"/>'
            '</Relationships>'
        )
    return parts


def test_accepts_normal_chart_location_and_content_types(tmp_path):
    path = tmp_path / "ok.xlsx"
    _write_xlsx(path, _minimal_parts())

    assert inspect_web_excel_package(path) == []


def test_rejects_bad_xml_default_content_type(tmp_path):
    path = tmp_path / "bad_content_type.xlsx"
    parts = _minimal_parts()
    parts["[Content_Types].xml"] = parts["[Content_Types].xml"].replace(
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    )
    _write_xlsx(path, parts)

    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "bad_xml_default_content_type" in codes


def test_rejects_chart_parts_under_drawings(tmp_path):
    path = tmp_path / "bad_chart_location.xlsx"
    _write_xlsx(path, _minimal_parts(drawings_chart_part=True))

    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "chart_parts_under_drawings" in codes
    assert "drawing_rel_targets_chart_under_drawings" in codes


def test_rejects_missing_and_absolute_relationship_targets(tmp_path):
    path = tmp_path / "bad_relationships.xlsx"
    parts = _minimal_parts()
    parts["xl/drawings/_rels/drawing1.xml.rels"] = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/missing.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="/xl/charts/chart1.xml"/>'
        '</Relationships>'
    )
    _write_xlsx(path, parts)

    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "missing_relationship_target" in codes
    assert "absolute_internal_relationship_target" in codes


def test_rejects_calc_chain_external_links_inline_strings_and_ns0(tmp_path):
    path = tmp_path / "bad_misc.xlsx"
    parts = _minimal_parts()
    parts["xl/calcChain.xml"] = "<calcChain/>"
    parts["xl/externalLinks/externalLink1.xml"] = "<externalLink/>"
    parts["xl/worksheets/sheet1.xml"] = '<worksheet xmlns:ns0="bad"><c t="inlineStr"><is><t>x</t></is></c><v>#REF!</v></worksheet>'
    _write_xlsx(path, parts)

    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "calc_chain_present" in codes
    assert "external_links_present" in codes
    assert "inline_string_cells_present" in codes
    assert "ns0_namespace_pollution" in codes
    assert "formula_error_text_present" in codes
