"""Generate the package-preserving AI Harness Prompt Kit V39 artifact.

V39 starts from the operator-accepted V38 workbook and appends five standard-AI,
local-first prompt tabs (P45-P49). It does not run the accepted workbook through
Excel, LibreOffice, openpyxl, or another whole-workbook serializer.

The generator also codifies the prompt-surface boundary:

* P26-P36 are Goodnight, Have Fun (GNHF) PowerShell launch prompts.
* P45-P49 are standard AI prompts and must never be shaped as GNHF commands.
* The GNHF and standard-AI prompt ranges remain contiguous and separate.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import posixpath
import re
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
APP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
NS = {"m": MAIN_NS, "r": REL_NS, "pr": PKG_REL_NS, "ct": CONTENT_TYPES_NS, "app": APP_NS, "vt": VT_NS}

ARTIFACT_NAME = "AI_Harness_Prompt_Kit_v39"
DEFAULT_OUTPUT_DIR = "Outputs/prompt_kit_v39"
DEFAULT_SPEC_PATH = Path("configs/prompt_kit/v39_local_first_prompts.json")
SOURCE_PROMPT_COUNT = 45
NEW_PROMPT_IDS = tuple(f"P{number:02d}" for number in range(45, 50))
GNHF_PROMPT_IDS = tuple(f"P{number:02d}" for number in range(26, 37))
ADVANCED_STANDARD_AI_IDS = tuple(f"P{number:02d}" for number in range(37, 50))
PROMPT_SHEET_RE = re.compile(r"^P\d{2,}_COPY_SAFE$")
LIBRARY_FORMULA_RE = re.compile(
    r'^HYPERLINK\("#\'(?P<sheet>P\d{2,}_COPY_SAFE)\'!(?P<range>A1:A[1-9]\d*)","(?P<label>[^"]+)"\)$',
    re.IGNORECASE,
)
CELL_RE = re.compile(r"^([A-Z]+)([1-9]\d*)$")
SHEET_PART_RE = re.compile(r"^xl/worksheets/sheet(\d+)\.xml$")

LIBRARY_FIELDS = {
    "Seq": "seq",
    "Prompt ID": "prompt_id",
    "Prompt Type": "prompt_type",
    "Prompt Class": "prompt_class",
    "Sprint Path Role": "sprint_path_role",
    "Use For Progress?": "use_for_progress",
    "Prompt Name": "prompt_name",
    "Use This When": "use_this_when",
    "Inspect First": "inspect_first",
    "Expected Output": "expected_output",
    "Next Step": "next_step",
    "Proof / Acceptance Gate": "proof_gate",
    "Color": "color",
    "Copy-Safe Sheet": "sheet_name",
}


@dataclass(frozen=True)
class V39ContractReport:
    path: str
    valid: bool
    prompt_count: int
    new_prompt_ids: tuple[str, ...]
    standard_ai_sections: tuple[tuple[str, ...], ...]
    gnhf_section: tuple[str, ...]
    directory_gate_prompts: tuple[str, ...]
    zero_token_prompts: tuple[str, ...]
    changed_parts: tuple[str, ...]
    findings: tuple[dict, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class WorkbookParts:
    infos: tuple[zipfile.ZipInfo, ...]
    order: tuple[str, ...]
    parts: Mapping[str, bytes]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str) -> PurePosixPath:
    member = PurePosixPath(name.replace("\\", "/"))
    if member.is_absolute() or not member.parts or any(part in {"", ".", ".."} for part in member.parts):
        raise ValueError(f"unsafe bundle member path: {name!r}")
    return member


def _source_workbook(source: Path, temp_dir: Path) -> tuple[Path, dict[str, bytes]]:
    if source.suffix.lower() == ".xlsx":
        return source, {}
    if source.suffix.lower() != ".zip":
        raise ValueError("source must be an operator-accepted V38 .xlsx workbook or a bundle containing exactly one workbook")
    with zipfile.ZipFile(source) as archive:
        members = {
            str(_safe_member(info.filename)): info
            for info in archive.infolist()
            if not info.is_dir()
        }
        workbook_names = [name for name in members if name.lower().endswith(".xlsx")]
        if len(workbook_names) != 1:
            raise ValueError(f"source bundle must contain exactly one workbook; found {sorted(workbook_names)}")
        workbook_name = workbook_names[0]
        workbook = temp_dir / Path(workbook_name).name
        workbook.write_bytes(archive.read(members[workbook_name]))
        extras = {
            name: archive.read(info)
            for name, info in members.items()
            if name != workbook_name
        }
    return workbook, extras


def _read_workbook(path: Path) -> WorkbookParts:
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"invalid ZIP member: {bad_member}")
        infos = tuple(copy.copy(info) for info in archive.infolist())
        order = tuple(info.filename for info in infos)
        if len(order) != len(set(order)):
            raise ValueError("workbook contains duplicate ZIP member names")
        parts = {name: archive.read(name) for name in order}
    required = {"[Content_Types].xml", "xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
    missing = sorted(required - set(parts))
    if missing:
        raise ValueError(f"workbook is missing required package parts: {missing}")
    return WorkbookParts(infos, order, parts)


def _root(data: bytes, part: str) -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML part {part}: {exc}") from exc


def _xml(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _column_number(column: str) -> int:
    result = 0
    for char in column:
        result = result * 26 + ord(char) - 64
    return result


def _column_name(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell_parts(ref: str) -> tuple[str, int]:
    match = CELL_RE.fullmatch(ref)
    if not match:
        raise ValueError(f"invalid cell reference: {ref}")
    return match.group(1), int(match.group(2))


def _sheet_map(parts: Mapping[str, bytes]) -> tuple[list[str], dict[str, str], dict[str, int], dict[str, str]]:
    workbook = _root(parts["xl/workbook.xml"], "xl/workbook.xml")
    rels = _root(parts["xl/_rels/workbook.xml.rels"], "xl/_rels/workbook.xml.rels")
    targets = {rel.attrib["Id"]: rel.attrib.get("Target", "") for rel in rels}
    order: list[str] = []
    mapping: dict[str, str] = {}
    sheet_ids: dict[str, int] = {}
    relationship_ids: dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        name = sheet.attrib["name"]
        rid = sheet.attrib.get(f"{{{REL_NS}}}id", "")
        target = targets.get(rid, "")
        if target.startswith("/"):
            part = target.lstrip("/")
        elif target.startswith("xl/"):
            part = target
        else:
            part = posixpath.normpath(posixpath.join("xl", target))
        if not target or part not in parts:
            raise ValueError(f"worksheet relationship is invalid for {name}: {target!r}")
        order.append(name)
        mapping[name] = part
        sheet_ids[name] = int(sheet.attrib["sheetId"])
        relationship_ids[name] = rid
    return order, mapping, sheet_ids, relationship_ids


def _shared_strings(parts: Mapping[str, bytes]) -> tuple[str, ...]:
    data = parts.get("xl/sharedStrings.xml")
    if data is None:
        return ()
    root = _root(data, "xl/sharedStrings.xml")
    return tuple(
        "".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
        for item in root.findall("m:si", NS)
    )


def _cell_display(cell: Optional[ET.Element], shared: Sequence[str]) -> str:
    if cell is None:
        return ""
    if cell.attrib.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return shared[int(value.text)]
        except (ValueError, IndexError):
            return ""
    return value.text


def _formula(cell: Optional[ET.Element]) -> str:
    if cell is None:
        return ""
    node = cell.find("m:f", NS)
    return node.text or "" if node is not None else ""


def _cells(root: ET.Element) -> dict[str, ET.Element]:
    return {
        cell.attrib["r"]: cell
        for cell in root.findall(".//m:c", NS)
        if cell.attrib.get("r")
    }


def _row_number(row: ET.Element) -> int:
    return int(row.attrib.get("r", "0"))


def _max_row(root: ET.Element) -> int:
    return max((_row_number(row) for row in root.findall("m:sheetData/m:row", NS)), default=0)


def _new_text_cell(ref: str, style: Optional[str], text: str) -> ET.Element:
    attrs = {"r": ref, "t": "str"}
    if style is not None:
        attrs["s"] = style
    cell = ET.Element(f"{{{MAIN_NS}}}c", attrs)
    ET.SubElement(cell, f"{{{MAIN_NS}}}v").text = text
    return cell


def _new_formula_cell(ref: str, style: Optional[str], formula: str, cached: str) -> ET.Element:
    attrs = {"r": ref, "t": "str"}
    if style is not None:
        attrs["s"] = style
    cell = ET.Element(f"{{{MAIN_NS}}}c", attrs)
    ET.SubElement(cell, f"{{{MAIN_NS}}}f").text = formula
    ET.SubElement(cell, f"{{{MAIN_NS}}}v").text = cached
    return cell


def _prompt_payload(parts: Mapping[str, bytes], sheet_part: str, last_row: int) -> list[str]:
    root = _root(parts[sheet_part], sheet_part)
    shared = _shared_strings(parts)
    cells = _cells(root)
    return [_cell_display(cells.get(f"A{row}"), shared) for row in range(1, last_row + 1)]


def _load_spec(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("V39 prompt spec requires schema_version 1")
    prompts = payload.get("new_prompts")
    if not isinstance(prompts, list) or [item.get("prompt_id") for item in prompts] != list(NEW_PROMPT_IDS):
        raise ValueError(f"V39 prompt spec must define exactly {list(NEW_PROMPT_IDS)} in order")
    sections = {section["id"]: section for section in payload.get("sections", [])}
    if sections.get("gnhf_launch", {}).get("prompt_ids") != list(GNHF_PROMPT_IDS):
        raise ValueError("V39 taxonomy must reserve P26-P36 as the contiguous GNHF launch section")
    if sections.get("standard_ai_advanced_local", {}).get("prompt_ids") != list(ADVANCED_STANDARD_AI_IDS):
        raise ValueError("V39 taxonomy must reserve P37-P49 as the contiguous advanced standard-AI section")
    for item in prompts:
        lines = item.get("lines")
        if item.get("surface") != "standard_ai" or item.get("section") != "standard_ai_advanced_local":
            raise ValueError(f"{item.get('prompt_id')} must be a standard-AI prompt in the advanced local section")
        if not isinstance(lines, list) or not lines or any(not isinstance(line, str) for line in lines):
            raise ValueError(f"{item.get('prompt_id')} requires a non-empty string line list")
        text = "\n".join(lines)
        if not text.startswith("PROMPT SURFACE: STANDARD AI."):
            raise ValueError(f"{item['prompt_id']} must declare its standard-AI surface on the first line")
        if "DIRECTORY GATE" not in text:
            raise ValueError(f"{item['prompt_id']} must contain a directory gate")
        if re.search(r"(?m)^\s*gnhf\s+`", text) or "--max-tokens" in text or "--max-iterations" in text:
            raise ValueError(f"{item['prompt_id']} is a standard-AI prompt but contains GNHF command markers")
    return payload


def _find_library_rows(parts: Mapping[str, bytes], library_part: str) -> tuple[ET.Element, dict[str, int], dict[str, int], int, str]:
    shared = _shared_strings(parts)
    root = _root(parts[library_part], library_part)
    cells = _cells(root)
    header_columns: dict[str, int] = {}
    for ref, cell in cells.items():
        column, row = _cell_parts(ref)
        if row == 1:
            header_columns[_cell_display(cell, shared)] = _column_number(column)
    missing = sorted(set(LIBRARY_FIELDS) - set(header_columns))
    if missing:
        raise ValueError(f"Prompt Library is missing required headers: {missing}")
    prompt_rows: dict[str, int] = {}
    for ref, cell in cells.items():
        column, row = _cell_parts(ref)
        if column != _column_name(header_columns["Prompt ID"]):
            continue
        match = LIBRARY_FORMULA_RE.fullmatch(_formula(cell))
        if match:
            prompt_id = match.group("sheet").removesuffix("_COPY_SAFE").upper()
            prompt_rows[prompt_id] = row
    if "P44" not in prompt_rows:
        raise ValueError("Prompt Library does not contain the required P44 template row")
    template_row = next(
        row for row in root.findall("m:sheetData/m:row", NS) if _row_number(row) == prompt_rows["P44"]
    )
    template_cells = {_cell_parts(cell.attrib["r"])[0]: cell for cell in template_row.findall("m:c", NS)}
    color_col = _column_name(header_columns["Color"])
    inherited_color = _cell_display(template_cells.get(color_col), shared)
    if not inherited_color:
        raise ValueError("P44 Prompt Library row has no color label to inherit")
    return root, header_columns, prompt_rows, _max_row(root), inherited_color


def _append_library_rows(
    root: ET.Element,
    header_columns: Mapping[str, int],
    prompt_rows: Mapping[str, int],
    start_row: int,
    prompts: Sequence[Mapping[str, object]],
    inherited_color: str,
) -> tuple[dict[str, int], list[tuple[str, str, str]]]:
    sheet_data = root.find("m:sheetData", NS)
    if sheet_data is None:
        raise ValueError("Prompt Library has no sheetData")
    template_row = next(
        row for row in sheet_data.findall("m:row", NS) if _row_number(row) == prompt_rows["P44"]
    )
    template_cells = {_cell_parts(cell.attrib["r"])[0]: cell for cell in template_row.findall("m:c", NS)}
    new_rows: dict[str, int] = {}
    hyperlinks: list[tuple[str, str, str]] = []
    for offset, prompt in enumerate(prompts, start=1):
        prompt_id = str(prompt["prompt_id"])
        sheet_name = f"{prompt_id}_COPY_SAFE"
        prompt_range = f"A1:A{len(prompt['lines'])}"
        row_number = start_row + offset
        row_attrs = dict(template_row.attrib)
        row_attrs["r"] = str(row_number)
        row = ET.Element(f"{{{MAIN_NS}}}row", row_attrs)
        values = dict(prompt)
        values["sheet_name"] = sheet_name
        values["color"] = inherited_color
        for column_number in range(1, 17):
            column = _column_name(column_number)
            template = template_cells.get(column)
            style = template.attrib.get("s") if template is not None else None
            ref = f"{column}{row_number}"
            if column_number in (1, 16):
                row.append(_new_text_cell(ref, style, ""))
                continue
            header = next((name for name, number in header_columns.items() if number == column_number), None)
            if header is None:
                row.append(_new_text_cell(ref, style, ""))
                continue
            field = LIBRARY_FIELDS[header]
            if field == "prompt_id":
                formula = f'HYPERLINK("#\'{sheet_name}\'!{prompt_range}","{prompt_id}")'
                row.append(_new_formula_cell(ref, style, formula, prompt_id))
                hyperlinks.append((ref, f"'{sheet_name}'!{prompt_range}", prompt_id))
            elif field == "sheet_name":
                formula = f'HYPERLINK("#\'{sheet_name}\'!{prompt_range}","{sheet_name}")'
                row.append(_new_formula_cell(ref, style, formula, sheet_name))
                hyperlinks.append((ref, f"'{sheet_name}'!{prompt_range}", sheet_name))
            else:
                row.append(_new_text_cell(ref, style, str(values.get(field, ""))))
        sheet_data.append(row)
        new_rows[prompt_id] = row_number
    dimension = root.find("m:dimension", NS)
    if dimension is not None:
        dimension.attrib["ref"] = f"A1:P{start_row + len(prompts)}"
    auto_filter = root.find("m:autoFilter", NS)
    if auto_filter is not None and auto_filter.attrib.get("ref"):
        start = auto_filter.attrib["ref"].split(":", 1)[0]
        auto_filter.attrib["ref"] = f"{start}:P{start_row + len(prompts)}"
    return new_rows, hyperlinks


def _hyperlinks_element(root: ET.Element) -> ET.Element:
    element = root.find("m:hyperlinks", NS)
    if element is not None:
        return element
    element = ET.Element(f"{{{MAIN_NS}}}hyperlinks")
    children = list(root)
    before_tags = {
        f"{{{MAIN_NS}}}printOptions",
        f"{{{MAIN_NS}}}pageMargins",
        f"{{{MAIN_NS}}}pageSetup",
        f"{{{MAIN_NS}}}headerFooter",
        f"{{{MAIN_NS}}}rowBreaks",
        f"{{{MAIN_NS}}}colBreaks",
        f"{{{MAIN_NS}}}customProperties",
        f"{{{MAIN_NS}}}cellWatches",
        f"{{{MAIN_NS}}}ignoredErrors",
        f"{{{MAIN_NS}}}smartTags",
        f"{{{MAIN_NS}}}drawing",
        f"{{{MAIN_NS}}}legacyDrawing",
        f"{{{MAIN_NS}}}legacyDrawingHF",
        f"{{{MAIN_NS}}}picture",
        f"{{{MAIN_NS}}}oleObjects",
        f"{{{MAIN_NS}}}controls",
        f"{{{MAIN_NS}}}webPublishItems",
        f"{{{MAIN_NS}}}tableParts",
        f"{{{MAIN_NS}}}extLst",
    }
    index = next((index for index, child in enumerate(children) if child.tag in before_tags), len(children))
    root.insert(index, element)
    return element


def _append_hyperlinks(root: ET.Element, links: Iterable[tuple[str, str, str]]) -> None:
    container = _hyperlinks_element(root)
    existing = {item.attrib.get("ref", "") for item in container.findall("m:hyperlink", NS)}
    for ref, location, display in links:
        if ref in existing:
            raise ValueError(f"worksheet already contains hyperlink metadata for {ref}")
        ET.SubElement(
            container,
            f"{{{MAIN_NS}}}hyperlink",
            {"ref": ref, "location": location, "display": display},
        )
        existing.add(ref)


def _template_styles(template_root: ET.Element) -> tuple[dict[str, Optional[str]], dict[str, dict[str, str]], int]:
    cells = _cells(template_root)
    a_rows = sorted(_cell_parts(ref)[1] for ref in cells if _cell_parts(ref)[0] == "A")
    if not a_rows:
        raise ValueError("P44 template sheet has no column-A payload cells")
    last = max(a_rows)
    middle_cell = cells.get("A2") if cells.get("A2") is not None else cells.get("A1")
    styles = {
        "a_first": cells.get("A1").attrib.get("s") if cells.get("A1") is not None else None,
        "a_middle": middle_cell.attrib.get("s") if middle_cell is not None else None,
        "a_last": cells.get(f"A{last}").attrib.get("s") if cells.get(f"A{last}") is not None else None,
        "b_first": cells.get("B1").attrib.get("s") if cells.get("B1") is not None else None,
        "b_last": cells.get(f"B{last}").attrib.get("s") if cells.get(f"B{last}") is not None else None,
        "c_first": cells.get("C1").attrib.get("s") if cells.get("C1") is not None else None,
        "c_last": cells.get(f"C{last}").attrib.get("s") if cells.get(f"C{last}") is not None else None,
    }
    row_attrs: dict[str, dict[str, str]] = {}
    rows = {_row_number(row): row for row in template_root.findall("m:sheetData/m:row", NS)}
    row_attrs["first"] = dict(rows.get(1, ET.Element("row")).attrib)
    row_attrs["middle"] = dict(rows.get(2, rows.get(1, ET.Element("row"))).attrib)
    row_attrs["last"] = dict(rows.get(last, rows.get(1, ET.Element("row"))).attrib)
    return styles, row_attrs, last


def _replace_sheet_data(root: ET.Element, new_sheet_data: ET.Element) -> None:
    old = root.find("m:sheetData", NS)
    if old is None:
        raise ValueError("template sheet has no sheetData")
    index = list(root).index(old)
    root.remove(old)
    root.insert(index, new_sheet_data)


def _make_prompt_sheet(template: bytes, prompt: Mapping[str, object], library_row: int) -> bytes:
    root = _root(template, "P44 template worksheet")
    styles, row_attrs, _ = _template_styles(root)
    lines = [str(line) for line in prompt["lines"]]
    last_row = len(lines)
    if last_row < 2:
        raise ValueError(f"{prompt['prompt_id']} must contain at least two prompt rows")
    sheet_data = ET.Element(f"{{{MAIN_NS}}}sheetData")
    for row_number, text in enumerate(lines, start=1):
        position = "first" if row_number == 1 else "last" if row_number == last_row else "middle"
        attrs = dict(row_attrs[position])
        attrs["r"] = str(row_number)
        if "spans" in attrs:
            attrs["spans"] = "1:3"
        row = ET.Element(f"{{{MAIN_NS}}}row", attrs)
        a_style = styles["a_first"] if row_number == 1 else styles["a_last"] if row_number == last_row else styles["a_middle"]
        row.append(_new_text_cell(f"A{row_number}", a_style, text))
        if row_number in (1, last_row):
            b_style = styles["b_first"] if row_number == 1 else styles["b_last"]
            c_style = styles["c_first"] if row_number == 1 else styles["c_last"]
            back_formula = f'HYPERLINK("#\'Prompt_Library\'!A{library_row}:P{library_row}","Prompt Library")'
            row.append(_new_formula_cell(f"B{row_number}", b_style, back_formula, "Prompt Library"))
            prompt_range = f"A1:A{last_row}"
            copy_formula = f'HYPERLINK("#\'{prompt["prompt_id"]}_COPY_SAFE\'!{prompt_range}","Copy {prompt_range} only")'
            row.append(_new_formula_cell(f"C{row_number}", c_style, copy_formula, f"Copy {prompt_range} only"))
        sheet_data.append(row)
    _replace_sheet_data(root, sheet_data)
    dimension = root.find("m:dimension", NS)
    if dimension is None:
        dimension = ET.Element(f"{{{MAIN_NS}}}dimension", {"ref": f"A1:C{last_row}"})
        root.insert(0, dimension)
    else:
        dimension.attrib["ref"] = f"A1:C{last_row}"
    for sheet_view in root.findall("m:sheetViews/m:sheetView", NS):
        sheet_view.attrib.pop("tabSelected", None)
    for tag in ("mergeCells", "autoFilter", "conditionalFormatting", "dataValidations", "tableParts"):
        for item in list(root.findall(f"m:{tag}", NS)):
            root.remove(item)
    hyperlinks = _hyperlinks_element(root)
    hyperlinks.clear()
    for ref in ("C1", f"C{last_row}"):
        ET.SubElement(
            hyperlinks,
            f"{{{MAIN_NS}}}hyperlink",
            {"ref": ref, "location": "'Prompt_Library'!A1", "display": f"Copy A1:A{last_row} only"},
        )
    return _xml(root)


def _next_relationship_id(rels: ET.Element) -> int:
    values = []
    for item in rels:
        match = re.fullmatch(r"rId(\d+)", item.attrib.get("Id", ""))
        if match:
            values.append(int(match.group(1)))
    return max(values, default=0) + 1


def _next_sheet_part(parts: Mapping[str, bytes]) -> int:
    values = [int(match.group(1)) for name in parts if (match := SHEET_PART_RE.fullmatch(name))]
    return max(values, default=0) + 1


def _append_workbook_sheets(
    parts: MutableMapping[str, bytes],
    prompts: Sequence[Mapping[str, object]],
    prompt_xml: Mapping[str, bytes],
) -> tuple[dict[str, str], dict[str, int]]:
    workbook = _root(parts["xl/workbook.xml"], "xl/workbook.xml")
    rels = _root(parts["xl/_rels/workbook.xml.rels"], "xl/_rels/workbook.xml.rels")
    content_types = _root(parts["[Content_Types].xml"], "[Content_Types].xml")
    sheets = workbook.find("m:sheets", NS)
    if sheets is None:
        raise ValueError("workbook has no sheets collection")
    existing_names = {sheet.attrib["name"] for sheet in sheets}
    duplicate = sorted({f"{item['prompt_id']}_COPY_SAFE" for item in prompts} & existing_names)
    if duplicate:
        raise ValueError(f"V39 source already contains new prompt sheets: {duplicate}")
    next_rid = _next_relationship_id(rels)
    next_part = _next_sheet_part(parts)
    next_sheet_id = max((int(sheet.attrib["sheetId"]) for sheet in sheets), default=0) + 1
    created_parts: dict[str, str] = {}
    created_ids: dict[str, int] = {}
    for offset, prompt in enumerate(prompts):
        prompt_id = str(prompt["prompt_id"])
        name = f"{prompt_id}_COPY_SAFE"
        rid = f"rId{next_rid + offset}"
        part = f"xl/worksheets/sheet{next_part + offset}.xml"
        sheet_id = next_sheet_id + offset
        ET.SubElement(
            sheets,
            f"{{{MAIN_NS}}}sheet",
            {"name": name, "sheetId": str(sheet_id), f"{{{REL_NS}}}id": rid},
        )
        ET.SubElement(
            rels,
            f"{{{PKG_REL_NS}}}Relationship",
            {
                "Id": rid,
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
                "Target": f"worksheets/{Path(part).name}",
            },
        )
        ET.SubElement(
            content_types,
            f"{{{CONTENT_TYPES_NS}}}Override",
            {
                "PartName": f"/{part}",
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
            },
        )
        parts[part] = prompt_xml[prompt_id]
        created_parts[name] = part
        created_ids[name] = sheet_id
    parts["xl/workbook.xml"] = _xml(workbook)
    parts["xl/_rels/workbook.xml.rels"] = _xml(rels)
    parts["[Content_Types].xml"] = _xml(content_types)
    return created_parts, created_ids


def _update_app_properties(parts: MutableMapping[str, bytes], new_names: Sequence[str]) -> bool:
    part = "docProps/app.xml"
    if part not in parts:
        return False
    root = _root(parts[part], part)
    changed = False
    titles = root.find("app:TitlesOfParts/vt:vector", NS)
    if titles is not None:
        existing = [item.text or "" for item in titles.findall("vt:lpstr", NS)]
        for name in new_names:
            if name not in existing:
                ET.SubElement(titles, f"{{{VT_NS}}}lpstr").text = name
                existing.append(name)
                changed = True
        titles.attrib["size"] = str(len(existing))
    heading = root.find("app:HeadingPairs/vt:vector", NS)
    if heading is not None:
        variants = heading.findall("vt:variant", NS)
        for index, variant in enumerate(variants[:-1]):
            label = variant.find("vt:lpstr", NS)
            if label is not None and (label.text or "").lower() == "worksheets":
                count = variants[index + 1].find("vt:i4", NS)
                if count is not None:
                    count.text = str(int(count.text or "0") + len(new_names))
                    changed = True
                break
    if changed:
        parts[part] = _xml(root)
    return changed


def _formula_cells(parts: Mapping[str, bytes]) -> set[tuple[int, str]]:
    order, mapping, sheet_ids, _ = _sheet_map(parts)
    result: set[tuple[int, str]] = set()
    for name in order:
        root = _root(parts[mapping[name]], mapping[name])
        for cell in root.findall(".//m:c", NS):
            formula = cell.find("m:f", NS)
            if formula is not None and formula.text:
                result.add((sheet_ids[name], cell.attrib["r"]))
    return result


def _rebuild_calc_chain(parts: MutableMapping[str, bytes]) -> bool:
    part = "xl/calcChain.xml"
    if part not in parts:
        return False
    root = ET.Element(f"{{{MAIN_NS}}}calcChain")
    for sheet_id, ref in sorted(_formula_cells(parts), key=lambda item: (item[0], _cell_parts(item[1])[1], _column_number(_cell_parts(item[1])[0]))):
        ET.SubElement(root, f"{{{MAIN_NS}}}c", {"r": ref, "i": str(sheet_id)})
    parts[part] = _xml(root)
    return True


def _fixed_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o600 << 16
    return info


def _write_package(source: WorkbookParts, output: Path, parts: Mapping[str, bytes], new_parts: Sequence[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for info in source.infos:
            archive.writestr(info, parts[info.filename])
        for name in new_parts:
            archive.writestr(_fixed_info(name), parts[name])


def _prompt_rows_and_ranges(parts: Mapping[str, bytes]) -> tuple[dict[str, int], dict[str, str]]:
    _, mapping, _, _ = _sheet_map(parts)
    library_part = mapping.get("Prompt_Library")
    if not library_part:
        raise ValueError("missing Prompt_Library")
    root = _root(parts[library_part], library_part)
    rows: dict[str, int] = {}
    ranges: dict[str, str] = {}
    for cell in root.findall(".//m:c", NS):
        ref = cell.attrib.get("r", "")
        if not ref.startswith("C"):
            continue
        match = LIBRARY_FORMULA_RE.fullmatch(_formula(cell))
        if not match:
            continue
        prompt_id = match.group("sheet").removesuffix("_COPY_SAFE").upper()
        rows[prompt_id] = _cell_parts(ref)[1]
        ranges[prompt_id] = match.group("range").upper()
    return rows, ranges


def _consecutive(order: Sequence[str], names: Sequence[str]) -> bool:
    try:
        positions = [order.index(name) for name in names]
    except ValueError:
        return False
    return positions == list(range(positions[0], positions[0] + len(positions)))


def validate_v39(path: str | Path, spec_path: str | Path = DEFAULT_SPEC_PATH, changed_parts: Sequence[str] = ()) -> V39ContractReport:
    workbook = Path(path)
    findings: list[dict] = []
    spec = _load_spec(Path(spec_path))
    if not workbook.exists():
        findings.append({"rule": "file exists", "path": str(workbook)})
        return V39ContractReport(str(workbook), False, 0, (), (), GNHF_PROMPT_IDS, (), (), tuple(changed_parts), tuple(findings))
    prompt_sheets: list[str] = []
    directory_gate: list[str] = []
    zero_token: list[str] = []
    try:
        package = _read_workbook(workbook)
        parts = package.parts
        order, mapping, _, _ = _sheet_map(parts)
        prompt_sheets = [name for name in order if PROMPT_SHEET_RE.fullmatch(name)]
        expected_prompt_sheets = [f"P{number:02d}_COPY_SAFE" for number in range(50)]
        if prompt_sheets != expected_prompt_sheets:
            findings.append({"rule": "prompt tabs P00-P49 exact order", "expected": expected_prompt_sheets, "actual": prompt_sheets})
        if not _consecutive(order, [f"{prompt_id}_COPY_SAFE" for prompt_id in GNHF_PROMPT_IDS]):
            findings.append({"rule": "GNHF P26-P36 contiguous section"})
        if not _consecutive(order, [f"{prompt_id}_COPY_SAFE" for prompt_id in ADVANCED_STANDARD_AI_IDS]):
            findings.append({"rule": "advanced standard-AI P37-P49 contiguous section"})
        rows, ranges = _prompt_rows_and_ranges(parts)
        new_rows = [rows.get(prompt_id) for prompt_id in NEW_PROMPT_IDS]
        if None in new_rows or new_rows != list(range(new_rows[0], new_rows[0] + len(new_rows))):
            findings.append({"rule": "P45-P49 Prompt Library rows contiguous", "actual": new_rows})
        shared = _shared_strings(parts)
        for prompt_id in GNHF_PROMPT_IDS:
            prompt_range = ranges.get(prompt_id)
            part = mapping.get(f"{prompt_id}_COPY_SAFE")
            if not prompt_range or not part:
                findings.append({"rule": "GNHF prompt registered", "prompt": prompt_id})
                continue
            last = int(prompt_range.rsplit("A", 1)[-1])
            payload = "\n".join(_prompt_payload(parts, part, last)).strip()
            if not payload.startswith("gnhf `"):
                findings.append({"rule": "GNHF prompt starts with gnhf", "prompt": prompt_id, "actual_start": payload[:40]})
        library_root = _root(parts[mapping["Prompt_Library"]], mapping["Prompt_Library"])
        library_cells = _cells(library_root)
        for prompt in spec["new_prompts"]:
            prompt_id = prompt["prompt_id"]
            prompt_range = ranges.get(prompt_id)
            part = mapping.get(f"{prompt_id}_COPY_SAFE")
            if not prompt_range or not part:
                findings.append({"rule": "new prompt registered", "prompt": prompt_id})
                continue
            last = int(prompt_range.rsplit("A", 1)[-1])
            payload = "\n".join(_prompt_payload(parts, part, last))
            if payload != "\n".join(prompt["lines"]):
                findings.append({"rule": "new prompt payload exact", "prompt": prompt_id})
            if not payload.startswith("PROMPT SURFACE: STANDARD AI."):
                findings.append({"rule": "standard-AI surface declaration", "prompt": prompt_id})
            if re.search(r"(?m)^\s*gnhf\s+`", payload) or "--max-tokens" in payload or "--max-iterations" in payload:
                findings.append({"rule": "standard AI must not contain GNHF command markers", "prompt": prompt_id})
            if "DIRECTORY GATE" in payload:
                directory_gate.append(prompt_id)
            else:
                findings.append({"rule": "directory gate present", "prompt": prompt_id})
            lowered = payload.lower()
            if "no model, api, provider, or coding-agent tokens" in lowered or "zero-token" in lowered:
                zero_token.append(prompt_id)
            row = rows.get(prompt_id)
            if row is not None:
                prompt_class = _cell_display(library_cells.get(f"E{row}"), shared)
                if "STANDARD AI" not in prompt_class or "GNHF" in prompt_class:
                    findings.append({"rule": "Prompt Library class separates standard AI from GNHF", "prompt": prompt_id, "actual": prompt_class})
            root = _root(parts[part], part)
            cells = _cells(root)
            expected_formula = f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A{last}","Copy A1:A{last} only")'
            for ref in ("C1", f"C{last}"):
                if _formula(cells.get(ref)) != expected_formula:
                    findings.append({"rule": "exact prompt-range copy link", "prompt": prompt_id, "cell": ref})
            links = {item.attrib.get("ref"): item.attrib.get("location") for item in root.findall("m:hyperlinks/m:hyperlink", NS)}
            for ref in ("C1", f"C{last}"):
                if links.get(ref) != "'Prompt_Library'!A1":
                    findings.append({"rule": "Prompt Library backlink metadata", "prompt": prompt_id, "cell": ref, "actual": links.get(ref)})
        if "P46" not in zero_token:
            findings.append({"rule": "P46 explicit zero-token boundary"})
        if "P47" not in directory_gate or "P48" not in directory_gate:
            findings.append({"rule": "factoring prompts enforce directory gate"})
        formulas = _formula_cells(parts)
        if "xl/calcChain.xml" in parts:
            chain = _root(parts["xl/calcChain.xml"], "xl/calcChain.xml")
            chain_cells = {(int(item.attrib["i"]), item.attrib["r"]) for item in chain.findall("m:c", NS)}
            if chain_cells != formulas:
                findings.append({"rule": "calcChain exact formula-cell match", "missing": sorted(formulas - chain_cells)[:10], "stale": sorted(chain_cells - formulas)[:10]})
    except (ValueError, KeyError, IndexError, zipfile.BadZipFile, ET.ParseError) as exc:
        findings.append({"rule": "package readable", "error": str(exc)})
    return V39ContractReport(
        path=str(workbook.resolve()),
        valid=not findings,
        prompt_count=len(prompt_sheets),
        new_prompt_ids=NEW_PROMPT_IDS,
        standard_ai_sections=(tuple(f"P{number:02d}" for number in range(26)), ADVANCED_STANDARD_AI_IDS),
        gnhf_section=GNHF_PROMPT_IDS,
        directory_gate_prompts=tuple(directory_gate),
        zero_token_prompts=tuple(zero_token),
        changed_parts=tuple(changed_parts),
        findings=tuple(findings),
    )


def generate_v39(
    source: Path,
    output_dir: Path,
    *,
    spec_path: Path = DEFAULT_SPEC_PATH,
    expected_source_prompt_count: int = SOURCE_PROMPT_COUNT,
) -> dict:
    source = source.resolve()
    output_dir = output_dir.resolve()
    spec_path = spec_path.resolve()
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    if not spec_path.exists():
        raise FileNotFoundError(spec_path)
    spec = _load_spec(spec_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prompt-kit-v39-") as temporary:
        source_workbook, extras = _source_workbook(source, Path(temporary))
        source_workbook_hash_before = _sha256(source_workbook)
        package = _read_workbook(source_workbook)
        parts = dict(package.parts)
        order, mapping, _, _ = _sheet_map(parts)
        referenced_worksheets = set(mapping.values())
        package_worksheets = {name for name in parts if SHEET_PART_RE.fullmatch(name)}
        orphan_worksheets = sorted(package_worksheets - referenced_worksheets)
        if orphan_worksheets:
            raise ValueError(f"V39 source contains unreferenced worksheet parts outside the exact V38 floor: {orphan_worksheets}")
        prompt_sheets = [name for name in order if PROMPT_SHEET_RE.fullmatch(name)]
        if prompt_sheets != [f"P{number:02d}_COPY_SAFE" for number in range(expected_source_prompt_count)]:
            raise ValueError(
                f"V39 requires an exact P00-P{expected_source_prompt_count - 1:02d} V38 prompt floor; discovered {prompt_sheets}"
            )
        library_part = mapping.get("Prompt_Library")
        template_part = mapping.get("P44_COPY_SAFE")
        if not library_part or not template_part:
            raise ValueError("V39 source must contain Prompt_Library and P44_COPY_SAFE")
        library_root, header_columns, prompt_rows, max_library_row, inherited_color = _find_library_rows(parts, library_part)
        new_library_rows, library_links = _append_library_rows(
            library_root,
            header_columns,
            prompt_rows,
            max_library_row,
            spec["new_prompts"],
            inherited_color,
        )
        _append_hyperlinks(library_root, library_links)
        parts[library_part] = _xml(library_root)
        prompt_xml = {
            item["prompt_id"]: _make_prompt_sheet(parts[template_part], item, new_library_rows[item["prompt_id"]])
            for item in spec["new_prompts"]
        }
        created_parts, _ = _append_workbook_sheets(parts, spec["new_prompts"], prompt_xml)
        app_changed = _update_app_properties(parts, list(created_parts))
        calc_changed = _rebuild_calc_chain(parts)
        changed_existing = {
            "[Content_Types].xml",
            "xl/workbook.xml",
            "xl/_rels/workbook.xml.rels",
            library_part,
        }
        if app_changed:
            changed_existing.add("docProps/app.xml")
        if calc_changed:
            changed_existing.add("xl/calcChain.xml")
        new_part_names = list(created_parts.values())
        workbook = output_dir / f"{ARTIFACT_NAME}.xlsx"
        if workbook.resolve() == source_workbook.resolve():
            raise ValueError("V39 output must not overwrite the accepted V38 source workbook")
        _write_package(package, workbook, parts, new_part_names)
        if _sha256(source_workbook) != source_workbook_hash_before:
            raise ValueError("V39 generation modified the accepted V38 source workbook")
        changed_parts = tuple(sorted(changed_existing | set(new_part_names)))
        report = validate_v39(workbook, spec_path, changed_parts)
        if not report.valid:
            raise ValueError(f"V39 contract failed: {list(report.findings)[:5]}")
        deterministic = Path(temporary) / f"{ARTIFACT_NAME}-deterministic.xlsx"
        second_parts = dict(package.parts)
        second_library_root, second_headers, second_rows, second_max, second_color = _find_library_rows(second_parts, library_part)
        second_new_rows, second_links = _append_library_rows(
            second_library_root, second_headers, second_rows, second_max, spec["new_prompts"], second_color
        )
        _append_hyperlinks(second_library_root, second_links)
        second_parts[library_part] = _xml(second_library_root)
        second_prompt_xml = {
            item["prompt_id"]: _make_prompt_sheet(second_parts[template_part], item, second_new_rows[item["prompt_id"]])
            for item in spec["new_prompts"]
        }
        second_created, _ = _append_workbook_sheets(second_parts, spec["new_prompts"], second_prompt_xml)
        _update_app_properties(second_parts, list(second_created))
        _rebuild_calc_chain(second_parts)
        _write_package(package, deterministic, second_parts, list(second_created.values()))
        if workbook.read_bytes() != deterministic.read_bytes():
            raise ValueError("V39 generation is not byte-deterministic for identical source and prompt spec")
        manifest_path = output_dir / f"{ARTIFACT_NAME}_manifest.json"
        bundle_path = output_dir / f"{ARTIFACT_NAME}_bundle.zip"
        manifest = {
            "schema_version": 1,
            "artifact": ARTIFACT_NAME,
            "generator": "triage.prompt_kit_v39_generator",
            "source_authority": spec["source_authority"],
            "source": str(source),
            "source_sha256": _sha256(source),
            "source_workbook_sha256": _sha256(source_workbook),
            "workbook": str(workbook),
            "workbook_sha256": _sha256(workbook),
            "bundle": str(bundle_path),
            "new_prompt_ids": list(NEW_PROMPT_IDS),
            "prompt_count": report.prompt_count,
            "prompt_surface_taxonomy": spec["prompt_surface_taxonomy"],
            "sections": spec["sections"],
            "directory_gate_prompts": list(report.directory_gate_prompts),
            "zero_token_prompts": list(report.zero_token_prompts),
            "changed_parts": list(changed_parts),
            "source_immutable": _sha256(source_workbook) == source_workbook_hash_before,
            "whole_workbook_serializer_forbidden": True,
            "byte_deterministic": True,
            "validation": report.to_dict(),
            "proof_level": "static_package_validation",
            "proof_ceiling": (
                "V39 prompt payloads, directory-first command guards, zero-token local-test guidance, "
                "repo-factoring prompts, prompt-surface separation, package structure, formulas, calculation "
                "chain, and deterministic generation. Excel for Web opening, clicking, selection, and operator "
                "acceptance remain a new field gate because V39 changes workbook topology."
            ),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(workbook, workbook.name)
            archive.write(manifest_path, manifest_path.name)
            for name, data in sorted(extras.items()):
                if not name.lower().endswith(".xlsx") and Path(name).name != manifest_path.name:
                    archive.writestr(name, data)
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    parser.add_argument("--spec", default=DEFAULT_SPEC_PATH, type=Path)
    parser.add_argument("--expected-source-prompt-count", default=SOURCE_PROMPT_COUNT, type=int)
    parser.add_argument("--validate-only", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.source and not args.validate_only:
        parser.error("--source is required unless --validate-only is used")
    try:
        if args.validate_only:
            result = validate_v39(args.validate_only, args.spec).to_dict()
            valid = result["valid"]
        else:
            result = generate_v39(
                args.source,
                args.out_dir,
                spec_path=args.spec,
                expected_source_prompt_count=args.expected_source_prompt_count,
            )
            valid = True
    except Exception as exc:
        print(f"V39 generation failed: {exc}")
        return 1
    print(json.dumps(result, indent=2) if args.json or args.validate_only else f"Generated: {result['workbook']}\nBundle: {result['bundle']}")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
