# Use Case: Monthly Header and Conditional Formatting Regression Guard

Captured: 2026-06-03

## Problem

The roster logs improved over time. Monthly headers became clearer, live sheets became easier to read, and conditional formatting became more useful for identifying partial days, overtime, malformed punches, and review conditions.

Those improvements can be lost when copying sheets, regenerating workbooks, or comparing old and new roster logs.

## Required behavior

Workbook comparison and generation must protect:

- monthly header formatting
- date row readability
- freeze panes
- conditional-formatting coverage
- partial-day highlighting
- overtime highlighting
- malformed-punch highlighting
- weekend/day-off visual logic

## Comparison checks

For like-artifact comparisons, inspect:

- first two header rows
- row heights
- fills
- fonts
- alignment
- merged cells
- freeze panes
- conditional-formatting rule counts
- conditional-formatting ranges
- conditional-formatting formulas

## Regression rules

Flag review when:

- a newer workbook has fewer CF rules without explanation
- CF ranges shrink unexpectedly
- monthly headers differ from the accepted profile
- freeze panes are removed
- one-off CF fragments appear where broad ranges are expected

## Generation rules

Generated roster/billing workbooks should use a named formatting profile instead of ad hoc formatting.

Suggested profile fields:

```text
header_fill
header_font
month_row_height
date_row_height
weekend_fill
partial_fill
overtime_fill
malformed_fill
full_day_fill
review_fill
```

## Test expectations

Synthetic tests should cover:

- identical header profile
- changed header fill
- removed freeze panes
- CF count decrease
- CF range fragmentation
- restored standard CF profile

## Practical rule

Formatting is not fluff here. It is the control surface techs use to avoid duplicate review and bad submissions.
