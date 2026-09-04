from tests._prompt_kit_fixture import build_prompt_kit, rewrite_part
from triage.worksheet_cell_integrity import inspect_worksheet_cell_integrity


def test_detects_duplicate_coordinate_and_stale_dimension(tmp_path):
    path = build_prompt_kit(tmp_path / "bad.xlsx", 21, require_backlinks=False)
    part = "xl/worksheets/sheet3.xml"
    def break_sheet(text):
        text = text.replace('<dimension ref="A1:A2"/>', '<dimension ref="A1:A1"/>')
        return text.replace('</sheetData>', '<row r="3"><c r="A2" s="0" t="s"><v>0</v></c></row></sheetData>')
    rewrite_part(path, part, break_sheet)
    codes = {issue.code for issue in inspect_worksheet_cell_integrity(path)}
    assert "duplicate_cell_coordinate" in codes
    assert "dimension_excludes_explicit_cells" in codes


def test_clean_fixture_passes(tmp_path):
    path = build_prompt_kit(tmp_path / "good.xlsx", 22, require_backlinks=True)
    assert inspect_worksheet_cell_integrity(path) == []
