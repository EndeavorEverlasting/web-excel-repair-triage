from __future__ import annotations

from xml.etree import ElementTree as ET

from triage import prompt_kit_v39_ooxml_base as ooxml


def _cell(ref: str, value: str) -> ET.Element:
    cell = ET.Element(f"{{{ooxml.MAIN_NS}}}c", {"r": ref, "t": "str"})
    ET.SubElement(cell, f"{{{ooxml.MAIN_NS}}}v").text = value
    return cell


def _prompt(prompt_id: str, color: str) -> dict:
    return {
        "seq": prompt_id.removeprefix("P"),
        "prompt_id": prompt_id,
        "prompt_type": "ANALYZE",
        "prompt_class": "STANDARD AI / TEST",
        "sprint_path_role": "test footer-aware insertion",
        "use_for_progress": "Support",
        "prompt_name": f"Prompt {prompt_id}",
        "use_this_when": "testing",
        "inspect_first": "fixture",
        "expected_output": "inserted row",
        "next_step": "validate",
        "proof_gate": "footer remains last",
        "color": color,
        "lines": ["PROMPT SURFACE: STANDARD AI.", "DIRECTORY GATE"],
    }


def test_v39_prompt_library_rows_insert_before_existing_footer() -> None:
    root = ET.Element(f"{{{ooxml.MAIN_NS}}}worksheet")
    ET.SubElement(root, f"{{{ooxml.MAIN_NS}}}dimension", {"ref": "A1:P47"})
    sheet_data = ET.SubElement(root, f"{{{ooxml.MAIN_NS}}}sheetData")

    template = ET.SubElement(
        sheet_data,
        f"{{{ooxml.MAIN_NS}}}row",
        {"r": "46", "spans": "1:16", "ht": "81.95", "customHeight": "1"},
    )
    for column in "ABCDEFGHIJKLMNOP":
        template.append(_cell(f"{column}46", "P44" if column == "C" else "Blue" if column == "N" else "template"))

    footer = ET.SubElement(
        sheet_data,
        f"{{{ooxml.MAIN_NS}}}row",
        {"r": "47", "spans": "1:16", "ht": "30", "customHeight": "1"},
    )
    footer.append(_cell("A47", "Top"))
    footer.append(_cell("B47", "End of Prompt Library"))
    footer.append(_cell("P47", "Top"))

    headers = {
        "Seq": 2,
        "Prompt ID": 3,
        "Prompt Type": 4,
        "Prompt Class": 5,
        "Sprint Path Role": 6,
        "Use For Progress?": 7,
        "Prompt Name": 8,
        "Use This When": 9,
        "Inspect First": 10,
        "Expected Output": 11,
        "Next Step": 12,
        "Proof / Acceptance Gate": 13,
        "Color": 14,
        "Copy-Safe Sheet": 15,
    }
    prompts = [_prompt("P50", "Ocean"), _prompt("P51", "Green")]

    rows, links = ooxml._append_library_rows(
        root,
        headers,
        {"P44": 46},
        47,
        prompts,
        "Blue",
    )

    assert rows == {"P50": 47, "P51": 48}
    assert [item.attrib["r"] for item in sheet_data.findall("m:row", ooxml.NS)] == ["46", "47", "48", "49"]
    shifted_footer = sheet_data.findall("m:row", ooxml.NS)[-1]
    assert shifted_footer.attrib["r"] == "49"
    assert [cell.attrib["r"] for cell in shifted_footer.findall("m:c", ooxml.NS)] == ["A49", "B49", "P49"]
    assert root.find("m:dimension", ooxml.NS).attrib["ref"] == "A1:P49"

    inserted = {int(row.attrib["r"]): row for row in sheet_data.findall("m:row", ooxml.NS)}
    colors = {}
    for row_number in (47, 48):
        cell = next(cell for cell in inserted[row_number].findall("m:c", ooxml.NS) if cell.attrib["r"] == f"N{row_number}")
        colors[row_number] = cell.find("m:v", ooxml.NS).text
    assert colors == {47: "Ocean", 48: "Green"}
    assert [ref for ref, _location, _display in links] == ["C47", "O47", "C48", "O48"]
