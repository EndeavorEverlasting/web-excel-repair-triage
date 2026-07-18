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

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET

from . import _prompt_kit_v39_package_primitives_impl as _impl
from . import prompt_kit_visual_contract as visual_contract
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
    "x16r2": "http://schemas.microsoft.com/office/spreadsheetml/2015/02/main",
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
_PROMPT_LIBRARY_ROW_COLUMNS = tuple(_impl._column_name(number) for number in range(2, 16))


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



def _prompt_library_row_formula(sheet_name: str, prompt_range: str, display: str) -> str:
    escaped = display.replace('"', '""')
    return f'HYPERLINK("#\'{sheet_name}\'!{prompt_range}","{escaped}")'


def _prompt_library_row_entries(root: ET.Element) -> list[tuple[int, str, str]]:
    entries: list[tuple[int, str, str]] = []
    for cell in root.findall(".//m:c", NS):
        ref = cell.attrib.get("r", "")
        if not ref.startswith("C"):
            continue
        match = LIBRARY_FORMULA_RE.fullmatch(_formula(cell))
        if match:
            entries.append((_cell_parts(ref)[1], match.group("sheet"), match.group("range").upper()))
    return sorted(set(entries))


def _apply_prompt_library_row_links(
    root: ET.Element,
    shared_strings: Sequence[str] = (),
) -> dict[str, object]:
    """Make every Prompt Library data cell B:O open its exact prompt range.

    Display values and cell styles are preserved. Columns A and P are excluded
    because they are the dedicated sparse top/bottom navigation surfaces.
    """
    entries = _prompt_library_row_entries(root)
    rows = _row_lookup(root)
    metadata: dict[str, tuple[str, str]] = {}
    linked_cells: list[str] = []
    for row_number, sheet_name, prompt_range in entries:
        row = rows.get(row_number)
        if row is None:
            raise ValueError(f"Prompt Library is missing prompt row {row_number}")
        cells = {cell.attrib.get("r", ""): cell for cell in row.findall("m:c", NS)}
        location = f"'{sheet_name}'!{prompt_range}"
        for column in _PROMPT_LIBRARY_ROW_COLUMNS:
            ref = f"{column}{row_number}"
            display = _cell_display(cells.get(ref), shared_strings)
            _replace_row_cell(
                row,
                ref,
                formula=_prompt_library_row_formula(sheet_name, prompt_range, display),
                cached=display,
            )
            metadata[ref] = (location, display)
            linked_cells.append(ref)
    _replace_navigation_metadata(root, metadata)
    return {
        "prompt_count": len(entries),
        "columns": _PROMPT_LIBRARY_ROW_COLUMNS,
        "linked_cell_count": len(linked_cells),
        "linked_cells": linked_cells,
    }


def _validate_prompt_library_row_links(
    root: ET.Element,
    shared_strings: Sequence[str] = (),
) -> tuple[dict[str, object], ...]:
    findings: list[dict[str, object]] = []
    cells = _cells(root)
    hyperlinks = {
        item.attrib.get("ref", ""): (item.attrib.get("location", ""), item.attrib.get("display", ""))
        for item in root.findall("m:hyperlinks/m:hyperlink", NS)
    }
    for row_number, sheet_name, prompt_range in _prompt_library_row_entries(root):
        location = f"'{sheet_name}'!{prompt_range}"
        for column in _PROMPT_LIBRARY_ROW_COLUMNS:
            ref = f"{column}{row_number}"
            display = _cell_display(cells.get(ref), shared_strings)
            expected_formula = _prompt_library_row_formula(sheet_name, prompt_range, display)
            if _formula(cells.get(ref)) != expected_formula:
                findings.append({"rule": "Prompt Library whole-row formula", "cell": ref, "expected": expected_formula})
            if hyperlinks.get(ref) != (location, display):
                findings.append({
                    "rule": "Prompt Library whole-row hyperlink metadata",
                    "cell": ref,
                    "expected": (location, display),
                    "actual": hyperlinks.get(ref),
                })
    return tuple(findings)

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
    if 1 not in rows:
        raise ValueError("Prompt Library navigation requires a header row")
    footer_candidates = [row for row in rows if row > prompt_rows[-1]]
    if footer_candidates:
        footer_row = max(footer_candidates)
    else:
        footer_row = prompt_rows[-1] + 1
        template = rows[prompt_rows[-1]]
        attrs = dict(template.attrib)
        attrs["r"] = str(footer_row)
        footer = ET.Element(f"{{{MAIN_NS}}}row", attrs)
        template_cells = {
            _cell_parts(cell.attrib["r"])[0]: cell
            for cell in template.findall("m:c", NS)
            if cell.attrib.get("r")
        }
        for column in _PROMPT_LIBRARY_EDGE_COLUMNS:
            style = template_cells.get(column).attrib.get("s") if template_cells.get(column) is not None else None
            footer.append(_impl._new_text_cell(f"{column}{footer_row}", style, ""))
        b_style = template_cells.get("B").attrib.get("s") if template_cells.get("B") is not None else None
        footer.insert(1, _impl._new_text_cell(f"B{footer_row}", b_style, ""))
        sheet_data = root.find("m:sheetData", NS)
        if sheet_data is None:
            raise ValueError("Prompt Library has no sheetData")
        sheet_data.append(footer)
        rows[footer_row] = footer
        dimension = root.find("m:dimension", NS)
        if dimension is not None:
            original_ref = dimension.attrib.get("ref", "A1:P1")
            end_ref = original_ref.split(":", 1)[-1]
            end_column, _ = _cell_parts(end_ref)
            dimension.attrib["ref"] = f"A1:{end_column}{footer_row}"

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


def _append_hyperlinks(
    root: ET.Element,
    links: Iterable[tuple[str, str, str]],
    shared_strings: Sequence[str] = (),
) -> None:
    """Append exact prompt links, whole-row links, then sparse edge navigation."""
    _impl._append_hyperlinks(root, links)
    _apply_prompt_library_row_links(root, shared_strings)
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



def _ensure_collection(root: ET.Element, tag: str) -> ET.Element:
    collection = root.find(f"m:{tag}", NS)
    if collection is None:
        raise ValueError(f"styles.xml is missing {tag}")
    return collection


def _element_key(element: ET.Element) -> bytes:
    return ET.tostring(element, encoding="utf-8")


def _ensure_style_child(collection: ET.Element, candidate: ET.Element) -> int:
    key = _element_key(candidate)
    for index, existing in enumerate(list(collection)):
        if _element_key(existing) == key:
            return index
    collection.append(candidate)
    collection.attrib["count"] = str(len(list(collection)))
    return len(list(collection)) - 1


def _ensure_fill(styles: ET.Element, rgb: str) -> int:
    fills = _ensure_collection(styles, "fills")
    fill = ET.Element(f"{{{MAIN_NS}}}fill")
    pattern = ET.SubElement(fill, f"{{{MAIN_NS}}}patternFill", {"patternType": "solid"})
    ET.SubElement(pattern, f"{{{MAIN_NS}}}fgColor", {"rgb": f"FF{rgb}"})
    ET.SubElement(pattern, f"{{{MAIN_NS}}}bgColor", {"indexed": "64"})
    return _ensure_style_child(fills, fill)


def _ensure_font(styles: ET.Element, base_font_id: int, rgb: str) -> int:
    fonts = _ensure_collection(styles, "fonts")
    font_items = list(fonts)
    if base_font_id >= len(font_items):
        raise ValueError(f"fontId {base_font_id} is outside styles.xml")
    font = deepcopy(font_items[base_font_id])
    color = font.find("m:color", NS)
    if color is None:
        color = ET.Element(f"{{{MAIN_NS}}}color")
        size = font.find("m:sz", NS)
        if size is not None:
            font.insert(list(font).index(size), color)
        else:
            font.append(color)
    color.attrib.clear()
    color.attrib["rgb"] = f"FF{rgb}"
    return _ensure_style_child(fonts, font)


def _ensure_cell_xf(styles: ET.Element, base_style_id: int, font_id: int, fill_id: int) -> int:
    xfs = _ensure_collection(styles, "cellXfs")
    xf_items = list(xfs)
    if base_style_id >= len(xf_items):
        raise ValueError(f"style id {base_style_id} is outside styles.xml")
    xf = deepcopy(xf_items[base_style_id])
    xf.attrib.update({"fontId": str(font_id), "fillId": str(fill_id), "applyFont": "1", "applyFill": "1"})
    return _ensure_style_child(xfs, xf)


def _style_colors(styles: ET.Element, style_id: int) -> tuple[str, str]:
    xfs = list(_ensure_collection(styles, "cellXfs"))
    if style_id >= len(xfs):
        return "", ""
    xf = xfs[style_id]
    fill_id = int(xf.attrib.get("fillId", "0"))
    font_id = int(xf.attrib.get("fontId", "0"))
    fills = list(_ensure_collection(styles, "fills"))
    fonts = list(_ensure_collection(styles, "fonts"))
    fill_rgb = ""
    font_rgb = ""
    if fill_id < len(fills):
        fg = fills[fill_id].find("m:patternFill/m:fgColor", NS)
        if fg is not None:
            fill_rgb = fg.attrib.get("rgb", "")[-6:].upper()
    if font_id < len(fonts):
        color = fonts[font_id].find("m:color", NS)
        if color is not None:
            font_rgb = color.attrib.get("rgb", "")[-6:].upper()
    return fill_rgb, font_rgb


def _set_tab_color(root: ET.Element, rgb: str) -> None:
    sheet_pr = root.find("m:sheetPr", NS)
    if sheet_pr is None:
        sheet_pr = ET.Element(f"{{{MAIN_NS}}}sheetPr")
        root.insert(0, sheet_pr)
    tab_color = sheet_pr.find("m:tabColor", NS)
    if tab_color is None:
        tab_color = ET.Element(f"{{{MAIN_NS}}}tabColor")
        sheet_pr.insert(0, tab_color)
    tab_color.attrib.clear()
    tab_color.attrib["rgb"] = f"FF{rgb}"


def _apply_prompt_visual_coordination(parts: Mapping[str, bytes] | dict[str, bytes]) -> tuple[set[str], dict[str, object]]:
    """Apply semantic Prompt Library row colors and matching prompt-tab colors."""
    mutable = parts
    _, mapping, _, _ = _sheet_map(mutable)
    library_part = mapping.get("Prompt_Library")
    if not library_part:
        raise ValueError("missing Prompt_Library while applying prompt visual coordination")
    if "xl/styles.xml" not in mutable:
        return set(), {"prompt_count": 0, "skipped": "source package has no styles.xml"}
    palette = visual_contract.palette()
    shared = _shared_strings(mutable)
    library_root = _root(mutable[library_part], library_part)
    styles = _root(mutable["xl/styles.xml"], "xl/styles.xml")
    rows = _row_lookup(library_root)
    changed: set[str] = {library_part, "xl/styles.xml"}
    prompts: list[dict[str, object]] = []
    fill_cache: dict[str, int] = {}
    font_cache: dict[tuple[int, str], int] = {}
    xf_cache: dict[tuple[int, int, int], int] = {}
    for row_number, sheet_name, _ in _prompt_library_row_entries(library_root):
        row = rows[row_number]
        cells = {cell.attrib.get("r", ""): cell for cell in row.findall("m:c", NS)}
        label = _cell_display(cells.get(f"N{row_number}"), shared)
        if label not in palette:
            raise ValueError(f"Prompt Library row {row_number} has unknown semantic Color label {label!r}")
        fill_rgb, text_rgb = palette[label]
        for column in _PROMPT_LIBRARY_ROW_COLUMNS:
            ref = f"{column}{row_number}"
            cell = cells.get(ref)
            if cell is None:
                raise ValueError(f"Prompt Library row color contract is missing {ref}")
            base_style = int(cell.attrib.get("s", "0"))
            if _style_colors(styles, base_style) == (fill_rgb, text_rgb):
                continue
            xfs = list(_ensure_collection(styles, "cellXfs"))
            base_xf = xfs[base_style]
            base_font_id = int(base_xf.attrib.get("fontId", "0"))
            font_key = (base_font_id, text_rgb)
            if font_key not in font_cache:
                font_cache[font_key] = _ensure_font(styles, base_font_id, text_rgb)
            if fill_rgb not in fill_cache:
                fill_cache[fill_rgb] = _ensure_fill(styles, fill_rgb)
            style_key = (base_style, font_cache[font_key], fill_cache[fill_rgb])
            if style_key not in xf_cache:
                xf_cache[style_key] = _ensure_cell_xf(styles, *style_key)
            cell.attrib["s"] = str(xf_cache[style_key])
        part = mapping.get(sheet_name)
        if not part:
            raise ValueError(f"Prompt Library points to missing prompt sheet {sheet_name}")
        prompt_root = _root(mutable[part], part)
        _set_tab_color(prompt_root, fill_rgb)
        mutable[part] = _xml(prompt_root)
        changed.add(part)
        prompts.append({"row": row_number, "sheet": sheet_name, "color": label, "rgb": fill_rgb})
    mutable[library_part] = _xml(library_root)
    mutable["xl/styles.xml"] = _xml(styles)
    return changed, {"prompt_count": len(prompts), "prompts": prompts}


def _normalize_prompt_placeholders(parts: Mapping[str, bytes] | dict[str, bytes]) -> tuple[set[str], dict[str, object]]:
    """Remove ASCII or smart quotes immediately surrounding xyz_ placeholders."""
    mutable = parts
    _, mapping, _, _ = _sheet_map(mutable)
    shared = _shared_strings(mutable)
    changed: set[str] = set()
    replacements: list[dict[str, str]] = []
    for sheet_name, part in mapping.items():
        if not PROMPT_SHEET_RE.fullmatch(sheet_name):
            continue
        root = _root(mutable[part], part)
        rows = _row_lookup(root)
        sheet_changed = False
        for row_number, row in rows.items():
            for cell in list(row.findall("m:c", NS)):
                if cell.find("m:f", NS) is not None:
                    continue
                ref = cell.attrib.get("r", "")
                display = _cell_display(cell, shared)
                normalized = visual_contract.unquote_placeholders(display)
                if normalized == display:
                    continue
                _replace_row_cell(row, ref, formula=None, cached=normalized)
                replacements.append({"sheet": sheet_name, "cell": ref, "before": display, "after": normalized})
                sheet_changed = True
        if sheet_changed:
            mutable[part] = _xml(root)
            changed.add(part)
    return changed, {"replacement_count": len(replacements), "replacements": replacements}


def _validate_prompt_placeholder_ergonomics(parts: Mapping[str, bytes]) -> tuple[dict[str, object], ...]:
    _, mapping, _, _ = _sheet_map(parts)
    shared = _shared_strings(parts)
    findings: list[dict[str, object]] = []
    for sheet_name, part in mapping.items():
        if not PROMPT_SHEET_RE.fullmatch(sheet_name):
            continue
        root = _root(parts[part], part)
        for cell in root.findall(".//m:c", NS):
            if cell.find("m:f", NS) is not None:
                continue
            display = _cell_display(cell, shared)
            quoted = visual_contract.quoted_placeholders(display)
            if quoted:
                findings.append({"rule": "bare prompt placeholder", "sheet": sheet_name, "cell": cell.attrib.get("r"), "quoted": list(quoted), "value": display})
    return tuple(findings)


TECHNICIAN_VIEW_PROFILE_PATH = Path(__file__).parents[1] / "configs/harness/technician_view_profile_v1.json"


_NAV_HYPERLINK_TARGET_RE = re.compile(r"'Prompt_Library'", re.IGNORECASE)


def _detect_prompt_tab_navigation_rows(root: ET.Element) -> tuple[int, int]:
    formula_rows: list[int] = []
    hyperlink_rows: list[int] = []
    for cell in root.findall(".//m:c", NS):
        formula = _formula(cell)
        if not formula:
            continue
        if "HYPERLINK" not in formula.upper():
            continue
        if not _NAV_HYPERLINK_TARGET_RE.search(formula):
            continue
        ref = cell.attrib.get("r", "")
        if not ref:
            continue
        _, row = _cell_parts(ref)
        formula_rows.append(row)
    for item in root.findall("m:hyperlinks/m:hyperlink", NS):
        location = item.attrib.get("location", "")
        if "Prompt_Library" not in location:
            continue
        ref = item.attrib.get("ref", "")
        if not ref:
            continue
        _, row = _cell_parts(ref)
        hyperlink_rows.append(row)
    nav_rows = sorted(set(formula_rows) & set(hyperlink_rows))
    if not nav_rows:
        raise ValueError("prompt tab has no navigation row hyperlinking to Prompt_Library")
    if len(nav_rows) == 1:
        raise ValueError("prompt tab has only one navigation row; cannot determine body range")
    top_nav = min(nav_rows)
    bottom_nav = max(nav_rows)
    return top_nav, bottom_nav


def _prompt_body_range(root: ET.Element, sheet_name: str) -> tuple[int, int, list[str], str]:
    top_nav, bottom_nav = _detect_prompt_tab_navigation_rows(root)
    dimension = root.find("m:dimension", NS)
    if dimension is None:
        raise ValueError(f"prompt tab {sheet_name} has no dimension element")
    dim_ref = dimension.attrib.get("ref", "")
    if ":" not in dim_ref:
        raise ValueError(f"prompt tab {sheet_name} has malformed dimension {dim_ref!r}")
    end_ref = dim_ref.split(":", 1)[-1]
    end_col, _ = _cell_parts(end_ref)
    columns = [_impl._column_name(n) for n in range(1, _impl._column_number(end_col) + 1) if _impl._column_name(n) <= end_col]
    range_str = f"A{top_nav}:{end_col}{bottom_nav}"
    return top_nav, bottom_nav, columns, range_str


def _apply_prompt_body_scaffold(parts: MutableMapping[str, bytes] | dict[str, bytes]) -> tuple[set[str], dict[str, object]]:
    mutable = parts
    _, mapping, _, _ = _sheet_map(mutable)
    if "xl/styles.xml" not in mutable:
        return set(), {"prompt_count": 0, "skipped": "source package has no styles.xml"}
    policy = visual_contract.load_policy()
    scaffold_rgb = policy.get("prompt_body_range", {}).get("scaffold_fill", {}).get("rgb", "F8FAFC")
    styles = _root(mutable["xl/styles.xml"], "xl/styles.xml")
    scaffold_fill_id = _ensure_fill(styles, scaffold_rgb)
    changed: set[str] = {"xl/styles.xml"}
    prompts: list[dict[str, object]] = []
    for sheet_name, part in mapping.items():
        if not PROMPT_SHEET_RE.fullmatch(sheet_name):
            continue
        prompt_root = _root(mutable[part], part)
        try:
            top_nav, bottom_nav, columns, range_str = _prompt_body_range(prompt_root, sheet_name)
        except ValueError as exc:
            prompts.append({"sheet": sheet_name, "error": str(exc)})
            continue
        rows = _row_lookup(prompt_root)
sheet_data = prompt_root.find("m:sheetData", NS)
if sheet_data is None:
    raise ValueError(f"prompt tab {sheet_name} has no sheetData element")
xfs_element = _ensure_collection(styles, "cellXfs")
scaffold_style_cache: dict[int, int] = {}

def scaffold_style_for(base_style: int) -> int:
    cached = scaffold_style_cache.get(base_style)
    if cached is not None:
        return cached
    xfs = list(xfs_element)
    if base_style < 0 or base_style >= len(xfs):
        raise ValueError(
            f"prompt tab {sheet_name} cell style {base_style} is outside cellXfs"
        )
    base_xf = xfs[base_style]
    base_fill_id = int(base_xf.attrib.get("fillId", "0"))
    if base_fill_id == scaffold_fill_id:
        scaffold_style_cache[base_style] = base_style
        return base_style
    new_xf = deepcopy(base_xf)
    new_xf.attrib["fillId"] = str(scaffold_fill_id)
    new_xf.attrib["applyFill"] = "1"
    style_id = _ensure_style_child(xfs_element, new_xf)
    scaffold_style_cache[base_style] = style_id
    return style_id

def ensure_row(row_number: int) -> ET.Element:
    existing = rows.get(row_number)
    if existing is not None:
        return existing
    row = ET.Element(f"{{{MAIN_NS}}}row", {"r": str(row_number)})
    insertion = len(list(sheet_data))
    for index, candidate in enumerate(list(sheet_data)):
        candidate_number = int(candidate.attrib.get("r", "0"))
        if candidate_number > row_number:
            insertion = index
            break
    sheet_data.insert(insertion, row)
    rows[row_number]] = row
    return row

def insert_cell(row: ET.Element, cell: ET.Element, ref: str) -> None:
    target_column = _impl._column_number(_cell_parts(ref)[0])
    insertion = len(list(row))
    for index, candidate in enumerate(list(row)):
        candidate_ref = candidate.attrib.get("r", "")
        if candidate_ref and _impl._column_number(_cell_parts(candidate_ref)[0]) > target_column:
            insertion = index
            break
    row.insert(insertion, cell)

filled = 0
materialized = 0
for row_number in range(top_nav, bottom_nav + 1):
    row = ensure_row(row_number)
    for col in columns:
        ref = f"{col}{row_number}"
        cell = next((c for c in row.findall("m:c", NS) if c.attrib.get("r") == ref), None)
        if cell is None:
            style_id = scaffold_style_for(0)
            cell = ET.Element(
                f"{{{MAIN_NS}}}c",
                {"r": ref, "s": str(style_id)},
            )
            insert_cell(row, cell, ref)
            filled += 1
            materialized += 1
            continue
        base_style = int(cell.attrib.get("s", "0"))
        style_id = scaffold_style_for(base_style)
        if style_id == base_style:
            continue
        cell.attrib["s"] = str(style_id)
        filled += 1
mutable[part] = _xml(prompt_root)
changed.add(part)
prompts.append({"sheet": sheet_name, "range": range_str, "top_nav_row": top_nav, "bottom_nav_row": bottom_nav, "columns": columns, "cells_filled": filled, "cells_materialized": materialized})
    mutable["xl/styles.xml"] = _xml(styles)
    return changed, {"prompt_count": len(prompts), "scaffold_rgb": scaffold_rgb, "prompts": prompts}


def _validate_prompt_body_scaffold(parts: Mapping[str, bytes]) -> tuple[dict[str, object], ...]:
    _, mapping, _, _ = _sheet_map(parts)
    if "xl/styles.xml" not in parts:
        return ()
    policy = visual_contract.load_policy()
    scaffold_rgb = policy.get("prompt_body_range", {}).get("scaffold_fill", {}).get("rgb", "F8FAFC")
    styles = _root(parts["xl/styles.xml"], "xl/styles.xml")
    scaffold_fill_ids: set[int] = set()
    fills = list(_ensure_collection(styles, "fills"))
    for idx, fill in enumerate(fills):
        fg = fill.find("m:patternFill/m:fgColor", NS)
        if fg is not None:
            fill_rgb = fg.attrib.get("rgb", "")[-6:].upper()
            if fill_rgb == scaffold_rgb:
                scaffold_fill_ids.add(idx)
    findings: list[dict[str, object]] = []
    for sheet_name, part in mapping.items():
        if not PROMPT_SHEET_RE.fullmatch(sheet_name):
            continue
        prompt_root = _root(parts[part], part)
        try:
            top_nav, bottom_nav, columns, range_str = _prompt_body_range(prompt_root, sheet_name)
        except ValueError as exc:
            findings.append({"rule": "prompt body range detection", "sheet": sheet_name, "error": str(exc)})
            continue
        rows = _row_lookup(prompt_root)
        uncovered: list[str] = []
        for row_number in range(top_nav, bottom_nav + 1):
    row = rows.get(row_number)
    if row is None:
        uncovered.extend(f"{col}{row_number}" for col in columns)
        continue
    for col in columns:
        ref = f"{col}{row_number}"
        cell = next((c for c in row.findall("m:c", NS) if c.attrib.get("r") == ref), None)
        if cell is None:
            uncovered.append(ref)
            continue
        style_id = int(cell.attrib.get("s", "0"))
                fill_id = int(list(_ensure_collection(styles, "cellXfs"))[style_id].attrib.get("fillId", "0"))
                if fill_id not in scaffold_fill_ids:
                    uncovered.append(ref)
        if uncovered:
            findings.append({"rule": "prompt body scaffold fill coverage", "sheet": sheet_name, "range": range_str, "uncovered_cells": uncovered, "uncovered_count": len(uncovered)})
    return tuple(findings)


def _load_technician_view_profile(path: str | Path = TECHNICIAN_VIEW_PROFILE_PATH) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("technician view profile must be one JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("technician view profile requires schema_version 1")
    return payload


def _apply_technician_column_visibility(
    parts: MutableMapping[str, bytes] | dict[str, bytes],
    profile: Mapping[str, object] | None = None,
) -> tuple[set[str], dict[str, object]]:
    if profile is None:
        profile = _load_technician_view_profile()
    hidden_columns = profile.get("hidden_columns")
    if not isinstance(hidden_columns, list) or not hidden_columns:
        return set(), {"hidden_count": 0, "skipped": "no columns configured for hiding"}
    target_sheet = profile.get("target_sheet", "Prompt_Library")
    mutable = parts
    _, mapping, _, _ = _sheet_map(mutable)
    library_part = mapping.get(target_sheet)
    if not library_part:
        raise ValueError(f"technician view target sheet {target_sheet} not found in workbook")
    library_root = _root(mutable[library_part], library_part)
    all_cells = _cells(library_root)
    for col in hidden_columns:
        col_cells = {ref: cell for ref, cell in all_cells.items() if _cell_parts(ref)[0] == col}
        if not col_cells:
            raise ValueError(f"column {col} has no cells in {target_sheet}; cannot hide an empty column without data loss detection")
    cols = library_root.find("m:cols", NS)
    if cols is None:
        cols = ET.Element(f"{{{MAIN_NS}}}cols")
        library_root.insert(0, cols)
    existing_cols = {(col.attrib.get("min"), col.attrib.get("max")): col for col in cols.findall("m:col", NS)}
    for col_letter in hidden_columns:
        col_number = _impl._column_number(col_letter)
        for (min_val, max_val), col_elem in existing_cols.items():
            mn = int(min_val) if min_val else 0
            mx = int(max_val) if max_val else 0
            if mn <= col_number <= mx:
                col_elem.attrib["hidden"] = "1"
                col_elem.attrib["customWidth"] = "0"
                break
        else:
            ET.SubElement(
                cols,
                f"{{{MAIN_NS}}}col",
                {"min": str(col_number), "max": str(col_number), "hidden": "1", "customWidth": "0", "width": "0"},
            )
    mutable[library_part] = _xml(library_root)
    return {library_part}, {"hidden_count": len(hidden_columns), "hidden_columns": hidden_columns, "target_sheet": target_sheet}


def _validate_technician_column_visibility(parts: Mapping[str, bytes]) -> tuple[dict[str, object], ...]:
    profile = _load_technician_view_profile()
    hidden_columns = profile.get("hidden_columns")
    if not isinstance(hidden_columns, list) or not hidden_columns:
        return ()
    target_sheet = profile.get("target_sheet", "Prompt_Library")
    _, mapping, _, _ = _sheet_map(parts)
    library_part = mapping.get(target_sheet)
    if not library_part:
        return ({"rule": "technician view target sheet", "sheet": target_sheet, "error": "not found"},)
    library_root = _root(parts[library_part], library_part)
    findings: list[dict[str, object]] = []
    cols = library_root.find("m:cols", NS)
    hidden_by_profile: dict[str, int] = {}
    for col in hidden_columns:
        col_number = _impl._column_number(col)
        hidden_by_profile[col] = col_number
    if cols is not None:
        for col_elem in cols.findall("m:col", NS):
            mn = int(col_elem.attrib.get("min", "0"))
            mx = int(col_elem.attrib.get("max", "0"))
            is_hidden = col_elem.attrib.get("hidden") == "1"
            for col_letter, col_number in hidden_by_profile.items():
                if mn <= col_number <= mx:
                    if not is_hidden:
                        findings.append({"rule": "technician column hidden", "column": col_letter, "actual": "visible"})
                    break
            else:
                if is_hidden:
                    col_name = _impl._column_name(mn)
                    if col_name not in hidden_columns:
                        findings.append({"rule": "technician column hidden unexpected", "column": col_name})
    rows = _row_lookup(library_root)
    for col in hidden_columns:
        cells_found = any(
            any(cell.attrib.get("r", "").startswith(col) for cell in list(row.findall("m:c", NS)))
            for row in rows.values()
        )
        if not cells_found:
            findings.append({"rule": "technician column data preserved", "column": col, "reason": "no cells found — possible deletion"})
    for col in hidden_columns:
        has_links = any(
            col in item.attrib.get("ref", "") or col in item.attrib.get("location", "")
            for item in library_root.findall("m:hyperlinks/m:hyperlink", NS)
        )
        formulae_with_col = any(
            col in (_formula(cell))
            for cell in library_root.findall(".//m:c", NS)
        )
        if has_links or formulae_with_col:
            continue
    return tuple(findings)


def _validate_prompt_visual_coordination(parts: Mapping[str, bytes]) -> tuple[dict[str, object], ...]:
    _, mapping, _, _ = _sheet_map(parts)
    library_part = mapping.get("Prompt_Library")
    if not library_part:
        return ({"rule": "prompt visual coordination", "error": "missing Prompt_Library"},)
    if "xl/styles.xml" not in parts:
        return ()
    palette = visual_contract.palette()
    shared = _shared_strings(parts)
    library_root = _root(parts[library_part], library_part)
    styles = _root(parts["xl/styles.xml"], "xl/styles.xml")
    rows = _row_lookup(library_root)
    findings: list[dict[str, object]] = []
    for row_number, sheet_name, _ in _prompt_library_row_entries(library_root):
        row = rows[row_number]
        cells = {cell.attrib.get("r", ""): cell for cell in row.findall("m:c", NS)}
        label = _cell_display(cells.get(f"N{row_number}"), shared)
        expected = palette.get(label)
        if expected is None:
            findings.append({"rule": "semantic prompt color label", "row": row_number, "actual": label})
            continue
        fill_rgb, text_rgb = expected
        for column in _PROMPT_LIBRARY_ROW_COLUMNS:
            ref = f"{column}{row_number}"
            cell = cells.get(ref)
            if cell is None:
                findings.append({"rule": "semantic prompt row cell", "cell": ref, "reason": "missing"})
                continue
            actual_fill, actual_text = _style_colors(styles, int(cell.attrib.get("s", "0")))
            if (actual_fill, actual_text) != (fill_rgb, text_rgb):
                findings.append({"rule": "semantic prompt row color", "cell": ref, "label": label, "expected": [fill_rgb, text_rgb], "actual": [actual_fill, actual_text]})
        part = mapping.get(sheet_name)
        if not part:
            findings.append({"rule": "semantic prompt tab color", "sheet": sheet_name, "reason": "missing sheet"})
            continue
        prompt_root = _root(parts[part], part)
        tab = prompt_root.find("m:sheetPr/m:tabColor", NS)
        actual_tab = tab.attrib.get("rgb", "")[-6:].upper() if tab is not None else ""
        if actual_tab != fill_rgb:
            findings.append({"rule": "semantic prompt tab color", "sheet": sheet_name, "label": label, "expected": fill_rgb, "actual": actual_tab})
    return tuple(findings)


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
    "_validate_prompt_visual_coordination",
    "_validate_prompt_body_scaffold",
    "_validate_prompt_placeholder_ergonomics",
    "_normalize_prompt_placeholders",
    "_apply_prompt_visual_coordination",
    "_apply_prompt_library_navigation",
    "_apply_prompt_library_row_links",
    "_apply_prompt_body_scaffold",
    "_detect_prompt_tab_navigation_rows",
    "_prompt_body_range",
    "_apply_technician_column_visibility",
    "_validate_technician_column_visibility",
    "_cell_display",
    "_cell_parts",
    "_cells",
    "_find_library_rows",
    "_formula",
    "_formula_cells",
    "_make_prompt_sheet",
    "_navigation_cadence",
    "_prompt_library_row_formula",
    "_prompt_payload",
    "_prompt_rows_and_ranges",
    "_read_workbook",
    "_rebuild_calc_chain",
    "_root",
    "_shared_strings",
    "_sheet_map",
    "_source_workbook",
    "_update_app_properties",
    "_validate_prompt_library_row_links",
    "_write_package",
    "_xml",
]
