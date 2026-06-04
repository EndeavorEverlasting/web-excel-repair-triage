# 1 Marcus Recon Part-Number Relink Contract

## Purpose

Automate the 1 Marcus inventory recon workbook cleanup that was proven manually on the 2026-05-28 Web Excel-safe artifact.

The repo should generate a client-shareable recon workbook where the pivot/recon module is wired to the current dated Part Numbers tab, formulas point to the current tab, stale workbook references are removed, and Excel for Web does not trigger repair.

This lane is inventory recon. Billing remains a valid repo capability, but this contract does not replace or rewrite billing logic.

Related issue: #30

## Business workflow

The operator updates the 1 Marcus recon workbook and pivots after physical or spreadsheet reconciliation work.

The updated workbook may contain a dated consolidated part-number reference tab from manual iteration, usually named like:

```text
5-28-2026 Part Numbers
```

Delivery workbooks must use the stable tab name:

```text
Part Numbers
```

Put dates in filenames, manifests, and visible pivot titles — not in the Part Numbers sheet tab name.

The operator may remember to rename the workbook and tab title. If they forget, the repo should infer the intended date and repair the mismatch before client delivery.

## Inputs

The first implementation should support local private inputs only. Do not commit real client workbooks.

Expected input patterns:

```text
Candidates/
  *1 Marcus*Recon*.xlsx
  *Part Numbers*.xlsx        optional, if consolidated reference is separate
```

Suggested CLI shape:

```bash
python -m triage.one_marcus_recon.cli \
  --input "Candidates/Tab-Linked 1 Marcus Compiled_Recon_Integrated_2026-05-28.xlsx" \
  --date auto \
  --output "Outputs/1_Marcus_Recon_2026-05-28_WEBSAFE.xlsx"
```

Optional flags:

```text
--part-number-tab "5-28-2026 Part Numbers"
--pivot-tab "1M Recon Pivot Module"
--dry-run
--strict
--report-json Outputs/1_Marcus_Recon_2026-05-28_preflight.json
```

## Date inference precedence

If the date is not supplied, infer it in this order:

1. Explicit CLI/config date.
2. Workbook filename date.
3. Existing latest dated Part Numbers tab.
4. File modified timestamp as a last-resort fallback, with warning.

The generated tab name must use:

```text
Part Numbers
```

Dated tab names (e.g. `5-28-2026 Part Numbers`) are source-only candidates detected during date inference. Relink and generate modes rename or emit the stable `Part Numbers` tab.

## Required behavior

### Tab handling

- Detect existing Part Numbers candidate tabs (dated or undated).
- Rename the chosen source tab to the stable `Part Numbers` tab.
- Preserve all unrelated tabs, sheet order, visibility, tab colors, tables, drawings, styles, filters, validation, conditional formatting, print settings, and workbook metadata unless explicitly changed.
- Never delete old tabs unless a cleanup flag explicitly says to do so.

### Formula rewiring

- Find formulas referencing older dated Part Numbers tabs.
- Repoint them to the stable `Part Numbers` tab.
- Correctly quote sheet names with spaces and hyphens.
- Localize formulas that point to stale external workbook references when the target tab exists locally.
- Report formulas that still reference old dates after rewrite.
- Report formulas that still reference external workbooks after rewrite.

### Pivot/recon module wiring

- The pivot/recon module must resolve from the current dated Part Numbers tab.
- Helper logic should prefer stable part/model identifiers over loose descriptions.
- Calculation labels should remain plain text or formula-clean values.
- Do not use hyperlink formulas inside helper/calculation labels used by rollups or validation.
- Presentation-only navigation links are allowed only where they cannot affect calculation logic.

### Web Excel safety

When formulas or workbook XML are patched:

- Remove stale `calcChain.xml` so Excel for Web can rebuild formulas.
- Remove unused `xl/externalLinks/*` package parts after formula localization.
- Remove or repair dangling relationship references caused by external link cleanup.
- Do not reserialize broad workbook structures when a surgical package/XML patch is sufficient.

## Output package

Expected outputs:

```text
Outputs/
  1_Marcus_Recon_YYYY-MM-DD_WEBSAFE.xlsx
  1_Marcus_Recon_YYYY-MM-DD_preflight.json
  1_Marcus_Recon_YYYY-MM-DD_manifest.json
  1_Marcus_Recon_YYYY-MM-DD_review_queue.csv
  1_Marcus_Recon_YYYY-MM-DD_carryover.md
  1_Marcus_Recon_YYYY-MM-DD_DELIVERY.zip
```

## Required report fields

The JSON report should include:

```text
input_workbook
output_workbook
inferred_update_date
final_part_number_tab
pivot_tab
renamed_tabs
formula_cells_scanned
formula_cells_patched
stale_tab_references_removed
remaining_stale_tab_references
external_link_parts_removed
remaining_external_links
calc_chain_removed
formula_error_scan
webexcel_preflight_pass
warnings
```

## Web Excel gates

Before success, scan for:

- `#REF!`
- `#VALUE!`
- `#NAME?`
- `#DIV/0!`
- `#N/A`
- stale dated Part Numbers tab references
- stale external workbook references
- unnecessary `xl/externalLinks/` package parts
- broken workbook relationships
- broken worksheet relationships
- stale `calcChain.xml` after formula rewrites
- `inlineStr`
- `ns0:`
- `xmlns:ns0`
- `_xlfn.`
- `_xludf.`
- `_xlpm`

## Acceptance criteria

1. Given a workbook containing stale references to `5-07-2026 Part Numbers`, the output rewrites formulas to `'5-28-2026 Part Numbers'` when the update date is 2026-05-28.
2. Given stale external workbook references for part-number lookups, the output localizes formulas when the dated Part Numbers tab exists locally.
3. Given formula rewrites, `calcChain.xml` is removed.
4. Given localized formulas, unneeded `xl/externalLinks/*` parts are removed.
5. The pivot/recon module resolves against the current dated Part Numbers tab.
6. Unrelated tabs and workbook presentation structure are preserved.
7. Dry run reports intended changes without writing a workbook.
8. Ambiguous multiple date candidates produce a warning or strict-mode failure.
9. The output passes Web Excel preflight.
10. No private workbook data or generated client workbooks are committed.

## Tests to add

Use sanitized fixtures only.

Suggested tests:

```text
test_infers_recon_update_date_from_filename
test_renames_part_number_tab_to_target_date
test_rewrites_formulas_from_old_part_number_tab
test_localizes_external_part_number_formulas
test_removes_external_link_parts_after_localization
test_removes_calc_chain_after_formula_patch
test_preserves_unrelated_tabs_and_sheet_order
test_dry_run_reports_without_output_write
test_warns_on_ambiguous_date_candidates
test_webexcel_preflight_rejects_stale_refs_and_stopship_tokens
```

## Non-goals for first sprint

- Do not build a general workbook framework before this concrete engine works.
- Do not merge billing behavior into this recon lane.
- Do not commit real 1 Marcus workbooks.
- Do not delete tabs or hide evidence by default.
- Do not claim Excel Web success without a package-level preflight at minimum.

## Operator rule

Automation should catch the boring mistake: the workbook date, Part Numbers tab title, formula references, and package metadata must agree before the file goes to a client.
