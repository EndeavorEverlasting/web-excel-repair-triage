"""OOXML finalizer for the AI Harness Prompt Kit V33 copy surface."""
from __future__ import annotations

import copy
import posixpath
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, MutableMapping, Sequence, Tuple
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS}
ET.register_namespace("", MAIN_NS)
ET.register_namespace("r", REL_NS)

PROMPT_IDS = tuple(f"P{n:02d}" for n in range(45))
PROMPT_LIBRARY = "Prompt_Library"
OPPORTUNITY_DISCOVERY = "Opportunity_Discovery"
PROMPT_SUFFIX = "_COPY_SAFE"
CREAM_TAB_COLOR = "FFF7E6C4"
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")


@dataclass(frozen=True)
class PromptRange:
    prompt_id: str
    sheet: str
    range: str
    last_row: int


def _root(parts: Mapping[str, bytes], name: str) -> ET.Element:
    try:
        return ET.fromstring(parts[name])
    except KeyError as exc:
        raise ValueError(f"required OOXML part missing: {name}") from exc


def _xml(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _col_number(name: str) -> int:
    value = 0
    for char in name:
        value = value * 26 + ord(char) - 64
    return value


def _ref_parts(ref: str) -> Tuple[int, int]:
    match = CELL_RE.fullmatch(ref)
    if not match:
        raise ValueError(f"invalid cell reference: {ref}")
    return _col_number(match.group(1)), int(match.group(2))


def _sheet_map(parts: Mapping[str, bytes]) -> Tuple[ET.Element, Dict[str, str]]:
    workbook = _root(parts, "xl/workbook.xml")
    rels = _root(parts, "xl/_rels/workbook.xml.rels")
    targets = {rel.attrib["Id"]: rel.attrib.get("Target", "") for rel in rels}
    sheets: Dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        target = targets.get(sheet.attrib.get(f"{{{REL_NS}}}id", ""), "")
        if target.startswith("/"):
            part = target.lstrip("/")
        elif target.startswith("xl/"):
            part = target
        else:
            part = posixpath.normpath(posixpath.join("xl", target))
        sheets[sheet.attrib["name"]] = part
    return workbook, sheets


def _shared_strings(parts: Mapping[str, bytes]) -> Sequence[str]:
    if "xl/sharedStrings.xml" not in parts:
        return ()
    root = _root(parts, "xl/sharedStrings.xml")
    return tuple(
        "".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
        for item in root.findall("m:si", NS)
    )


def _text(cell: ET.Element, shared: Sequence[str]) -> str:
    formula = cell.find("m:f", NS)
    if formula is not None and formula.text:
        return formula.text
    if cell.attrib.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return shared[int(value.text)]
        except (IndexError, ValueError):
            return ""
    return value.text


def _ensure_row(sheet: ET.Element, number: int) -> ET.Element:
    data = sheet.find("m:sheetData", NS)
    if data is None:
        data = ET.SubElement(sheet, f"{{{MAIN_NS}}}sheetData")
    for row in data.findall("m:row", NS):
        if int(row.attrib.get("r", "0")) == number:
            return row
    new = ET.Element(f"{{{MAIN_NS}}}row", {"r": str(number)})
    for index, row in enumerate(list(data)):
        if int(row.attrib.get("r", "0")) > number:
            data.insert(index, new)
            return new
    data.append(new)
    return new


def _ensure_cell(sheet: ET.Element, ref: str) -> ET.Element:
    existing = sheet.find(f".//m:c[@r='{ref}']", NS)
    if existing is not None:
        return existing
    column, row_number = _ref_parts(ref)
    row = _ensure_row(sheet, row_number)
    cell = ET.Element(f"{{{MAIN_NS}}}c", {"r": ref})
    for index, other in enumerate(list(row)):
        other_ref = other.attrib.get("r")
        if other_ref and _ref_parts(other_ref)[0] > column:
            row.insert(index, cell)
            return cell
    row.append(cell)
    return cell


def _set_formula(sheet: ET.Element, ref: str, target: str, label: str) -> None:
    cell = _ensure_cell(sheet, ref)
    for child in list(cell):
        if child.tag in {f"{{{MAIN_NS}}}f", f"{{{MAIN_NS}}}v", f"{{{MAIN_NS}}}is"}:
            cell.remove(child)
    cell.attrib["t"] = "str"
    ET.SubElement(cell, f"{{{MAIN_NS}}}f").text = f'HYPERLINK("#{target}","{label}")'


def _prompt_last_row(sheet: ET.Element, shared: Sequence[str]) -> int:
    rows = []
    for cell in sheet.findall(".//m:c", NS):
        ref = cell.attrib.get("r", "")
        match = CELL_RE.fullmatch(ref)
        if match and match.group(1) == "A" and _text(cell, shared):
            rows.append(int(match.group(2)))
    if not rows or 1 not in rows:
        raise ValueError("prompt sheet must start with a populated A1")
    return max(rows)


def _set_tab_color(sheet: ET.Element) -> None:
    sheet_pr = sheet.find("m:sheetPr", NS)
    if sheet_pr is None:
        sheet_pr = ET.Element(f"{{{MAIN_NS}}}sheetPr")
        sheet.insert(0, sheet_pr)
    for child in list(sheet_pr):
        if child.tag == f"{{{MAIN_NS}}}tabColor":
            sheet_pr.remove(child)
    sheet_pr.insert(0, ET.Element(f"{{{MAIN_NS}}}tabColor", {"rgb": CREAM_TAB_COLOR}))


def _protect(sheet: ET.Element) -> None:
    old = sheet.find("m:sheetProtection", NS)
    if old is not None:
        sheet.remove(old)
    protection = ET.Element(f"{{{MAIN_NS}}}sheetProtection", {
        "sheet": "1", "objects": "1", "scenarios": "1", "formatCells": "1",
        "formatColumns": "1", "formatRows": "1", "insertColumns": "1",
        "insertRows": "1", "insertHyperlinks": "1", "deleteColumns": "1",
        "deleteRows": "1", "sort": "1", "autoFilter": "1", "pivotTables": "1",
    })
    data = sheet.find("m:sheetData", NS)
    sheet.insert(list(sheet).index(data) + 1 if data is not None else len(sheet), protection)


def _unlocked_style_factory(styles: ET.Element):
    xfs = styles.find("m:cellXfs", NS)
    if xfs is None or not list(xfs):
        raise ValueError("styles.xml has no cellXfs")
    cache: Dict[int, int] = {}

    def unlocked(style_id: int) -> int:
        if style_id in cache:
            return cache[style_id]
        current = list(xfs)
        if not 0 <= style_id < len(current):
            raise ValueError(f"invalid style id: {style_id}")
        clone = copy.deepcopy(current[style_id])
        clone.attrib["applyProtection"] = "1"
        protection = clone.find("m:protection", NS)
        if protection is None:
            protection = ET.SubElement(clone, f"{{{MAIN_NS}}}protection")
        protection.attrib["locked"] = "0"
        xfs.append(clone)
        xfs.attrib["count"] = str(len(list(xfs)))
        cache[style_id] = len(list(xfs)) - 1
        return cache[style_id]

    return unlocked


def _unlock_opportunity(sheet: ET.Element, styles: ET.Element) -> None:
    unlocked = _unlocked_style_factory(styles)
    row_style = unlocked(0)
    for number in range(1, 101):
        row = _ensure_row(sheet, number)
        row.attrib.update({"s": str(row_style), "customFormat": "1"})
    for cell in sheet.findall(".//m:c", NS):
        column, row = _ref_parts(cell.attrib["r"])
        if column <= 18 and row <= 100:
            cell.attrib["s"] = str(unlocked(int(cell.attrib.get("s", "0"))))


def _validate_p02(sheet: ET.Element, shared: Sequence[str]) -> None:
    text = "\n".join(_text(cell, shared) for cell in sheet.findall(".//m:c", NS) if cell.attrib.get("r", "").startswith("A"))
    required = (
        "HARNESS BUILD OWNERSHIP",
        "Do not stop at describing, classifying, or mapping the harness.",
        "commit coherent changes",
        "push normally",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise ValueError(f"P02 does not assign executable harness construction: {missing}")


def finalize_workbook(source: Path, output: Path, gnhf_build_prompt: str = "P39") -> Tuple[PromptRange, ...]:
    if gnhf_build_prompt not in PROMPT_IDS:
        raise ValueError(f"unknown GNHF build prompt: {gnhf_build_prompt}")
    with zipfile.ZipFile(source) as archive:
        parts: MutableMapping[str, bytes] = {name: archive.read(name) for name in archive.namelist()}
    workbook, sheets = _sheet_map(parts)
    required = {PROMPT_LIBRARY, OPPORTUNITY_DISCOVERY, *(f"{pid}{PROMPT_SUFFIX}" for pid in PROMPT_IDS)}
    missing = sorted(required - set(sheets))
    if missing:
        raise ValueError(f"source workbook is missing V33 sheets: {missing}")

    shared = _shared_strings(parts)
    roots = {name: _root(parts, part) for name, part in sheets.items()}
    ranges = []
    for prompt_id in PROMPT_IDS:
        name = f"{prompt_id}{PROMPT_SUFFIX}"
        last = _prompt_last_row(roots[name], shared)
        ranges.append(PromptRange(prompt_id, name, f"A1:A{last}", last))
    _validate_p02(roots["P02_COPY_SAFE"], shared)

    library = roots[PROMPT_LIBRARY]
    last_library_row = max(_ref_parts(cell.attrib["r"])[1] for cell in library.findall(".//m:c", NS) if cell.attrib.get("r"))
    _set_formula(library, "A1", f"'{PROMPT_LIBRARY}'!A{last_library_row}", "↓ Bottom")
    _set_formula(library, "P1", f"'{PROMPT_LIBRARY}'!P{last_library_row}", "↓ Bottom")
    _set_formula(library, f"A{last_library_row}", f"'{PROMPT_LIBRARY}'!A1", "↑ Top")
    _set_formula(library, f"P{last_library_row}", f"'{PROMPT_LIBRARY}'!P1", "↑ Top")

    for item in ranges:
        row = int(item.prompt_id[1:]) + 2
        _set_formula(library, f"C{row}", f"'{item.sheet}'!{item.range}", item.prompt_id)
        target = f"'{PROMPT_LIBRARY}'!A{row}:P{row}"
        prompt = roots[item.sheet]
        for ref, label in (
            ("B1", f"← Prompt Library · {item.prompt_id}"),
            ("E1", f"{item.prompt_id} · Prompt Library →"),
            (f"B{item.last_row}", f"← Prompt Library · {item.prompt_id}"),
            (f"E{item.last_row}", f"{item.prompt_id} · Prompt Library →"),
        ):
            _set_formula(prompt, ref, target, label)

    cream_tabs = (PROMPT_LIBRARY, OPPORTUNITY_DISCOVERY, "P07_COPY_SAFE", f"{gnhf_build_prompt}{PROMPT_SUFFIX}")
    for name in cream_tabs:
        _set_tab_color(roots[name])

    styles = _root(parts, "xl/styles.xml")
    _unlock_opportunity(roots[OPPORTUNITY_DISCOVERY], styles)
    for root in roots.values():
        _protect(root)
    protection = workbook.find("m:workbookProtection", NS)
    if protection is None:
        protection = ET.Element(f"{{{MAIN_NS}}}workbookProtection")
        sheets_node = workbook.find("m:sheets", NS)
        workbook.insert(list(workbook).index(sheets_node), protection)
    protection.attrib["lockStructure"] = "1"
    calc = workbook.find("m:calcPr", NS)
    if calc is None:
        calc = ET.SubElement(workbook, f"{{{MAIN_NS}}}calcPr")
    calc.attrib.update({"calcMode": "auto", "fullCalcOnLoad": "1", "forceFullCalc": "1"})

    parts["xl/workbook.xml"] = _xml(workbook)
    parts["xl/styles.xml"] = _xml(styles)
    for name, part in sheets.items():
        parts[part] = _xml(roots[name])
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(parts):
            archive.writestr(name, parts[name])
    return tuple(ranges)
