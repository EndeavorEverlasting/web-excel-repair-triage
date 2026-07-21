import tempfile
from pathlib import Path
import zipfile

from tests._prompt_kit_fixture import build_prompt_kit
from triage.workbook_package_hygiene import validate_workbook_package


def test_missing_file_is_a_failure():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "missing.xlsx"
        report = validate_workbook_package(path)
        assert not report.package_valid
        assert report.failures[0].name == "file exists"


def test_malformed_table_count_is_reported_without_crash(tmp_path):
    path = build_prompt_kit(tmp_path / "bad_table.xlsx", 21, require_backlinks=False)
    with zipfile.ZipFile(path) as source:
        parts = {info.filename: source.read(info.filename) for info in source.infolist()}
    parts["xl/tables/table1.xml"] = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" id="1" name="T" displayName="T" ref="A1:A2">'
        b'<autoFilter ref="A1:A2"/><tableColumns count="not-a-number"><tableColumn id="1" name="A"/></tableColumns></table>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for name, content in parts.items():
            target.writestr(name, content)
    report = validate_workbook_package(path)
    table_check = next(check for check in report.checks if check.name == "native table metadata")
    assert table_check.status == "FAIL"
    assert any(item["issue"] == "invalid_declared_column_count" for item in table_check.findings)


def test_clean_prompt_fixture_passes_package_hygiene(tmp_path):
    path = build_prompt_kit(tmp_path / "good.xlsx", 22, require_backlinks=True)
    report = validate_workbook_package(path, [f"P{i:02d}_COPY_SAFE" for i in range(22)])
    assert report.package_valid, report.to_dict()
