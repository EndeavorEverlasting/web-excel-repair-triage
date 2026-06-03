# Use Case: Patricia CASR Issue Day-Off Handling

Captured: 2026-06-03

## Problem

Patricia was marked incomplete even though the roster entry clearly indicated a CASR issue. That should not be treated as malformed attendance requiring billing work. It should be accepted as evidence that the day is not billable work time for the target billing output.

## Required behavior

The attendance parser and billing generator must recognize CASR issue notes as valid non-work/day-off evidence when no billable punch pair is present.

## Classification

Suggested normalized status:

```text
non_billable_day_off_evidence
```

Suggested reason code:

```text
casr_issue
```

## Billing behavior

When a row indicates CASR issue and lacks a billable punch pair:

- do not mark as incomplete for billing submission
- do not include hours in billable totals
- preserve the note in internal review output
- keep the share-ready summary clean

## Difference from malformed attendance

CASR issue is not the same as a broken punch.

Broken punch:

- intended workday may need correction
- should appear in exception review

CASR issue day-off evidence:

- explains why there are no billable hours
- should be excluded cleanly
- should not pollute billing exceptions unless policy requests it

## Test expectations

Synthetic tests should cover:

- Patricia row with CASR issue note and blank punches
- CASR issue note with zero hours
- malformed punch without CASR issue
- CASR issue plus accidental partial punch requiring review

## Practical rule

If the sheet explains the absence with CASR issue, do not call it incomplete. The pipeline should accept the explanation and disregard the hours as a day off.
