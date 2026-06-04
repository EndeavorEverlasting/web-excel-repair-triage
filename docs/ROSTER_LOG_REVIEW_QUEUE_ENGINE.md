# Roster Log Review Queue Engine

XML-graft engine that reproduces the blessed reference workbook pattern:

- **Stage A (`review-only`)**: Review Dashboard-first layer (Review Queue, Review Rules, CF Dictionary)
- **Stage B (`live-cf-only`)**: Append global operator CF to every `Live - ...` tab via column-cloning
- **`full`**: Stage A + B

## Quick start

```powershell
# Extract operator CF pack from local blessed ZIP (once; commits configs/)
python scripts/extract_roster_operator_pack.py `
  --reference-zip "Candidates/Roster Log/Roster_Log_ReviewQueue_CF_2026-06-03_2340_ALL_LIVE_CF_REPAIR_SAFE.zip" `
  --out-dir configs/roster_log_review_queue

# Stage B only (input already has review tabs)
python -m triage.roster_log_review_queue --mode live-cf-only `
  --input "<roster>.xlsx" --output "Outputs/Roster_Log_CF.xlsx" `
  --provenance-out "Outputs/Roster_Log_CF.provenance.json"

# Full pipeline (Stage A scaffold + Stage B)
python -m triage.roster_log_review_queue --mode full `
  --input "<roster>.xlsx" --output "Outputs/Roster_Log_FULL.xlsx" `
  --zip-out "Outputs/Roster_Log_FULL.zip"
```

## Modes

| Mode | Delivers |
|------|----------|
| `live-cf-only` | Append operator CF to all Live tabs (like 2340 artifact) |
| `review-only` | Review layer graft (Stage A — follow-up) |
| `full` | Review layer + Live CF |
| `blank` | Empty template shells (Stage A — follow-up) |

## Live CF patcher

The operator CF pack (`configs/roster_log_review_queue/operator_cf_pack.json`) holds:

1. **Project column block** — 1 rule on column B (`AND($A3<>"",$B3="")`)
2. **Clock pair block** — 6 rules per in/out column pair (PTO, missing punch, long/OT/partial shift, note-bearing)

For each Live sheet, `live_column_map` detects clock pairs from row-2 headers (`Mon DD - Clock In | Clock Out`). `live_cf_patcher` clones templates with column letter substitution and sequential priorities via `triage/cf_engine.apply_cf_dictionary(..., mode="append")`.

**No `openpyxl.save()`** on the roster — only ZIP/XML graft. `openpyxl` read-only is used for header scanning only.

## Provenance

Each run emits JSON matching the blessed contract (`live_cf`, `live_cf_counts_after`, `verification`, `repair_safety.openpyxl_save_used: false`).

## Compare

```powershell
python -m triage.roster_log_compare.compare `
  --left "<older>.xlsx" `
  --right "<generated>.xlsx" `
  --out artifacts/roster_log_comparison.xlsx `
  --json-out artifacts/roster_log_comparison.json
```

## Config layout

```
configs/roster_log_review_queue/
  operator_cf_pack.json    # 6-rule template + DXF styles
  cf_markers.json          # Preflight formula substrings
  review_rules_seed.json   # 17 rule codes
  priority_policy.json
```

## Status

| Component | Status |
|-----------|--------|
| `live_cf_patcher` + configs | Shipped |
| `preflight` + `provenance` | Shipped |
| `live-cf-only` CLI | Shipped |
| Stage A review graft + queue builder | Follow-up |
| `blank` template mode | Follow-up |
