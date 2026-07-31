# Finding: duplicate worksheet row records can survive XML gates and lose data during Excel repair

Date: 2026-07-31  
Status: confirmed from candidate/repaired workbook pair; detector + bounded repair added  
Severity: stop-ship when duplicate `<row r="…">` records are present

## Executive finding

The 2026-07-31 field candidate contained **13 duplicate worksheet row records** on its newly added activity-ledger sheet:

`r=24` through `r=36` each appeared twice.

The first occurrences were in the normal ascending `sheetData` sequence. After row 210, a second set of rows 24–36 had been appended to hold the right-side assignment-device detail. The XML was well-formed, but the logical worksheet row index was not unique and row order moved backward from 210 to 24.

Excel's repaired copy removed the duplicate row records. That normalized the worksheet, but it also discarded the cells stored only in the appended duplicate rows, including the 11-line assignment detail at `Q26:X36`. The repaired table headers were regenerated as generic `Column1` … `Column8`, demonstrating that "Excel repaired the file" is **not** equivalent to "the repair preserved workbook semantics."

## Why the old package gates missed it

Generic checks can all pass while duplicate row records remain:

- the worksheet XML is syntactically valid;
- every cell reference can itself be valid;
- relationships and content types are unrelated;
- there is no `#REF!` requirement for this failure.

The missing invariant was: **within each worksheet `sheetData`, row indices must be unique and monotonic.**

## Root generation mistake

When adding cells to columns far to the right of an existing ledger, the generator appended brand-new `<row r="24">` … `<row r="36">` elements rather than locating the existing row elements and adding new `<c>` children to those rows.

This is an important harness rule for any direct OOXML writer:

> Adding a cell to an existing row means editing that row record, not appending another row record with the same `r` value.

## New guard

`triage.worksheet_row_integrity.scan_worksheet_row_integrity()` reports:

- duplicate `row/@r` values; and
- non-monotonic row ordering inside `sheetData`.

Run:

```bash
python -m triage.worksheet_row_integrity path/to/workbook.xlsx --json
```

A clean workbook exits `0`; a workbook with duplicate/non-monotonic rows exits `1`.

## Bounded repair

The same module provides a conservative repair path:

```bash
python -m triage.worksheet_row_integrity candidate.xlsx \
  --repair-out output.xlsx \
  --json
```

It merges duplicate row records only when:

1. their cell references are disjoint;
2. donor duplicate rows contain cells/whitespace only; and
3. appending the donor cells keeps cell columns strictly increasing.

If any duplicate occurrence overlaps the same cell coordinate or would require guessing, the repair stops with `DuplicateRowConflict` and writes no accepted output.

The source is never overwritten.

## Acceptance lesson

A candidate/repaired pair must be checked at two levels:

1. **structural delta:** what did Excel normalize or remove?
2. **semantic preservation:** did cell records, table payloads, formulas, comments, or other operational data disappear?

For this incident, the repaired workbook removed the duplicate rows but also lost the right-side assignment-detail payload. That makes the Excel-produced repaired file evidence for diagnosis, not automatically the new golden workbook.

## Privacy / fixture policy

No operational workbook or user data is committed. Tests synthesize tiny OOXML ZIPs that reproduce only the duplicate-row invariant.
