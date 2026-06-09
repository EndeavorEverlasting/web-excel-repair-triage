# Worker Project Hours Trace Doctrine

This doctrine exists so payroll, billing, and Neuron Track Hours logic do not rediscover the same workbook rules every sprint.

## Core rule

A worker's hours are traceable by project because the Active Roster Log resolves attendance at the **worker + date + project** grain.

Do not assume one worker has one project for a month. That shortcut is wrong.

The worker's clocked hours come from `Live - {Month YYYY}`. The project attached to those hours is resolved from the monthly project tabs.

## Workbook surfaces

For each month, the controlling input surfaces are:

| Surface | Purpose |
| --- | --- |
| `Live - {Month YYYY}` | Attendance punches: staff, default project, daily clock-in / clock-out pairs. |
| `Worked Projects - {Month YYYY}` | Per-worker, per-date worked-project classification. This captures the project actually worked that day when populated. |
| `Assignments - {Month YYYY}` main table | Per-worker, per-date planned/default project assignment. |
| `Assignments - {Month YYYY}` Overrides sub-table | Reviewed corrections at the bottom of the Assignments tab. This is intentional operator control, not noise. |

The `Projects` catalog provides allowed project names and downstream billing bucket mapping.

## Resolution order

Resolve project for each worker/date in this order:

1. `Assignments - {Month}` Overrides sub-table
2. `Worked Projects - {Month}` per-date cell
3. `Assignments - {Month}` main-table per-date cell
4. `Live - {Month}` default Project column
5. `Unassigned / Review` when no project can be resolved

This is implemented in `triage.admin_billing_summary.reader.read_month`.

## Why the bottom override table matters

The bottom section of each `Assignments - {Month}` tab allows reviewed exceptions without rewriting the main grid. A row like:

| Override Staff Name | Override Date | Override Project | Notes |
| --- | --- | --- | --- |
| Richard Perez | 2026-05-14 | Neuron Deployments | Richard review: Neurons confirmed |

means the resolved project for Richard Perez on 2026-05-14 is `Neuron Deployments`, even if another surface says something else.

Future engines must parse this table. Skipping it is a defect.

## Paylocity and payroll evidence

Paylocity PDFs are payroll evidence. They can identify paid dates that are missing from the roster and should be reviewed.

Paylocity does not create Northwell billable hours by itself.

Correct flow:

1. Compare Paylocity paid hours against roster-derived hours.
2. Flag Paylocity-only dates as variance evidence.
3. Review and, if valid, correct the roster log.
4. Regenerate billing and Neuron Track Hours from the corrected roster.

Incorrect flow:

1. Find Paylocity hours.
2. Add them directly to billing.

That is how naive artifacts get fat and wrong.

## Holidays and non-billable paid time

Paid holidays for Agilant employees can appear in Paylocity while not representing Northwell billable work.

Example: Memorial Day 2026-05-25 for Richard Perez was paid, but it is not Northwell billable unless the roster contains an explicit work record showing Northwell project work.

The roster controls billing. Payroll controls payroll variance review.

## Required outputs from engines

Any billing or payroll reconciliation engine should be able to emit:

- Worker/date/project detail rows
- Worker/project/month summary rows
- Project resolution source: `override`, `worked`, `assignment`, `live_default`, or `review`
- Paylocity-only variance rows without billing them
- Holiday/non-work exclusion rows when payroll contains paid non-work time

## Guardrail

If a generated artifact cannot answer this question, it is not ready:

> For this worker, on this date, which project did the roster say they worked, which surface supplied that project, and how many net hours did that create?

No answer, no submission.
