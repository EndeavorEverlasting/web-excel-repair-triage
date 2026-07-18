from __future__ import annotations

from triage import prompt_kit_v39_ooxml_base as ooxml
from triage.prompt_kit_v39_generator import ARTIFACT_NAME, generate_v39
from tests.test_prompt_kit_v39_generator import GNHF_SPEC, STANDARD_SPEC, _build_v38


def test_generated_v39_enforces_sparse_bidirectional_library_navigation(tmp_path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    output = tmp_path / "out"
    _build_v38(source)

    generate_v39(
        source,
        output,
        standard_ai_spec=STANDARD_SPEC,
        gnhf_spec=GNHF_SPEC,
    )

    package = ooxml._read_workbook(output / f"{ARTIFACT_NAME}.xlsx")
    _order, mapping, _sheet_ids, _relationship_ids = ooxml._sheet_map(package.parts)
    library_part = mapping["Prompt_Library"]
    root = ooxml._root(package.parts[library_part], library_part)
    prompt_rows = ooxml._prompt_library_prompt_rows(root)
    cells = ooxml._cells(root)
    footer_row = max(
        int(row.attrib["r"])
        for row in root.findall("m:sheetData/m:row", ooxml.NS)
        if int(row.attrib["r"]) > prompt_rows[-1]
    )

    assert len(prompt_rows) == 56
    assert ooxml._navigation_cadence(len(prompt_rows)) == 2
    assert footer_row == 58

    linked_rows = prompt_rows[::2]
    midpoint = len(prompt_rows) / 2
    for position, row_number in enumerate(prompt_rows):
        for column in ("A", "P"):
            formula = ooxml._formula(cells.get(f"{column}{row_number}"))
            if row_number not in linked_rows:
                assert formula == ""
                continue
            expected_target = footer_row if position < midpoint else 1
            expected_label = "↓ Bottom" if expected_target == footer_row else "↑ Top"
            assert formula == (
                f'HYPERLINK("#\'Prompt_Library\'!{column}{expected_target}",'
                f'"{expected_label}")'
            )

    for column in ("A", "P"):
        assert ooxml._formula(cells[f"{column}1"]) == (
            f'HYPERLINK("#\'Prompt_Library\'!{column}{footer_row}","↓ Bottom")'
        )
        assert ooxml._formula(cells[f"{column}{footer_row}"]) == (
            f'HYPERLINK("#\'Prompt_Library\'!{column}1","↑ Top")'
        )

    hyperlinks = {
        item.attrib["ref"]: (item.attrib["location"], item.attrib["display"])
        for item in root.findall("m:hyperlinks/m:hyperlink", ooxml.NS)
    }
    expected_navigation_refs = {
        *[f"{column}{row}" for column in ("A", "P") for row in linked_rows],
        "A1",
        "P1",
        f"A{footer_row}",
        f"P{footer_row}",
    }
    assert expected_navigation_refs <= hyperlinks.keys()
    assert hyperlinks["A2"] == ("'Prompt_Library'!A58", "↓ Bottom")
    assert hyperlinks["P56"] == ("'Prompt_Library'!P1", "↑ Top")

    shared = ooxml._shared_strings(package.parts)
    assert ooxml._cell_display(cells[f"B{footer_row}"], shared) == (
        "End of Prompt Library · 56 prompts"
    )
