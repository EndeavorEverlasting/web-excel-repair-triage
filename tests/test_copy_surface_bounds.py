from tests._prompt_kit_fixture import build_prompt_kit, rewrite_part
from triage.copy_surface_bounds import validate_copy_surface


def test_dense_copy_surface_passes(tmp_path):
    path = build_prompt_kit(tmp_path / "good.xlsx", 21, require_backlinks=False)
    result = validate_copy_surface(path, "P07_COPY_SAFE")
    assert result.valid
    assert result.first_payload_row == 1
    assert result.last_payload_row == 2


def test_non_a_cell_and_dimension_drift_fail(tmp_path):
    path = build_prompt_kit(tmp_path / "bad.xlsx", 21, require_backlinks=False)
    part = "xl/worksheets/sheet10.xml"
    rewrite_part(path, part, lambda text: text.replace('</row></sheetData>', '<c r="B2" s="0" t="s"><v>0</v></c></row></sheetData>', 1))
    result = validate_copy_surface(path, "P07_COPY_SAFE")
    assert not result.valid
    assert "explicit_cells_outside_column_a" in result.issues
