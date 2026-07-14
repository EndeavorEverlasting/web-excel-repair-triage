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
        b'</Relationships>'
    )
    _write_parts(path, parts)
    codes = {issue.code for issue in inspect_web_excel_package(path)}
    assert "relationship_target_escapes_package" in codes


def test_synchronized_calc_chain_is_allowed_and_stale_entry_fails(tmp_path):
    path = build_prompt_kit(tmp_path / "calc.xlsx", 21, require_backlinks=False)
    parts = _read_parts(path)
    sheet_part = "xl/worksheets/sheet3.xml"
    parts[sheet_part] = parts[sheet_part].replace(b'<c r="A1" s="0" t="s"><v>', b'<c r="A1" s="0"><f>1+1</f><v>')
    parts["xl/calcChain.xml"] = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><c r="A1" i="3"/></calcChain>'
    )
    _write_parts(path, parts)
    assert "stale_calc_chain_entry" not in {issue.code for issue in inspect_web_excel_package(path)}
    parts = _read_parts(path)
    parts["xl/calcChain.xml"] = parts["xl/calcChain.xml"].replace(b'r="A1"', b'r="A99"')
    _write_parts(path, parts)
    assert "stale_calc_chain_entry" in {issue.code for issue in inspect_web_excel_package(path)}
