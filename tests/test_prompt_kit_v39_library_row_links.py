from __future__ import annotations

from xml.etree import ElementTree as ET

from triage import prompt_kit_v39_ooxml_base as ooxml


def _cell(ref: str, value: str, *, formula: str | None = None) -> ET.Element:
    cell = ET.Element(f"{{{ooxml.MAIN_NS}}}c", {"r": ref, "t": "str"})
    if formula is not None:
        ET.SubElement(cell, f"{{{ooxml.MAIN_NS}}}f").text = formula
    ET.SubElement(cell, f"{{{ooxml.MAIN_NS}}}v").text = value
    return cell


def test_prompt_library_whole_row_links_preserve_values_and_exact_ranges() -> None:
    root = ET.Element(f"{{{ooxml.MAIN_NS}}}worksheet")
    data = ET.SubElement(root, f"{{{ooxml.MAIN_NS}}}sheetData")
    for row_number, prompt_id, prompt_range in ((2, "P00", "A1:A9"), (3, "P57", "A1:A42")):
        row = ET.SubElement(data, f"{{{ooxml.MAIN_NS}}}row", {"r": str(row_number)})
        for number in range(1, 17):
            column = ooxml._impl._column_name(number)
            value = f'{column} value "{prompt_id}"'
            formula = None
            if column == "C":
                value = prompt_id
                formula = f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!{prompt_range}","{prompt_id}")'
            row.append(_cell(f"{column}{row_number}", value, formula=formula))
    ET.SubElement(root, f"{{{ooxml.MAIN_NS}}}hyperlinks")

    report = ooxml._apply_prompt_library_row_links(root)
    assert report["prompt_count"] == 2
    assert report["linked_cell_count"] == 28
    assert ooxml._validate_prompt_library_row_links(root) == ()

    cells = ooxml._cells(root)
    links = {
        item.attrib["ref"]: (item.attrib["location"], item.attrib["display"])
        for item in root.findall("m:hyperlinks/m:hyperlink", ooxml.NS)
    }
    for row_number, prompt_id, prompt_range in ((2, "P00", "A1:A9"), (3, "P57", "A1:A42")):
        for number in range(2, 16):
            column = ooxml._impl._column_name(number)
            ref = f"{column}{row_number}"
            display = ooxml._cell_display(cells[ref], ())
            assert ooxml._formula(cells[ref]) == ooxml._prompt_library_row_formula(
                f"{prompt_id}_COPY_SAFE", prompt_range, display
            )
            assert links[ref] == (f"'{prompt_id}_COPY_SAFE'!{prompt_range}", display)
        assert ooxml._formula(cells[f"A{row_number}"]) == ""
        assert ooxml._formula(cells[f"P{row_number}"]) == ""
