from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest

from triage import prompt_kit_v39_ooxml_base as ooxml


def _text_cell(ref: str, value: str = "") -> ET.Element:
    cell = ET.Element(f"{{{ooxml.MAIN_NS}}}c", {"r": ref, "t": "str", "s": "1"})
    ET.SubElement(cell, f"{{{ooxml.MAIN_NS}}}v").text = value
    return cell


def _formula_cell(ref: str, formula: str, cached: str) -> ET.Element:
    cell = _text_cell(ref, cached)
    ET.SubElement(cell, f"{{{ooxml.MAIN_NS}}}f").text = formula
    value = cell.find("m:v", ooxml.NS)
    cell.remove(value)
    cell.append(value)
    return cell


def _library(prompt_count: int) -> ET.Element:
    root = ET.Element(f"{{{ooxml.MAIN_NS}}}worksheet")
    ET.SubElement(root, f"{{{ooxml.MAIN_NS}}}dimension", {"ref": f"A1:P{prompt_count + 2}"})
    data = ET.SubElement(root, f"{{{ooxml.MAIN_NS}}}sheetData")
    header = ET.SubElement(data, f"{{{ooxml.MAIN_NS}}}row", {"r": "1"})
    for column in "ABCDEFGHIJKLMNOP":
        header.append(_text_cell(f"{column}1", "header"))
    for offset in range(prompt_count):
        row_number = offset + 2
        prompt_id = f"P{offset:02d}"
        row = ET.SubElement(data, f"{{{ooxml.MAIN_NS}}}row", {"r": str(row_number)})
        for column in "ABCDEFGHIJKLMNOP":
            if column == "C":
                row.append(
                    _formula_cell(
                        f"C{row_number}",
                        f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A2","{prompt_id}")',
                        prompt_id,
                    )
                )
            else:
                row.append(_text_cell(f"{column}{row_number}"))
    footer_row = prompt_count + 2
    footer = ET.SubElement(data, f"{{{ooxml.MAIN_NS}}}row", {"r": str(footer_row)})
    for column in "ABCDEFGHIJKLMNOP":
        footer.append(_text_cell(f"{column}{footer_row}", "footer" if column == "B" else ""))
    return root


def _formulas(root: ET.Element) -> dict[str, str]:
    return {
        cell.attrib["r"]: ooxml._formula(cell)
        for cell in root.findall(".//m:c", ooxml.NS)
        if ooxml._formula(cell)
    }


def test_navigation_cadence_selects_fewest_evenly_divisible_links() -> None:
    assert ooxml._navigation_cadence(50) == 10
    assert ooxml._navigation_cadence(45) == 5
    assert ooxml._navigation_cadence(56) == 2
    with pytest.raises(ValueError, match="divisible"):
        ooxml._navigation_cadence(7)


def test_v39_prompt_library_has_sparse_bidirectional_edge_links() -> None:
    root = _library(56)

    report = ooxml._apply_prompt_library_navigation(root)

    assert report == {
        "prompt_count": 56,
        "cadence": 2,
        "linked_rows": list(range(2, 58, 2)),
        "footer_row": 58,
    }
    formulas = _formulas(root)
    assert formulas["A1"] == 'HYPERLINK("#\'Prompt_Library\'!A58","↓ Bottom")'
    assert formulas["P1"] == 'HYPERLINK("#\'Prompt_Library\'!P58","↓ Bottom")'
    assert formulas["A58"] == 'HYPERLINK("#\'Prompt_Library\'!A1","↑ Top")'
    assert formulas["P58"] == 'HYPERLINK("#\'Prompt_Library\'!P1","↑ Top")'

    for row_number in range(2, 29, 2):
        assert formulas[f"A{row_number}"] == 'HYPERLINK("#\'Prompt_Library\'!A58","↓ Bottom")'
        assert formulas[f"P{row_number}"] == 'HYPERLINK("#\'Prompt_Library\'!P58","↓ Bottom")'
    for row_number in range(30, 58, 2):
        assert formulas[f"A{row_number}"] == 'HYPERLINK("#\'Prompt_Library\'!A1","↑ Top")'
        assert formulas[f"P{row_number}"] == 'HYPERLINK("#\'Prompt_Library\'!P1","↑ Top")'
    for row_number in range(3, 58, 2):
        assert f"A{row_number}" not in formulas
        assert f"P{row_number}" not in formulas

    hyperlinks = {
        item.attrib["ref"]: (item.attrib["location"], item.attrib["display"])
        for item in root.findall("m:hyperlinks/m:hyperlink", ooxml.NS)
    }
    assert hyperlinks["A2"] == ("'Prompt_Library'!A58", "↓ Bottom")
    assert hyperlinks["P56"] == ("'Prompt_Library'!P1", "↑ Top")
    footer = next(row for row in root.findall("m:sheetData/m:row", ooxml.NS) if row.attrib["r"] == "58")
    footer_b = next(cell for cell in footer.findall("m:c", ooxml.NS) if cell.attrib["r"] == "B58")
    assert ooxml._cell_display(footer_b, ()) == "End of Prompt Library · 56 prompts"
