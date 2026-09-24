# Admin Billing Summary — OpenAI-format contract (native tables)

## Purpose

Generate per-month **Internal** and **Client** billing summaries in the OpenAI WEBSAFE layout from the Active Roster Log. Both variants share the same resolved totals. Internal copies keep technician, punch, Neuron detail, Bonita tracker, and review evidence. Client copies are aggregate billing-support documentation only.

Engine: [triage/admin_billing_summary/](triage/admin_billing_summary/) (`reader` → `aggregator` → `exporter` → `cli`).

See also [WEBEXCEL_REPAIR_PHASE0_FINDINGS.md](WEBEXCEL_REPAIR_PHASE0_FINDINGS.md).

## Project resolution

Per staff/date: `Assignments Override > Worked Projects > Assignments main > Live default`.

Net hours = gross span − lunch (≥8h:1.0, ≥6h:0.5, else 0).

## Deliverables (per month)

| File | Tabs |
| --- | --- |
| `{Month}_{Year}_Billing_Summary_Internal.xlsx` | Start Here, Executive Dashboard, Monthly Summary, Project Summary (+ chart), Tech Summary, Tech Project Summary (+ chart), `{Month} Neuron Hours`, `{Mon YY}` Bonita tracker, Review Flags, CF Dictionary, WebExcel QC |
| `{Month}_{Year}_Billing_Summary_Client.xlsx` | Start Here (support/historical/privacy wording), Executive Dashboard, Monthly Summary, Project Summary (+ chart), `{Mon YY}` aggregate Neuron compatibility tab. **No** technician names, punches, Tech Summary, Tech Project Summary, `{Month} Neuron Hours`, Review Flags, CF Dictionary, or WebExcel QC. |

Standalone Bonita workbook remains `Bonita_Neuron_Track_Hours_April_May_2026.xlsx` (two tabs only) via `triage.nw_prj_neuron_track_hours.bonita_cli`.

## CLI

```powershell
python -m triage.admin_billing_summary.cli `
  --roster-log "<roster>.xlsx" `
  --months 2026-04 2026-05 `
  --out-dir "Outputs\admin_billing_summary_2026_06_02" `
  --prior "<April prior copy>.xlsx" `
  --websafe
```

Sidecars (gitignored under `Outputs/`):

```text
{Month}_{Year}_Billing_Summary_Internal.xlsx
{Month}_{Year}_Billing_Summary_Client.xlsx
{stem}_preflight.json (per variant)
{Month}_{Year}_Billing_Summary_review_queue.csv
{Month}_{Year}_Billing_Summary_Internal_delta.json   # April when --prior set
admin_billing_summary_manifest.json
index.html                    # human review portal (see docs/SIDECAR_HTML_PORTAL.md)
```

## Web Excel safety

- Native `Table` objects with `TableStyleMedium4`.
- `fix_inlinestr` from [triage/xlsx_utils.py](triage/xlsx_utils.py) after save when openpyxl emits `inlineStr` (spec-correct `sharedStrings` count).
- **Not** the legacy private `_repair_inlinestr` in the Neuron exporter (count corruption risk).

## Tests

[tests/test_admin_billing_summary.py](tests/test_admin_billing_summary.py) — resolution, Internal/Client tab sets, native tables, Neuron detail vs summary totals, Bonita tab Neuron-only, preflight, delta.

[tests/test_admin_billing_client_hygiene.py](tests/test_admin_billing_client_hygiene.py) — client disclosure boundary: aggregate-only client copy, support/historical wording, internal audit detail retained.

## Known gaps

- Internal `{Mon YY}` still uses the **Bonita two-line** Neuron tracker (not the full OpenAI analytics detail table). Client `{Mon YY}` is aggregate Neuron support only.
- `Billing Bucket Snapshot` / trucking prose from the hand-made April workbook are not in this OpenAI layout.
- Submitted payroll Regular/OT is not in the roster (informational only if a feed is added later).
- `ASSIGNMENT TYPE` on the Internal Bonita tab remains operator-classified.
