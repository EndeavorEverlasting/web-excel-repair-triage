# Roster Billing Pipeline Insights

This document captures operating insights for Web Excel repair, roster reconciliation, admin-sheet generation, and task-tracker alignment.

The goal is to help future agents and scripts produce correct artifacts from imperfect operational spreadsheets without exposing private work notes or turning submission outputs into scratchpads.

## Core Insight

The admin workbook is an output product. It is not where reasoning should happen.

The roster log and task tracker may contain messy operational truth. The admin sheet should receive clean, resolved, submission-safe values.

## Three Different Jobs

| Direction | Job | Risk if confused |
|---|---|---|
| Roster Log to Admin Sheet | Produce clean submission artifact | Internal notes leak or wrong hours are submitted |
| Roster Log to Task Tracker | Explain what hours supported | Context gets mistaken for billing output |
| Task Tracker to Roster Log | Propose reviewed backfill updates | Tracker notes silently rewrite the operational record |

## Artifact Philosophy

Scripts should accept imperfect source data and generate clean outputs.

Good source handling:

- tolerate notes in user-maintained sheets
- preserve useful context internally
- classify work through explicit rules and overrides
- flag ambiguous records for review
- continue generating non-blocked artifacts

Bad source handling:

- crash because a human wrote a note near a time
- silently rewrite project classification from weak evidence
- expose private notes in admin-facing sheets
- bury exceptions inside formatting only
- require users to make operational spreadsheets sterile

## Resolution Hierarchy

Use this order when resolving project classification:

1. Approved explicit override
2. Resolved worked-project rule
3. Assignment/default project
4. Raw note as evidence only
5. Exception queue if conflict remains

Raw notes are useful, but they are not final authority by themselves.

## Admin Output Contract

Admin-facing workbooks should be narrow, clean, and boring.

Default behavior:

- output only requested submission tabs
- preserve expected layout where possible
- avoid private notes
- avoid confidence fields
- avoid internal review columns
- keep formulas compatible with Excel for Web
- include only values needed for the recipient workflow

If the user asks for a one-tab admin workbook, do not include unrelated tabs.

## Internal Context Contract

Internal context artifacts can be richer.

They may include:

- exception queues
- project mapping rationale
- note-derived signals
- missing-day review items
- weekend handling notes
- staff/date/project contribution summaries

These internal artifacts should not be pasted into admin-facing workbooks unless explicitly requested.

## Web Excel Safety Rules

When producing or repairing Excel artifacts for this repository:

- prefer deterministic workbook generation
- keep formulas simple and compatible with Excel for Web
- avoid volatile or unsupported formula features unless explicitly required
- preserve workbook structure when repairing OOXML directly
- do not introduce namespace churn during XML repair
- test for broken references, missing table parts, and formula instability
- favor readable formatting that helps users follow logic

## Friday Reporting Insight

Friday is the reporting batch marker.

Work performed Monday through Friday maps to that Friday reporting batch. Weekend work generally rolls into the next Friday batch unless explicitly handled otherwise.

This lets scripts reason about weekly summaries without pretending every artifact is a full payroll system.

## Exception Handling Insight

Exceptions should be useful, not theatrical.

Good exceptions:

- staff name
- date
- source cell or source field when available
- issue type
- suspected cause
- proposed correction
- whether it blocks submission

Bad exceptions:

- vague warnings
- color-only signals
- private notes in public-facing outputs
- unreviewed automatic reclassification

## Minimum Acceptance Checks

A generated admin artifact should pass these checks:

- expected date range is present
- expected staff rows are present or intentionally excluded
- totals calculate correctly
- overrides are honored
- off-project work is excluded or classified correctly
- private notes are not exposed
- Excel for Web opens without repair prompts
- requested tab scope is respected

## Mental Model

Operational sheets are field notebooks.

Submission sheets are invoices wearing a tie.

The code must translate between them without losing truth or leaking the workshop floor into the boardroom.
