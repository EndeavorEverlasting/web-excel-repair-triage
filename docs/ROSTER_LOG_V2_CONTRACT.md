# Roster Log V2 — Normalized Multi-Project Contract

## Status

Roster Log V2 is a **new replacement candidate**. The existing roster remains untouched and authoritative until V2 earns operator acceptance. Promotion to `CURRENT` is an explicit lifecycle action, not an automatic consequence of generation.

## Why V2 exists

The legacy roster is a wide monthly attendance matrix with project attribution layered through overrides, Worked Projects, Assignments, and later allocation ledgers. That remains reproducible, but split-project days are harder to enter and audit than they need to be.

V2 makes the existing truth model first-class:

- **Attendance** records paid time once per staff/date.
- **Project Allocations** explain where that paid day belongs.
- one project is the normal default;
- an operator may add a second or third project to the same day;
- a deliberate whole-day project decision is equally valid;
- multi-project status is not itself an exception;
- only allocation variance requires reconciliation.

## Data contract

Canonical local state: `roster-log-v2/v1` JSON.

### Attendance

One row per staff/date:

- `date`
- `staff`
- `clock_in`
- `clock_out`
- `paid_hours`
- `default_project`
- optional `notes`

Attendance owns paid hours. Project allocation cannot create additional paid time.

### Project Allocations

Zero or more explicit rows per attendance day:

- `allocation_id`
- `date`
- `staff`
- `project`
- optional `workstream`
- `hours`
- `status`
- optional `notes`

If a paid attendance day has **no** explicit allocation rows, the producer creates one default allocation for the attendance row's `default_project` and full `paid_hours`.

If multiple project rows are supplied, they are preserved. The project mode is derived as `MULTI` when more than one distinct project is present. No ratio is inferred.

## Reconciliation

For each staff/date:

`attendance paid hours - sum(project allocation hours) = variance`

A day is reconciled when `abs(variance) <= 0.01`.

The following are valid examples for an 8-hour attendance day:

- one project / 8.0 hours;
- H&H 6.4 + Northwell 1.6;
- Northwell 8.0 after an explicit operator full-day decision;
- three projects whose hours sum to 8.0.

The producer does **not** manufacture an 80/20 split, nor does it reject a deliberate full-day project decision because other activity may have occurred that day. Allocation is an operator/evidence decision; reconciliation is arithmetic.

## Local-first website

`web/roster-log-v2/` is the daily entry surface.

- state is cached in browser `localStorage`;
- a new day starts with one allocation card;
- **Add project** adds another allocation row;
- **Use one project for whole day** resets the day to one full-paid-hours allocation;
- unreconciled totals are visibly marked `DRAFT — ADJUST ALLOCATION` but may be saved locally;
- JSON export is the canonical portable state artifact;
- Attendance CSV and Project Allocations CSV are convenience exports;
- no network call is required for local operation.

## Workbook producer

`python -m triage.roster_log_v2.cli --state <state.json> --output Outputs/.../Roster_Log_V2.xlsx`

The generated workbook contains:

1. `Dashboard`
2. `Attendance`
3. `Project Allocations`
4. `Dictionaries`
5. `Review Queue`
6. `Read Me`

The producer uses Triage's output-path protection, shared-string repair, and Web Excel package validator. Mutable dropdowns point to worksheet dictionary ranges instead of duplicated inline lists.

## Relationship to the legacy roster

V2 does not delete, rewrite, or silently migrate the existing roster. Historical evidence remains where it is. A separate migration/import can populate the V2 JSON state when required; until operator acceptance, V2 is a replacement candidate beside the legacy workbook rather than a destructive upgrade in place.
