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
