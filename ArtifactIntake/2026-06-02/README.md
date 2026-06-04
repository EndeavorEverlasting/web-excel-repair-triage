# 2026-06-02 Artifact Intake

Use this dated folder for the 2026-06-02 billing/admin comparison cycle.

Real workbooks stay local. Do not commit private artifacts.

**Emulator rule:** folders under `admin/`, `internal/`, and sibling raw trees are
read-only inputs for engines. Generators write only under `Outputs/` or
`artifacts/` (or manually promote into `outputs/admin-ready/` after review). See
[`docs/OPERATOR_SOURCE_IMMUTABILITY.md`](../../docs/OPERATOR_SOURCE_IMMUTABILITY.md).

## Put files here

```text
ArtifactIntake/2026-06-02/
  admin/
    nw-prj-hours/
    monthly-billing-summaries/
  internal/
    dashboards/
    tooling-workbooks/
    roster-logs/
    comparison-workbench/
  outputs/
    admin-ready/
    internal-review/
    comparison-reports/
```

## Classification for this cycle

### Admin artifacts

These are candidates for submission/admin review after validation:

- NW PRJ Hours
- NW PRJ Tech Hours
- monthly billing summary workbooks
- final admin-ready outputs generated from validated evidence

Place them under:

```text
admin/nw-prj-hours/
admin/monthly-billing-summaries/
outputs/admin-ready/
```

### Internal artifacts

These are workbench/control/tooling files. They support truth-pass comparison but are not submission outputs:

- dashboards
- tooling workbooks
- active roster logs
- correction ledgers
- internal comparison workbooks
- dashboard generators
- scratch/control workbooks with review machinery

Place them under:

```text
internal/dashboards/
internal/tooling-workbooks/
internal/roster-logs/
internal/comparison-workbench/
outputs/internal-review/
```

## Submission rule

Submit only from:

```text
outputs/admin-ready/
```

Do not submit from `internal/` or raw `admin/` source folders.

Raw admin source folders hold evidence. Final admin-ready folders hold output.

## Required comparison before submitting

Before an automated artifact is submitted, compare:

1. NW PRJ Hours admin source vs generated NW PRJ Hours output.
2. Monthly billing summary source vs generated monthly billing summary output.
3. Generated totals vs newest roster/admin evidence.
4. Admin-ready output vs internal dashboard/control assumptions.

Stop if:

- totals drift without explanation
- resolved items are still flagged as open
- internal-only columns appear in admin output
- dashboard/tooling tabs leak into admin workbook
- Excel Web repairs the candidate

## Local command target

Future CLI should accept this date folder as the root input:

```powershell
python -m triage.billing_artifact_compare ^
  --intake-root ArtifactIntake/2026-06-02 ^
  --strict ^
  --emit-admin-ready
```

Expected emitted outputs:

```text
outputs/comparison-reports/2026-06-02_Billing_Comparison_Report.json
outputs/comparison-reports/2026-06-02_Billing_Comparison_Report.md
outputs/admin-ready/2026-06-02_Admin_Ready_NW_PRJ_Hours.xlsx
outputs/admin-ready/2026-06-02_Admin_Ready_Monthly_Billing_Summary.xlsx
```
