# NW PRJ April/May Billing Summary Engine — Contract

Package: `triage/nw_prj_billing_summary/`
Tests: `tests/test_nw_prj_billing_summary.py` (fixture-only)
Direction: **Roster Log to Admin Sheet** (see `AGENTS.md` / `docs/BILLING_PIPELINE_DIRECTIONAL_CONTRACT.md`)

## Goal

Produce a single combined April + May NW PRJ billing summary as a Web Excel-safe
workbook plus preflight / review / manifest / ZIP sidecars, generated locally
from private source workbooks. No private workbook is ever committed; tests use
sanitized fixtures only.

## Inputs

- `--roster-log` (required): Active Roster Log `.xlsx`
  - `Live - {Month YYYY}` wide form: `Staff Name | Project | <Mon DD - Clock In/Out> ...`
  - `Worked Projects - {Month YYYY}` (optional): per-date project classification
  - `Assignments - {Month YYYY}` (optional): per-date override table
- `--invoices` (optional): invoice files (`.docx`) parsed via `triage.invoice_parser`
- `--months` (default `2026-04 2026-05`)

## Resolution & doctrine rules

1. April and May are both in scope.
2. Friday is the reporting batch marker. Mon–Fri map to that week's Friday.
3. Weekend work rolls to the **next** Friday batch.
4. Project resolution: **Worked-Project cell > Assignments override > Live default**.
5. Raw punch notes are evidence, not authority; note-bearing rows go to review.
6. Notes are preserved in the internal review queue, never in admin tabs.
7. Admin-facing tabs are clean submission outputs, not reasoning scratchpads.
8. Source workbooks are never mutated.
9. Non-member names (`Yostinn Minaya`, `Steven Marques`/`Inventory`) are excluded
   from Project Team totals by default and routed to review.
10. `Rich`/`Richard Perez` full/long admin days are **not** downgraded to partial
    on hours alone (pinned full-day guard); only a truly missing punch flags.
11. Partial hours, missing roster, and mismatches route to the review queue and
    are kept out of admin totals.
12. Lunch deduction follows the roster policy (≥8h → 1.0, ≥6h → 0.5, else 0).

## Outputs (under `--out-dir`)

```
NW_PRJ_Billing_Summary_April_May_2026_WEBSAFE.xlsx
NW_PRJ_Billing_Summary_April_May_2026_manifest.json
NW_PRJ_Billing_Summary_April_May_2026_review_queue.csv
NW_PRJ_Billing_Summary_April_May_2026_preflight.json
NW_PRJ_Billing_Summary_April_May_2026_DELIVERY.zip   (with --zip)
```

Workbook tabs: `Dashboard`, one per month, `Friday Batches`, `By Project`,
`Invoice Pivot`.

## Web Excel safety

`fix_inlinestr` is applied to the saved workbook, then a self-contained preflight
(`preflight.py`) scans the OOXML package for stop-ship tokens (`inlineStr`,
`ns0:`, `xmlns:ns0`, `_xlfn.`, …), `calcChain.xml`, `xl/externalLinks/*`, error
values, and broken relationships. `--websafe` exits non-zero if preflight fails.

## Reuse

- `triage.roster_parser`: lunch policy + Assignments override loading.
- `triage.nw_prj_neuron_track_hours.reader`: note-aware punch parsing, clock
  formatting, worked-project lookup.
- `triage.xlsx_utils.fix_inlinestr`: Web Excel-safe string repair.
- Preflight + manifest + review-queue + ZIP pattern from the three proven engines.
