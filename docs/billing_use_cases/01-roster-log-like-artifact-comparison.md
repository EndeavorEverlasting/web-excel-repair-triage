# Use Case: Compare Like-Family Roster Logs

Captured: 2026-06-03

## Problem

Two roster logs from the same month/family can get mixed up during fast billing work. Filename and workbook metadata alone are not enough to decide which file is the operational candidate.

Example discovered during triage: a 2026-05-19 May billing roster and a 2026-06-02 May billing roster both had similar workbook metadata, but the 2026-06-02 file was the better operational candidate because its content showed later roster corrections and more May conditional-formatting coverage.

## Required behavior

Build a read-only comparison engine that accepts two .xlsx roster logs and outputs:

- recommended file to use
- evidence behind the recommendation
- changed dates
- affected staff
- changed punch cells
- conditional-formatting differences
- override-table status
- expected-hours status
- structural risks

## Evidence ranking

Content beats metadata.

Priority order:

1. Validated attendance content
2. Workbook sheet structure
3. Override table functionality
4. Conditional-formatting coverage
5. Expected-hours recency
6. Filename date
7. Workbook embedded metadata

## Output artifacts

The engine should create:

- JSON summary for automation
- XLSX comparison report for human review

Recommended tabs:

- Verdict
- Workbook Metadata
- Sheet Structure Diff
- Live Date Diffs
- CF Summary
- Override Table Check
- Expected Hours Check
- Risk Flags

## Stop-ship risks

Flag manual review when:

- content recency conflicts with filename recency
- override table is missing or not referenced by formulas
- changed punch cells affect submitted billing dates
- expected-hours tab appears stale
- CF changes are fragmented into suspicious one-off ranges

## Test cases

Synthetic fixtures must cover:

- identical workbooks
- newer filename with identical content
- older filename with newer content
- changed punches by date/staff
- added/removed CF rules
- missing override table
- stale expected-hours snapshot
- changed header styling

## Implementation lane

Suggested package:

```text
triage/roster_log_compare/
```

Suggested CLI:

```bash
python -m triage.roster_log_compare.compare \
  --left path/to/older.xlsx \
  --right path/to/newer.xlsx \
  --out artifacts/roster_log_comparison.xlsx \
  --json-out artifacts/roster_log_comparison.json
```
