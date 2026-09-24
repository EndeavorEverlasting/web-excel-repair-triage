"""Detect and safely repair duplicate worksheet <row r="…"> records.

OOXML worksheets require one logical row record per row index. A generator can
accidentally append a second <row r="24"> later in sheetData when adding cells
in distant columns. The XML remains well-formed, but Excel repair may discard
one of the duplicate row records and therefore discard data.

The repair routine here is deliberately bounded: it merges duplicate rows only
when their cell references are disjoint and their merged cell order is strictly
increasing. Ambiguous overlaps stop instead of guessing.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

_ROW_RE = re.compile(rb'(<row\b[^>]*\br="(\d+)"[^>]*>)(.*?)(</row>)', re.DOTALL)
_CELL_RE = re.compile(rb'<c\b[^>]*\br="([A-Z]+\d+)"[^>]*(?:/>|>.*?</c>)', re.DOTALL)


class DuplicateRowConflict(RuntimeError):
    """Raised when duplicate rows cannot be merged without guessing."""


@dataclass(frozen=True)
class DuplicateRowFinding:
    sheet_part: str
    row: int
    occurrences: int
    cell_refs_by_occurrence: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class RowOrderFinding:
    sheet_part: str
    previous_row: int
    next_row: int
    occurrence_index: int


@dataclass
class WorksheetRowIntegrityReport:
    path: str
    duplicate_rows: list[DuplicateRowFinding] = field(default_factory=list)
    order_violations: list[RowOrderFinding] = field(default_factory=list)

    @property
    def pass_all(self) -> bool:
        return not self.duplicate_rows and not self.order_violations

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "pass": self.pass_all,
            "duplicate_rows": [asdict(item) for item in self.duplicate_rows],
            "order_violations": [asdict(item) for item in self.order_violations],
        }


def _worksheet_parts(z: zipfile.ZipFile) -> list[str]:
    return sorted(
        n for n in z.namelist()
        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
    )


def _cell_refs(row_body: bytes) -> tuple[str, ...]:
    return tuple(match.group(1).decode("ascii") for match in _CELL_RE.finditer(row_body))


def _col_number(cell_ref: str) -> int:
    match = re.match(r"^([A-Z]+)\d+$", cell_ref)
    if not match:
        raise ValueError(f"Unsupported cell ref: {cell_ref}")
    value = 0
    for ch in match.group(1):
        value = value * 26 + (ord(ch) - 64)
    return value


def scan_worksheet_row_integrity(path: str | Path) -> WorksheetRowIntegrityReport:
    path = str(path)
    report = WorksheetRowIntegrityReport(path=path)
    with zipfile.ZipFile(path, "r") as z:
        for part in _worksheet_parts(z):
            raw = z.read(part)
            matches = list(_ROW_RE.finditer(raw))
            row_numbers = [int(m.group(2)) for m in matches]
            counts = Counter(row_numbers)
            by_row: dict[int, list[tuple[str, ...]]] = defaultdict(list)
            for match in matches:
                by_row[int(match.group(2))].append(_cell_refs(match.group(3)))

            for row, count in sorted(counts.items()):
                if count > 1:
                    report.duplicate_rows.append(DuplicateRowFinding(
                        sheet_part=part,
                        row=row,
                        occurrences=count,
                        cell_refs_by_occurrence=tuple(by_row[row]),
                    ))

            for idx, (prev, nxt) in enumerate(zip(row_numbers, row_numbers[1:]), start=1):
                if nxt <= prev:
                    report.order_violations.append(RowOrderFinding(
                        sheet_part=part,
                        previous_row=prev,
                        next_row=nxt,
                        occurrence_index=idx,
                    ))
    return report


def _merge_duplicate_rows_in_sheet(raw: bytes, part: str) -> tuple[bytes, int]:
    matches = list(_ROW_RE.finditer(raw))
    if not matches:
        return raw, 0

    grouped: dict[int, list[re.Match[bytes]]] = defaultdict(list)
    for match in matches:
        grouped[int(match.group(2))].append(match)
    duplicate_rows = {row: items for row, items in grouped.items() if len(items) > 1}
    if not duplicate_rows:
        return raw, 0

    replacement_for_start: dict[int, bytes] = {}
    skipped_starts: set[int] = set()

    for row, items in sorted(duplicate_rows.items()):
        first = items[0]
        all_refs: set[str] = set()
        bodies: list[bytes] = []
        ordered_refs: list[str] = []

        for occurrence, match in enumerate(items, start=1):
            body = match.group(3)
            refs = list(_cell_refs(body))
            overlap = all_refs.intersection(refs)
            if overlap:
                raise DuplicateRowConflict(
                    f"{part} row {row} has overlapping duplicate cell refs: {sorted(overlap)}"
                )
            all_refs.update(refs)
            ordered_refs.extend(refs)
            bodies.append(body)

            if occurrence > 1:
                residue = _CELL_RE.sub(b"", body).strip()
                if residue:
                    raise DuplicateRowConflict(
                        f"{part} row {row} duplicate occurrence {occurrence} contains non-cell XML"
                    )

        col_order = [_col_number(ref) for ref in ordered_refs]
        if col_order != sorted(col_order) or len(col_order) != len(set(col_order)):
            raise DuplicateRowConflict(
                f"{part} row {row} duplicate cell order is not a safe append-only merge: {ordered_refs}"
            )

        merged_body = b"".join(bodies)
        replacement_for_start[first.start()] = first.group(1) + merged_body + first.group(4)
        skipped_starts.update(item.start() for item in items[1:])

    out: list[bytes] = []
    cursor = 0
    for match in matches:
        out.append(raw[cursor:match.start()])
        if match.start() in replacement_for_start:
            out.append(replacement_for_start[match.start()])
        elif match.start() in skipped_starts:
            pass
        else:
            out.append(match.group(0))
        cursor = match.end()
    out.append(raw[cursor:])
    return b"".join(out), sum(len(items) - 1 for items in duplicate_rows.values())


def repair_duplicate_rows(source: str | Path, destination: str | Path) -> dict:
    """Merge safe duplicate row records and write a new workbook.

    Only worksheet XML parts containing duplicate rows are rewritten. All other
    ZIP members are copied byte-for-byte. The source is never modified.
    """
    source = Path(source)
    destination = Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("destination must differ from source")

    pre = scan_worksheet_row_integrity(source)
    if not pre.duplicate_rows:
        shutil.copyfile(source, destination)
        return {
            "source": str(source),
            "destination": str(destination),
            "merged_rows": 0,
            "post_pass": pre.pass_all,
        }

    merged_count = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent, delete=False
    ) as handle:
        temp_path = Path(handle.name)

    try:
        with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(temp_path, "w") as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename.startswith("xl/worksheets/sheet") and info.filename.endswith(".xml"):
                    data, merged = _merge_duplicate_rows_in_sheet(data, info.filename)
                    merged_count += merged
                zout.writestr(info, data)

        post = scan_worksheet_row_integrity(temp_path)
        if not post.pass_all:
            raise DuplicateRowConflict(
                "repair output still fails row-integrity checks: "
                + json.dumps(post.to_dict(), sort_keys=True)
            )
        temp_path.replace(destination)
    except Exception:
        temp_path.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise

    return {
        "source": str(source),
        "destination": str(destination),
        "merged_rows": merged_count,
        "post_pass": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect or safely merge duplicate worksheet row records.")
    parser.add_argument("workbook", help="Path to .xlsx workbook")
    parser.add_argument("--repair-out", help="Write a repaired copy by merging only safe, disjoint duplicate rows")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    report = scan_worksheet_row_integrity(args.workbook)
    payload: dict = {"scan": report.to_dict()}
    exit_code = 0 if report.pass_all else 1

    if args.repair_out:
        payload["repair"] = repair_duplicate_rows(args.workbook, args.repair_out)
        exit_code = 0

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        state = "PASS" if report.pass_all else "FAIL"
        print(f"{state}: {args.workbook}")
        for finding in report.duplicate_rows:
            print(
                f"  duplicate row {finding.row} x{finding.occurrences} in {finding.sheet_part}: "
                f"{finding.cell_refs_by_occurrence}"
            )
        for finding in report.order_violations:
            print(
                f"  row order violation in {finding.sheet_part}: "
                f"{finding.previous_row} -> {finding.next_row}"
            )
        if "repair" in payload:
            print(
                f"  repaired: {payload['repair']['destination']} "
                f"({payload['repair']['merged_rows']} merged row records)"
            )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
