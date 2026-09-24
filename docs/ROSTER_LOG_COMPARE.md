# Roster log comparison (internal)

Compare two **Active Roster Log** workbooks of the same family to pick the operational source before regenerating admin artifacts.

**Audience:** internal only. Do not submit comparison workbooks. Do not compare a roster log to a billing summary as a full workbook diff.

## CLI

```powershell
python -m triage.roster_log_compare.compare `
  --left Candidates/older_roster.xlsx `
  --right Candidates/newer_roster.xlsx `
  --out artifacts/roster_log_comparison.xlsx `
  --json-out artifacts/roster_log_comparison.json
```

## Outputs

| Output | Purpose |
|--------|---------|
| JSON | Machine-readable verdict, sections A–G, risk flags |
| XLSX | Human review tabs: Verdict, Metadata, Structure, Live Date Diffs, CF, Override, Expected Hours, Risk Flags |

## Verdict

- `use_right` / `use_left` — weighted evidence (content completeness, Live punches, CF coverage; filename/mtime are weak signals)
- `manual_review_required` — conflicting signals or equivalent evidence

Override checks are **structural** (table + formula refs). They do not validate recalculated results.

## Same-family spine

For intake scanning and submission readiness, use [`SAME_FAMILY_COMPARE.md`](SAME_FAMILY_COMPARE.md). Roster logs are classified as `active_roster_log` and delegated to this engine.

## Review Queue family

After running the review-queue graft engine ([`ROSTER_LOG_REVIEW_QUEUE_ENGINE.md`](ROSTER_LOG_REVIEW_QUEUE_ENGINE.md)), compare an older roster against the generated or blessed gold workbook:

```powershell
python -m triage.roster_log_compare.compare `
  --left Candidates/Roster Log/older.xlsx `
  --right Candidates/Roster Log/Roster_Log_ReviewQueue_CF_2026-06-03_2340_ALL_LIVE_CF_REPAIR_SAFE.xlsx `
  --out artifacts/roster_log_comparison.xlsx `
  --json-out artifacts/roster_log_comparison.json
```

Focus areas for review-queue artifacts:

- **CF coverage** on all `Live - ...` tabs (June gold: 95 groups, 30 clock pairs)
- **Review layer presence** — Review Dashboard first, Review Queue / Rules / CF Dictionary tabs
- **Live punch deltas** — section C in the comparison JSON/XLSX

Review Queue row-level diff is not yet in the compare engine; use the Review Queue sheet in the workbook for row review until `--include-review-queue` is added.
