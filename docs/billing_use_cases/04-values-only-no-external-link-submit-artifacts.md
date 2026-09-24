# Use Case: Values-Only Submit Artifacts, No External Link Dependency

Captured: 2026-06-03

## Problem

Some workbook data is linked. Links can be useful while developing, but they create operational risk when tabs are pasted into other workbooks or when Excel requires the user to trust external links before graphs and summaries populate.

Observed failure mode:

- April billing summary graphs did not populate until workbook links were trusted.

That is not acceptable for a submit-ready billing artifact.

## Required behavior

Submit-ready billing summaries must be values-only for final totals and dashboard source tables.

Allowed during internal generation:

- formulas
- helper tabs
- linked development workbooks
- staging tables

Required in final share artifact:

- no external workbook dependencies
- chart source data stored locally
- dashboard source tables populated as values
- final totals independent of Trust Links prompts

## Generator modes

Suggested modes:

```text
internal_working = may preserve formulas and helper sheets
submit_values_only = must freeze external-link-sensitive outputs
```

## Verification

The final artifact check should flag:

- external workbook references
- formulas pointing to closed workbook paths
- charts with external source references
- empty dashboard chart sources
- defined names pointing outside the workbook

## Test expectations

Synthetic tests should confirm:

- workbook with linked formulas can be exported as values-only
- final dashboard chart source ranges contain static values
- external references are absent from final submit artifact

## Practical rule

If a graph only works after trusting links, the output is not submit-ready.
