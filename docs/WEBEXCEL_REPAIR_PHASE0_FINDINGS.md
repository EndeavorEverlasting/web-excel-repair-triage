# Web Excel repair — Phase 0 findings (2026-06-02)

## Compared artifacts

- OpenAI WEBSAFE: `Outputs/neuron_track_hours_2026_06_02/openai got close/` (Neuron, Client Update, Internal Review)
- Current generators: `Outputs/admin_billing_summary_2026_06_02/`, Bonita standalone

## Findings

1. **`sharedStrings` count mismatch alone is not the repair trigger.** OpenAI Client Update declares `count=2497` with only `2411` `t="s"` references and opens cleanly in Excel for Web.

2. **Current billing outputs (post-fix commit) are structurally sound:** no `inlineStr`, `sharedStrings` `count` equals total `t="s"` refs on April/May preferred-format builds.

3. **Excel-for-Web “repair” on older May/Bonita copies dropped `xl/sharedStrings.xml` entirely** and rewrote `calcPr` — consistent with a corrupted or hostile package, not a count off-by-one.

4. **`_repair_inlinestr` zip surgery is the historical culprit** when it rewrote `sharedStrings` with `uniqueCount` as `count`. Billing exporter path must use a **single clean `wb.save()`** with **no post-processing**.

5. **Structural gap vs OpenAI:** OpenAI workbooks use **native Excel Tables** (`xl/tables/tableN.xml`, `TableStyleMedium4`); our billing summaries used styled ranges only.

## Locked build approach

- Native `openpyxl.worksheet.table.Table` + `TableStyleInfo` for every data region.
- Title row 1, subtitle row 2, blank rows 3–4, header row 5, data row 6+.
- One `wb.save()` per artifact, then **`fix_inlinestr`** from `triage/xlsx_utils.py` only when openpyxl emits `inlineStr` (native tables do). Uses spec-correct `sharedStrings` total ref count — not the legacy Neuron `_repair_inlinestr`.
- Bonita standalone keeps existing layout; billing embeds the same `_write_month_tab` source of truth.
