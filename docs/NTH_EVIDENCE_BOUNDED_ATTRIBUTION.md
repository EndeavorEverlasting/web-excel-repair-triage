# NTH Evidence-Bounded Attribution Contract

## Purpose

Neuron Track Hours reconstruction sometimes has exact attendance but incomplete intra-day task labels. In those cases, stronger device/workstation evidence can establish how much task workload plausibly existed without becoming a labor-hours source itself.

This contract prevents two opposite errors:

1. under-attributing a task lane because the old reconstruction lacked enough scope evidence; and
2. creating labor hours by multiplying device counts by a planning duration.

## Core rule

Attendance is the labor-hours ceiling.

Workload evidence is a task-capacity ceiling.

A reconstructed Configuration allocation may not exceed either ceiling after stronger dated non-Configuration evidence is reserved.

```text
configuration workload envelope
  = workstations
  × devices per workstation
  × direct configuration hours per device

attendance remaining for Configuration
  = attendance hours
  - explicitly supported non-Configuration hours

maximum defensible Configuration allocation
  = min(configuration workload envelope,
        attendance remaining for Configuration)
```

The maximum is a **ceiling, not a target**. Stronger dated evidence can require a lower Configuration allocation.

## Canonical worked example

For a scope with:

- 38 workstations;
- 2 configured devices per workstation;
- 2.0 direct technician-hours per device;
- 125.0 attendance hours in the questioned window;

then:

```text
38 × 2 = 76 devices
76 × 2.0h = 152.0h Configuration workload envelope
```

Because attendance is only 125.0h, the evidence does **not** authorize 152.0h of NTH labor. It establishes that Configuration workload was large enough that Configuration may consume a substantial share of the 125.0h window if stronger dated evidence does not require those hours elsewhere.

If 27.0h is independently supported as Deployment, Logistics, Inventory, Survey/Recon, Documentation, Coordination, Troubleshooting, or another non-Configuration lane, then:

```text
125.0h attendance - 27.0h evidenced non-Configuration = 98.0h remaining
min(152.0h scope envelope, 98.0h remaining attendance) = 98.0h max Configuration
```

## Device count is not completion count

A workstation/device population can prove workload scale without proving every device was configured inside the same attendance window.

Do not convert a target/install population into a same-week completed-device count unless dated device-level evidence supports that assertion.

When configuration and installation occur in the same week, some devices may have been:

- configured before the window;
- configured during staging/handout;
- configured and then deployed;
- deployed with later rework;
- still pending configuration.

Keep `Configurations` and `Deployments` as separate task lanes even when they support the same workstation.

## Rework and contingency

Do not automatically add a historical or operator-reported failure/rework percentage to attendance or task allocation.

A contingency rate may be retained as planning context, but NTH should allocate actual rework only when dated evidence supports Configuration or Troubleshooting work within the attendance window.

## Relationship to percentage distributions

Evidence-bounded attribution takes precedence over generic thin-context percentage distributions when stronger evidence establishes a bounded workload and/or explicit non-Configuration activity.

Generic percentage rules remain useful when context is thin. They must not override stronger dated evidence merely to preserve a historical ratio.

## Implementation

Reusable helper:

```text
triage/nth_evidence_bounded_allocation.py
```

Primary class:

```python
EvidenceBoundedAllocation(
    workstations=...,
    devices_per_workstation=...,
    direct_hours_per_device=...,
    attendance_hours=...,
    explicit_non_configuration_hours=...,
)
```

Key outputs:

- `device_count`
- `configuration_workload_envelope_hours`
- `attendance_remaining_after_explicit_non_configuration`
- `max_defensible_configuration_hours`
- `audit_record()`

The helper is deliberately a bounded calculator, not an automatic row classifier. The operator/generator still needs dated evidence to decide which attendance hours belong to which non-Configuration lanes.

## Workbook audit requirement

When this rule is used to construct a Neuron Track Hours workbook, the internal audit surface should preserve:

- attendance basis and total;
- workstation count;
- devices per workstation;
- direct hours per device planning basis;
- computed workload envelope;
- each explicitly reserved non-Configuration amount and evidence reference;
- resulting maximum defensible Configuration hours;
- actual chosen Configuration allocation;
- explanation when actual allocation is below the maximum.

The client/management-facing sheet should show the resulting clean task allocation, not the internal allocation mechanics unless specifically requested.

## Validation

```powershell
python -m pytest tests/test_nth_evidence_bounded_allocation.py -q
```

The tests enforce the 38-workstation example, attendance bounding, non-Configuration reservation, workload-envelope bounding, audit separation, and fail-closed invalid inputs.
