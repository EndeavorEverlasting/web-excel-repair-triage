import zipfile

from tests._prompt_kit_fixture import build_prompt_kit
from triage.web_excel_compatibility_rules import inspect_web_excel_package


def _write_parts(path, parts):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in parts.items():
            zf.writestr(name, content)


def _read_parts(path):
    with zipfile.ZipFile(path) as zf:
        return {info.filename: zf.read(info.filename) for info in zf.infolist()}


def test_clean_fixture_has_no_static_compatibility_issues(tmp_path):
    path = build_prompt_kit(tmp_path / "good.xlsx", 22, require_backlinks=True)
    assert inspect_web_excel_package(path) == []


def test_rejects_missing_and_absolute_relationship_targets(tmp_path):
    path = build_prompt_kit(tmp_path / "bad_relationships.xlsx", 21, require_backlinks=False)
    parts = _read_parts(path)
    parts["xl/_rels/workbook.xml.rels"] = parts["xl/_rels/workbook.xml.rels"].replace(
        b"</Relationships>",
        b'<Relationship Id="rId999" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="/xl/theme/missing.xml"/></Relationships>',
    )
    _write_parts(path, parts)
    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "absolute_internal_relationship_target" in codes
    assert "missing_relationship_target" in codes


def test_rejects_relationship_target_escape(tmp_path):
    path = build_prompt_kit(tmp_path / "escape.xlsx", 21, require_backlinks=False)
    parts = _read_parts(path)
    parts["_rels/.rels"] = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="../xl/workbook.xml"/>'
        b"</Relationships>"
    )
    _write_parts(path, parts)
    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "relationship_target_escapes_package" in codes


def test_synchronized_calc_chain_is_allowed_and_stale_entry_fails(tmp_path):
    path = build_prompt_kit(tmp_path / "calc.xlsx", 21, require_backlinks=False)
    parts = _read_parts(path)
    sheet_part = "xl/worksheets/sheet3.xml"
    parts[sheet_part] = parts[sheet_part].replace(
        b'<c r="A1" s="0" t="s"><v>',
        b'<c r="A1" s="0"><f>1+1</f><v>',
    )
    parts["xl/calcChain.xml"] = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><c r="A1" i="3"/></calcChain>'
    )
    _write_parts(path, parts)
    assert "stale_calc_chain_entry" not in {
        issue.code for issue in inspect_web_excel_package(path)
    }
    parts = _read_parts(path)
    parts["xl/calcChain.xml"] = parts["xl/calcChain.xml"].replace(
        b'r="A1"', b'r="A99"'
    )
    _write_parts(path, parts)
    assert "stale_calc_chain_entry" in {
        issue.code for issue in inspect_web_excel_package(path)
    }


def test_calc_chain_entries_inherit_omitted_sheet_id(tmp_path):
    path = build_prompt_kit(tmp_path / "calc_inherit.xlsx", 21, require_backlinks=False)
    parts = _read_parts(path)
    sheet_part = "xl/worksheets/sheet3.xml"
    parts[sheet_part] = parts[sheet_part].replace(
        b'<c r="A1" s="0" t="s"><v>',
        b'<c r="A1" s="0"><f>1+1</f><v>',
    )
    parts[sheet_part] = parts[sheet_part].replace(
        b'<c r="A2" s="0" t="s"><v>',
        b'<c r="A2" s="0"><f>2+2</f><v>',
    )
    parts["xl/calcChain.xml"] = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        b'<c r="A1" i="3"/><c r="A2"/></calcChain>'
    )
    _write_parts(path, parts)
    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "invalid_calc_chain_sheet_id" not in codes
    assert "stale_calc_chain_entry" not in codes


def test_rejects_undeclared_markup_compatibility_prefix_values(tmp_path):
    path = build_prompt_kit(tmp_path / "mc_prefix_corruption.xlsx", 21, require_backlinks=False)
    parts = _read_parts(path)
    workbook = parts["xl/workbook.xml"]
    workbook = workbook.replace(
        b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"',
        b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        b'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        b'xmlns:ns2="http://schemas.microsoft.com/office/spreadsheetml/2010/11/main" '
        b'mc:Ignorable="x15"',
    )
    workbook = workbook.replace(
        b"<sheets>",
        b'<mc:AlternateContent><mc:Choice Requires="x15"><ns2:absPath url="C:\\temp\\"/></mc:Choice></mc:AlternateContent><sheets>',
    )
    parts["xl/workbook.xml"] = workbook
    _write_parts(path, parts)

    issues = inspect_web_excel_package(path)
    assert "xml_parse_error" not in {issue.code for issue in issues}
    mc_issues = [
        issue
        for issue in issues
        if issue.code == "undeclared_markup_compatibility_prefix"
    ]
    assert mc_issues
    assert {issue.part for issue in mc_issues} == {"xl/workbook.xml"}
    assert any("'x15'" in issue.message for issue in mc_issues)


def test_accepts_declared_markup_compatibility_prefix_values(tmp_path):
    path = build_prompt_kit(tmp_path / "mc_prefix_valid.xlsx", 21, require_backlinks=False)
    parts = _read_parts(path)
    workbook = parts["xl/workbook.xml"]
    workbook = workbook.replace(
        b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"',
        b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        b'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        b'xmlns:ns0="http://schemas.microsoft.com/office/spreadsheetml/2010/11/main" '
        b'mc:Ignorable="ns0"',
    )
    workbook = workbook.replace(
        b"<sheets>",
        b'<mc:AlternateContent><mc:Choice Requires="ns0"><ns0:absPath url="C:\\temp\\"/></mc:Choice></mc:AlternateContent><sheets>',
    )
    parts["xl/workbook.xml"] = workbook
    _write_parts(path, parts)

    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "xml_parse_error" not in codes
    assert "undeclared_markup_compatibility_prefix" not in codes
    assert "ns0_namespace_pollution" not in codes
