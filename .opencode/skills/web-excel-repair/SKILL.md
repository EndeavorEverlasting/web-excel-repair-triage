---
name: web-excel-repair
description: Use when diagnosing or repairing Excel workbooks that trigger repair dialogs, working with OOXML structure, running gate checks, or applying patch recipes. Also use when asked about web Excel compatibility or stop-ship rules.
---

# Web Excel Repair

Use this skill when diagnosing or repairing xlsx workbooks.

## Pipeline phases

1. **Phase 1**: Gate checks (10 structural hazard checks) → `triage/gate_checks.py`
2. **Phase 2**: Part-level diff → `triage/diff.py`
3. **Phase 3**: Pattern classification → `triage/patterns.py`
4. **Phase 4**: Recipe generation → `triage/patcher.py`
5. **Phase 5**: Recipe application → `triage/patcher.py`
6. **Phase 6**: Graph probe → `triage/graph_probe.py`
7. **Optional**: Browser probe → `triage/web_excel_browser.py`
8. **Optional**: Desktop probe → `triage/excel_desktop.py`

## Key commands

```bash
# Run gate checks on a workbook
python -c "from triage.gate_checks import run_gate_checks; import json; print(json.dumps(run_gate_checks('path/to/file.xlsx'), indent=2))"

# Run full pipeline
python -c "from triage.agents import TriageOrchestrator; ..."
```

## Stop-ship tokens

Read `configs/web_excel_stop_ship_tokens.json`:
- XML tokens: `_xlfn.`, `_xludf.`, `_xlpm.`, `AGGREGATE(`
- Error literals: `#REF!`, `#VALUE!`, `#NAME?`
- Filename markers: `repaired_`, `Deprecated_repaired_`, `web_repaired_`

## Validation

Read `.ai/validators.json` for all validation commands.

## Structure preservation

Read `docs/XLSX_STRUCTURE_PRESERVATION_CONTRACT.md` for the full contract.

Key rule: Prefer in-place mutation of a known-good workbook over wholesale regeneration.
