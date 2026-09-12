"""Read-only duplicate-cell, dimension-coverage, and merge-overlap checks for XLSX."""
from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from triage.prompt_kit_common import CELL_RE, NS, parse_ref, workbook_sheet_map, xml_root


@dataclass(frozen=True)
class WorksheetIntegrityIssue:
    code: str
    sheet: str
    detail: str


def _rectangles_overlap(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def inspect_worksheet_cell_integrity(path: str | Path) -> List[WorksheetIntegrityIssue]:
    issues: List[WorksheetIntegrityIssue] = []
    with zipfile.ZipFile(Path(path)) as zf:
        for sheet, part in workbook_sheet_map(zf).items():
            root = xml_root(zf, part)
            seen = set()
            max_col = 0
            max_row = 0
            for cell in root.findall(".//m:c", NS):
                ref = cell.attrib.get("r", "")
                if ref in seen:
                    issues.append(WorksheetIntegrityIssue("duplicate_cell_coordinate", sheet, ref))
                seen.add(ref)
                match = CELL_RE.fullmatch(ref)
                if not match:
                    issues.append(WorksheetIntegrityIssue("invalid_cell_coordinate", sheet, ref))
                    continue
                col_num = 0
                for char in match.group(1):
                    col_num = col_num * 26 + ord(char) - 64
                max_col = max(max_col, col_num)
                max_row = max(max_row, int(match.group(2)))
            dimension = root.find("m:dimension", NS)
            parsed_dimension = parse_ref(dimension.attrib.get("ref", "") if dimension is not None else "")
            if seen and (parsed_dimension is None or parsed_dimension[2] < max_col or parsed_dimension[3] < max_row):
                issues.append(WorksheetIntegrityIssue(
                    "dimension_excludes_explicit_cells",
                    sheet,
                    f"dimension={dimension.attrib.get('ref', '') if dimension is not None else ''}; max_col={max_col}; max_row={max_row}",
                ))
            merge_node = root.find("m:mergeCells", NS)
            merges: List[Tuple[str, Tuple[int, int, int, int]]] = []
            if merge_node is not None:
                for merge in merge_node.findall("m:mergeCell", NS):
                    ref = merge.attrib.get("ref", "")
                    parsed = parse_ref(ref)
                    if parsed is not None:
                        merges.append((ref, parsed))
                for index, (left_ref, left) in enumerate(merges):
                    for right_ref, right in merges[index + 1:]:
                        if _rectangles_overlap(left, right):
                            issues.append(WorksheetIntegrityIssue("overlapping_merge_rectangles", sheet, f"{left_ref} overlaps {right_ref}"))
    return issues


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        issues = inspect_worksheet_cell_integrity(args.workbook)
    except (FileNotFoundError, zipfile.BadZipFile) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"FAIL: {exc}")
        return 1
    payload = {"valid": not issues, "issues": [asdict(issue) for issue in issues]}
    print(json.dumps(payload, indent=2) if args.json else ("PASS" if not issues else "\n".join(f"FAIL {i.code} {i.sheet}: {i.detail}" for i in issues)))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
