# NW PRJ Dashboard v6.8 Carryover Notes

Generated from:
- Dashboard: `NW_PRJ_Tech_Roster_Dashboard_v6_7_STATUS_DICTIONARY_WEBSAFE-5-28-2026.xlsx`
- Admin scratch/control copy: `NW PRJ Tech hours 5-27-2026 - Khadejah and Alejandro Updates - Manually Updated 5x.xlsx`
- Roster log provided for checkpoint: `INTERNAL_May_Billing_Active_Roster_Log_2026-05-28-update so that partial hours are flagged before submission.xlsx`

## Sprint outcome

- Active admin work surface now has 1 open/addressed row(s).
- Review guardrails retain 16 row(s).
- Partial hours retain 9 row(s).
- Resolved_Queue collected 21 row(s) from current work tabs.

## Known gaps

1. `Resolved_Queue` is values-based in v6.8. v7.x should generate it dynamically from work tabs.
2. Manual status and `Preserve Notes / Context` must be treated as evidence, not disposable comments.
3. Every invented dropdown/status term must exist in `Definitions_Current` and `Status_Decision_Map`.
4. Every visual color must be codified in `CF_Dictionary` and `Visual_System_v6_8` with plain color name plus hex.
5. Tech-facing work surfaces should be clean; backend/full-schema tabs can stay hidden or separated.

## Known risks

1. Manual closed rows can be falsely reopened if old proposed values are treated as final.
2. `Addressed` can be mistaken for `Resolved`; it must remain teal and explicitly not holistically closed.
3. Excel Web repair prefixes such as `Deprecated_repaired_` are STOP-SHIP indicators.
4. Start sheets can open at blank scrolled ranges unless active view is controlled.
5. Conditional formatting must evaluate Column A status before queue labels.

## Repo targets

- Add `docs/NW_PRJ_DASHBOARD_V6_CONTRACT.md`.
- Add `docs/CF_DICTIONARY_AND_VISUAL_SYSTEM.md`.
- Add `configs/cf_palette_v1.json`.
- Add `configs/status_values_v1.json`.
- Add validator tests for Column A override, no stale reopen, no repaired output, and Start Here active view.
- Add local CLI generator accepting dashboard, admin scratch/control copy, and roster log.

## v7.x target

Build linked/dynamic `Resolved_Queue` generation in `EndeavorEverlasting/web-excel-repair-triage` so manual status changes flow into the ledger without regenerating static rows by hand.
