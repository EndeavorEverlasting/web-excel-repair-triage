"""Narrow package-preserving OOXML primitives for the segmented V39 generator.

This module intentionally exposes no prompt numbering, prompt taxonomy, V39
composition, or generator entrypoint. Semantic section ownership lives only in
``triage.prompt_kit_v39_generator`` and the two V39 prompt-contract files.

The implementation module is quarantined because it originated during an
abandoned numbering experiment. Only the generic package functions explicitly
re-exported below are supported; its former prompt IDs and generator functions
are not authority and must not be invoked.
"""
from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET

from . import _prompt_kit_v39_package_primitives_impl as _impl
from ._prompt_kit_v39_package_primitives_impl import (
    APP_NS,
    CELL_RE,
    CONTENT_TYPES_NS,
    LIBRARY_FIELDS,
    LIBRARY_FORMULA_RE,
    MAIN_NS,
    NS,
    PKG_REL_NS,
    PROMPT_SHEET_RE,
    REL_NS,
    SHEET_PART_RE,
    VT_NS,
    WorkbookParts,
    _append_workbook_sheets,
    _cell_display,
    _cell_parts,
    _cells,
    _find_library_rows,
    _formula,
    _formula_cells,
    _make_prompt_sheet,
    _prompt_payload,
    _prompt_rows_and_ranges,
    _read_workbook,
    _rebuild_calc_chain,
    _root,
    _shared_strings,
    _sheet_map,
    _source_workbook,
    _update_app_properties,
    _write_package,
)

MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_PREFIXES = {
    "r": REL_NS,
    "mc": MC_NS,
    "x14ac": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac",
    "x15": "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main",
    "xr": "http://schemas.microsoft.com/office/spreadsheetml/2014/revision",
    "xr2": "http://schemas.microsoft.com/office/spreadsheetml/2015/revision2",
    "xr3": "http://schemas.microsoft.com/office/spreadsheetml/2016/revision3",
    "xr6": "http://schemas.microsoft.com/office/spreadsheetml/2016/revision6",
    "xr10": "http://schemas.microsoft.com/office/spreadsheetml/2016/revision10",
}
for _prefix, _uri in _PREFIXES.items():
    ET.register_namespace(_prefix, _uri)

PROMPT_LIBRARY_NAVIGATION_CADENCES = (10, 5, 2)
_PROMPT_LIBRARY_EDGE_COLUMNS = ("A", "P")


def _namespace_uri(tag: str) -> str | None:
    if not tag.startswith("{"):
        return None
    return tag[1:].split("}", 1)[0]


def _xml(root: ET.Element) -> bytes:
    """Serialize one OOXML part with Excel-compatible namespace declarations.

    ElementTree normally rewrites package roots to ``ns0`` and omits named
    namespaces that are referenced only by the value of ``mc:Ignorable``.
    Strict Excel-compatible readers reject that shape even though a generic XML
    parser accepts it. Set the root namespace as the default for each part and
    inject any otherwise-unused ignorable prefix into the root start tag.
    """
    root_namespace = _namespace_uri(root.tag)
    if root_namespace:
        ET.register_namespace("", root_namespace)
    for prefix, uri in _PREFIXES.items():
        ET.register_namespace(prefix, uri)

    serialized = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ignorable = root.attrib.get(f"{{{MC_NS}}}Ignorable")
    if not ignorable:
        return serialized

    text = serialized.decode("utf-8")
    declaration_end = text.find("?>")
    root_start = text.find("<", declaration_end + 2)
    root_end = text.find(">", root_start)
    if root_start < 0 or root_end < 0:
        raise ValueError("serialized OOXML part has no root start tag")
    opening_tag = text[root_start:root_end]
    missing = []
    for prefix in ignorable.split():
        uri = _PREFIXES.get(prefix)
        if uri is None:
            raise ValueError(f"mc:Ignorable references unknown namespace prefix: {prefix}")
        if not re.search(rf"\bxmlns:{re.escape(prefix)}=", opening_tag):
            missing.append(f' xmlns:{prefix}="{uri}"')
    if missing:
        text = text[:root_end] + "".join(missing) + text[root_end:]
    return text.encode("utf-8")


_impl._xml = _xml


def _navigation_cadence(prompt_count: int) -> int:
    """Choose the sparsest allowed cadence that evenly divides the prompt count."""
    if prompt_count < 1:
        raise ValueError("Prompt Library navigation requires at least one prompt")
    for cadence in PROMPT_LIBRARY_NAVIGATION_CADENCES:
        if prompt_count % cadence == 0:
            return cadence
    raise ValueError(
        "Prompt Library prompt count must be divisible by one of "
        f"{PROMPT_LIBRARY_NAVIGATION_CADENCES}; found {prompt_count}"
    )


def _row_lookup(root: ET.Element) -> dict[int, ET.Element]:
    return {
        int(row.attrib.get("r", "0")): row
        for row in root.findall("m:sheetData/m:row", NS)
        if int(row.attrib.get("r", "0")) > 0
    }


def _replace_row_cell(
    row: ET.Element,
    ref: str,
    *,
    formula: str | None,
    cached: str,
) -> None:
    cells = list(row.findall("m:c", NS))
    existing = next((cell for cell in cells if cell.attrib.get("r") == ref), None)
    style = existing.attrib.get("s") if existing is not None else None
    if existing is not None:
        row.remove(existing)
    if formula is None:
        replacement = _impl._new_text_cell(ref, style, cached)
    else:
        replacement = _impl._new_formula_cell(ref, style, formula, cached)
    target_column = _impl._column_number(_cell_parts(ref)[0])
    insertion = len(list(row))
    for index, cell in enumerate(list(row)):
        cell_ref = cell.attrib.get("r")
        if cell_ref and _impl._column_number(_cell_parts(cell_ref)[0]) > target_column:
            insertion = index
            break
    row.insert(insertion, replacement)


def _prompt_library_prompt_rows(root: ET.Element) -> list[int]:
    rows = []
    for cell in root.findall(".//m:c", NS):
        ref = cell.attrib.get("r", "")
        if not ref.startswith("C"):
            continue
        if LIBRARY_FORMULA_RE.fullmatch(_formula(cell)):
            rows.append(_cell_parts(ref)[1])
    return sorted(set(rows))


def _navigation_formula(column: str, target_row: int, label: str) -> str:
    return f'HYPERLINK("#\'Prompt_Library\'!{column}{target_row}","{label}")'


def _replace_navigation_metadata(
    root: ET.Element,
    navigation: Mapping[str, tuple[str, str]],
) -> None:
    container = _impl._hyperlinks_element(root)
    for item in list(container.findall("m:hyperlink", NS)):
        if item.attrib.get("ref") in navigation:
            container.remove(item)
    for ref, (location, display) in navigation.items():
        ET.SubElement(
            container,
            f"{{{MAIN_NS}}}hyperlink",
            {"ref": ref, "location": location, "display": display},
        )


def _apply_prompt_library_navigation(root: ET.Element) -> dict[str, object]:
    """Apply deterministic sparse top/bottom links to Prompt Library edges.

    The cadence is the largest member of ``(10, 5, 2)`` that evenly divides the
    current prompt count, which yields the fewest navigation links. Linked prompt
    rows in the upper half point to the footer; linked prompt rows in the lower
    half point to the header. Both left and right edge columns receive links.
    """
    prompt_rows = _prompt_library_prompt_rows(root)
    if not prompt_rows:
        return {"prompt_count": 0, "cadence": None, "linked_rows": []}
    rows = _row_lookup(root)
    footer_candidates = [row for row in rows if row > prompt_rows[-1]]
    if not footer_candidates:
        raise ValueError("Prompt Library navigation requires a footer row after the prompts")
    footer_row = max(footer_candidates)
    if 1 not in rows or footer_row not in rows:
        raise ValueError("Prompt Library navigation requires header and footer rows")

    cadence = _navigation_cadence(len(prompt_rows))
    linked_rows = prompt_rows[::cadence]
    prompt_position = {row: index for index, row in enumerate(prompt_rows)}

    for row_number in prompt_rows:
        row = rows[row_number]
        for column in _PROMPT_LIBRARY_EDGE_COLUMNS:
            _replace_row_cell(row, f"{column}{row_number}", formula=None, cached="")

    navigation: dict[str, tuple[str, str]] = {}

    def set_link(row_number: int, column: str, target_row: int, label: str) -> None:
        ref = f"{column}{row_number}"
        _replace_row_cell(
            rows[row_number],
            ref,
            formula=_navigation_formula(column, target_row, label),
            cached=label,
        )
        navigation[ref] = (f"'Prompt_Library'!{column}{target_row}", label)

    for column in _PROMPT_LIBRARY_EDGE_COLUMNS:
        set_link(1, column, footer_row, "↓ Bottom")
        set_link(footer_row, column, 1, "↑ Top")

    midpoint = len(prompt_rows) / 2
    for row_number in linked_rows:
        if prompt_position[row_number] < midpoint:
            target_row, label = footer_row, "↓ Bottom"
        else:
            target_row, label = 1, "↑ Top"
        for column in _PROMPT_LIBRARY_EDGE_COLUMNS:
            set_link(row_number, column, target_row, label)

    _replace_row_cell(
        rows[footer_row],
        f"B{footer_row}",
        formula=None,
        cached=f"End of Prompt Library · {len(prompt_rows)} prompts",
    )
    _replace_navigation_metadata(root, navigation)
    return {
        "prompt_count": len(prompt_rows),
        "cadence": cadence,
        "linked_rows": linked_rows,
        "footer_row": footer_row,
    }


def _append_hyperlinks(root: ET.Element, links: Iterable[tuple[str, str, str]]) -> None:
    """Append prompt links, then enforce Prompt Library sparse navigation."""
    _impl._append_hyperlinks(root, links)
    _apply_prompt_library_navigation(root)


def _append_library_rows(
    root: ET.Element,
    header_columns: Mapping[str, int],
    prompt_rows: Mapping[str, int],
    start_row: int,
    prompts: Sequence[Mapping[str, object]],
    inherited_color: str,
) -> tuple[dict[str, int], list[tuple[str, str, str]]]:
    """Insert new prompt rows before the existing Prompt Library footer.

    The accepted V38 workbook ends the Prompt Library with a navigation/footer
    row after P44. The quarantined primitive originally appended after the
    worksheet's maximum row, which placed V39 prompts below that footer. This
    wrapper treats the last existing prompt row as the insertion boundary,
    shifts all later rows, and then delegates row construction to the generic
    primitive. Prompt-specific color labels are preserved when supplied.
    """
    del start_row
    if "P44" not in prompt_rows:
        raise ValueError("Prompt Library does not contain the P44 insertion boundary")
    sheet_data = root.find("m:sheetData", NS)
    if sheet_data is None:
        raise ValueError("Prompt Library has no sheetData")

    boundary = prompt_rows["P44"]
    tail_rows = [
        row for row in sheet_data.findall("m:row", NS)
        if int(row.attrib.get("r", "0")) > boundary
    ]
    original_tail_rows = [int(row.attrib["r"]) for row in tail_rows]
    for row in tail_rows:
        sheet_data.remove(row)

    new_rows, links = _impl._append_library_rows(
        root,
        header_columns,
        prompt_rows,
        boundary,
        prompts,
        inherited_color,
    )

    delta = len(prompts)
    for row, original_row in zip(tail_rows, original_tail_rows):
        shifted_row = original_row + delta
        row.attrib["r"] = str(shifted_row)
        for cell in row.findall("m:c", NS):
            ref = cell.attrib.get("r")
            if not ref:
                continue
            column, _ = _cell_parts(ref)
            cell.attrib["r"] = f"{column}{shifted_row}"
        sheet_data.append(row)

    color_column_number = header_columns.get("Color")
    if color_column_number:
        color_column = _impl._column_name(color_column_number)
        row_lookup = {
            int(row.attrib["r"]): row for row in sheet_data.findall("m:row", NS)
        }
        for prompt in prompts:
            prompt_id = str(prompt["prompt_id"])
            color = str(prompt.get("color") or inherited_color)
            row_number = new_rows[prompt_id]
            row = row_lookup[row_number]
            ref = f"{color_column}{row_number}"
            cell = next((item for item in row.findall("m:c", NS) if item.attrib.get("r") == ref), None)
            if cell is None:
                raise ValueError(f"Prompt Library row {row_number} is missing Color cell {ref}")
            cell.attrib["t"] = "str"
            value = cell.find("m:v", NS)
            if value is None:
                value = ET.SubElement(cell, f"{{{MAIN_NS}}}v")
            value.text = color

    final_max_row = max(
        [boundary + delta, *[row + delta for row in original_tail_rows]],
        default=boundary + delta,
    )
    dimension = root.find("m:dimension", NS)
    if dimension is not None:
        original_ref = dimension.attrib.get("ref", "A1:P1")
        end_ref = original_ref.split(":", 1)[-1]
        end_column, _ = _cell_parts(end_ref)
        dimension.attrib["ref"] = f"A1:{end_column}{final_max_row}"

    return new_rows, links


__all__ = [
    "APP_NS",
    "CELL_RE",
    "CONTENT_TYPES_NS",
    "LIBRARY_FIELDS",
    "LIBRARY_FORMULA_RE",
    "MAIN_NS",
    "MC_NS",
    "NS",
    "PKG_REL_NS",
    "PROMPT_LIBRARY_NAVIGATION_CADENCES",
    "PROMPT_SHEET_RE",
    "REL_NS",
    "SHEET_PART_RE",
    "VT_NS",
    "WorkbookParts",
    "_append_hyperlinks",
    "_append_library_rows",
    "_append_workbook_sheets",
    "_apply_prompt_library_navigation",
    "_cell_display",
    "_cell_parts",
    "_cells",
    "_find_library_rows",
    "_formula",
    "_formula_cells",
    "_make_prompt_sheet",
    "_navigation_cadence",
    "_prompt_payload",
    "_prompt_rows_and_ranges",
    "_read_workbook",
    "_rebuild_calc_chain",
    "_root",
    "_shared_strings",
    "_sheet_map",
    "_source_workbook",
    "_update_app_properties",
    "_write_package",
    "_xml",
]
