# Use Case: Share Tab Boundary

Captured: 2026-06-03

## Problem

Billing workbooks contain two kinds of material:

1. final summary material that can be shared
2. review/control material used to prove the summary

Those should not be mixed by accident.

## Required behavior

Generated billing workbooks must separate:

- share-ready summary tabs
- internal review tabs
- machine-readable outputs
- exception-review tabs

## Share-ready tabs may include

- final summarized hours
- month totals
- technician totals
- project totals
- clean billing categories
- charts and dashboard visuals
- concise review flags only when required

## Share-ready tabs should not include by default

- raw punch parsing internals
- scratch logic
- unresolved review commentary
- implementation caveats
- hidden helper columns

## Internal tabs may include

- parsed punch details
- note-bearing punch text
- raw project evidence
- override provenance
- rejected rows
- expected-hours warnings
- exception classifications

## Test expectations

Generated workbooks should be checked for:

- share tabs do not expose internal helper columns
- dashboard charts are present and populated
- internal tabs are retained only in internal artifact mode
- summary totals match internal detail totals

## Implementation note

This boundary should be part of the artifact profile, not handwritten per workbook.

Suggested mode flag:

```text
artifact_mode = internal | admin_share | leadership_share
```

Default billing summary mode should be `admin_share` unless an internal review workbook is explicitly requested.
