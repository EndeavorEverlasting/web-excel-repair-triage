# Artifact Intake

Use this folder as the local dated intake map for billing, admin, dashboard, and tooling artifacts.

The repository should make it obvious where a file belongs before any script touches it. If placement is ambiguous, stop and classify the artifact first.

## Golden rule

Do not commit real workbooks, screenshots, payroll exports, roster logs, or client/private artifacts to this public repo.

Commit only:

- README files
- folder maps
- sanitized docs
- synthetic fixtures
- generated reports that contain no private data

Place real artifacts locally in the dated folders described below. The folder structure is tracked with `.gitkeep` and README files. Workbook contents stay local unless explicitly sanitized.

## Date-folder pattern

Use ISO dates:

```text
ArtifactIntake/YYYY-MM-DD/
```

Example:

```text
ArtifactIntake/2026-06-02/
```

Each date folder should use this structure:

```text
ArtifactIntake/YYYY-MM-DD/
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

## Classification rules

| Artifact type | Classification | Folder |
| --- | --- | --- |
| NW PRJ Tech Hours / NW PRJ Hours | Admin artifact | `admin/nw-prj-hours/` |
| Monthly billing summary workbook | Admin artifact | `admin/monthly-billing-summaries/` |
| Admin submission-ready workbook | Admin artifact | `outputs/admin-ready/` |
| Dashboard workbook | Internal artifact | `internal/dashboards/` |
| Tooling workbook | Internal artifact | `internal/tooling-workbooks/` |
| Active roster log | Internal artifact | `internal/roster-logs/` |
| Scratch comparison workbook | Internal artifact | `internal/comparison-workbench/` |
| Machine comparison report | Depends on contents | `outputs/comparison-reports/` if sanitized |

## Admin vs internal boundary

Admin artifacts are meant to be clean enough for submission or admin review. They should not expose internal notes, confidence scoring, private correction logic, or dashboard-only machinery.

Internal artifacts can contain working logic, review queues, dashboards, correction ledgers, and tooling support. They are not submission artifacts.

If a workbook contains both admin-facing output and internal review machinery, classify it as internal until an admin-only output is generated.

## Billing comparison workflow

Use the dated intake folder to compare billing artifacts before submitting automated outputs.

Recommended local flow:

1. Create today's folder.
2. Place NW PRJ Hours under `admin/nw-prj-hours/`.
3. Place monthly billing summaries under `admin/monthly-billing-summaries/`.
4. Place dashboard/tooling/roster workbooks under `internal/`.
5. Run comparison scripts against the dated folder, not random Downloads paths.
6. Emit comparison reports under `outputs/comparison-reports/`.
7. Emit final admin-ready artifacts under `outputs/admin-ready/`.
8. Only submit files from `outputs/admin-ready/` after package validation and truth-pass reconciliation.

## Required checks before admin submission

A file in `outputs/admin-ready/` must pass:

1. Web Excel package validation.
2. Billing truth-pass comparison against the newest roster/admin evidence.
3. Admin/internal boundary scan.
4. No private notes or internal dashboard scaffolding.
5. No stale flags that were already resolved.
6. No Excel Web repair banner after upload/open.

## Naming conventions

Use stable names that sort naturally:

```text
YYYY-MM-DD_NW_PRJ_Hours_admin_source.xlsx
YYYY-MM-DD_Monthly_Billing_Summary_admin_source.xlsx
YYYY-MM-DD_Billing_Comparison_Report.json
YYYY-MM-DD_Admin_Ready_NW_PRJ_Hours.xlsx
YYYY-MM-DD_Admin_Ready_Monthly_Billing_Summary.xlsx
```

Avoid names like `final`, `final2`, `really_final`, or `use_this_one`. The judge sees this and removes points.

## Relationship to existing repo folders

- `Candidates/` remains the generic workbook triage drop zone.
- `Repaired/` remains the place for Excel Web repaired exports.
- `Outputs/` remains the app/runtime output area.
- `ArtifactIntake/YYYY-MM-DD/` is the business-context intake lane for a specific reporting day.

For billing/admin work, start in `ArtifactIntake/YYYY-MM-DD/`, then copy candidate workbooks into `Candidates/` only when running package repair triage.
