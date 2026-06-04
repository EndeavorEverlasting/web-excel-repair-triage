# One Marcus Source Overwrite Incident — 2026-06-04

## Summary

An agent run **overwrote** the operator handoff workbook in `Candidates/inventory recon/1M_Recon_READY.xlsx` by copying a **generate-mode** output onto the source path. The operator restored the working file manually.

**This must never happen again.**

## Timeline

1. Operator had a working integrated workbook (~7 sheets, ~69 KB) validated in Excel for Web.
2. Agent ran `generate` mode, which uses **openpyxl** to build a **new 2-sheet workbook** ([`generator.py`](../triage/one_marcus_recon/generator.py)).
3. Agent ran `Copy-Item` to replace `Candidates/inventory recon/1M_Recon_READY.xlsx` with generator output.
4. Operator lost the integrated workbook on disk; restored from backup as `Try Again Asshole - 1M_Recon_READY.xlsx`.

## Damage (forensic compare)

| Artifact | Sheets | Size | Notes |
|----------|--------|------|-------|
| Working baseline | **7** | 69,298 B | Full integrated READY workbook |
| Generator output (`Cursor_broke_this_one_…`) | **2** | 56,940 B | 5 sheets **deleted**; pivot gutted (1533 → 272 cells) |
| Excel-repaired broken file | **2** | 39,024 B | Further degraded |

Package preflight **passed** on the broken 2-sheet stub — gates were too narrow and did not compare against the source baseline.

## Root causes

1. **Wrong engine lane**: `generate` is for sanitized 2-sheet fixtures, not integrated READY workbooks.
2. **Source path treated as output**: violated read-only `Candidates/` doctrine.
3. **No backup** before overwrite.
4. **No fingerprint / sheet-preservation gate** before claiming success.

## Hard rules for agents

1. **`Candidates/` and `Active/` are read-only inputs.** All engine output goes under `Outputs/`.
2. **Never set `--output` equal to `--input`.** Never `Copy-Item` delivery output into `Candidates/` or `Active/`.
3. **Integrated multi-sheet workbooks use `relink` (OOXML graft), not `generate`.**
4. **Before delivery pass**: run baseline compare; **fail if any non-Part-Numbers sheet is deleted**.
5. **Overwrite requires backup** under `Outputs/backups/backup_<timestamp>/` ([`repo_apply.py`](../triage/repo_apply.py) pattern).

## Recovery path

```powershell
python -m triage.one_marcus_recon.cli relink `
  --input "Candidates/inventory recon/Try Again Asshole - 1M_Recon_READY.xlsx" `
  --output "Outputs/one_marcus_recon/1M_Recon_READY_relink.xlsx" `
  --date auto
```

Then compare output vs baseline (expect tab rename drift only, **zero sheet deletions**).

Forensic report: `Outputs/one_marcus_recon/incident_2026-06-04/incident_compare.json`

## Related docs

- [`ONE_MARCUS_RECON_FAILURE_ANALYSIS_2026_06_03.md`](ONE_MARCUS_RECON_FAILURE_ANALYSIS_2026_06_03.md) — failure mode #7
- [`AGENTS.md`](../AGENTS.md) — operator source immutability section
