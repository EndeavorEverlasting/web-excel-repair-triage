# One Marcus Recon Failure Analysis - 2026-06-03

## Purpose

This document records why multiple One Marcus recon artifacts failed before the accepted checkpoint, and what finally made the last functional submission correct.

The value is not the single workbook. The value is learning how to distinguish package validity, visual correctness, source-data correctness, and operator acceptance.

## Root problem

The failed versions confused different definitions of done.

A workbook was treated as successful when it satisfied one narrow check, such as:

- opened in Excel for Web
- passed local ZIP/XML inspection
- had improved tab colors
- retained some formulas
- contained some chart or visual-looking object
- had a plausible executive tab name

Those checks were necessary but not sufficient.

The actual requirement was narrower and more operational:

```text
The 1M Recon Pivot Module must contain the executive rollup with a visible Visual column using row-level quantity bars, while the workbook remains usable in Excel for Web.
```

## Failure modes observed

### 1. Package safety was mistaken for workbook success

Several outputs focused on removing OOXML hazards, stale links, calc chains, or unsupported package parts. That work mattered, but it did not prove the executive panel was correct.

A workbook can pass package checks and still be functionally wrong if the requested visual field is missing.

### 2. Separate charts were mistaken for the required visual field

The operator asked for the visual component in the executive tab. The response initially interpreted this as a separate graph/chart.

That was wrong.

The required visual aid was the embedded `Visual` column inside `1M Recon Pivot Module`, aligned row-by-row with `Inventory Rollup by Item` and `Total Qty`.

A separate chart can be useful, but it is not a substitute.

### 3. Styling was treated as the artifact instead of the presentation layer

Some versions had nicer tab colors and calmer formatting but lacked the embedded executive visual field. That is not success.

Style is valuable only after the functional layout is intact.

### 4. Sheet protection was introduced too early

Sheet protection is an operational guardrail, not the core deliverable.

Adding protection before the executive view was proven created extra noise. Protection belongs in a follow-up lane after the functional workbook path is stable.

### 5. Naming/link issues polluted review

Long filenames, spaces through sandbox URLs, and `%20` encoding created confusion. URL encoding is normal in links, but workbook-visible `%20` text or confusing handoff names are not acceptable.

The accepted handoff moved toward short names such as:

```text
1M_Recon_READY.xlsx
1M_Recon_READY.zip
```

### 6. Local confidence was trusted over operator review

The operator repeatedly verified in Excel for Web that the `Visual` field was missing. That feedback should have overridden local assertions immediately.

The correct behavior is: if the operator says a field is missing, inspect the exact worksheet and exact region before claiming success.

## What finally fixed it

The final accepted checkpoint succeeded because the build targeted the exact missing requirement instead of broad workbook hygiene.

The effective correction was:

1. Start from a workbook lineage that actually contained the executive visual field.
2. Ensure `1M Recon Pivot Module` contained `Visual` in the executive rollup table.
3. Ensure the `Visual` column appeared directly after `Total Qty`.
4. Populate the field with row-level in-cell progression bars.
5. Keep sheet protection out of the functional recovery pass.
6. Use concise output names.
7. Remove workbook-facing compatibility bragging text.
8. Let Excel for Web operator review decide success.

## Correct success definition

A One Marcus recon artifact is successful only when all of these are true:

- opens in Excel for Web without destructive repair behavior
- contains `1M Recon Pivot Module`
- contains `Part Numbers` as the source stock surface
- the executive rollup contains `Visual`
- `Visual` is directly associated with quantity rows, not a separate chart elsewhere
- the visual field uses visible in-cell quantity bars
- calm slate styling is preserved
- workbook-visible text does not claim compatibility status
- workbook-visible text does not contain URL-encoded `%20`
- operator validates the artifact in Excel for Web

## Test implications

Future tests must not stop at ZIP/XML preflight.

Add workbook semantic checks that inspect the actual executive panel:

- find `1M Recon Pivot Module`
- locate the executive rollup header row
- assert `Visual` exists
- assert `Visual` appears immediately after `Total Qty`
- assert at least the first several inventory rows have nonblank visual bars or accepted visual formulas
- assert the source stock sheet still exists
- assert style-only passes do not change formula text
- assert workbook-visible text excludes `%20` and compatibility claims

## Product insight

This failure sequence is exactly why the repo exists.

Excel artifacts fail across multiple layers:

1. Package layer: OOXML opens cleanly.
2. Web compatibility layer: Excel for Web accepts the workbook.
3. Semantic layer: required tabs, fields, formulas, and visual aids exist.
4. Presentation layer: the workbook is readable and executive-safe.
5. Operator layer: the person using the artifact confirms it solves the actual workflow.

The app should model those layers separately. Passing one layer must not imply the others passed.

## Doctrine

Do not call an artifact successful because it is merely valid.

Valid means it opens.

Correct means the requested operational surface exists and behaves.

Accepted means the operator validated it in the real target environment.
