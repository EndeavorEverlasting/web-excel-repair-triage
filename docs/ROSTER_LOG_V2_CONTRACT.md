# Roster Log V2 — Normalized Multi-Project Contract

## Status

Roster Log V2 is a **replacement candidate**. The existing roster remains untouched and authoritative until V2 earns operator acceptance. Promotion to `CURRENT` is an explicit lifecycle action, not an automatic consequence of generation.

This file is the canonical V2 doctrine. Future humans and agents must extend these owners instead of rediscovering project-attribution rules from historical workbooks.

## Core invariant

Roster V2 has two grains and they must never be collapsed:

1. **Attendance grain:** one paid-time row per `staff + date`.
2. **Allocation grain:** one or more project rows per `staff + date`, each with its own hours and basis.

**Attendance owns paid hours. Project Allocations own project attribution.**

A worker can have one project, two projects, or several projects in the same day. Multi-project status is normal. The only arithmetic failure is allocation variance.

## Default / fallback project is not final project truth

`attendance.default_project` is fallback metadata. It exists so an ordinary paid day can become one project without repetitive entry.

The normalization rule is deterministic:

- If a paid attendance day has **no explicit allocation rows**, create one full-day allocation using `default_project` and mark its basis `DEFAULT`.
- If **any explicit allocation rows exist** for that staff/date, those allocation rows define the actual reported project membership. Do **not** add or report the attendance default as another project.

This boundary is regression-critical. A default project can be unrelated to the project actually worked on a particular date.

### Canonical example: non-NTH default overridden by Neuron work

A technician may have `Mobile Device Support / iPhone Support` as the default project while a dated assignment explicitly places that day on the Neuron/NTH project. The explicit Neuron allocation is project truth for that day; Mobile Device Support is not additionally reported.

Historical `Neuron Deployments` override labels therefore represent project-resolution provenance, not a second Neuron project identity. Recipient normalization may map those dated Neuron assignments to the current outward project identity while preserving the literal source label privately.

## Canonical local state

Schema: `roster-log-v2/v1` JSON.

### Attendance

One row per staff/date:

- `date`
- `staff`
- `clock_in`
- `clock_out`
- `paid_hours`
- `default_project` — fallback only
- optional `notes`

Paid hours cannot be created by allocation rows.

### Project Allocations

Zero or more explicit rows per attendance day:

- `allocation_id`
- `date`
- `staff`
- `project`
- `basis`
- optional `workstream`
- `hours`
- `status`
- optional `notes`

`basis` is mandatory after normalization and has exactly three values:

| Basis | Meaning |
| --- | --- |
| `DEFAULT` | Producer-created fallback because the paid day had no explicit allocations. |
| `EXPLICIT` | Operator/evidence intentionally assigned these hours to this project. |
| `OVERRIDE` | Operator/evidence intentionally corrects the default or a prior project classification. |

Existing v1 allocation rows that predate `basis` remain backward-compatible and normalize to `EXPLICIT`; producers must not guess `OVERRIDE` merely because an allocation differs from the attendance default.

## Reconciliation

For each staff/date:

`attendance paid hours - sum(project allocation hours) = variance`

A day is reconciled when `abs(variance) <= 0.01`.

Valid examples for an 8-hour attendance day include:

- one DEFAULT project / 8.0 hours;
- H&H 6.4 + Northwell 1.6;
- Northwell 8.0 after an explicit full-day decision;
- a dated Neuron OVERRIDE of an iPhone-support default / 8.0 hours;
- three projects whose hours sum to 8.0.

The system does **not** manufacture an 80/20 split and does not reject a deliberate full-day decision because other activity may have occurred. Allocation is an operator/evidence decision; reconciliation is arithmetic.

## Deterministic reporting contract

Canonical report version: `roster-log-v2-project-report/v1`.

The Python owner is `triage.roster_log_v2.report.report_snapshot`. The website mirrors this projection for local use.

Project reports must:

1. normalize state first;
2. derive project membership and hours **only from normalized allocation rows**;
3. never add attendance `default_project` after explicit allocations exist;
4. report `paid_hours`, `allocated_hours`, total variance, multi-project-day count, and unreconciled-day count;
5. emit one stable project row containing `project`, `allocated_hours`, `day_count`, `staff_count`, and `allocation_count`;
6. count a staff/date only once per project even when that project has multiple allocation rows that day;
7. use deterministic codepoint/project-name ordering rather than locale-dependent sorting;
8. preserve the invariant that sum(project allocated hours) equals total allocated hours.

Human-facing and machine-facing reports therefore answer the same question:

> Which projects received these attendance hours, by how much, and from how many staff/days/allocation rows?

## Local-first website

`web/roster-log-v2/` is the daily entry and local reporting surface.

The website must make the model visible rather than relying on training:

- label attendance project as **Default / fallback project**;
- state that explicit allocations control project reporting;
- start a new day with one `DEFAULT` allocation card;
- **Add project** creates an `EXPLICIT` allocation row;
- **Use one project for whole day** records an explicit full-day decision;
- allow the user to mark an allocation `OVERRIDE` when correcting a default/prior classification;
- support any number of allocation rows whose hours reconcile to paid attendance;
- show actual project membership in the day ledger;
- show a deterministic Project Report on-page;
- export canonical JSON, Attendance CSV, Allocations CSV (including basis), Project Report CSV, and Project Report JSON;
- normalize imported v1 state so old basis-less allocations become `EXPLICIT` and missing explicit allocations receive a `DEFAULT` row;
- use stable ordering for exports;
- make no network call for local operation.

## Workbook producer

```text
python -m triage.roster_log_v2.cli --state <state.json> --output Outputs/.../Roster_Log_V2.xlsx
```

The generated workbook contains:

1. `Dashboard`
2. `Attendance`
3. `Project Allocations`
4. `Project Report`
5. `Dictionaries`
6. `Review Queue`
7. `Read Me`

Workbook-specific invariants:

- `Attendance` labels the fallback field `Default / Fallback Project`.
- `Project Allocations` contains `Allocation Basis`.
- `Project Report` is generated from the same normalized allocation report contract.
- dropdowns remain range-backed through `Dictionaries`.
- bounded formulas are required for Web Excel compatibility.
- V2 preflight fails if the reporting sheet, basis field, or core doctrine text disappears.

The producer uses Triage output-path protection, shared-string repair, and Web Excel package validation.

## Regression proof

`tests/test_roster_log_v2.py` is the executable owner of these invariants. At minimum it must prove:

- default single-project normalization;
- backward-compatible basis normalization;
- explicit NTH/Neuron override of a non-NTH iPhone/mobile default does not report the default project;
- valid same-day multi-project allocation;
- deterministic project sorting/totals/day counts;
- invalid basis rejection;
- variance-only review behavior;
- workbook `Project Report` + `Allocation Basis` contract;
- Web Excel package safety;
- website basis/report/export semantics and absence of locale-dependent project sorting.

A future implementation that removes one of these behaviors must fail the owning test/preflight rather than silently changing semantics.

## Relationship to the legacy roster

V2 does not delete, rewrite, or silently migrate the existing roster. Historical evidence remains where it is. Migration/import can populate V2 JSON state, but it must preserve project-resolution provenance and allocation basis where known.

Until operator acceptance, V2 remains a candidate beside the legacy workbook rather than a destructive upgrade in place.
