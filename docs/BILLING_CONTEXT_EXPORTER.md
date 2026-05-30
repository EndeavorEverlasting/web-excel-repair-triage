# Billing Context Exporter

Generate contextualized April/May billing artifacts and a self-contained browser dashboard.

**Classification rules (canonical):** [`BILLING_WORK_CONTEXT_RULES.md`](BILLING_WORK_CONTEXT_RULES.md)

**Output quality / leadership boundaries:** [`CONTEXTUALIZED_BILLING_ARTIFACTS.md`](CONTEXTUALIZED_BILLING_ARTIFACTS.md)

## Command

```bash
python -m triage.billing_context.cli \
  --track-hours "<track-hours.xlsx>" \
  --april-context "<task-context.xlsx>" \
  --roster-log "<roster-log.xlsx>" \
  --admin-copy "<admin-copy.xlsx>" \
  --dashboard "<dashboard.xlsx>" \
  --out-dir Outputs \
  --html \
  --zip \
  --internal-xlsx
```

Optional flags:

- `--include-tracker-import` — add internal Tracker Import sheet to monthly summaries
- `--internal-xlsx` — separate internal detail workbook with provenance columns
- `--zip` — bundle all outputs into one ZIP with manifest validation

Sprint carryover: [`ARTIFACT_SPRINT_CARRYOVER_2026-05-30.md`](ARTIFACT_SPRINT_CARRYOVER_2026-05-30.md)

## Outputs

| File | Purpose |
|------|---------|
| `Neuron_Project_Hours_April_May_2026_CONTEXTUALIZED_WEBSAFE.xlsx` | Row-level context by month + summary charts |
| `April_2026_Billing_Summary_CONTEXTUALIZED_CHARTED_WEBSAFE.xlsx` | April leadership summary with charts |
| `May_2026_Billing_Summary_CONTEXTUALIZED_CHARTED_WEBSAFE.xlsx` | May leadership summary with charts |
| `billing_context_dashboard.html` | Self-contained browser review (no Office, no network) |
| `billing_context_mismatches.json` / `.csv` | Internal cross-source mismatch report |

## Validation

```bash
python -m pytest tests/test_billing_context_rules.py tests/test_billing_context_reconcile.py tests/test_billing_context_html.py -q
```

Stop-ship checks (CLI enforces language and formula-error scan):

- `Neuron Installation` must not dominate work context
- Summary workbooks must contain charts
- Leadership workbooks must not contain blocked language or internal fields
- No `#REF!`, `#VALUE!`, etc.

## Related

- Admin posture pipeline: [`2026-05-20-admin-billing-context-pipeline.md`](2026-05-20-admin-billing-context-pipeline.md)
- NW PRJ dashboard (separate artifact family): [`NW_PRJ_DASHBOARD_V6_CONTRACT.md`](NW_PRJ_DASHBOARD_V6_CONTRACT.md)
