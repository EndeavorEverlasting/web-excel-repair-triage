from __future__ import annotations

from triage import prompt_kit_v39_ooxml_base as ooxml
from triage.prompt_kit_v39_generator import ARTIFACT_NAME, EXPECTED_PROMPT_ORDER, generate_v39
from tests.test_prompt_kit_v39_generator import GNHF_SPEC, STANDARD_SPEC, _build_v38


def test_generated_v39_links_every_prompt_library_data_cell_to_exact_prompt_range(tmp_path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    output = tmp_path / "out"
    _build_v38(source)
    generate_v39(source, output, standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC)

    package = ooxml._read_workbook(output / f"{ARTIFACT_NAME}.xlsx")
    _order, mapping, _sheet_ids, _relationship_ids = ooxml._sheet_map(package.parts)
    library_part = mapping["Prompt_Library"]
    root = ooxml._root(package.parts[library_part], library_part)
    shared = ooxml._shared_strings(package.parts)
    assert ooxml._validate_prompt_library_row_links(root, shared) == ()

    rows, ranges = ooxml._prompt_rows_and_ranges(package.parts)
    cells = ooxml._cells(root)
    hyperlinks = {
        item.attrib["ref"]: (item.attrib["location"], item.attrib["display"])
        for item in root.findall("m:hyperlinks/m:hyperlink", ooxml.NS)
    }
    assert len(EXPECTED_PROMPT_ORDER) == 58
    for prompt_id in EXPECTED_PROMPT_ORDER:
        row = rows[prompt_id]
        prompt_range = ranges[prompt_id]
        sheet_name = f"{prompt_id}_COPY_SAFE"
        for number in range(2, 16):
            column = ooxml._impl._column_name(number)
            ref = f"{column}{row}"
            display = ooxml._cell_display(cells[ref], shared)
            assert ooxml._formula(cells[ref]) == ooxml._prompt_library_row_formula(
                sheet_name, prompt_range, display
            )
            assert hyperlinks[ref] == (f"'{sheet_name}'!{prompt_range}", display)
