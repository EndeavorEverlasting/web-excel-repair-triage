"""Validate dense, bounded copy-safe prompt worksheet surfaces without rewriting XLSX."""
from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Sequence

from triage.prompt_kit_common import prompt_surface, shared_strings, workbook_sheet_map, xml_root


@dataclass(frozen=True)
class CopySurfaceResult:
    sheet: str
    valid: bool
    first_payload_row: int
    last_payload_row: int
    populated_payload_row_count: int
    explicit_cell_count: int
    dimension: str
    issues: List[str]


def validate_copy_surface(path: str | Path, sheet: str) -> CopySurfaceResult:
    workbook = Path(path)
    issues: List[str] = []
    with zipfile.ZipFile(workbook) as zf:
        sheets = workbook_sheet_map(zf)
        if sheet not in sheets:
            return CopySurfaceResult(sheet, False, 0, 0, 0, 0, "", ["missing_sheet"])
        shared = shared_strings(zf)
        surface = prompt_surface(xml_root(zf, sheets[sheet]), shared)
    rows = surface["payload_rows"]
    first = min(rows) if rows else 0
    last = surface["last_payload_row"]
    if first != 1:
        issues.append("payload_does_not_begin_at_row_1")
    if not surface["dense"]:
        issues.append("internal_blank_or_noncontiguous_payload_rows")
    if surface["non_a_cells"]:
        issues.append("explicit_cells_outside_column_a")
    if surface["blank_explicit_cells"]:
        issues.append("explicit_blank_cells_present")
    if not surface["exact_cell_endpoint"]:
        issues.append("explicit_cells_extend_beyond_payload_endpoint")
    if surface["duplicates"]:
        issues.append("duplicate_cell_coordinates")
    expected_dimension = f"A1:A{last}" if last else "A1"
    if surface["dimension"] != expected_dimension:
        issues.append("dimension_does_not_equal_payload_endpoint")
    invariant = (last - first + 1) if first and last else 0
    if invariant != len(rows):
        issues.append("dense_payload_invariant_failed")
    return CopySurfaceResult(
        sheet=sheet,
        valid=not issues,
        first_payload_row=first,
        last_payload_row=last,
        populated_payload_row_count=len(rows),
        explicit_cell_count=len(surface["refs"]),
        dimension=surface["dimension"],
        issues=issues,
    )


def validate_copy_surfaces(path: str | Path, sheets: Optional[Sequence[str]] = None) -> List[CopySurfaceResult]:
    workbook = Path(path)
    with zipfile.ZipFile(workbook) as zf:
        available = workbook_sheet_map(zf)
    selected = list(sheets) if sheets else sorted(name for name in available if name.endswith("_COPY_SAFE"))
    return [validate_copy_surface(workbook, sheet) for sheet in selected]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook")
    parser.add_argument("--sheet", action="append", dest="sheets")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        results = validate_copy_surfaces(args.workbook, args.sheets)
    except (FileNotFoundError, zipfile.BadZipFile) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"FAIL: {exc}")
        return 1
    valid = bool(results) and all(result.valid for result in results)
    payload = {"valid": valid, "results": [asdict(result) for result in results]}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for result in results:
            print(f"[{'PASS' if result.valid else 'FAIL'}] {result.sheet}: A1:A{result.last_payload_row}; issues={','.join(result.issues) or 'none'}")
        print(f"Result: valid={str(valid).lower()}")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
