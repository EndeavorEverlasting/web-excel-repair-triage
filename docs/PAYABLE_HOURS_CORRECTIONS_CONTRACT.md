# Payable Hours Corrections Contract

## Purpose

The Active Roster Log is the source of truth for who worked and what operational day/project the work belongs to. However, the visible punch cells may sometimes contain standard hours when overtime was actually worked and paid.

When payroll evidence shows real work but the roster has standard hours, the smoothest correction point is a roster-side **Payable Hours Corrections** table. This preserves the original punch cells while giving the reconciliation pipeline the correct payable target.

This is preferred over editing final dashboards, because dashboards are outputs. It is also preferred over distorting clock-out times when the visible 9:00 AM to 6:00 PM punch pair is a placeholder rather than the exact physical clock span.

## Where to edit

Add or update a private/local tab or CSV named:

```text
Payable Hours Corrections
```

The correction table should live beside the roster input or be passed as a private CSV. It should not be committed with private evidence rows to an open repo.

## Required columns

| Column | Required | Meaning |
| --- | --- | --- |
| `date` | Yes | Work date, e.g. `2026-04-28` |
| `staff_name` | Yes | Staff member whose payable target is corrected |
| `mode` | Yes | `set_payable_hours` or `add_payable_hours` |
| `hours` | Yes | Target payable hours when mode is `set`; extra hours when mode is `add` |
| `scope` | Recommended | `payroll_delta`, `billing`, or `both` |
| `reason` | Recommended | Plain-English correction reason |
| `evidence_source` | Recommended | Source evidence, e.g. Paylocity PDF |
| `evidence_hours` | Recommended | Evidence hours before rounding or adjustment |
| `project_name` | Optional | Project context if the correction should stay project-scoped |

## Preferred mode

Prefer:

```text
set_payable_hours
```

This is idempotent. If the base roster is later corrected, the target remains stable and does not accidentally double-count.

Use:

```text
add_payable_hours
```

only when the operator is intentionally adding a small known amount to a correct base row.

## Example: April 28 and April 29 cleanup

If Paylocity shows real worked hours and the roster only shows standard placeholder hours, add correction rows like:

| date | staff_name | mode | hours | scope | reason | evidence_source | evidence_hours | project_name |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- |
| 2026-04-28 | Richard Perez | set_payable_hours | 14.00 | payroll_delta | Roster had standard placeholder hours; Paylocity shows longer worked day. Rounded to nearest hour per operator rule. | Paylocity April 2026 PDF | 13.98 | Neuron Deployments |
| 2026-04-29 | Richard Perez | set_payable_hours | 17.00 | payroll_delta | Roster had standard placeholder hours; Paylocity shows longer worked day. Rounded to nearest hour per operator rule. | Paylocity April 2026 PDF | 16.95 | Neuron Deployments |

## Pipeline behavior

The reconciliation pipeline must resolve payable target in this order:

1. Parse roster punch/date/project normally.
2. Deduct lunch using repo lunch rules.
3. Resolve base roster payable hours.
4. Look up a matching Payable Hours Correction by date + staff name.
5. Apply correction based on scope.
6. Use corrected payable hours in payroll delta calculations.
7. Preserve original roster payable hours and correction metadata in an audit table.
8. Do not let corrected April roster-underreported overtime become a false offset against May underpayment.

## Dashboard output behavior

Admin-facing dashboards should show:

- corrected payable target
- paid Paylocity work hours
- unpaid hours to repay
- a clear note that corrections were applied from reviewed payable-hours corrections

Internal audit tabs may show:

- original roster payable hours
- corrected payable hours
- correction mode
- reason
- evidence source
- evidence hours

## Private data posture

The public repo stores:

- schema
- parser
- validation rules
- tests
- report generator behavior

Private/local storage contains:

- staff names
- actual correction rows
- source excerpts
- encrypted evidence packages if used

## Acceptance checks

Generated artifacts should verify:

- every correction row matched an existing staff/date or is explicitly flagged unmatched
- corrected payable target replaced or added exactly as requested
- no additive correction double-counted after the roster was later updated
- correction metadata appears only in internal/audit sheets unless explicitly requested
- admin-facing summary does not present unresolved offsets as repayment reductions
