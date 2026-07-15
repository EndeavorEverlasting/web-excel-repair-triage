---
name: roster-blank-shell
description: Use when working on the roster blank shell runtime proof sprint, generating blank roster workbooks, fixing CF/dxf issues, or working with the roster_log_review_queue module. Also use when asked about openpyxl styles.xml compatibility or OOXML schema order.
---

# Roster Blank Shell Runtime Proof

Use this skill when working with the roster blank shell generation pipeline.

## Key files

| File | Purpose |
|------|---------|
| `triage/roster_log_review_queue/run.py` | Blank mode pipeline orchestrator |
| `triage/roster_log_review_queue/blank_builder.py` | openpyxl workbook generator (6 sheets) |
| `triage/roster_log_review_queue/live_cf_patcher.py` | XML-level CF patcher |
| `triage/cf_engine.py:375-411` | `_patch_styles_dxf` with OOXML schema order |
| `triage/xlsx_utils.py:193` | `fix_inlinestr()` converts inlineStr → shared strings |
| `triage/excel_recovery_check.py` | Automated Excel repair detector |
| `configs/roster_log_review_queue/operator_cf_pack.json` | CF rules + dxf styles (7 entries) |

## Known traps

1. **TRAP-001**: inlineStr causes Excel repair → call fix_inlinestr() after pkg.write()
2. **TRAP-002**: OOXML dxf schema order → insert dxfs between </cellStyles> and <tableStyles>
3. **TRAP-003**: openpyxl styles.xml incompatibility with dxfs → ACTIVE BUG
4. **TRAP-008**: COM automation fails on openpyxl+dxf files

## Proof levels

1. static_proof — tests pass
2. structural_proof — OOXML structure correct
3. runtime_proof — no repair dialog in Excel
4. harness_proof — harness CLI exists
5. launcher_proof — launcher script exists

## Current status

- static_proof: PASS (21 tests)
- structural_proof: PASS (correct dxfs position)
- runtime_proof: FAIL (TRAP-003 active)
- harness_proof: NOT_RUN (no CLI)
- launcher_proof: NOT_RUN (no launcher)
