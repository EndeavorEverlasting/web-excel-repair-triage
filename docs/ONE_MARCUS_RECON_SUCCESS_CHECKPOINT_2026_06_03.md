# One Marcus Recon Success Checkpoint - 2026-06-03

## Status

A functional One Marcus inventory recon artifact was reached after multiple failed candidates.

The working checkpoint is the workbook saved by the operator in OneDrive after validating the executive view in Excel for Web and then applying sheet protection manually.

Do not treat earlier generated candidates as successful just because they opened, styled correctly, or passed local package checks. The success condition is the artifact that combined all required behaviors at once.

## Successful artifact requirements

The One Marcus inventory recon artifact must include:

- `1M Recon Pivot Module` as the executive-facing view
- `Part Numbers` as the source stock edit surface
- `Visual` column inside the executive rollup table
- row-level in-cell quantity progression bars in the `Visual` column
- calm slate/charcoal styling from `configs/spreadsheet_style_v1.json`
- no claim text telling recipients the workbook is Web Excel-safe
- no `%20` text in workbook-visible titles or names
- no protection requirement for the first functional generator pass

Protection is a follow-up lane. It should not block recovery of the functional artifact.

## Required executive visual field

The executive visual field is not a separate chart. It is an in-cell visual field embedded in the `1M Recon Pivot Module` table.

Expected layout:

```text
Inventory Rollup by Item | Total Qty | Visual | Lines | ...
```

The `Visual` column must contain a compact progression bar aligned to the row quantity. The prior useful pattern was based on `REPT("█", ...)`.

## Failed artifact lessons

Failed outputs included at least one of these defects:

- opened in Excel for Web but lacked the `Visual` column
- had improved tab colors but no executive visual field
- used a separate chart as a substitute for the embedded visual field
- used file names or workbook-visible text polluted by URL encoding such as `%20`
- claimed Web Excel safety inside the workbook text
- over-focused on sheet protection before the functional executive view was correct
- passed local checks while still failing the operator's actual Excel for Web review

## Operator doctrine

The operator's Excel for Web review wins over local confidence.

When operator feedback says a field is missing, do not defend local verification. Reopen the artifact, inspect the exact tab and cell region, and prove the requested field exists in the workbook before responding.

## Checkpoint naming

Use concise file names for handoff artifacts:

```text
1M_Recon_READY.xlsx
1M_Recon_READY.zip
```

Avoid long URLs or names with spaces when the delivery interface may flatten links or expose encoded spaces.

## Follow-up lanes

After functional output is proven:

1. Codify the visual field generator.
2. Codify the slate styling system.
3. Add a regression fixture that proves `Visual` exists in `1M Recon Pivot Module`.
4. Add a style-only pass test proving formula counts and formula text are unchanged.
5. Add sheet protection as a separate PR only after the functional output path is stable.
