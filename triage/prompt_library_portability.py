"""Read-only OOXML contract for Prompt Library row links and sparse navigation."""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "pr": PKG_REL_NS}
PROMPT_ID_RE = re.compile(r"^P\d{2,3}$", re.IGNORECASE)
COPY_LOCATION_RE = re.compile(r"^'?([^']+)'?!A1:A(\d+)$")
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
ALLOWED_CADENCES = (10, 5, 2)
LINK_COLUMNS = tuple(chr(code) for code in range(ord("B"), ord("O") + 1))
NAV_COLUMNS = ("A", "P")


@dataclass
class Finding:
    code: str
    message: str
    row: int | None = None
    cell: str | None = None


@dataclass
class PromptLibraryPortabilityReport:
    path: str
    valid: bool
    prompt_count: int
    cadence: int | None
    prompt_rows: list[int] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema_version": "prompt-library-portability-result/v1",
            "path": self.path,
            "valid": self.valid,
            "prompt_count": self.prompt_count,
            "cadence": self.cadence,
            "prompt_rows": self.prompt_rows,
            "findings": [asdict(item) for item in self.findings],
            "proof_ceiling": (
                "Static OOXML hyperlink, exact-copy-range, and sparse-navigation proof. "
                "Desktop Excel and Excel for Web click behavior remain runtime gates."
            ),
        }


def select_sparse_navigation_cadence(prompt_count: int) -> int:
    """Return the largest allowed divisor or fail closed."""
    if prompt_count <= 0:
        raise ValueError("prompt count must be positive")
    for cadence in ALLOWED_CADENCES:
        if prompt_count % cadence == 0:
            return cadence
    raise ValueError(
        f"prompt count {prompt_count} is not divisible by any allowed cadence: "
        f"{', '.join(map(str, ALLOWED_CADENCES))}"
    )


def _xml(zf: zipfile.ZipFile, part: str) -> ET.Element:
    try:
        return ET.fromstring(zf.read(part))
    except KeyError as exc:
        raise ValueError(f"missing OOXML part: {part}") from exc
    except ET.ParseError as exc:
        raise ValueError(f"malformed OOXML part {part}: {exc}") from exc


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = _xml(zf, "xl/sharedStrings.xml")
    return [
        "".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
        for item in root.findall("m:si", NS)
    ]


def _cell_text(cell: ET.Element, shared: Sequence[str]) -> str:
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


def _sheet_parts(zf: zipfile.ZipFile) -> dict[str, str]:
    workbook = _xml(zf, "xl/workbook.xml")
    rels = _xml(zf, "xl/_rels/workbook.xml.rels")
    targets = {item.attrib["Id"]: item.attrib.get("Target", "") for item in rels}
    result: dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        relationship = sheet.attrib.get(f"{{{REL_NS}}}id", "")
        target = targets.get(relationship, "")
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


def _cells(root: ET.Element, shared: Sequence[str]) -> dict[str, tuple[ET.Element, str]]:
    result: dict[str, tuple[ET.Element, str]] = {}
    for cell in root.findall(".//m:c", NS):
        reference = cell.attrib.get("r", "")
        if reference:
            result[reference] = (cell, _cell_text(cell, shared))
    return result


def _hyperlinks(root: ET.Element) -> dict[str, str]:
    return {
        item.attrib.get("ref", ""): item.attrib.get("location", "")
        for item in root.findall(".//m:hyperlinks/m:hyperlink", NS)
        if item.attrib.get("ref")
    }


def _last_content_row(root: ET.Element, shared: Sequence[str], column: str = "A") -> int:
    rows: list[int] = []
    for reference, (_, text) in _cells(root, shared).items():
        match = CELL_RE.match(reference)
        if match and match.group(1) == column and text.strip():
            rows.append(int(match.group(2)))
    return max(rows, default=0)


def _normalized_sheet_from_location(location: str) -> tuple[str, int] | None:
    match = COPY_LOCATION_RE.match(location)
    if not match:
        return None
    return match.group(1).replace("''", "'"), int(match.group(2))


def validate_prompt_library_workbook(path: str | Path) -> PromptLibraryPortabilityReport:
    workbook_path = Path(path).expanduser().resolve()
    findings: list[Finding] = []
    prompt_rows: list[int] = []
    cadence: int | None = None

    try:
        with zipfile.ZipFile(workbook_path) as zf:
            shared = _shared_strings(zf)
            sheets = _sheet_parts(zf)
            library_part = sheets.get("Prompt_Library")
            if not library_part:
                raise ValueError("Prompt_Library worksheet is missing")
            library_root = _xml(zf, library_part)
            cells = _cells(library_root, shared)
            links = _hyperlinks(library_root)

            for reference, (_, text) in cells.items():
                match = CELL_RE.match(reference)
                if match and match.group(1) == "C" and PROMPT_ID_RE.match(text.strip()):
                    prompt_rows.append(int(match.group(2)))
            prompt_rows.sort()
            if not prompt_rows:
                raise ValueError("Prompt_Library contains no prompt rows in column C")

            try:
                cadence = select_sparse_navigation_cadence(len(prompt_rows))
            except ValueError as exc:
                findings.append(Finding("SPARSE_CADENCE_UNAVAILABLE", str(exc)))

            last_library_row = prompt_rows[-1]
            for ordinal, row in enumerate(prompt_rows, start=1):
                prompt_id = cells.get(f"C{row}", (None, ""))[1].strip().upper()
                associated_sheet = f"{prompt_id}_COPY_SAFE"
                expected_location: str | None = None
                expected_sheet: str | None = None
                expected_end: int | None = None

                for column in LINK_COLUMNS:
                    reference = f"{column}{row}"
                    value = cells.get(reference, (None, ""))[1]
                    location = links.get(reference, "")
                    if not value:
                        findings.append(
                            Finding(
                                "PROMPT_ROW_VALUE_MISSING",
                                "B:O displayed values must remain populated",
                                row,
                                reference,
                            )
                        )
                    if not location:
                        findings.append(
                            Finding(
                                "PROMPT_ROW_LINK_MISSING",
                                "every B:O cell must link to the prompt tab copy range",
                                row,
                                reference,
                            )
                        )
                        continue
                    target = _normalized_sheet_from_location(location)
                    if target is None:
                        findings.append(
                            Finding(
                                "PROMPT_ROW_LINK_INVALID",
                                f"link is not an exact A1:A<n> copy range: {location}",
                                row,
                                reference,
                            )
                        )
                        continue
                    sheet_name, end_row = target
                    if expected_location is None:
                        expected_location = location
                        expected_sheet = sheet_name
                        expected_end = end_row
                    elif target != (expected_sheet, expected_end):
                        findings.append(
                            Finding(
                                "PROMPT_ROW_LINK_DRIFT",
                                "B:O cells on one prompt row must share one exact target",
                                row,
                                reference,
                            )
                        )

                if expected_sheet and expected_sheet != associated_sheet:
                    findings.append(
                        Finding(
                            "PROMPT_TARGET_SHEET_MISMATCH",
                            f"{prompt_id} row must target {associated_sheet}, not {expected_sheet}",
                            row,
                        )
                    )

                if expected_sheet:
                    prompt_part = sheets.get(expected_sheet)
                    if not prompt_part:
                        findings.append(
                            Finding(
                                "PROMPT_TARGET_SHEET_MISSING",
                                f"linked prompt sheet is missing: {expected_sheet}",
                                row,
                            )
                        )
                    else:
                        prompt_root = _xml(zf, prompt_part)
                        actual_end = _last_content_row(prompt_root, shared)
                        if actual_end != expected_end:
                            findings.append(
                                Finding(
                                    "PROMPT_COPY_RANGE_NOT_EXACT",
                                    f"linked A1:A{expected_end} but prompt content ends at A{actual_end}",
                                    row,
                                )
                            )

                should_navigate = cadence is not None and (ordinal - 1) % cadence == 0
                top_ref, bottom_ref = f"A{row}", f"P{row}"
                top_location = links.get(top_ref, "")
                bottom_location = links.get(bottom_ref, "")
                if should_navigate:
                    if top_location != "Prompt_Library!A1":
                        findings.append(
                            Finding(
                                "TOP_NAVIGATION_MISSING",
                                "cadence row A must link to Prompt_Library!A1",
                                row,
                                top_ref,
                            )
                        )
                    if bottom_location != f"Prompt_Library!P{last_library_row}":
                        findings.append(
                            Finding(
                                "BOTTOM_NAVIGATION_MISSING",
                                "cadence row P must link to the final Prompt Library row",
                                row,
                                bottom_ref,
                            )
                        )
                elif top_location or bottom_location:
                    findings.append(
                        Finding(
                            "SPARSE_NAVIGATION_DENSITY_DRIFT",
                            "A/P links may appear only on deterministic cadence rows",
                            row,
                        )
                    )
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        findings.append(Finding("WORKBOOK_READ_FAILED", str(exc)))

    return PromptLibraryPortabilityReport(
        path=str(workbook_path),
        valid=not findings,
        prompt_count=len(prompt_rows),
        cadence=cadence,
        prompt_rows=prompt_rows,
        findings=findings,
    )


def _safe_output(value: str | None) -> Path | None:
    if not value:
        return None
    output = Path(value).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[1]
    outputs = (repo_root / "Outputs").resolve()
    try:
        output.relative_to(outputs)
    except ValueError as exc:
        raise ValueError(f"report output must remain under {outputs}") from exc
    return output


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = validate_prompt_library_workbook(args.workbook)
    payload = report.to_dict()
    try:
        destination = _safe_output(args.output)
    except ValueError as exc:
        print(f"Prompt Library portability: FAIL: {exc}", file=sys.stderr)
        return 2
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        status = "PASS" if report.valid else "FAIL"
        print(
            f"Prompt Library portability: {status} "
            f"({report.prompt_count} prompts, cadence={report.cadence}, "
            f"findings={len(report.findings)})"
        )
        for finding in report.findings:
            location = f" row={finding.row}" if finding.row else ""
            cell = f" cell={finding.cell}" if finding.cell else ""
            print(f"- {finding.code}:{location}{cell} {finding.message}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
