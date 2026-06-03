# One Marcus Executive Visual Panel Protection

## Rule

The `1M Recon Pivot Module` sheet is the executive visual panel. It is not the stock data-entry sheet.

Generated One Marcus inventory recon workbooks must protect this tab by default so operators do not accidentally overwrite formulas, rollups, visual bars, or layout.

## Required source-edit surface

Operators should edit stock data only on the Part Numbers sheet.

## Required executive visual field

The executive tab must include the `Visual` column inside the `Inventory Rollup by Item` section.

That field is the primary visual aid for row-level stock magnitude. A separate chart is optional and must not replace the embedded executive visual field.

## Protection intent

Protection is operational guardrail behavior, not a security feature. It exists to prevent accidental edits to the leadership-facing panel.

## Acceptance checks

A generated One Marcus inventory recon workbook should pass when:

- `1M Recon Pivot Module` is protected by default
- Part Numbers remains the intended editable source surface
- the `Visual` field exists in the executive rollup table
- formulas and visual bars are preserved during restyling
- a chart, if present, is secondary to the embedded visual field
