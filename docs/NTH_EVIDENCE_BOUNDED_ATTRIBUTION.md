# NTH Evidence-Bounded Attribution Contract

## Purpose

Neuron Track Hours reconstruction sometimes has a known labor total but incomplete intra-day task labels. In those cases, stronger device/workstation evidence can establish how much task workload plausibly existed without becoming a labor-hours source itself.

This contract prevents two opposite errors:

1. under-attributing a task lane because an earlier reconstruction lacked enough scope evidence; and
2. creating labor hours by multiplying device counts by a planning duration.

## Core rule

The selected historical labor record is the labor-hours ceiling for the reconstruction being performed.

Workload evidence is a task-capacity ceiling.

A reconstructed Configuration allocation may not exceed either ceiling after stronger dated non-Configuration evidence is reserved.

```text
configuration workload envelope
  = workstations
  × devices per workstation
  × direct configuration hours per device

labor remaining for Configuration
  = selected historical labor total
  - explicitly supported non-Configuration hours

maximum defensible Configuration allocation
  = min(configuration workload envelope,
        labor remaining for Configuration)
```

The maximum is a **ceiling, not a target**. Stronger dated evidence can require a lower Configuration allocation.

## Canonical questioned-week example

For the historical May 26–29 tracker/model associated with the questioned approximately 105 Configuration hours:

- tracker total: **135.00h**;
- Configuration: **104.78h**;
- Inventory Management: **20.65h**;
- Deployments: **5.24h**;
- Logistics: **4.33h**;
- workstation scope: **38 workstations**;
- configured devices per workstation: **2** (one Cybernet + one Neuron);
- direct Configuration planning basis: **2.0h/device**.

The scope calculation is:

```text
38 × 2 = 76 devices
76 × 2.0h = 152.0h Configuration workload envelope
```

The historical non-Configuration lanes total:

```text
20.65 + 5.24 + 4.33 = 30.22h
```

Therefore:

```text
135.00h historical tracker total
- 30.22h historical non-Configuration lanes
= 104.78h remaining for Configuration

min(152.0h workload envelope, 104.78h remaining labor)
= 104.78h maximum Configuration
```

This is the important relationship for the questioned tracker: the corrected workstation/device scope is large enough to make its old **104.78h Configuration** attribution capacity-plausible.

It does **not** prove that the old lane split was a minute-level time study. It shows that the earlier 38-device interpretation was not a valid reason to reject a Configuration allocation near 105 hours.

## Multiple historical records must not collapse

The May 26–29 evidence family contains distinct historical hour surfaces. A generator or analyst must not silently substitute one for another:

- **135.00h historical tracker/model** — the record paired with the approximately 105h Configuration question;
- **125.00h / 13 shifts later NTH reconstruction** — a separate retrospective record;
- **147.00 net project hours June 4 billing-thread record** — another separate historical scope.

The evidence-bounded helper accepts a labor total as an input. The caller is responsible for selecting the correct historical authority for the question being answered and recording that provenance in the audit.

For the specific historical `~105h Configuration` tracker question, use **135.00h**, not 125.00h.

## Device count is not completion count

A workstation/device population can prove workload scale without proving every device was configured inside the same labor window.

Do not convert a target/install population into a same-week completed-device count unless dated device-level evidence supports that assertion.

When configuration and installation occur in the same week, some devices may have been:

- configured before the window;
- configured during staging/handout;
- configured and then deployed;
- deployed with later rework;
- still pending configuration.

Keep `Configurations` and `Deployments` as separate task lanes even when they support the same workstation.

## Rework and contingency

Do not automatically add a historical or operator-reported failure/rework percentage to a labor total or task allocation.

A contingency rate may be retained as planning context, but actual NTH rework belongs in Configuration or Troubleshooting only when the selected historical evidence supports it within the chosen labor control.

## Relationship to percentage distributions

Evidence-bounded attribution takes precedence over generic thin-context percentage distributions when stronger evidence establishes a bounded workload and/or explicit non-Configuration activity.

Generic percentage rules remain useful when context is thin. They must not override stronger dated evidence merely to preserve a later historical ratio.

In particular, a later conservative management allocation must not silently overwrite the historical 135h questioned-week tracker when the task is to explain that tracker.

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
    attendance_hours=...,  # selected historical labor control
    explicit_non_configuration_hours=...,
)
```

The field remains named `attendance_hours` for API compatibility; the audit must state which historical labor source supplied that value.

Key outputs:

- `device_count`
- `configuration_workload_envelope_hours`
- `attendance_remaining_after_explicit_non_configuration`
- `max_defensible_configuration_hours`
- `audit_record()`

The helper is deliberately a bounded calculator, not an automatic row classifier or historical-authority selector.

## Workbook audit requirement

When this rule is used to construct a Neuron Track Hours workbook, the internal audit surface should preserve:

- selected historical labor source and total;
- competing historical records and why they were not selected;
- workstation count;
- devices per workstation;
- direct hours per device planning basis;
- computed workload envelope;
- each explicitly reserved non-Configuration amount and evidence reference;
- resulting maximum defensible Configuration hours;
- actual chosen Configuration allocation;
- explanation when actual allocation is below the maximum.

The client/management-facing sheet should show the resulting clean task allocation, not internal allocation mechanics unless specifically requested.

## Validation

```powershell
python -m pytest tests/test_nth_evidence_bounded_allocation.py -q
```

The tests enforce the corrected historical example: 38 workstations / 76 devices / 152h workload envelope, 135h tracker total, 30.22h non-Configuration, and 104.78h remaining Configuration capacity.
