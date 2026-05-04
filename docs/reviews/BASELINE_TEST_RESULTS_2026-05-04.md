# Baseline Test Results - 2026-05-04

Branch: candidate/2026-05-04-web-excel-triage-suite

## Targeted Tests

Command:

python -m pytest tests/test_roster_parser.py tests/test_attendance_report.py -q

Result:

66 passed in 13.36s

## Full Suite

Command:

python -m pytest -q

Result:

10 failed, 226 passed, 5 skipped, 6 errors

## Notes

The targeted roster and attendance-report tests passed.

The full-suite failures appear outside the immediate #16/#17 scope.

Failure clusters:

- Billing regression layout mismatches
- Invoice DOCX fixture/package read errors under attached_assets
- Older malformed-row expectations that no longer match current parser behavior

Proceeding with #16/#17 against the targeted roster and attendance-report test baseline.
