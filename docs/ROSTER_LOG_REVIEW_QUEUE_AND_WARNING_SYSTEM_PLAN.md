# Roster Log Review Queue and Warning System Plan

Captured: 2026-06-03

## Source workbook observed

The current uploaded roster log shows a mature but warning-light workbook structure:

- 75 sheets total
- monthly `Live`, `Automated`, `Assignments`, and `Worked Projects` sheets
- review-adjacent tabs already exist, including `Expected Hours - May 2026`, `Expected Hours Rules`, `Billing Exceptions - May 2026`, `Unassigned Hours - May 2026`, `Billing Summary - Internal`, and `Admin Summary Export`
- May Live sheet has expanded conditional formatting compared with the older May roster, but conditional formatting alone is not enough for the next stage

## Problem

The roster log needs more than conditional formatting. Color can show a symptom, but it does not create a durable work queue.

Current risks:

- missing project corrections may only be visible through indirect output errors
- partial hours can be visually flagged but not queued for resolution
- note-bearing punches may require parser-aware classification
- CASR/day-off evidence should be accepted without polluting billing exceptions
- manual review items can get scattered across monthly tabs
- billing summaries can be generated before review status is truly closed

## Target concept

Add a workbook-native review queue that sits inside the roster log and acts as the operational control surface for unresolved attendance and project-assignment issues.

This should become the workbook's review cockpit.

## Proposed new sheets

### `Review Queue`

One row per active review item.

Recommended columns:

| Column | Purpose |
|---|---|
| Review ID | Stable identifier for the issue |
| Month | Month being reviewed |
| Date | Work date |
| Staff | Technician/person |
| Source Sheet | Sheet where the issue was detected |
| Source Cell(s) | Cell references involved |
| Rule Code | Machine-readable issue type |
| Severity | Stop Ship / Review / Info |
| Current Status | Open / In Review / Resolved / Accepted / Ignored |
| Detected Value | Raw value or observed condition |
| Suggested Resolution | Proposed fix or classification |
| Resolution Value | Final human-approved correction |
| Resolution Source | Manual / Tracker / Worked Projects / Note / CASR / Rule |
| Owner | Person responsible for clearing it |
| Last Reviewed | Date/time reviewed |
| Notes | Human-readable explanation |

### `Review Rules`

Rule definitions used to populate the queue.

Recommended columns:

| Column | Purpose |
|---|---|
| Rule Code | Stable machine-readable code |
| Rule Name | Human-readable name |
| Applies To | Live / Assignments / Worked Projects / Expected Hours / Billing |
| Severity | Stop Ship / Review / Info |
| Default Status | Open / Accepted / Info |
| Description | What the rule means |
| Suggested Action | What to do next |
| Share Output Behavior | Hide / Summarize / Block Export |

### `Review Dashboard`

Visual summary of queue state.

Minimum dashboard cards:

- open Stop Ship items
- open Review items
- resolved this run
- accepted non-billable explanations
- missing project corrections
- note-bearing punches accepted
- stale expected-hours indicators

## Rule codes

Initial required rule codes:

| Rule Code | Severity | Meaning |
|---|---|---|
| `MISSING_PROJECT_CORRECTION` | Stop Ship | Work is billable but final project attribution is missing or unresolved |
| `PROJECT_CONFLICT` | Stop Ship | Worked Projects, correction table, and note evidence disagree |
| `PARTIAL_HOURS_REVIEW` | Review | Actual hours are below expected and not already explained |
| `OT_REVIEW` | Review | Hours exceed standard day and need accepted context |
| `NOTE_BEARING_PUNCH` | Info/Review | Punch includes note text and should be parsed, preserved, and classified |
| `CASR_DAY_OFF_ACCEPTED` | Info | CASR issue explains no billable hours; do not mark incomplete |
| `INVALID_PUNCH_PAIR` | Stop Ship | Time pair cannot be parsed into valid hours |
| `MISSING_EXPECTED_HOURS` | Review | Expected hours are blank or unavailable for a worked date |
| `STALE_EXPECTED_HOURS_SNAPSHOT` | Review | Expected Hours tab does not reflect latest roster date/rules |
| `UNASSIGNED_WORKED_HOURS` | Stop Ship | Worked hours exist but no resolved project exists |
| `MISSING_REZAUL_NEURON_ATTRIBUTION` | Stop Ship | Rezaul Roman appears in the tracker but lacks explicit Neuron attribution when expected |

## Workbook behavior

### Conditional formatting remains useful, but secondary

CF should highlight cells and row states, but the queue owns resolution.

Live/Assignments/Worked Projects tabs should use CF for quick detection:

- red: Stop Ship
- amber: Review
- blue/purple: OT/extended
- green: resolved/accepted
- grey: day off/weekend/non-billable explanation

### Review Queue owns status

A row should stay open until it has:

- status set to `Resolved`, `Accepted`, or `Ignored`
- resolution source recorded
- resolution value recorded when needed
- reviewer/owner recorded when applicable

## Export gate

Billing summary generation should check the Review Queue before creating share-ready billing artifacts.

Suggested export rules:

- Stop Ship open: block share-ready export
- Review open: allow internal export, warn on share-ready export
- Info open: allow export
- Accepted CASR/day-off item: exclude from billable totals and do not count as incomplete

## Implementation plan

### PR 1: Doctrine and schema

- Add this plan document
- Add schema contract for Review Queue and Review Rules
- Add tests using synthetic workbook fixtures

### PR 2: Queue builder

- Scan Live, Automated, Assignments, Worked Projects, Expected Hours, and billing exception tabs
- Generate Review Queue rows deterministically
- Preserve source sheet and cell references
- Do not mutate source tabs silently

### PR 3: Workbook integration

- Add Review Queue, Review Rules, and Review Dashboard tabs to generated roster logs
- Add dropdowns for severity/status/source fields
- Add CF to queue rows based on severity and status
- Add dashboard cards and counts

### PR 4: Export gate

- Require the billing summary generator to inspect queue state
- Block share-ready export when open Stop Ship items exist
- Include machine-readable review status in provenance JSON

### PR 5: Regression hardening

- Add tests for Cyen April 2 note-bearing punch handling
- Add tests for Patricia CASR day-off acceptance
- Add tests for Rezaul Roman Neuron attribution
- Add tests for stale expected-hours detection
- Add tests for missing project correction detection

## Acceptance criteria

A roster log review queue implementation is acceptable when:

- it creates a deterministic `Review Queue` from the latest roster workbook
- missing project corrections are visible as queue rows, not only CF
- Patricia CASR-style day-off entries are accepted and excluded cleanly
- Cyen April 2 Bonita note-bearing punch remains parseable and billable
- Rezaul Roman requires explicit Neuron attribution before inclusion
- share-ready billing export is blocked by unresolved Stop Ship rows
- queue output is values-backed and Excel for Web safe
- no private workbook data is committed to the public repo

## Design principle

The workbook should not merely show warnings. It should assign work, preserve evidence, and prove that review is closed before billing leaves the building.
