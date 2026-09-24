# PR Plan: Roster Log Review Queue Sprint

Captured: 2026-06-03

## Branch suggestion

```text
feat/roster-log-review-queue-warning-system
```

## PR title

```text
feat: add roster log review queue and warning gate plan
```

## Purpose

Upgrade the roster log from a conditionally formatted workbook into a review-controlled billing source. Conditional formatting remains useful, but the workbook needs a formal review queue that tracks missing project corrections, partial/OT review, note-bearing punches, CASR/day-off evidence, stale expected-hours snapshots, and unassigned worked hours.

## Grounding from latest roster workbook

The latest roster log already contains:

- monthly `Live` sheets
- monthly `Automated` sheets
- monthly `Assignments` sheets
- monthly `Worked Projects` sheets
- `Expected Hours - May 2026`
- `Expected Hours Rules`
- `Billing Exceptions - May 2026`
- `Unassigned Hours - May 2026`
- `Billing Summary - Internal`
- `Admin Summary Export`

This means the next step is not inventing a new workbook from scratch. The next step is adding a durable review layer over the existing workbook system.

## Scope

### In scope

- Document Review Queue schema
- Document Review Rules schema
- Define warning rule codes
- Define export-gate behavior
- Define acceptance criteria for implementation
- Plan tests using synthetic workbooks

### Out of scope for this first PR

- Committing private roster workbooks
- Mutating production roster files
- Generating share-ready billing outputs
- Building the full queue engine in the same PR unless small and well-tested

## Required rule codes

```text
MISSING_PROJECT_CORRECTION
PROJECT_CONFLICT
PARTIAL_HOURS_REVIEW
OT_REVIEW
NOTE_BEARING_PUNCH
CASR_DAY_OFF_ACCEPTED
INVALID_PUNCH_PAIR
MISSING_EXPECTED_HOURS
STALE_EXPECTED_HOURS_SNAPSHOT
UNASSIGNED_WORKED_HOURS
MISSING_REZAUL_NEURON_ATTRIBUTION
```

## Review Queue required columns

```text
Review ID
Month
Date
Staff
Source Sheet
Source Cell(s)
Rule Code
Severity
Current Status
Detected Value
Suggested Resolution
Resolution Value
Resolution Source
Owner
Last Reviewed
Notes
```

## Review Rules required columns

```text
Rule Code
Rule Name
Applies To
Severity
Default Status
Description
Suggested Action
Share Output Behavior
```

## Export gate behavior

```text
Open Stop Ship item  -> block share-ready billing export
Open Review item     -> allow internal export; warn on share-ready export
Open Info item       -> allow export
Accepted day off     -> exclude from billable totals, do not mark incomplete
```

## Implementation follow-up PRs

1. `feat/roster-review-queue-schema`
   - create schema constants and docs
   - add synthetic workbook fixtures

2. `feat/roster-review-queue-builder`
   - scan Live, Automated, Assignments, Worked Projects, Expected Hours, Billing Exceptions
   - emit deterministic queue rows

3. `feat/roster-review-dashboard`
   - add Review Queue, Review Rules, Review Dashboard tabs to generated roster logs
   - add dropdowns, CF, and dashboard cards

4. `feat/billing-export-review-gate`
   - prevent share-ready billing output when Stop Ship rows remain open
   - include queue status in provenance JSON

## Acceptance criteria for this planning PR

- repo contains a clear review-queue doctrine
- repo contains a clear PR implementation plan
- no private workbook data is committed
- warning rules are explicit
- export-gate behavior is explicit
- future implementation can be tested with synthetic workbook fixtures

## Notes for implementation agent

Do not confuse conditional formatting with workflow state. CF helps the eye. The Review Queue controls the process.

The goal is to make unresolved review impossible to miss and difficult to accidentally bypass.
