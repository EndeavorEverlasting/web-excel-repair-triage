# Billing Context Real Workbook E2E Runbook

Use this after synthetic CLI tests pass. **Do not commit real billing workbooks.**

## Prerequisites

```powershell
git checkout main
git pull --ff-only
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Drop inputs (gitignored)

Place five workbooks in [`Candidates/`](../Candidates/):

| File | Role |
|------|------|
| Track-hours workbook | Neuron track hours (April/May) |
| April context workbook | Admin billing context / task tracker |
| Roster log | Active roster log |
| Admin copy | NW PRJ tech hours admin copy |
| Dashboard | NW PRJ resolution ledger dashboard |

## Run CLI

```bash
python -m triage.billing_context.cli \
  --track-hours "Candidates/<track-hours>.xlsx" \
  --april-context "Candidates/<april-context>.xlsx" \
  --roster-log "Candidates/<roster-log>.xlsx" \
  --admin-copy "Candidates/<admin-copy>.xlsx" \
  --dashboard "Candidates/<dashboard>.xlsx" \
  --out-dir Outputs \
  --html \
  --zip \
  --internal-xlsx
```

## Acceptance checklist

- [ ] CLI exits 0; stdout JSON includes `manifest` with all `exists: true`
- [ ] `Outputs/billing_context_artifacts_YYYY-MM-DD.zip` exists
- [ ] Leadership XLSX columns: Date, Tech, Hours, Work Context only
- [ ] No `Tracker Import` sheet unless `--include-tracker-import`
- [ ] `billing_context_internal_detail.xlsx` present when `--internal-xlsx`
- [ ] Open `Outputs/billing_context_dashboard.html` via `file://` (no network)
- [ ] Mismatch CSV: formula-like values prefixed with `'`
- [ ] No visible `...`, `…`, `TBD`, `TODO` in leadership Work Context
- [ ] No `#REF!`, `#VALUE!`, etc. in generated workbooks
- [ ] `Neuron Installation` is not the dominant work context category

## Ahead / Behind report

After the CLI run, generate the cross-source alignment report:

```powershell
python -m triage.billing_context.ahead_behind_report
```

Open `Outputs/billing_context_ahead_behind.html` in your browser. It shows:

- **Ahead/Behind Matrix** — which source has entries another source lacks
- **Technician drill-down** — who has the most missing entries or hour deltas
- **Actionable fixes** — exactly what to add or reconcile to bring sources into sync

> If `track_hours` is far **ahead** of `roster_log` / `admin_copy`, the roster/admin sheets are missing rows. Add them, re-run the CLI, and the delta should drop.

## Automated guard

CI runs synthetic E2E via [`tests/test_billing_context_cli_e2e.py`](../tests/test_billing_context_cli_e2e.py) — no real workbooks required.
