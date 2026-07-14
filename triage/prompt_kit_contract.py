"""Read-only OOXML validator for the AI Prompt Kit V19 contract."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional, Sequence
from xml.etree import ElementTree as ET

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": MAIN, "r": REL}
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
RANGE_RE = re.compile(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$")
DEFAULT_PROMPT_IDS = tuple(f"P{i:02d}" for i in range(21))


def _xml(z: zipfile.ZipFile, part: str) -> ET.Element:
    return ET.fromstring(z.read(part))


def _resolve(owner: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    parts: list[str] = []
    for piece in (PurePosixPath(owner).parent / target).parts:
        if piece in ("", "."):
            continue
        if piece == "..":
            if parts:
                parts.pop()
        else:
            parts.append(piece)
    return "/".join(parts)


def _sheets(z: zipfile.ZipFile) -> dict[str, str]:
    wb = _xml(z, "xl/workbook.xml")
    rels = _xml(z, "xl/_rels/workbook.xml.rels")
    targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
    out: dict[str, str] = {}
    for sheet in wb.findall("m:sheets/m:sheet", NS):
        rid = sheet.attrib.get(f"{{{REL}}}id")
        if rid in targets:
            out[sheet.attrib["name"]] = _resolve("xl/workbook.xml", targets[rid])
    return out


def _shared(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    return [
        "".join(t.text or "" for t in item.iter(f"{{{MAIN}}}t"))
        for item in _xml(z, "xl/sharedStrings.xml").findall("m:si", NS)
    ]


def _value(cell: ET.Element, shared: Sequence[str]) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(f"{{{MAIN}}}t"))
    node = cell.find("m:v", NS)
    if node is None or node.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return shared[int(node.text)]
        except (ValueError, IndexError):
            return ""
    return node.text


def _position(ref: str) -> Optional[tuple[str, int]]:
    match = CELL_RE.fullmatch(ref or "")
    return (match.group(1), int(match.group(2))) if match else None


def _dimension_end(ref: Optional[str]) -> int:
    if not ref:
        return 0
    match = RANGE_RE.fullmatch(ref)
    if match:
        return int(match.group(4))
    pos = _position(ref)
    return pos[1] if pos else 0


def _fonts(z: zipfile.ZipFile) -> tuple[list[dict], list[int]]:
    root = _xml(z, "xl/styles.xml")
    fonts: list[dict] = []
    for font in root.findall("m:fonts/m:font", NS):
        name = font.find("m:name", NS)
        size = font.find("m:sz", NS)
        fonts.append(
            {
                "family": name.attrib.get("val", "") if name is not None else "",
                "size": float(size.attrib["val"])
                if size is not None and size.attrib.get("val")
                else None,
                "bold": font.find("m:b", NS) is not None,
            }
        )
    xfs: list[int] = []
    for xf in root.findall("m:cellXfs/m:xf", NS):
        try:
            xfs.append(int(xf.attrib.get("fontId", "0")))
        except ValueError:
            xfs.append(0)
    return fonts, xfs


def _font(cell: ET.Element, fonts: Sequence[dict], xfs: Sequence[int]) -> dict:
    try:
        style = int(cell.attrib.get("s", "0"))
    except ValueError:
        style = 0
    font_id = xfs[style] if 0 <= style < len(xfs) else 0
    return (
        fonts[font_id]
        if 0 <= font_id < len(fonts)
        else {"family": "", "size": None, "bold": False}
    )


def _surface(root: ET.Element, shared: Sequence[str], name: str) -> dict:
    populated: list[tuple[str, int]] = []
    cell_rows: list[int] = []
    for cell in root.findall(".//m:c", NS):
        pos = _position(cell.attrib.get("r", ""))
        if not pos:
            continue
        column, row = pos
        cell_rows.append(row)
        if _value(cell, shared):
            populated.append((column, row))
    rows = sorted({row for _, row in populated})
    first = rows[0] if rows else 0
    last = rows[-1] if rows else 0
    dim = root.find("m:dimension", NS)
    row_nodes = [
        int(r.attrib["r"])
        for r in root.findall("m:sheetData/m:row", NS)
        if r.attrib.get("r", "").isdigit()
    ]
    end = max(
        _dimension_end(dim.attrib.get("ref") if dim is not None else None),
        max(row_nodes, default=0),
        max(cell_rows, default=0),
    )
    return {
        "sheet": name,
        "first_payload_row": first,
        "last_payload_row": last,
        "populated_rows": len(rows),
        "internal_blank_rows": max(0, last - first + 1 - len(rows)) if rows else 0,
        "package_end_row": end,
        "trailing_rows": max(0, end - last),
        "populated_columns": sorted({column for column, _ in populated}),
    }


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    findings: list[dict] = field(default_factory=list)
    summary: str = ""


@dataclass(frozen=True)
class Report:
    path: str
    passed: bool
    checks: list[Check]
    copy_surfaces: list[dict]
    field_acceptance: str = "manual_web_excel_test_required"

    @property
    def pass_all(self) -> bool:
        return self.passed

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "pass": self.passed,
            "field_acceptance": self.field_acceptance,
            "checks": [asdict(c) for c in self.checks],
            "copy_surfaces": self.copy_surfaces,
        }

    def render_text(self) -> str:
        lines = ["PROMPT KIT V19 CONTRACT"]
        lines.extend(
            f"[{c.status}] {c.name}{': ' + c.summary if c.summary else ''}"
            for c in self.checks
        )
        lines.extend(
            [
                "",
                f"Result: pass={str(self.passed).lower()}, "
                f"field_acceptance={self.field_acceptance}",
            ]
        )
        return "\n".join(lines)


def validate_prompt_kit_contract(
    path: str,
    *,
    prompt_ids: Iterable[str] = DEFAULT_PROMPT_IDS,
    allowed_font_families: Iterable[str] = ("Aptos",),
) -> Report:
    expected = tuple(dict.fromkeys(prompt_ids))
    allowed = set(allowed_font_families)
    checks: list[Check] = []
    surfaces: list[dict] = []
    with zipfile.ZipFile(path, "r") as z:
        sheets, shared, (fonts, xfs) = _sheets(z), _shared(z), _fonts(z)
        required = {
            "Prompt_Library",
            "Prompt_Class_Legend",
            *(f"{p}_COPY_SAFE" for p in expected),
        }
        missing = sorted(required - set(sheets))
        checks.append(
            Check(
                "required sheets",
                "FAIL" if missing else "PASS",
                [{"sheet": s} for s in missing],
            )
        )

        bad_fonts: list[dict] = []
        for sheet, part in sheets.items():
            for cell in _xml(z, part).findall(".//m:c", NS):
                if _value(cell, shared):
                    spec = _font(cell, fonts, xfs)
                    if spec["family"] not in allowed:
                        bad_fonts.append(
                            {"sheet": sheet, "cell": cell.attrib.get("r"), **spec}
                        )
        checks.append(
            Check(
                "visible fonts approved",
                "FAIL" if bad_fonts else "PASS",
                bad_fonts[:50],
                f"allowed: {', '.join(sorted(allowed))}",
            )
        )

        rows: dict[str, int] = {}
        lib_cells: dict[str, ET.Element] = {}
        lib_values: dict[str, str] = {}
        links: dict[str, str] = {}
        colors: list[str] = []
        structure: list[dict] = []
        typography: list[dict] = []
        if "Prompt_Library" in sheets:
            root = _xml(z, sheets["Prompt_Library"])
            for cell in root.findall(".//m:c", NS):
                ref = cell.attrib.get("r", "")
                lib_cells[ref], lib_values[ref] = cell, _value(cell, shared)
            for link in root.findall("m:hyperlinks/m:hyperlink", NS):
                if link.attrib.get("location"):
                    links[link.attrib.get("ref", "")] = (
                        link.attrib["location"]
                        .lstrip("#")
                        .replace("'", "")
                        .replace("$", "")
                    )
            for ref, wanted in {
                "B1": "Prompt ID",
                "H1": "Use This When",
                "M1": "Color",
                "N1": "Copy-Safe Sheet",
            }.items():
                if lib_values.get(ref, "") != wanted:
                    structure.append(
                        {
                            "cell": ref,
                            "expected": wanted,
                            "actual": lib_values.get(ref, ""),
                        }
                    )
            for ref, value in lib_values.items():
                pos = _position(ref)
                if pos and pos[0] == "B" and value in expected:
                    rows[value] = pos[1]
            for prompt_id in expected:
                row = rows.get(prompt_id)
                if row is None:
                    structure.append(
                        {"prompt_id": prompt_id, "issue": "prompt_id_missing"}
                    )
                    continue
                sheet = f"{prompt_id}_COPY_SAFE"
                if lib_values.get(f"N{row}", "") != sheet:
                    structure.append(
                        {
                            "cell": f"N{row}",
                            "expected": sheet,
                            "actual": lib_values.get(f"N{row}", ""),
                        }
                    )
                color = lib_values.get(f"M{row}", "")
                colors.append(color)
                if not color:
                    structure.append(
                        {"cell": f"M{row}", "issue": "color_missing"}
                    )
            if "H1" in lib_cells:
                spec = _font(lib_cells["H1"], fonts, xfs)
                if spec["family"] != "Aptos" or not spec["bold"]:
                    typography.append(
                        {"cell": "H1", "expected": "Aptos bold", "actual": spec}
                    )
            for prompt_id, row in rows.items():
                cell = lib_cells.get(f"H{row}")
                spec = _font(cell, fonts, xfs) if cell is not None else None
                if (
                    spec is None
                    or spec["family"] != "Aptos"
                    or spec["size"] != 12.0
                    or spec["bold"]
                ):
                    typography.append(
                        {
                            "cell": f"H{row}",
                            "prompt_id": prompt_id,
                            "expected": "Aptos regular 12pt",
                            "actual": spec,
                        }
                    )
        checks.append(
            Check(
                "Prompt Library contract columns",
                "FAIL" if structure else "PASS",
                structure[:50],
            )
        )
        checks.append(
            Check(
                "Prompt Library column H typography",
                "FAIL" if typography else "PASS",
                typography[:50],
            )
        )

        surface_issues: list[dict] = []
        by_sheet: dict[str, dict] = {}
        for prompt_id in expected:
            name = f"{prompt_id}_COPY_SAFE"
            if name not in sheets:
                continue
            surface = _surface(_xml(z, sheets[name]), shared, name)
            surfaces.append(surface)
            by_sheet[name] = surface
            if surface["first_payload_row"] != 1:
                surface_issues.append(
                    {
                        "sheet": name,
                        "issue": "payload_does_not_start_at_row_1",
                        "actual": surface["first_payload_row"],
                    }
                )
            if surface["populated_columns"] != ["A"]:
                surface_issues.append(
                    {
                        "sheet": name,
                        "issue": "payload_not_single_column_A",
                        "columns": surface["populated_columns"],
                    }
                )
            if surface["internal_blank_rows"]:
                surface_issues.append(
                    {
                        "sheet": name,
                        "issue": "internal_blank_rows",
                        "count": surface["internal_blank_rows"],
                    }
                )
            if surface["trailing_rows"]:
                surface_issues.append(
                    {
                        "sheet": name,
                        "issue": "trailing_package_rows",
                        "count": surface["trailing_rows"],
                    }
                )
        checks.append(
            Check(
                "copy surfaces dense and bounded",
                "FAIL" if surface_issues else "PASS",
                surface_issues[:50],
            )
        )

        link_issues: list[dict] = []
        for prompt_id in expected:
            row, name = rows.get(prompt_id), f"{prompt_id}_COPY_SAFE"
            surface = by_sheet.get(name)
            if row is None or not surface or not surface["last_payload_row"]:
                continue
            wanted = f"{name}!A1:A{surface['last_payload_row']}"
            for column in ("B", "N"):
                ref = f"{column}{row}"
                if links.get(ref) != wanted:
                    link_issues.append(
                        {
                            "prompt_id": prompt_id,
                            "cell": ref,
                            "expected": wanted,
                            "actual": links.get(ref),
                        }
                    )
        checks.append(
            Check(
                "Prompt Library links select exact payload ranges",
                "FAIL" if link_issues else "PASS",
                link_issues[:50],
                "package proof only; browser selection remains a field gate",
            )
        )

        legend_issues: list[dict] = []
        if "Prompt_Class_Legend" in sheets:
            legend_rows: dict[int, dict[str, str]] = {}
            for cell in _xml(z, sheets["Prompt_Class_Legend"]).findall(
                ".//m:c", NS
            ):
                pos = _position(cell.attrib.get("r", ""))
                if pos:
                    legend_rows.setdefault(pos[1], {})[pos[0]] = _value(
                        cell, shared
                    )
            header_row, color_col, meaning_col = 0, "", ""
            for number in sorted(legend_rows)[:10]:
                for column, text in legend_rows[number].items():
                    normalized = text.strip().lower()
                    if normalized == "color":
                        color_col = column
                    if "meaning" in normalized or "operational" in normalized:
                        meaning_col = column
                if color_col and meaning_col:
                    header_row = number
                    break
            if not header_row:
                legend_issues.append({"issue": "legend_headers_missing"})
            else:
                mappings: dict[str, list[str]] = {}
                for number, values in legend_rows.items():
                    if number > header_row and values.get(color_col, "").strip():
                        mappings.setdefault(values[color_col].strip(), []).append(
                            values.get(meaning_col, "").strip()
                        )
                for color in sorted(set(colors)):
                    entries = mappings.get(color, [])
                    if len(entries) != 1 or not entries[0]:
                        legend_issues.append(
                            {
                                "color": color,
                                "issue": "color_requires_exactly_one_nonempty_meaning",
                                "entries": entries,
                            }
                        )
        checks.append(
            Check(
                "Prompt Class Legend covers every library color",
                "FAIL" if legend_issues else "PASS",
                legend_issues[:50],
            )
        )

    passed = all(check.status == "PASS" for check in checks)
    return Report(str(Path(path).resolve()), passed, checks, surfaces)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the prompt-kit V19 contract without rewriting the workbook"
    )
    parser.add_argument("workbook")
    parser.add_argument("--prompt-id", action="append", dest="prompt_ids")
    parser.add_argument("--allow-font", action="append", dest="fonts")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = validate_prompt_kit_contract(
        args.workbook,
        prompt_ids=args.prompt_ids or DEFAULT_PROMPT_IDS,
        allowed_font_families=args.fonts or ("Aptos",),
    )
    print(
        json.dumps(report.to_dict(), indent=2)
        if args.as_json
        else report.render_text()
    )
    raise SystemExit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
