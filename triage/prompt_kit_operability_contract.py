"""Read-only V32+ operability validator for AI Harness Prompt Kit workbooks.

This contract validates the human copy surface and the terminal launch surface
without loading or saving the workbook through an Office serializer. It treats
Excel for Web and desktop clipboard behavior as separate field-acceptance gates.
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "pr": PKG_REL_NS}
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
RANGE_RE = re.compile(r"^'?([^']+)'?!A1:A(\d+)$")

BASE_PROMPT_IDS = tuple(f"P{index:02d}" for index in range(37))
GNHF_PROMPT_IDS = tuple(f"P{index:02d}" for index in range(26, 37))
LIBRARY_HEADERS = (
    "Seq",
    "Prompt ID",
    "Prompt Type",
    "Prompt Class",
    "Sprint Path Role",
    "Use For Progress?",
    "Prompt Name",
    "Use This When",
    "Inspect First",
    "Expected Output",
    "Next Step",
    "Proof / Acceptance Gate",
    "Color",
    "Copy-Safe Sheet",
)

PALETTE: Mapping[str, Tuple[str, str]] = {
    "Slate": ("F1F5F9", "334155"),
    "Gray": ("E5E7EB", "374151"),
    "Sky": ("E0F2FE", "075985"),
    "Amber": ("FEF3C7", "92400E"),
    "Blue": ("DBEAFE", "1D4ED8"),
    "Green": ("DCFCE7", "166534"),
    "Rose": ("FFE4E6", "9F1239"),
    "Purple": ("F3E8FF", "6B21A8"),
    "Peach": ("FFEDD5", "9A3412"),
    "Teal": ("CCFBF1", "0F766E"),
    "Lavender": ("EDE9FE", "5B21B6"),
    "Cyan": ("CFFAFE", "0E7490"),
    "Indigo": ("E0E7FF", "3730A3"),
    "Blue-Green": ("CCFBF1", "0F766E"),
    "Gold": ("FEF3C7", "92400E"),
    "Sand": ("FDE68A", "854D0E"),
    "Cream": ("FFF2CC", "7C5C00"),
    "Orange": ("FED7AA", "9A3412"),
    "Emerald": ("D1FAE5", "047857"),
    "Coral": ("FFE4E6", "BE123C"),
    "Ocean": ("DBEAFE", "1D4ED8"),
    "Mint": ("D1FAE5", "047857"),
    "Night": ("E0E7FF", "3730A3"),
    "Violet": ("F3E8FF", "6B21A8"),
}

FONT_RULES: Mapping[str, Tuple[float, bool]] = {
    "B": (10.0, True),
    "C": (28.0, True),
    "D": (10.0, True),
    "E": (10.0, True),
    "G": (10.0, True),
    "H": (12.0, True),
    "N": (10.0, True),
    "O": (10.0, True),
}


@dataclass
class Check:
    name: str
    status: str
    findings: List[dict] = field(default_factory=list)
    summary: str = ""


@dataclass
class PromptKitOperabilityReport:
    path: str
    checks: List[Check] = field(default_factory=list)

    @property
    def failures(self) -> List[Check]:
        return [check for check in self.checks if check.status == "FAIL"]

    @property
    def warnings(self) -> List[Check]:
        return [check for check in self.checks if check.status == "WARN"]

    @property
    def valid(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "valid": self.valid,
            "counts": {
                "pass": sum(check.status == "PASS" for check in self.checks),
                "warn": len(self.warnings),
                "fail": len(self.failures),
            },
            "checks": [asdict(check) for check in self.checks],
            "proof_ceiling": (
                "static OOXML, copy-range, protection, style, and command-shape proof; "
                "PowerShell execution, provider readiness, desktop Excel, and Excel for Web remain runtime gates"
            ),
        }

    def render_text(self) -> str:
        lines = ["PROMPT KIT OPERABILITY CONTRACT"]
        for check in self.checks:
            suffix = f": {check.summary}" if check.summary else ""
            lines.append(f"[{check.status}] {check.name}{suffix}")
        lines.extend(("", f"Result: valid={str(self.valid).lower()}"))
        return "\n".join(lines)


def _xml_root(zf: zipfile.ZipFile, part: str) -> ET.Element:
    return ET.fromstring(zf.read(part))


def _shared_strings(zf: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = _xml_root(zf, "xl/sharedStrings.xml")
    return [
        "".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
        for item in root.findall("m:si", NS)
    ]


def _cell_value(cell: ET.Element, shared: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        try:
            return shared[int(value.text)]
        except (ValueError, IndexError):
            return ""
    return value.text


def _worksheet_cells(root: ET.Element, shared: Sequence[str]) -> Dict[str, Tuple[ET.Element, str]]:
    return {
        cell.attrib.get("r", ""): (cell, _cell_value(cell, shared))
        for cell in root.findall(".//m:c", NS)
        if cell.attrib.get("r")
    }


def _workbook_sheet_map(zf: zipfile.ZipFile) -> Dict[str, str]:
    workbook = _xml_root(zf, "xl/workbook.xml")
    rels = _xml_root(zf, "xl/_rels/workbook.xml.rels")
    targets = {rel.attrib["Id"]: rel.attrib.get("Target", "") for rel in rels}
    result: Dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        rid = sheet.attrib.get(f"{{{REL_NS}}}id", "")
        target = targets.get(rid, "")
        if not target:
            continue
        if target.startswith("/"):
            part = target.lstrip("/")
        elif target.startswith("xl/"):
            part = target
        else:
            part = posixpath.normpath(posixpath.join("xl", target))
        result[sheet.attrib["name"]] = part
    return result


def _sheet_hyperlinks(
    root: ET.Element,
    zf: zipfile.ZipFile | None = None,
    sheet_part: str | None = None,
) -> Dict[str, str]:
    relationships: Dict[str, str] = {}
    if zf is not None and sheet_part is not None:
        directory, filename = posixpath.split(sheet_part)
        relationship_part = posixpath.join(directory, "_rels", filename + ".rels")
        if relationship_part in zf.namelist():
            rel_root = _xml_root(zf, relationship_part)
            relationships = {
                rel.attrib.get("Id", ""): rel.attrib.get("Target", "").lstrip("#")
                for rel in rel_root
            }
    result: Dict[str, str] = {}
    for link in root.findall(".//m:hyperlinks/m:hyperlink", NS):
        ref = link.attrib.get("ref", "")
        if not ref:
            continue
        location = link.attrib.get("location", "")
        if not location:
            rid = link.attrib.get(f"{{{REL_NS}}}id", "")
            location = relationships.get(rid, "")
        result[ref] = location
    return result


def _rgb(value: str) -> str:
    raw = (value or "").upper()
    return raw[-6:] if len(raw) >= 6 else raw


def _styles(zf: zipfile.ZipFile) -> Tuple[List[dict], List[dict], List[dict]]:
    root = _xml_root(zf, "xl/styles.xml")
    fonts: List[dict] = []
    for font in root.findall("m:fonts/m:font", NS):
        name = font.find("m:name", NS)
        size = font.find("m:sz", NS)
        color = font.find("m:color", NS)
        fonts.append(
            {
                "name": name.attrib.get("val", "") if name is not None else "",
                "size": float(size.attrib.get("val", "0")) if size is not None else 0.0,
                "bold": font.find("m:b", NS) is not None,
                "italic": font.find("m:i", NS) is not None,
                "color": _rgb(color.attrib.get("rgb", "")) if color is not None else "",
            }
        )
    fills: List[dict] = []
    for fill in root.findall("m:fills/m:fill", NS):
        fg = fill.find("m:patternFill/m:fgColor", NS)
        fills.append({"color": _rgb(fg.attrib.get("rgb", "")) if fg is not None else ""})
    xfs: List[dict] = []
    for xf in root.findall("m:cellXfs/m:xf", NS):
        protection = xf.find("m:protection", NS)
        xfs.append(
            {
                "font_id": int(xf.attrib.get("fontId", "0")),
                "fill_id": int(xf.attrib.get("fillId", "0")),
                "locked": protection is None or protection.attrib.get("locked", "1") != "0",
            }
        )
    return fonts, fills, xfs


def _style_for_cell(cell: ET.Element, fonts: Sequence[dict], fills: Sequence[dict], xfs: Sequence[dict]) -> dict:
    style_id = int(cell.attrib.get("s", "0"))
    xf = xfs[style_id]
    return {
        "font": fonts[xf["font_id"]],
        "fill": fills[xf["fill_id"]],
        "locked": xf["locked"],
        "style_id": style_id,
    }


def _payload_lines(cells: Mapping[str, Tuple[ET.Element, str]], last_row: int) -> List[str]:
    return [cells.get(f"A{row}", (None, ""))[1] for row in range(1, last_row + 1)]


def validate_gnhf_launch_command(text: str) -> List[dict]:
    """Return command-shape findings; an empty list means the text is launchable in PowerShell."""
    findings: List[dict] = []
    normalized = text.replace("\r\n", "\n").strip()
    lines = normalized.split("\n") if normalized else []
    if not lines or lines[0].strip() != "gnhf `":
        findings.append({"rule": "command starts with PowerShell gnhf continuation", "expected": "gnhf `"})
        return findings

    required_patterns = {
        "agent": r"(?m)^\s*--agent\s+opencode\s+`$",
        "max_iterations": r"(?m)^\s*--max-iterations\s+(\d+)\s+`$",
        "max_tokens": r"(?m)^\s*--max-tokens\s+(\d+)\s+`$",
        "prevent_sleep": r"(?m)^\s*--prevent-sleep\s+on\s+`$",
        "stop_when": r'(?m)^\s*--stop-when\s+"[^"\n]+"\s+`$',
    }
    matches: Dict[str, re.Match[str]] = {}
    for name, pattern in required_patterns.items():
        match = re.search(pattern, normalized)
        if match is None:
            findings.append({"rule": f"required flag: {name}"})
        else:
            matches[name] = match

    has_worktree = bool(re.search(r"(?m)^\s*--worktree\s+`$", normalized))
    has_current = bool(re.search(r"(?m)^\s*--current-branch\s+`$", normalized))
    if has_worktree == has_current:
        findings.append({"rule": "exactly one Git execution mode", "worktree": has_worktree, "current_branch": has_current})
    if re.search(r"(?m)^\s*--push\b", normalized):
        findings.append({"rule": "automatic push forbidden"})

    if "max_iterations" in matches:
        value = int(matches["max_iterations"].group(1))
        if not 1 <= value <= 10:
            findings.append({"rule": "bounded iterations", "actual": value, "allowed": "1-10"})
    if "max_tokens" in matches:
        value = int(matches["max_tokens"].group(1))
        if not 50_000 <= value <= 1_500_000:
            findings.append({"rule": "bounded tokens", "actual": value, "allowed": "50000-1500000"})

    objective_index = next((index for index, line in enumerate(lines) if line.lstrip().startswith('"Repo:')), None)
    if objective_index is None:
        findings.append({"rule": "quoted objective begins with Repo placeholder"})
    else:
        if not lines[-1].endswith('"'):
            findings.append({"rule": "quoted objective closes on final line"})
        objective = "\n".join(lines[objective_index:])
        if "xyz_repo_or_path" not in objective:
            findings.append({"rule": "generalized repo placeholder"})
        if len(objective.split()) > 650:
            findings.append({"rule": "atomic objective length", "words": len(objective.split()), "maximum": 650})

    for index, line in enumerate(lines[:objective_index] if objective_index is not None else lines, start=1):
        if index == 1:
            continue
        if line.strip() and not line.rstrip().endswith("`"):
            findings.append({"rule": "PowerShell continuation", "line": index, "text": line})
    if any(line.rstrip() != line for line in lines):
        findings.append({"rule": "no trailing spaces after PowerShell continuation"})
    return findings


def validate_prompt_kit_operability(path: str | Path) -> PromptKitOperabilityReport:
    workbook = Path(path)
    report = PromptKitOperabilityReport(str(workbook.resolve()))
    if not workbook.exists():
        report.checks.append(Check("file exists", "FAIL", [{"path": str(workbook)}]))
        return report
    try:
        with zipfile.ZipFile(workbook) as zf:
            sheets = _workbook_sheet_map(zf)
            shared = _shared_strings(zf)
            fonts, fills, xfs = _styles(zf)

            library_root = _xml_root(zf, sheets["Prompt_Library"])
            library_cells = _worksheet_cells(library_root, shared)
            library_links = _sheet_hyperlinks(
                library_root,
                zf,
                sheets["Prompt_Library"],
            )
            prompt_numbers = sorted(
                int(value[1:])
                for ref, (_, value) in library_cells.items()
                if ref.startswith("C") and re.fullmatch(r"P\d{2}", value)
            )
            max_prompt = max(prompt_numbers, default=36)
            prompt_ids = tuple(f"P{index:02d}" for index in range(max(36, max_prompt) + 1))

            required = {
                "Prompt_Library",
                "Prompt_Sequence",
                "Opportunity_Discovery",
                "GNHF_Workflow_Map",
                *{f"{prompt_id}_COPY_SAFE" for prompt_id in prompt_ids},
            }
            missing = sorted(required - set(sheets))
            report.checks.append(Check("required operability sheets", "FAIL" if missing else "PASS", [{"missing": item} for item in missing]))
            if missing:
                return report

            workbook_root = _xml_root(zf, "xl/workbook.xml")
            structure = workbook_root.find("m:workbookProtection", NS)
            report.checks.append(
                Check(
                    "workbook structure locked",
                    "PASS" if structure is not None and structure.attrib.get("lockStructure") == "1" else "FAIL",
                )
            )

            protection_findings = []
            for name, part in sheets.items():
                root = _xml_root(zf, part)
                if root.find("m:sheetProtection", NS) is None:
                    protection_findings.append({"sheet": name, "reason": "missing sheetProtection"})
            report.checks.append(
                Check(
                    "all worksheets protected",
                    "FAIL" if protection_findings else "PASS",
                    protection_findings,
                    f"{len(sheets) - len(protection_findings)}/{len(sheets)} protected",
                )
            )

            opportunity_root = _xml_root(zf, sheets["Opportunity_Discovery"])
            opportunity_cells = _worksheet_cells(opportunity_root, shared)
            unlock_findings = []
            for row in range(1, 101):
                for column_number in range(1, 19):
                    number = column_number
                    column = ""
                    while number:
                        number, remainder = divmod(number - 1, 26)
                        column = chr(65 + remainder) + column
                    ref = f"{column}{row}"
                    cell = opportunity_cells.get(ref, (None, ""))[0]
                    if cell is None:
                        unlock_findings.append({"cell": ref, "reason": "not materialized"})
                        continue
                    style = _style_for_cell(cell, fonts, fills, xfs)
                    if style["locked"]:
                        unlock_findings.append({"cell": ref, "reason": "locked"})
            report.checks.append(
                Check(
                    "Opportunity_Discovery A1:R100 unlocked",
                    "FAIL" if unlock_findings else "PASS",
                    unlock_findings[:100],
                    f"{1800 - len(unlock_findings)}/1800 editable",
                )
            )

            header_findings = []
            for index, expected in enumerate(LIBRARY_HEADERS, start=2):
                number = index
                column = ""
                while number:
                    number, remainder = divmod(number - 1, 26)
                    column = chr(65 + remainder) + column
                actual = library_cells.get(f"{column}1", (None, ""))[1]
                if actual != expected:
                    header_findings.append({"cell": f"{column}1", "expected": expected, "actual": actual})
            report.checks.append(Check("Prompt Library B:O headers", "FAIL" if header_findings else "PASS", header_findings))

            footer_row = len(prompt_ids) + 2
            nav_expected = {
                "A1": ("↓ Bottom", f"'Prompt_Library'!A{footer_row}"),
                "P1": ("↓ Bottom", f"'Prompt_Library'!P{footer_row}"),
                f"A{footer_row}": ("↑ Top", "'Prompt_Library'!A1"),
                f"P{footer_row}": ("↑ Top", "'Prompt_Library'!P1"),
            }
            nav_findings = []
            for ref, (label, location) in nav_expected.items():
                actual_label = library_cells.get(ref, (None, ""))[1]
                actual_location = library_links.get(ref, "")
                if actual_label != label or actual_location != location:
                    nav_findings.append(
                        {"cell": ref, "expected_label": label, "actual_label": actual_label, "expected_location": location, "actual_location": actual_location}
                    )
            report.checks.append(Check("Prompt Library left-right top-bottom navigation", "FAIL" if nav_findings else "PASS", nav_findings))

            row_findings = []
            style_findings = []
            forward_findings = []
            backlink_findings = []
            command_findings = []
            for index, prompt_id in enumerate(prompt_ids):
                row = index + 2
                copy_sheet = f"{prompt_id}_COPY_SAFE"
                actual_id = library_cells.get(f"C{row}", (None, ""))[1]
                actual_copy = library_cells.get(f"O{row}", (None, ""))[1]
                if actual_id != prompt_id:
                    row_findings.append({"cell": f"C{row}", "expected": prompt_id, "actual": actual_id})
                if actual_copy != copy_sheet:
                    row_findings.append({"cell": f"O{row}", "expected": copy_sheet, "actual": actual_copy})

                color_label = library_cells.get(f"N{row}", (None, ""))[1]
                expected_palette = PALETTE.get(color_label)
                if expected_palette is None:
                    style_findings.append({"row": row, "color": color_label, "reason": "unknown palette label"})
                for column in range(2, 16):
                    number = column
                    col = ""
                    while number:
                        number, remainder = divmod(number - 1, 26)
                        col = chr(65 + remainder) + col
                    cell = library_cells.get(f"{col}{row}", (None, ""))[0]
                    if cell is None:
                        style_findings.append({"cell": f"{col}{row}", "reason": "missing cell"})
                        continue
                    info = _style_for_cell(cell, fonts, fills, xfs)
                    if expected_palette:
                        expected_fill, expected_text = expected_palette
                        if info["fill"]["color"] != expected_fill or info["font"]["color"] != expected_text:
                            style_findings.append(
                                {
                                    "cell": f"{col}{row}",
                                    "color_label": color_label,
                                    "expected_fill": expected_fill,
                                    "actual_fill": info["fill"]["color"],
                                    "expected_text": expected_text,
                                    "actual_text": info["font"]["color"],
                                }
                            )
                for col, (size, bold) in FONT_RULES.items():
                    cell = library_cells.get(f"{col}{row}", (None, ""))[0]
                    if cell is None:
                        continue
                    font = _style_for_cell(cell, fonts, fills, xfs)["font"]
                    if font["name"] != "Aptos" or font["size"] != size or font["bold"] != bold:
                        style_findings.append(
                            {"cell": f"{col}{row}", "expected": {"name": "Aptos", "size": size, "bold": bold}, "actual": font}
                        )

                target = library_links.get(f"C{row}", "")
                copy_target = library_links.get(f"O{row}", "")
                match = RANGE_RE.fullmatch(target)
                if match is None or match.group(1) != copy_sheet:
                    forward_findings.append({"cell": f"C{row}", "expected_sheet": copy_sheet, "actual": target})
                    continue
                last_row = int(match.group(2))
                if copy_target != target:
                    forward_findings.append({"cell": f"O{row}", "expected": target, "actual": copy_target})

                copy_root = _xml_root(zf, sheets[copy_sheet])
                copy_cells = _worksheet_cells(copy_root, shared)
                payload = _payload_lines(copy_cells, last_row)
                endpoint_missing = not payload or not payload[0] or not payload[-1]
                after_payload = [
                    ref
                    for ref, (_, value) in copy_cells.items()
                    if value and (match_ref := CELL_RE.fullmatch(ref)) and match_ref.group(1) == "A" and int(match_ref.group(2)) > last_row
                ]
                if endpoint_missing or after_payload:
                    forward_findings.append(
                        {"sheet": copy_sheet, "payload_endpoints_nonempty": not endpoint_missing, "nonempty_after_payload": after_payload}
                    )

                copy_links = _sheet_hyperlinks(copy_root, zf, sheets[copy_sheet])
                self_target = f"'{copy_sheet}'!A1:A{last_row}"
                legacy_target = "'Prompt_Library'!A1"
                uses_range_recovery = copy_links.get("C1") == self_target
                if uses_range_recovery:
                    for ref in ("C1", f"C{last_row}"):
                        if copy_links.get(ref) != self_target:
                            backlink_findings.append({"sheet": copy_sheet, "cell": ref, "expected": self_target, "actual": copy_links.get(ref)})
                    expected_backlink = f"'Prompt_Library'!A{row}:P{row}"
                    for ref in ("B1", "E1", f"B{last_row}", f"E{last_row}"):
                        if copy_links.get(ref) != expected_backlink:
                            backlink_findings.append({"sheet": copy_sheet, "cell": ref, "expected": expected_backlink, "actual": copy_links.get(ref)})
                else:
                    for ref in ("C1", f"C{last_row}"):
                        if copy_links.get(ref) != legacy_target:
                            backlink_findings.append({"sheet": copy_sheet, "cell": ref, "expected": legacy_target, "actual": copy_links.get(ref)})

                if prompt_id in GNHF_PROMPT_IDS:
                    findings = validate_gnhf_launch_command("\n".join(payload))
                    if findings:
                        command_findings.append({"prompt": prompt_id, "findings": findings})

            report.checks.append(Check("Prompt Library prompt rows", "FAIL" if row_findings else "PASS", row_findings))
            report.checks.append(Check("Prompt Library semantic fonts and color coordination", "FAIL" if style_findings else "PASS", style_findings[:200]))
            report.checks.append(Check("forward links select exact column-A payloads", "FAIL" if forward_findings else "PASS", forward_findings))
            report.checks.append(Check("top and bottom Prompt Library backlinks", "FAIL" if backlink_findings else "PASS", backlink_findings))
            report.checks.append(Check("P26-P36 atomic PowerShell GNHF commands", "FAIL" if command_findings else "PASS", command_findings))
    except (zipfile.BadZipFile, ET.ParseError, KeyError, IndexError, ValueError) as exc:
        report.checks.append(Check("package readable", "FAIL", [{"error": str(exc)}]))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_prompt_kit_operability(args.workbook)
    print(json.dumps(report.to_dict(), indent=2) if args.json else report.render_text())
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
