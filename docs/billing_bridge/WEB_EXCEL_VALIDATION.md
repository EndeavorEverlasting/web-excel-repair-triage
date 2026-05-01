# Billing Bridge — Web Excel Validation Contract

## Purpose

This repo guards the workbook gate. It validates candidate billing workbooks for Web Excel compatibility **without changing the file**. The result is a JSON report that fits into the shared `billing_runs/YYYY-MM/validation/` artifact tree.

## Shared Manifest Contract

Every billing run MUST produce a `run_manifest.json` at:

```
billing_runs/
  YYYY-MM/
    inputs/
    normalized/
    workbook/
    validation/
    llm_packet/
    run_manifest.json
```

Core manifest fields:

```json
{
  "run_id": "billing-2026-04-001",
  "month": "2026-04",
  "source_files": [],
  "normalized_outputs": [],
  "workbook_outputs": [],
  "validation_outputs": [],
  "exceptions": [],
  "status": "draft | review | websafe | submitted"
}
```

## Validation Stages

All stages are read-only (no XML reserialization, no file writes).

| # | Stage | Purpose | Failure Action |
|---|-------|---------|--------------|
| 1 | Workbook ZIP scan | Verify the .xlsx is a well-formed OOXML ZIP package | Block candidate |
| 2 | STOP-SHIP token scan | Detect `_xlfn.`, `_xludf.`, `_xlpm.`, `AGGREGATE(` | Block candidate |
| 3 | Relationship target check | Verify every `.rels` Target resolves to a ZIP member | Block candidate |
| 4 | Table integrity check | Detect tableColumn names with illegal control characters | Block candidate |
| 5 | Conditional formatting integrity check | Detect `#REF!` in CF rules, OOB dxfId references | Block candidate |
| 6 | Shared string check | Detect shared-formula ref/bbox mismatches | Warn |
| 7 | Formula compatibility check | Flag known Web-Excel formula hazards | Warn |
| 8 | Billing profile detection | Confirm the workbook matches known billing structures | Warn |
| 9 | Web Excel probe-ready report | Emit a JSON artifact ready for downstream Graph probe | Pass through |

## Output Schema

```json
{
  "run_id": "billing-2026-04-001",
  "candidate_workbook": "CANDIDATE_April_2026_Billing_Bridge_WEBSAFE.xlsx",
  "status": "pass",
  "web_excel_safe": true,
  "checks": {
    "stop_ship_tokens": "pass",
    "relationships": "pass",
    "tables": "pass",
    "conditional_formatting": "pass",
    "shared_strings": "pass",
    "formulas": "warn"
  },
  "warnings": [],
  "failures": []
}
```

- `status`: `pass` | `fail` | `warn`
- `web_excel_safe`: `true` only when status is `pass` and no blocking failures exist.
- `checks`: per-stage verdict (`pass` | `warn` | `fail`).
- `warnings`: non-blocking findings.
- `failures`: blocking findings that make the candidate unsafe.

## Integration Points

- **CLI**: `python -m triage.billing_bridge_validator <workbook> --run-id <id> --month <YYYY-MM>`
- **AxTask**: import `triage.billing_bridge_validator.validate_billing_workbook` and call with paths.
- **Output folder**: writes to `billing_runs/<YYYY-MM>/validation/` by default.

## Do Not

- Do not calculate billing.
- Do not classify PDFs.
- Do not generate emails.
- Do not reserialize XML casually.
