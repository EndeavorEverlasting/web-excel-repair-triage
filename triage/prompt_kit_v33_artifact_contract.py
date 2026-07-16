"""Validate the generated AI Harness Prompt Kit V33 workbook UX contract.

This module is intentionally read-only. It validates the final workbook artifact
independently from the generator so a regression in generation and its internal
self-check cannot silently agree on the same broken output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from openpyxl import load_workbook
from openpyxl.cell import Cell
from openpyxl.utils import range_boundaries

LIBRARY_SHEET = "Prompt_Library"
LIBRARY_PROMPT_ID_COLUMN = 3
LIBRARY_SHEET_NAME_COLUMN = 15
LIBRARY_LAST_COLUMN = 16
CREAM_RGB = "FFF2CC"
CREAM_TABS = (
    "Prompt_Library",
    "Opportunity_Discovery",
    "P07_COPY_SAFE",
    "P46_COPY_SAFE",
)
EDITABLE_RANGES: Mapping[str, str] = {"Opportunity_Discovery": "A1:R100"}
REQUIRED_PROMPT_IDS = ("P45", "P46", "P47")
PROMPT_ID_RE = re.compile(r"^P\d{2,}$")
PROMPT_RANGE_RE = re.compile(r"^A1:A([1-9]\d*)$")
HYPERLINK_FORMULA_RE = re.compile(r'^=HYPERLINK\("((?:[^"]|"")*)"\s*,', re.IGNORECASE)


@dataclass(frozen=True)
class ArtifactContractResult:
    workbook: str
    sha256: str
    prompt_count: int
    prompt_ids: tuple[str, ...]
    findings: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict:
        return {
            "workbook": self.workbook,
            "sha256": self.sha256,
            "status": "PASS" if self.passed else "FAIL",
            "prompt_count": self.prompt_count,
            "prompt_ids": list(self.prompt_ids),
            "findings": list(self.findings),
            "proof_ceiling": (
                "OOXML workbook structure, internal range links, coordinated prompt-row "
                "formatting, required cream tab colors, prompt presence, and worksheet "
                "protection. Excel Desktop/Web open, clipboard behavior, and operator "
                "acceptance remain runtime gates."
            ),
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _target(cell: Cell) -> str:
    if cell.hyperlink:
        return cell.hyperlink.target
    value = cell.value
    if isinstance(value, str):
        match = HYPERLINK_FORMULA_RE.match(value)
        if match:
            return match.group(1).replace('""', '"')
    return ""


def _find_footer_row(library) -> int:
    for row in range(2, library.max_row + 1):
        text = " | ".join(
            str(library.cell(row=row, column=column).value)
            for column in range(1, LIBRARY_LAST_COLUMN + 1)
            if library.cell(row=row, column=column).value is not None
        )
        if "End of Prompt Library" in text or "↑ Top" in text:
            return row
    return library.max_row + 1


def _prompt_rows(library, footer_row: int) -> dict[str, tuple[int, str]]:
    prompts: dict[str, tuple[int, str]] = {}
    for row in range(2, footer_row):
        prompt_value = library.cell(row=row, column=LIBRARY_PROMPT_ID_COLUMN).value
        prompt_id = prompt_value if isinstance(prompt_value, str) and PROMPT_ID_RE.fullmatch(prompt_value) else ""
        if not prompt_id:
            sequence = library.cell(row=row, column=2).value
            if isinstance(sequence, int) or (isinstance(sequence, str) and sequence.isdigit()):
                prompt_id = f"P{int(sequence):02d}"
        sheet_name = library.cell(row=row, column=LIBRARY_SHEET_NAME_COLUMN).value
        if not prompt_id:
            continue
        if prompt_id in prompts:
            raise ValueError(f"duplicate Prompt Library ID: {prompt_id}")
        prompts[prompt_id] = (row, str(sheet_name or ""))
    return prompts


def _color_token(color) -> str:
    if color is None:
        return ""
    color_type = str(getattr(color, "type", "") or "")
    value = getattr(color, color_type, "") if color_type else ""
    tint = getattr(color, "tint", 0)
    return f"{color_type}:{value}:{tint}".upper()


def _normalize_rgb(color) -> str:
    if color is None or getattr(color, "type", None) != "rgb":
        return _color_token(color)
    value = getattr(color, "rgb", "")
    return str(value).upper()[-6:]


def _inside(bounds: tuple[int, int, int, int], row: int, column: int) -> bool:
    min_col, min_row, max_col, max_row = bounds
    return min_row <= row <= max_row and min_col <= column <= max_col


def _validate_protection(workbook, findings: list[str]) -> None:
    editable_bounds = {
        sheet_name: range_boundaries(cell_range)
        for sheet_name, cell_range in EDITABLE_RANGES.items()
    }
    for ws in workbook.worksheets:
        if not ws.protection.sheet:
            findings.append(f"worksheet is not protected: {ws.title}")
        bounds = editable_bounds.get(ws.title)
        for row in ws.iter_rows():
            for cell in row:
                allowed = bounds is not None and _inside(bounds, cell.row, cell.column)
                if allowed and cell.protection.locked:
                    findings.append(f"editable cell is locked: {ws.title}!{cell.coordinate}")
                    return
                if not allowed and not cell.protection.locked:
                    findings.append(f"cell outside editable range is unlocked: {ws.title}!{cell.coordinate}")
                    return
        if bounds is not None:
            min_col, min_row, max_col, max_row = bounds
            for row in ws.iter_rows(
                min_row=min_row,
                max_row=max_row,
                min_col=min_col,
                max_col=max_col,
            ):
                for cell in row:
                    if cell.protection.locked:
                        findings.append(f"editable cell is locked: {ws.title}!{cell.coordinate}")
                        return


def validate_artifact(path: Path) -> ArtifactContractResult:
    if not path.exists():
        raise FileNotFoundError(path)
    workbook = load_workbook(path, keep_links=True, data_only=False)
    findings: list[str] = []
    if LIBRARY_SHEET not in workbook.sheetnames:
        return ArtifactContractResult(
            workbook=str(path),
            sha256=_sha256(path),
            prompt_count=0,
            prompt_ids=(),
            findings=(f"missing required sheet: {LIBRARY_SHEET}",),
        )

    library = workbook[LIBRARY_SHEET]
    footer_row = _find_footer_row(library)
    try:
        prompts = _prompt_rows(library, footer_row)
    except ValueError as exc:
        findings.append(str(exc))
        prompts = {}

    expected_corners = {
        "A1": f"#'{LIBRARY_SHEET}'!A{footer_row}",
        "P1": f"#'{LIBRARY_SHEET}'!P{footer_row}",
        f"A{footer_row}": f"#'{LIBRARY_SHEET}'!A1",
        f"P{footer_row}": f"#'{LIBRARY_SHEET}'!P1",
    }
    for coordinate, expected in expected_corners.items():
        actual = _target(library[coordinate])
        if actual != expected:
            findings.append(f"{LIBRARY_SHEET}!{coordinate} target {actual!r} != {expected!r}")

    for required in REQUIRED_PROMPT_IDS:
        if required not in prompts:
            findings.append(f"missing required prompt: {required}")

    for prompt_id, (row, sheet_name) in sorted(prompts.items()):
        if not sheet_name:
            findings.append(f"{prompt_id} has no copy-safe sheet name")
            continue
        if sheet_name not in workbook.sheetnames:
            findings.append(f"{prompt_id} references missing sheet: {sheet_name}")
            continue
        forward = _target(library.cell(row=row, column=LIBRARY_PROMPT_ID_COLUMN))
        prefix = f"#'{sheet_name}'!"
        if not forward.startswith(prefix):
            findings.append(f"{prompt_id} forward link {forward!r} does not target {sheet_name}")
            continue
        prompt_range = forward[len(prefix):]
        range_match = PROMPT_RANGE_RE.fullmatch(prompt_range)
        if not range_match:
            findings.append(f"{prompt_id} forward link must select full A1:A<n> range: {forward!r}")
            continue
        last_row = int(range_match.group(1))
        ws = workbook[sheet_name]
        if not any(ws.cell(row=index, column=1).value not in (None, "") for index in range(1, last_row + 1)):
            findings.append(f"{sheet_name} prompt payload range is blank: {prompt_range}")
        expected_back = f"#'{LIBRARY_SHEET}'!A{row}:P{row}"
        for coordinate in ("B1", "E1", f"B{last_row}", f"E{last_row}"):
            actual = _target(ws[coordinate])
            if actual != expected_back:
                findings.append(f"{sheet_name}!{coordinate} target {actual!r} != {expected_back!r}")
        if prompt_id in REQUIRED_PROMPT_IDS:
            row_fills = {
                (
                    library.cell(row=row, column=column).fill.fill_type,
                    _normalize_rgb(library.cell(row=row, column=column).fill.fgColor),
                )
                for column in range(1, 17)
            }
            if len(row_fills) != 1 or next(iter(row_fills))[0] != "solid":
                findings.append(f"{prompt_id} Prompt Library row does not use one coordinated solid fill")
            prompt_cell = library.cell(row=row, column=LIBRARY_PROMPT_ID_COLUMN)
            if not prompt_cell.font.bold or prompt_cell.font.underline != "single":
                findings.append(f"{prompt_id} Prompt Library link is not bold and underlined")
        if (ws.column_dimensions["A"].width or 0) < 60:
            findings.append(f"{sheet_name} copy-safe column A is too narrow")

    for sheet_name in CREAM_TABS:
        if sheet_name not in workbook.sheetnames:
            findings.append(f"missing cream-tab sheet: {sheet_name}")
            continue
        actual = _normalize_rgb(workbook[sheet_name].sheet_properties.tabColor)
        if actual != CREAM_RGB:
            findings.append(f"{sheet_name} tab color {actual!r} != {CREAM_RGB!r}")

    _validate_protection(workbook, findings)
    prompt_ids = tuple(sorted(prompts))
    return ArtifactContractResult(
        workbook=str(path),
        sha256=_sha256(path),
        prompt_count=len(prompt_ids),
        prompt_ids=prompt_ids,
        findings=tuple(findings),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate AI Harness Prompt Kit V33 links, ranges, formatting, tabs, prompts, and protection."
    )
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    result = validate_artifact(args.workbook)
    payload = result.to_dict()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
