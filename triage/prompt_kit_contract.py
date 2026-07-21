"""Version-aware read-only contract validator for AI Harness Prompt Kit V20/V21.

The validator inspects OOXML directly. It never loads or saves the workbook with a
serializer. Package validity is not Excel-for-Web or clipboard field acceptance.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence
from xml.etree import ElementTree as ET

from triage.prompt_kit_common import (
    NS,
    cell_value,
    drawing_backlink_target,
    font_for_cell,
    prompt_surface,
    shared_strings,
    sheet_hyperlinks,
    styles,
    workbook_sheet_map,
    worksheet_cells,
    xml_root,
)

LIBRARY_HEADERS = [
    "Seq", "Prompt ID", "Prompt Type", "Prompt Class", "Sprint Path Role",
    "Use For Progress?", "Prompt Name", "Use This When", "Inspect First",
    "Expected Output", "Next Step", "Proof / Acceptance Gate", "Color",
    "Copy-Safe Sheet",
]
P21_REQUIRED_HEADINGS = [
    "MISSION",
    "SOURCE PROMPT DISPOSITION",
    "CONFLICT RESOLUTION",
    "IMMEDIATE OWNED SCOPE",
    "FORBIDDEN SCOPE",
    "REPOSITORY EVIDENCE REQUIRED",
    "EXECUTION CONTRACT",
    "VALIDATION",
    "DEFERRED DOCUMENTATION BRANCH",
    "FINAL HANDOFF",
]
P21_DISPOSITIONS = [
    "included",
    "merged",
    "deferred-to-docs",
    "superseded",
    "rejected-with-reason",
    "unresolved-blocker",
]


@dataclass(frozen=True)
class ContractProfile:
    name: str
    artifact_version: str
    prompt_count: int
    require_backlinks: bool
    require_p21_contract: bool


PROFILES: Mapping[str, ContractProfile] = {
    "v20": ContractProfile("v20", "V20", 21, False, False),
    "v21": ContractProfile("v21", "V21", 22, True, True),
}


@dataclass
class Check:
    name: str
    status: str
    findings: List[dict] = field(default_factory=list)
    summary: str = ""


@dataclass
class PromptKitContractReport:
    path: str
    profile: str
    checks: List[Check] = field(default_factory=list)

    @property
    def failures(self) -> List[Check]:
        return [check for check in self.checks if check.status == "FAIL"]

    @property
    def warnings(self) -> List[Check]:
        return [check for check in self.checks if check.status == "WARN"]

    @property
    def contract_valid(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "profile": self.profile,
            "contract_valid": self.contract_valid,
            "counts": {
                "pass": sum(check.status == "PASS" for check in self.checks),
                "warn": len(self.warnings),
                "fail": len(self.failures),
            },
            "checks": [asdict(check) for check in self.checks],
        }

    def render_text(self) -> str:
        lines = [f"PROMPT KIT {self.profile.upper()} CONTRACT"]
        for check in self.checks:
            suffix = f": {check.summary}" if check.summary else ""
            lines.append(f"[{check.status}] {check.name}{suffix}")
        lines.append("")
        lines.append(f"Result: contract_valid={str(self.contract_valid).lower()}")
        return "\n".join(lines)


def _infer_profile(zf: zipfile.ZipFile) -> ContractProfile:
    sheets = workbook_sheet_map(zf)
    return PROFILES["v21"] if "P21_COPY_SAFE" in sheets else PROFILES["v20"]


def _expected_prompt_ids(profile: ContractProfile) -> List[str]:
    return [f"P{index:02d}" for index in range(profile.prompt_count)]


def _legend_color_meanings(root, shared: Sequence[str]) -> Dict[str, List[str]]:
    cells = {ref: value for ref, (_, value) in worksheet_cells(root, shared).items()}
    meanings: Dict[str, List[str]] = {}
    for row in range(1, 200):
        color = cells.get(f"J{row}", "").strip()
        meaning = cells.get(f"K{row}", "").strip()
        if color:
            meanings.setdefault(color, []).append(meaning)
    return meanings


def validate_prompt_kit_contract(path: str | Path, profile: str = "auto") -> PromptKitContractReport:
    workbook = Path(path)
    requested = profile.lower()
    report = PromptKitContractReport(str(workbook.resolve()), requested)
    if not workbook.exists():
        report.checks.append(Check("file exists", "FAIL", [{"path": str(workbook)}]))
        return report
    try:
        with zipfile.ZipFile(workbook) as zf:
            selected = _infer_profile(zf) if requested == "auto" else PROFILES[requested]
            report.profile = selected.name
            sheets = workbook_sheet_map(zf)
            shared = shared_strings(zf)
            prompt_ids = _expected_prompt_ids(selected)
            copy_sheets = [f"{prompt_id}_COPY_SAFE" for prompt_id in prompt_ids]

            missing = [sheet for sheet in copy_sheets if sheet not in sheets]
            report.checks.append(Check(
                "required prompt tabs",
                "FAIL" if missing else "PASS",
                [{"missing": sheet} for sheet in missing],
                f"{len(copy_sheets) - len(missing)}/{len(copy_sheets)} present",
            ))
            for required in ("Prompt_Library", "Prompt_Class_Legend"):
                report.checks.append(Check(f"{required} present", "PASS" if required in sheets else "FAIL"))
            if missing or "Prompt_Library" not in sheets or "Prompt_Class_Legend" not in sheets:
                return report

            library_root = xml_root(zf, sheets["Prompt_Library"])
            library_cells = worksheet_cells(library_root, shared)
            header_findings = []
            for index, expected in enumerate(LIBRARY_HEADERS, 1):
                column = ""
                number = index
                while number:
                    number, remainder = divmod(number - 1, 26)
                    column = chr(65 + remainder) + column
                actual = library_cells.get(f"{column}1", (None, ""))[1]
                if actual != expected:
                    header_findings.append({"cell": f"{column}1", "expected": expected, "actual": actual})
            report.checks.append(Check("Prompt Library headers", "FAIL" if header_findings else "PASS", header_findings))

            row_findings = []
            surface_findings = []
            forward_findings = []
            backlink_findings = []
            hyperlinks = sheet_hyperlinks(zf, sheets["Prompt_Library"])
            for index, prompt_id in enumerate(prompt_ids):
                row = index + 2
                copy_sheet = f"{prompt_id}_COPY_SAFE"
                actual_id = library_cells.get(f"B{row}", (None, ""))[1]
                actual_sheet = library_cells.get(f"N{row}", (None, ""))[1]
                if actual_id != prompt_id:
                    row_findings.append({"cell": f"B{row}", "expected": prompt_id, "actual": actual_id})
                if actual_sheet != copy_sheet:
                    row_findings.append({"cell": f"N{row}", "expected": copy_sheet, "actual": actual_sheet})
                root = xml_root(zf, sheets[copy_sheet])
                surface = prompt_surface(root, shared)
                last = surface["last_payload_row"]
                expected_dimension = f"A1:A{last}"
                if (
                    not surface["dense"]
                    or surface["non_a_cells"]
                    or surface["blank_explicit_cells"]
                    or not surface["exact_cell_endpoint"]
                    or surface["duplicates"]
                    or surface["dimension"] != expected_dimension
                ):
                    surface_findings.append({"sheet": copy_sheet, **surface, "expected_dimension": expected_dimension})
                expected_location = f"{copy_sheet}!A1:A{last}"
                for ref in (f"B{row}", f"N{row}"):
                    if hyperlinks.get(ref) != expected_location:
                        forward_findings.append({"cell": ref, "expected": expected_location, "actual": hyperlinks.get(ref)})
                if selected.require_backlinks:
                    label, target = drawing_backlink_target(zf, sheets[copy_sheet])
                    expected_target = f"#Prompt_Library!B{row}"
                    if label != "Back to Prompt Library" or target != expected_target:
                        backlink_findings.append({
                            "sheet": copy_sheet,
                            "expected_label": "Back to Prompt Library",
                            "actual_label": label,
                            "expected_target": expected_target,
                            "actual_target": target,
                        })
            report.checks.append(Check("Prompt Library prompt rows", "FAIL" if row_findings else "PASS", row_findings))
            report.checks.append(Check("copy surfaces dense and bounded", "FAIL" if surface_findings else "PASS", surface_findings))
            expected_forward = selected.prompt_count * 2
            report.checks.append(Check(
                "forward links target exact payload ranges",
                "FAIL" if forward_findings or len(hyperlinks) != expected_forward else "PASS",
                forward_findings,
                f"{len(hyperlinks)}/{expected_forward} links",
            ))
            if selected.require_backlinks:
                report.checks.append(Check(
                    "drawing backlinks target matching library rows",
                    "FAIL" if backlink_findings else "PASS",
                    backlink_findings,
                    f"{selected.prompt_count - len(backlink_findings)}/{selected.prompt_count} valid",
                ))

            font_nodes, xfs = styles(zf)
            bad_fonts = sorted({font["name"] for font in font_nodes if font["name"] and font["name"] != "Aptos"})
            report.checks.append(Check("Aptos font family", "FAIL" if bad_fonts else "PASS", [{"font": font} for font in bad_fonts]))
            h_findings = []
            for row in range(2, selected.prompt_count + 2):
                cell = library_cells.get(f"H{row}", (None, ""))[0]
                info = font_for_cell(cell, font_nodes, xfs) if cell is not None else None
                if not info or info["name"] != "Aptos" or info["size"] != 12.0 or info["bold"] or info["italic"]:
                    h_findings.append({"cell": f"H{row}", "font": info})
            report.checks.append(Check("Prompt Library H body is 12-point regular Aptos", "FAIL" if h_findings else "PASS", h_findings))

            legend = _legend_color_meanings(xml_root(zf, sheets["Prompt_Class_Legend"]), shared)
            color_findings = []
            for row in range(2, selected.prompt_count + 2):
                color = library_cells.get(f"M{row}", (None, ""))[1].strip()
                meanings = legend.get(color, [])
                nonempty = [meaning for meaning in meanings if meaning]
                if len(meanings) != 1 or len(nonempty) != 1:
                    color_findings.append({"row": row, "color": color, "legend_meanings": meanings})
            report.checks.append(Check("library colors have one operational meaning", "FAIL" if color_findings else "PASS", color_findings))

            if selected.require_p21_contract:
                p21_root = xml_root(zf, sheets["P21_COPY_SAFE"])
                p21_lines = [
                    cell_value(cell, shared)
                    for cell in p21_root.findall(".//m:c", NS)
                    if re.fullmatch(r"A\d+", cell.attrib.get("r", ""))
                ]
                p21_text = "\n".join(p21_lines)
                p21_findings = []
                for heading in P21_REQUIRED_HEADINGS:
                    if heading not in p21_lines:
                        p21_findings.append({"missing_heading": heading})
                for disposition in P21_DISPOSITIONS:
                    if not re.search(rf"(?:^|\n)-?\s*{re.escape(disposition)}(?:$|\n)", p21_text):
                        p21_findings.append({"missing_disposition": disposition})
                for phrase in (
                    "No source requirement may disappear silently.",
                    "ARTIFACT EXECUTION MODE",
                    "branch name from the target repository existing conventions",
                ):
                    if phrase.lower() not in p21_text.lower():
                        p21_findings.append({"missing_contract_phrase": phrase})
                report.checks.append(Check("P21 consolidation contract", "FAIL" if p21_findings else "PASS", p21_findings))
    except KeyError:
        report.checks.append(Check("profile", "FAIL", [{"requested": requested, "allowed": ["auto", *PROFILES]}]))
    except (zipfile.BadZipFile, ValueError, ET.ParseError) as exc:
        report.checks.append(Check("package readable", "FAIL", [{"error": str(exc)}]))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook")
    parser.add_argument("--profile", choices=["auto", "v20", "v21"], default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_prompt_kit_contract(args.workbook, args.profile)
    print(json.dumps(report.to_dict(), indent=2) if args.json else report.render_text())
    return 0 if report.contract_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
