# Same-family artifact comparison

Final truth-pass layer before admin submission readiness. Compare **like with like** only.

## Doctrine

| Admin (submit from `outputs/admin-ready/`) | Internal (never submit as-is) |
|---------------------------------------------|-------------------------------|
| NW PRJ Hours, billing summaries, client workbooks | Dashboards, roster logs, comparison workbooks, raw sidecars |

## Scan intake (Phase 1)

```powershell
python -m triage.same_family_compare --intake-root ArtifactIntake/2026-06-03 --scan-only --out-dir artifacts/intake_scan
```

Writes `artifact_inventory.json`, `unknown_artifacts.json`, `family_grouping_summary.json`.

## Compare (Phase 3)

```powershell
python -m triage.same_family_compare `
  --baseline References/approved/April_2026_Billing_Summary_Client.xlsx `
  --candidate Outputs/admin-ready/April_2026_Billing_Summary_Client.xlsx `
  --family admin_billing_summary `
  --months 2026-04 `
  --out-dir artifacts/same_family_compare
```

## Outputs

- `same_family_comparison.json` / `.md`
- `same_family_delta_rows.csv`
- `submission_readiness.md`

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `READY` | Gates pass |
| `NOT_READY` | Blocking failure |
| `READY_WITH_EXCLUSIONS` | Documented exclusions only |
| `EXCEL_FOR_WEB_NOT_PROVEN` | Browser proof missing |
| `INSUFFICIENT_METADATA` | Cannot compare safely |

## Rules

1. Unparseable baseline → **fail loud** (not empty baseline).
2. Family mismatch → stop unless `--cross-family-map` (future).
3. Month set mismatch → stop unless partial compare declared.
4. Roster log vs billing summary → **invalid** full workbook compare.

## PR #35 merge gate

See [`PR35_CHECKPOINT_AND_PROOF_GUIDE.md`](PR35_CHECKPOINT_AND_PROOF_GUIDE.md): preflight + semantic + same-family + Excel Web manual proof + readiness report.
