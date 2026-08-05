#!/usr/bin/env python3
"""Fail-closed OOXML validator for workbook colors, style ranges, and layout."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "configs" / "workbook_visual_integrity_v1.json"
REGISTRY_PATH = ROOT / "harness" / "workbook-visual-integrity" / "registry.json"

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
N = {"m": NS_MAIN, "r": NS_REL, "p": NS_PKG_REL}

CELL_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")
RANGE_RE = re.compile(r"^([A-Z]+[1-9][0-9]*):([A-Z]+[1-9][0-9]*)$")
SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm", ".xltx", ".xltm"}


class VisualValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class CellStyle:
    fill: str
    font: tuple[Any, ...]
    border: tuple[Any, ...]
    alignment: tuple[Any, ...]
    number_format: str

    def selected(self, attributes: Iterable[str]) -> tuple[Any, ...]:
        return tuple(getattr(self, attribute) for attribute in attributes)


@dataclass
class SheetData:
    name: str
    path: str
    cells: dict[str, dict[str, Any]]
    merges: tuple[str, ...]
    tab_color: str | None
    freeze_pane: str | None
    column_widths: dict[str, float]
    row_heights: dict[int, float]


@dataclass
class WorkbookData:
    path: Path
    sha256: str
    size_bytes: int
    sheet_order: list[str]
    sheets: dict[str, SheetData]
    styles: list[CellStyle]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VisualValidationError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VisualValidationError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualValidationError(f"JSON root must be an object: {path}")
    return value


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_color(value: str | None) -> str:
    if not value:
        return "00000000"
    cleaned = value.strip().upper().replace("#", "")
    if len(cleaned) == 6:
        cleaned = "FF" + cleaned
    if len(cleaned) != 8 or any(ch not in "0123456789ABCDEF" for ch in cleaned):
        return cleaned
    return cleaned


def _color_from_element(element: ET.Element | None) -> str:
    if element is None:
        return "00000000"
    if element.get("rgb"):
        return _normalize_color(element.get("rgb"))
    if element.get("indexed") is not None:
        return f"INDEXED:{element.get('indexed')}"
    if element.get("theme") is not None:
        return f"THEME:{element.get('theme')}:{element.get('tint', '0')}"
    if element.get("auto") is not None:
        return f"AUTO:{element.get('auto')}"
    return "00000000"


def _column_to_number(column: str) -> int:
    value = 0
    for char in column:
        value = value * 26 + (ord(char) - 64)
    return value


def _number_to_column(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _split_cell(address: str) -> tuple[int, int]:
    match = CELL_RE.fullmatch(address.upper())
    if not match:
        raise VisualValidationError(f"invalid cell address: {address}")
    return _column_to_number(match.group(1)), int(match.group(2))


def _parse_range(value: str) -> tuple[int, int, int, int]:
    match = RANGE_RE.fullmatch(value.upper())
    if not match:
        raise VisualValidationError(f"invalid range: {value}")
    c1, r1 = _split_cell(match.group(1))
    c2, r2 = _split_cell(match.group(2))
    if c1 > c2 or r1 > r2:
        raise VisualValidationError(f"range is reversed: {value}")
    return c1, r1, c2, r2


def _iter_range(value: str) -> Iterable[str]:
    c1, r1, c2, r2 = _parse_range(value)
    for row in range(r1, r2 + 1):
        for column in range(c1, c2 + 1):
            yield f"{_number_to_column(column)}{row}"


def _column_span(start: str, end: str) -> list[str]:
    left = _column_to_number(start)
    right = _column_to_number(end)
    if left > right:
        raise VisualValidationError(f"column span is reversed: {start}:{end}")
    return [_number_to_column(index) for index in range(left, right + 1)]


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.findall(".//m:t", N)) for item in root.findall("m:si", N)]


def _read_styles(archive: zipfile.ZipFile) -> list[CellStyle]:
    if "xl/styles.xml" not in archive.namelist():
        raise VisualValidationError("workbook is missing xl/styles.xml")
    root = ET.fromstring(archive.read("xl/styles.xml"))
    fonts: list[tuple[Any, ...]] = []
    fonts_root = root.find("m:fonts", N)
    if fonts_root is not None:
        for font in fonts_root.findall("m:font", N):
            name = font.find("m:name", N)
            size = font.find("m:sz", N)
            color = font.find("m:color", N)
            underline = font.find("m:u", N)
            fonts.append((
                name.get("val") if name is not None else "",
                size.get("val") if size is not None else "",
                font.find("m:b", N) is not None,
                font.find("m:i", N) is not None,
                underline.get("val", "single") if underline is not None else "",
                _color_from_element(color),
            ))
    if not fonts:
        fonts.append(("", "", False, False, "", "00000000"))

    fills: list[str] = []
    fills_root = root.find("m:fills", N)
    if fills_root is not None:
        for fill in fills_root.findall("m:fill", N):
            pattern = fill.find("m:patternFill", N)
            if pattern is None:
                fills.append("00000000")
                continue
            fg = pattern.find("m:fgColor", N)
            bg = pattern.find("m:bgColor", N)
            color = _color_from_element(fg)
            if color == "00000000" and pattern.get("patternType", "") == "solid":
                color = _color_from_element(bg)
            fills.append(color)
    if not fills:
        fills.append("00000000")

    borders: list[tuple[Any, ...]] = []
    borders_root = root.find("m:borders", N)
    if borders_root is not None:
        for border in borders_root.findall("m:border", N):
            sides: list[Any] = []
            for side_name in ("left", "right", "top", "bottom"):
                side = border.find(f"m:{side_name}", N)
                sides.append((
                    side.get("style", "") if side is not None else "",
                    _color_from_element(side.find("m:color", N)) if side is not None else "00000000",
                ))
            borders.append(tuple(sides))
    if not borders:
        borders.append(tuple())

    num_formats: dict[int, str] = {}
    num_fmts = root.find("m:numFmts", N)
    if num_fmts is not None:
        for item in num_fmts.findall("m:numFmt", N):
            try:
                num_formats[int(item.get("numFmtId", "0"))] = item.get("formatCode", "")
            except ValueError:
                continue

    styles: list[CellStyle] = []
    cell_xfs = root.find("m:cellXfs", N)
    if cell_xfs is None:
        raise VisualValidationError("styles.xml is missing cellXfs")
    for xf in cell_xfs.findall("m:xf", N):
        font_id = int(xf.get("fontId", "0"))
        fill_id = int(xf.get("fillId", "0"))
        border_id = int(xf.get("borderId", "0"))
        num_fmt_id = int(xf.get("numFmtId", "0"))
        alignment = xf.find("m:alignment", N)
        styles.append(CellStyle(
            fill=fills[fill_id] if fill_id < len(fills) else f"MISSING_FILL:{fill_id}",
            font=fonts[font_id] if font_id < len(fonts) else (f"MISSING_FONT:{font_id}",),
            border=borders[border_id] if border_id < len(borders) else (f"MISSING_BORDER:{border_id}",),
            alignment=tuple(sorted(alignment.attrib.items())) if alignment is not None else tuple(),
            number_format=num_formats.get(num_fmt_id, str(num_fmt_id)),
        ))
    if not styles:
        styles.append(CellStyle("00000000", fonts[0], borders[0], tuple(), "0"))
    return styles


def _resolve_target(base: str, target: str) -> str:
    normalized = target.replace("\\", "/")
    if normalized.startswith("/"):
        return normalized.lstrip("/")
    if normalized.startswith("xl/"):
        return normalized
    parts = base.split("/")[:-1]
    for segment in normalized.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if parts:
                parts.pop()
        else:
            parts.append(segment)
    return "/".join(parts)


def _read_workbook(path: Path) -> WorkbookData:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise VisualValidationError(f"unsupported workbook extension: {path.suffix}")
    if not path.is_file():
        raise VisualValidationError(f"workbook does not exist: {path}")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        for required in ("xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/styles.xml"):
            if required not in names:
                raise VisualValidationError(f"workbook is missing required package part: {required}")
        shared_strings = _read_shared_strings(archive)
        styles = _read_styles(archive)
        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
        rel_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relationships = {
            rel.get("Id", ""): _resolve_target("xl/workbook.xml", rel.get("Target", ""))
            for rel in rel_root.findall("p:Relationship", N)
        }
        sheet_order: list[str] = []
        sheets: dict[str, SheetData] = {}
        for sheet in workbook_root.findall("m:sheets/m:sheet", N):
            name = sheet.get("name", "")
            rid = sheet.get(f"{{{NS_REL}}}id", "")
            target = relationships.get(rid)
            if not target or target not in names:
                raise VisualValidationError(f"worksheet target is missing: {name} -> {target}")
            root = ET.fromstring(archive.read(target))
            cells: dict[str, dict[str, Any]] = {}
            for cell in root.findall(".//m:sheetData/m:row/m:c", N):
                address = cell.get("r", "").upper()
                if not address:
                    continue
                style_id = int(cell.get("s", "0"))
                cell_type = cell.get("t", "")
                formula_node = cell.find("m:f", N)
                value_node = cell.find("m:v", N)
                inline_node = cell.find("m:is", N)
                raw_value = value_node.text if value_node is not None else None
                if cell_type == "s" and raw_value is not None:
                    try:
                        value: Any = shared_strings[int(raw_value)]
                    except (ValueError, IndexError):
                        value = raw_value
                elif cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(node.text or "" for node in inline_node.findall(".//m:t", N))
                elif cell_type == "b" and raw_value is not None:
                    value = raw_value == "1"
                else:
                    value = raw_value
                cells[address] = {
                    "style_id": style_id,
                    "value": value,
                    "formula": formula_node.text if formula_node is not None else None,
                }
            merges_root = root.find("m:mergeCells", N)
            merges = tuple(sorted(merge.get("ref", "") for merge in merges_root.findall("m:mergeCell", N))) if merges_root is not None else tuple()
            sheet_pr = root.find("m:sheetPr", N)
            tab_color = _color_from_element(sheet_pr.find("m:tabColor", N)) if sheet_pr is not None else None
            if tab_color == "00000000":
                tab_color = None
            pane = root.find("m:sheetViews/m:sheetView/m:pane", N)
            freeze_pane = pane.get("topLeftCell") if pane is not None and pane.get("state") == "frozen" else None
            widths: dict[str, float] = {}
            cols_root = root.find("m:cols", N)
            if cols_root is not None:
                for col in cols_root.findall("m:col", N):
                    try:
                        minimum = int(col.get("min", "0")); maximum = int(col.get("max", "0")); width = float(col.get("width", "0"))
                    except ValueError:
                        continue
                    for index in range(minimum, maximum + 1):
                        widths[_number_to_column(index)] = width
            heights: dict[int, float] = {}
            for row in root.findall(".//m:sheetData/m:row", N):
                if row.get("ht") is not None:
                    try:
                        heights[int(row.get("r", "0"))] = float(row.get("ht", "0"))
                    except ValueError:
                        pass
            sheet_order.append(name)
            sheets[name] = SheetData(name, target, cells, merges, tab_color, freeze_pane, widths, heights)
    return WorkbookData(path, _sha256_file(path), path.stat().st_size, sheet_order, sheets, styles)


def _cell_style(workbook: WorkbookData, sheet: SheetData, address: str) -> CellStyle:
    item = sheet.cells.get(address)
    style_id = int(item.get("style_id", 0)) if item else 0
    if style_id >= len(workbook.styles):
        return CellStyle(f"MISSING_STYLE:{style_id}", tuple(), tuple(), tuple(), "")
    return workbook.styles[style_id]


def _cell_value(sheet: SheetData, address: str) -> Any:
    item = sheet.cells.get(address)
    return item.get("value") if item else None


def _resolve_role_fill(policy: dict[str, Any], profile: dict[str, Any], role: str) -> str:
    semantic = policy.get("semantic_roles", {})
    if role in semantic:
        return _normalize_color(str(semantic[role]["fill"]))
    artifact_specific = profile.get("artifact_specific_roles", {})
    if role in artifact_specific:
        return _normalize_color(str(artifact_specific[role]))
    raise VisualValidationError(f"profile uses an unresolved visual role: {role}")


def _resolve_expected_fill(policy: dict[str, Any], profile: dict[str, Any], value: str) -> str:
    return _resolve_role_fill(policy, profile, value.split(":", 1)[1]) if value.startswith("role:") else _normalize_color(value)


def _violation(rule_id: str, location: str, **details: Any) -> dict[str, Any]:
    payload = {"rule_id": rule_id, "location": location}; payload.update(details); return payload


def _validate_required_sheets(workbook: WorkbookData, profile: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for sheet in profile.get("required_sheets", []):
        if sheet not in workbook.sheets:
            violations.append(_violation("WVI002", f"sheet:{sheet}", profile_rule="required_sheets"))
    for pattern in profile.get("required_sheet_patterns", []):
        regex = re.compile(pattern)
        if not any(regex.search(name) for name in workbook.sheet_order):
            violations.append(_violation("WVI002", f"sheet-pattern:{pattern}", profile_rule="required_sheet_patterns"))
    return violations


def _validate_filename(workbook: WorkbookData, profile: dict[str, Any]) -> list[dict[str, Any]]:
    if not any(re.fullmatch(pattern, workbook.path.name) for pattern in profile.get("filename_patterns", [])):
        return [_violation("WVI001", f"artifact:{workbook.path.name}", profile_rule="filename_patterns")]
    return []


def _range_fill_rule(workbook: WorkbookData, sheet: SheetData, rule: dict[str, Any], policy: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    expected = _resolve_expected_fill(policy, profile, str(rule["expected_fill"]))
    return [
        _violation("WVI008", f"{sheet.name}!{address}", profile_rule=rule["id"], expected_fill=expected, actual_fill=_cell_style(workbook, sheet, address).fill)
        for address in _iter_range(str(rule["range"]))
        if _cell_style(workbook, sheet, address).fill != expected
    ]


def _same_key_style_rule(workbook: WorkbookData, sheet: SheetData, rule: dict[str, Any]) -> list[dict[str, Any]]:
    start_row, end_row = [int(value) for value in rule["rows"]]
    key_column = str(rule["key_column"]).upper()
    start_col, end_col = [str(value).upper() for value in rule["style_columns"]]
    attributes = tuple(rule.get("attributes", ["fill"]))
    columns = _column_span(start_col, end_col)
    groups: dict[Any, list[int]] = {}
    for row in range(start_row, end_row + 1):
        key = _cell_value(sheet, f"{key_column}{row}")
        if key is not None:
            groups.setdefault(key, []).append(row)
    violations: list[dict[str, Any]] = []
    for rows in groups.values():
        if len(rows) < 2:
            continue
        baseline_row = rows[0]
        baseline = tuple(_cell_style(workbook, sheet, f"{column}{baseline_row}").selected(attributes) for column in columns)
        for row in rows[1:]:
            current = tuple(_cell_style(workbook, sheet, f"{column}{row}").selected(attributes) for column in columns)
            if current != baseline:
                violations.append(_violation("WVI004", f"{sheet.name}!{start_col}{row}:{end_col}{row}", profile_rule=rule["id"], baseline_row=baseline_row, divergent_row=row))
    return violations


def _semantic_rows_rule(workbook: WorkbookData, sheet: SheetData, rule: dict[str, Any], policy: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    start_row, end_row = [int(value) for value in rule["rows"]]
    label_column = str(rule["label_column"]).upper()
    start_col, end_col = [str(value).upper() for value in rule["style_columns"]]
    columns = _column_span(start_col, end_col)
    mode = rule.get("match_mode", "prefix")
    violations: list[dict[str, Any]] = []
    for row in range(start_row, end_row + 1):
        raw = _cell_value(sheet, f"{label_column}{row}")
        if raw is None:
            continue
        label = str(raw)
        matched: dict[str, Any] | None = None
        for mapping in rule.get("mappings", []):
            token = str(mapping["token"])
            if mode == "prefix" and label.casefold().startswith(token.casefold()): matched = mapping
            elif mode == "contains" and token.casefold() in label.casefold(): matched = mapping
            elif mode == "regex" and re.search(token, label): matched = mapping
            if matched is not None: break
        if matched is None:
            continue
        expected = _resolve_role_fill(policy, profile, str(matched["role"]))
        for column in columns:
            address = f"{column}{row}"; actual = _cell_style(workbook, sheet, address).fill
            if actual != expected:
                violations.append(_violation("WVI003", f"{sheet.name}!{address}", profile_rule=rule["id"], role=matched["role"], expected_fill=expected, actual_fill=actual))
    return violations


def _boundary_rule(workbook: WorkbookData, sheet: SheetData, rule: dict[str, Any], policy: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    c1, r1, c2, r2 = _parse_range(str(rule["range"])); expected = _resolve_expected_fill(policy, profile, str(rule["expected_fill"])); edges = set(rule.get("edges", ["top", "bottom", "left", "right"])); candidates: list[tuple[int, int]] = []
    if "top" in edges and r1 > 1: candidates.extend((column, r1 - 1) for column in range(c1, c2 + 1))
    if "bottom" in edges: candidates.extend((column, r2 + 1) for column in range(c1, c2 + 1))
    if "left" in edges and c1 > 1: candidates.extend((c1 - 1, row) for row in range(r1, r2 + 1))
    if "right" in edges: candidates.extend((c2 + 1, row) for row in range(r1, r2 + 1))
    return [_violation("WVI005", f"{sheet.name}!{_number_to_column(column)}{row}", profile_rule=rule["id"], bleeding_fill=expected) for column, row in candidates if _cell_style(workbook, sheet, f"{_number_to_column(column)}{row}").fill == expected]


def _row_fill(workbook: WorkbookData, sheet: SheetData, columns: range, row: int) -> str:
    fills = [_cell_style(workbook, sheet, f"{_number_to_column(column)}{row}").fill for column in columns]
    non_default = [fill for fill in fills if fill != "00000000"]
    return non_default[0] if non_default else fills[0]


def _paired_range_rule(workbook: WorkbookData, sheet: SheetData, rule: dict[str, Any]) -> list[dict[str, Any]]:
    lc1, lr1, lc2, lr2 = _parse_range(str(rule["left_range"])); rc1, rr1, rc2, rr2 = _parse_range(str(rule["right_range"]))
    if (lr2 - lr1) != (rr2 - rr1):
        return [_violation("WVI006", f"{sheet.name}!{rule['left_range']}|{rule['right_range']}", profile_rule=rule["id"], reason="row_count")]
    violations: list[dict[str, Any]] = []
    for offset in range(lr2 - lr1 + 1):
        left_row = lr1 + offset; right_row = rr1 + offset
        left_fill = _row_fill(workbook, sheet, range(lc1, lc2 + 1), left_row); right_fill = _row_fill(workbook, sheet, range(rc1, rc2 + 1), right_row)
        if left_fill != right_fill:
            violations.append(_violation("WVI006", f"{sheet.name}!row:{left_row}|{right_row}", profile_rule=rule["id"], left_fill=left_fill, right_fill=right_fill))
    return violations


def _layout_rule(workbook: WorkbookData, sheet: SheetData, rule: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if "tab_color" in rule and sheet.tab_color != _normalize_color(str(rule["tab_color"])):
        violations.append(_violation("WVI008", f"{sheet.name}!tabColor", profile_rule=rule["id"], expected=rule["tab_color"], actual=sheet.tab_color))
    if "freeze_pane" in rule and sheet.freeze_pane != rule["freeze_pane"]:
        violations.append(_violation("WVI008", f"{sheet.name}!freezePane", profile_rule=rule["id"], expected=rule["freeze_pane"], actual=sheet.freeze_pane))
    for column, expected in rule.get("column_widths", {}).items():
        actual = sheet.column_widths.get(column); tolerance = float(rule.get("width_tolerance", 0.01))
        if actual is None or abs(actual - float(expected)) > tolerance:
            violations.append(_violation("WVI008", f"{sheet.name}!column:{column}", profile_rule=rule["id"], expected=expected, actual=actual))
    for row_text, expected in rule.get("row_heights", {}).items():
        row = int(row_text); actual = sheet.row_heights.get(row); tolerance = float(rule.get("height_tolerance", 0.01))
        if actual is None or abs(actual - float(expected)) > tolerance:
            violations.append(_violation("WVI008", f"{sheet.name}!row:{row}", profile_rule=rule["id"], expected=expected, actual=actual))
    return violations


def _baseline_violations(candidate: WorkbookData, baseline: WorkbookData, preserve: list[str]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if "sheet_order" in preserve and candidate.sheet_order != baseline.sheet_order:
        violations.append(_violation("WVI007", "workbook:sheet_order", reason="sheet_order_changed"))
    for name in [item for item in baseline.sheet_order if item in candidate.sheets]:
        left = baseline.sheets[name]; right = candidate.sheets[name]
        if "merged_ranges" in preserve and left.merges != right.merges:
            violations.append(_violation("WVI007", f"{name}!merged_ranges", reason="merged_ranges_changed"))
        for address in sorted(set(left.cells) | set(right.cells)):
            left_cell = left.cells.get(address, {}); right_cell = right.cells.get(address, {})
            if "cell_values" in preserve and left_cell.get("value") != right_cell.get("value"):
                violations.append(_violation("WVI007", f"{name}!{address}", reason="cell_value_changed"))
            if "formulas" in preserve and left_cell.get("formula") != right_cell.get("formula"):
                violations.append(_violation("WVI007", f"{name}!{address}", reason="formula_changed"))
    for name in baseline.sheet_order:
        if name not in candidate.sheets:
            violations.append(_violation("WVI007", f"sheet:{name}", reason="sheet_removed"))
    return violations


def _validate_profile_contract(policy: dict[str, Any], profile: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if profile.get("schema") != "workbook-visual-profile/v1": violations.append(_violation("WVI009", str(path), reason="schema"))
    for key in ("profile_id", "artifact_family", "filename_patterns", "rules", "generator_binding", "proof_ceiling"):
        if not profile.get(key): violations.append(_violation("WVI009", str(path), reason=f"missing:{key}"))
    for pattern in profile.get("filename_patterns", []):
        try: re.compile(pattern)
        except re.error: violations.append(_violation("WVI009", str(path), reason="invalid_filename_pattern"))
    for pattern in profile.get("required_sheet_patterns", []):
        try: re.compile(pattern)
        except re.error: violations.append(_violation("WVI009", str(path), reason="invalid_sheet_pattern"))
    all_role_fills = {role: _normalize_color(str(value["fill"])) for role, value in policy.get("semantic_roles", {}).items()}
    all_role_fills.update({role: _normalize_color(str(fill)) for role, fill in profile.get("artifact_specific_roles", {}).items()})
    reverse: dict[str, list[str]] = {}
    for role, fill in all_role_fills.items(): reverse.setdefault(fill, []).append(role)
    for fill, roles in reverse.items():
        if len(roles) > 1: violations.append(_violation("WVI009", str(path), reason="duplicate_role_color", fill=fill, roles=sorted(roles)))
    unknown = set(profile.get("artifact_specific_roles", {})) - set(policy.get("artifact_specific_roles", []))
    if unknown: violations.append(_violation("WVI009", str(path), reason="unknown_artifact_specific_roles", roles=sorted(unknown)))
    has_legacy = any(item.get("type") == "legacy_date_band" for item in profile.get("exceptions", []))
    for rule in profile.get("rules", []):
        if not rule.get("id") or not rule.get("type"): violations.append(_violation("WVI009", str(path), reason="rule_identity"))
        if rule.get("type") == "same_key_style" and str(rule.get("key_column", "")).upper() in {"A", "B"} and not has_legacy and "date" in profile.get("scope", "").casefold():
            violations.append(_violation("WVI009", str(path), reason="unbounded_date_striping_rule", profile_rule=rule.get("id")))
        for range_key in ("range", "left_range", "right_range"):
            if range_key in rule:
                try: _parse_range(str(rule[range_key]))
                except VisualValidationError: violations.append(_violation("WVI009", str(path), reason=f"invalid_{range_key}", profile_rule=rule.get("id")))
        if rule.get("type") == "semantic_rows":
            for mapping in rule.get("mappings", []):
                try: _resolve_role_fill(policy, profile, str(mapping.get("role", "")))
                except VisualValidationError: violations.append(_violation("WVI009", str(path), reason="unresolved_role", profile_rule=rule.get("id")))
    binding = profile.get("generator_binding", {})
    required_fields = {"visual_profile_id", "visual_policy_sha256", "visual_validation_result", "artifact_sha256", "font_validation_result", "operator_excel_for_web_status"}
    if binding.get("required") is not True or not required_fields.issubset(set(binding.get("manifest_fields", []))):
        violations.append(_violation("WVI009", str(path), reason="generator_binding"))
    return violations


def audit_profiles(policy_path: Path = POLICY_PATH, registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    policy = _load_json(policy_path); registry = _load_json(registry_path); violations: list[dict[str, Any]] = []
    if policy.get("schema") != "workbook-visual-integrity-policy/v1": violations.append(_violation("WVI009", str(policy_path), reason="policy_schema"))
    if policy.get("fonts", {}).get("default") != "Aptos" or "Carlito" not in policy.get("fonts", {}).get("forbidden", []): violations.append(_violation("WVI009", str(policy_path), reason="font_alignment"))
    canonical = policy.get("semantic_roles", {})
    if len(canonical) != 8: violations.append(_violation("WVI009", str(policy_path), reason="canonical_role_count"))
    canonical_fills = [_normalize_color(str(item.get("fill", ""))) for item in canonical.values()]
    if len(canonical_fills) != len(set(canonical_fills)): violations.append(_violation("WVI009", str(policy_path), reason="canonical_color_collision"))
    profile_results: list[dict[str, Any]] = []
    for relative in registry.get("profiles", []):
        path = ROOT / relative
        try:
            profile = _load_json(path); profile_violations = _validate_profile_contract(policy, profile, path)
        except VisualValidationError as exc:
            profile = {"profile_id": relative}; profile_violations = [_violation("WVI009", relative, reason=str(exc))]
        violations.extend(profile_violations)
        profile_results.append({"profile_id": profile.get("profile_id", relative), "path": relative, "sha256": _sha256_file(path) if path.is_file() else None, "status": "PASS" if not profile_violations else "FAIL", "violation_count": len(profile_violations)})
    return {"schema": "workbook-visual-profile-audit-result/v1", "status": "PASS" if not violations else "FAIL", "policy": {"policy_id": policy.get("policy_id"), "sha256": _sha256_file(policy_path)}, "profile_count": len(profile_results), "profiles": profile_results, "violation_count": len(violations), "violations": violations, "proof_ceiling": policy.get("proof_ceiling", "Static profile proof only.")}


def validate_workbook(workbook_path: Path, profile_path: Path, baseline_path: Path | None = None) -> dict[str, Any]:
    policy = _load_json(POLICY_PATH); profile = _load_json(profile_path); workbook = _read_workbook(workbook_path); violations = list(_validate_profile_contract(policy, profile, profile_path)); violations.extend(_validate_filename(workbook, profile)); violations.extend(_validate_required_sheets(workbook, profile)); baseline = _read_workbook(baseline_path) if baseline_path else None; executed_rules = 0
    for rule in profile.get("rules", []):
        rule_type = rule.get("type")
        if rule_type in {"profile_palette", "defense_tab_sections", "chrome_contract", "forbid_unbounded_striping"}: continue
        executed_rules += 1
        if rule_type == "style_only_baseline":
            if baseline is not None: violations.extend(_baseline_violations(workbook, baseline, list(rule.get("preserve", []))))
            continue
        sheet_name = rule.get("sheet")
        if not sheet_name or sheet_name not in workbook.sheets:
            if sheet_name: violations.append(_violation("WVI002", f"sheet:{sheet_name}", profile_rule=rule.get("id")))
            continue
        sheet = workbook.sheets[sheet_name]
        if rule_type == "range_fill": violations.extend(_range_fill_rule(workbook, sheet, rule, policy, profile))
        elif rule_type == "same_key_style": violations.extend(_same_key_style_rule(workbook, sheet, rule))
        elif rule_type == "semantic_rows": violations.extend(_semantic_rows_rule(workbook, sheet, rule, policy, profile))
        elif rule_type == "boundary": violations.extend(_boundary_rule(workbook, sheet, rule, policy, profile))
        elif rule_type == "paired_range_fill": violations.extend(_paired_range_rule(workbook, sheet, rule))
        elif rule_type == "layout": violations.extend(_layout_rule(workbook, sheet, rule))
        else: violations.append(_violation("WVI009", f"profile-rule:{rule.get('id')}", reason="unsupported_rule_type"))
    return {"schema": "triage-workbook-visual-validation-result/v1", "status": "PASS" if not violations else "FAIL", "artifact": {"filename": workbook.path.name, "size_bytes": workbook.size_bytes, "sha256": workbook.sha256}, "baseline": None if baseline is None else {"filename": baseline.path.name, "size_bytes": baseline.size_bytes, "sha256": baseline.sha256}, "policy": {"policy_id": policy.get("policy_id"), "sha256": _sha256_file(POLICY_PATH)}, "profile": {"profile_id": profile.get("profile_id"), "sha256": _sha256_file(profile_path)}, "counts": {"rules": executed_rules, "violations": len(violations)}, "violations": violations, "proof_ceiling": profile.get("proof_ceiling", policy.get("proof_ceiling"))}


def _write_report(report: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is None: print(text, end="")
    else: output.parent.mkdir(parents=True, exist_ok=True); output.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate workbook color, formatting, and range contracts.")
    parser.add_argument("--workbook", type=Path); parser.add_argument("--profile", type=Path); parser.add_argument("--baseline", type=Path); parser.add_argument("--validate-profiles", action="store_true"); parser.add_argument("--output", type=Path); parser.add_argument("--summary", action="store_true"); args = parser.parse_args(argv)
    try:
        if args.validate_profiles:
            if args.workbook or args.profile or args.baseline: raise VisualValidationError("--validate-profiles cannot be combined with workbook arguments")
            report = audit_profiles()
        else:
            if args.workbook is None or args.profile is None: raise VisualValidationError("--workbook and --profile are required")
            report = validate_workbook(args.workbook, args.profile, args.baseline)
    except (VisualValidationError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError, re.error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr); return 2
    if args.output is not None or not args.summary: _write_report(report, args.output)
    if args.summary:
        if report["schema"] == "workbook-visual-profile-audit-result/v1": print(f"{report['status']}: profiles={report['profile_count']} violations={report['violation_count']}")
        else: print(f"{report['status']}: artifact={report['artifact']['filename']} rules={report['counts']['rules']} violations={report['counts']['violations']}")
        if args.output: print(args.output)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
