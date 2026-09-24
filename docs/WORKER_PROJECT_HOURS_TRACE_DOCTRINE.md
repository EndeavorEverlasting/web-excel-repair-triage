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

## Default-project overrides do not create a second project identity

A dated project value can exist specifically to override a worker's non-NTH default project. Do not confuse that resolution evidence with a new client-facing project taxonomy.

The June 2026 NTH record is the canonical example:

- Some source rows use the literal dated-assignment label `Neuron Deployments`.
- That label was useful when the worker's default project could be `Mobile Device Support` / `iPhone Support`, another project managed during the same period.
- The dated `Neuron Deployments` value therefore proves that the worker/date belongs to the Neuron/NTH project rather than the non-NTH default. It does **not** mean those hours belong to a second Neuron project distinct from Wave 3.
- For the Jon Zhou June 2026 NTH submission, qualifying June rows normalize outward to the single project identity `Wave-3 Neurons & Cybernets`.
- Private evidence must preserve the literal source label, the worker's default-project context, and the resolution source so the reason for the override is recoverable later.

This normalization changes presentation only. It must not add, remove, or redistribute paid hours, and the legacy label alone must not be used to invent a task/workstream assignment.

## Roster Log V2 continuation contract

Roster Log V2 replaces the wide-sheet ambiguity with two explicit grains while preserving the legacy evidence semantics above:

- one Attendance row owns paid time for a worker/date;
- one or more Project Allocation rows own project attribution for that worker/date;
- the Attendance `default_project` is fallback metadata only;
- when no explicit allocation exists, normalization creates one `DEFAULT` allocation for the fallback project;
- when explicit allocations exist, they are the complete project truth for reporting and the attendance default is not additionally counted;
- a reviewed correction of a default/prior classification is represented by allocation basis `OVERRIDE`;
- an intentionally entered allocation that is not a correction uses basis `EXPLICIT`;
- multiple same-day allocation rows are valid and remain distinct when their hours reconcile to paid attendance.

Legacy project-resolution evidence should therefore migrate into **allocation rows**, not overwrite the semantic meaning of Attendance defaults. For the June example, a Mobile Device Support / iPhone Support default can coexist with a Wave-3 Neurons & Cybernets `OVERRIDE` allocation without reporting any iPhone hours for that date.

Deterministic Roster V2 reporting derives project membership, hours, day counts, and staff counts only from normalized allocation rows. It must never infer project hours from a default field once explicit allocations exist.

The executable owners are:

- `triage/roster_log_v2/schema.py` — normalization and basis rules;
- `triage/roster_log_v2/report.py` — deterministic project report;
- `web/roster-log-v2/` — local-first entry/reporting surface;
- `tests/test_roster_log_v2.py` — regression proof.

If a future implementation cannot deterministically answer **worker + date + project + allocated hours + allocation basis**, the V2 project-attribution model has regressed.

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

Roster V2 reporting additionally emits project allocation basis (`DEFAULT`, `EXPLICIT`, `OVERRIDE`) and must preserve same-day multi-project allocations instead of flattening them.

## Guardrail

If a generated artifact cannot answer this question, it is not ready:

> For this worker, on this date, which project did the roster say they worked, which surface supplied that project, and how many net hours did that create?

For V2 the equivalent question is:

> For this worker, on this date, which project allocation rows explain the paid hours, what basis does each row carry, and do the allocated hours reconcile to attendance?

No answer, no submission.
