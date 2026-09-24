# Use Case: Latest Source Tracker Intake for Regeneration

Captured: 2026-06-03

## Problem

When billing summaries are regenerated, the engine must know whether it has the latest validated tracker. A previous workbook may be structurally usable but stale after project attribution or attendance corrections are made.

Specific trigger: Rezaul Roman was updated to be part of the Neuron project. If that update is only in a later tracker, summaries generated from an earlier tracker are not final.

## Required behavior

Before regenerating billing summaries, the pipeline must identify the latest validated source workbook and compare it against any previously used source.

## Intake checks

The generator should record:

- source workbook filename
- source workbook modified timestamp when available
- workbook core metadata
- relevant sheet names
- latest populated roster date
- latest populated Worked Projects date
- override table presence
- explicit project-attribution entries

## Regeneration rule

If the user reports a material update that affects billing totals or project attribution, regenerate from the updated source tracker.

Material updates include:

- staff moved into Neuron project
- corrected punch time
- corrected day-off evidence
- override table change
- conditional-formatting change that affects review visibility
- expected-hours rule change

## Output requirement

Every generated billing package should include a machine-readable provenance JSON file with:

```text
source_workbook
source_sheets_used
source_months
generated_at
material_assumptions
known_review_items
```

## Test expectations

Synthetic tests should cover:

- older tracker rejected when newer tracker has changed project assignment
- regenerated summaries reflect latest attribution
- provenance JSON records the source workbook name
- no silent reuse of stale source after material update

## Practical rule

If a tracker has been updated after the last generated summary, use the updated tracker. Billing arithmetic is only as good as the source it drank from.
