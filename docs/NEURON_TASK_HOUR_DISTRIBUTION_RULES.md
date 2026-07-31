# Neuron Task Hour Distribution Rules

## Purpose

The Active Roster Log proves who worked, when they worked, and whether the work belongs to Neuron scope. It does not always preserve exact intra-day task context.

When event-level context is missing, Neuron Track Hours must use declared task-hour distribution rules instead of pretending the roster knows the exact activity mix.

The goal is repeatable, explainable output without embedding private technician names in the public repo.

## Task lanes

Supported task lanes:

| Lane |
| --- |
| Configurations |
| Deployments |
| Logistics |
| Inventory Management |
| Documentation |
| Client Coordination |
| Ticket Forwarding |
| Troubleshooting / Incident Response |
| Warehouse Maintenance |
| Survey |

`Warehouse Maintenance` and `Survey` are allowed as real operational lanes, but they should only be used when explicit evidence or a private/local override identifies them. Otherwise, warehouse maintenance generally falls under Inventory Management or Logistics, and survey work generally falls under Documentation, Inventory Management, or Troubleshooting depending on context.

## General support distribution

For thin-context Neuron support days, use the operations-approved general distribution:

| Task lane | Share |
| --- | ---: |
| Configurations | 55% |
| Deployments | 5% |
| Logistics | 20% |
| Inventory Management | 10% |
| Documentation | 5% |
| Client Coordination | 5% |

## April rules

| Situation | Distribution |
| --- | --- |
| Saturday | Deployment plus documentation day: 80% Deployments, 20% Documentation |
| Sunday | 100% Logistics |
| Monday / Wednesday non-evening deployment window | Deployment plus documentation day: 80% Deployments, 20% Documentation |
| Weekday shift starting 2:00 PM or later | Deployment plus documentation day: 80% Deployments, 20% Documentation |
| Evening hours | 100% Configurations |
| Other thin-context Neuron support | General support distribution |

If April rules conflict, evening configuration takes precedence over the broader deployment windows because evening April work was generally configuration-heavy.

## May rules

| Situation | Distribution |
| --- | --- |
| Saturday | Configurations + Inventory Management |
| Sunday | Configurations + Inventory Management |
| Evening hours | Configurations + Inventory Management |
| Daytime support | Logistics, Configurations, Client Coordination, Ticket Forwarding, and Inventory Management |
| Confirmed May deployment field team | 30% Logistics, 50% Deployments, 20% Documentation |

May deployment work is sparse. Do not mark broad May work as deployment by default.

For known May deployment days, the public repo stores the rule only. Private workbooks or local config should identify which rows belong to the deployment field team using a role/cohort label such as `may_deployment_field_team`.

## May 6 rule

May 6, 2026 is a confirmed May deployment day for a limited field team.

The public repo must not hardcode technician names. The private/local layer should mark the applicable rows with:

```text
may_deployment_field_team
```

Those rows use:

| Task lane | Share |
| --- | ---: |
| Logistics | 30% |
| Deployments | 50% |
| Documentation | 20% |

Other Neuron-scoped rows on the same date remain standard support unless separately overridden.

## Stronger-evidence override: bounded workload attribution

Generic percentage distributions are a fallback for thin context. They must not override stronger dated evidence.

When workstation/device evidence establishes a bounded Configuration workload for a historical labor window, use the evidence-bounded contract in:

```text
docs/NTH_EVIDENCE_BOUNDED_ATTRIBUTION.md
triage/nth_evidence_bounded_allocation.py
```

Core rules:

1. Select the correct historical labor record for the question being answered; do not silently substitute a later reconstruction.
2. Device/workstation counts may establish a Configuration workload envelope, but they do not create labor hours.
3. Reserve hours required by stronger dated non-Configuration evidence before assigning the remaining defensible labor to Configuration.
4. Configuration may not exceed either the remaining selected labor total or the workload envelope.
5. The resulting maximum is a ceiling, not a quota.
6. Keep Configuration and Deployment distinct even when both support the same workstation population.
7. Do not turn target/install counts into same-window completed-device counts without dated device-level proof.
8. Do not automatically add a failure/rework contingency; actual rework requires dated evidence within the selected historical labor total.

### May 26–29 questioned tracker regression

For the historical tracker/model tied to the approximately 105 Configuration-hour question:

```text
Historical tracker total: 135.00h
Configuration:            104.78h
Inventory Management:      20.65h
Deployments:                 5.24h
Logistics:                   4.33h
```

The corrected workstation scope is:

```text
38 workstations × 2 devices/workstation × 2.0h/device
= 152.0h full-population Configuration workload capacity
```

The three non-Configuration lanes total `30.22h`, leaving `104.78h` of the 135h tracker. Therefore the 152h workload envelope is sufficient to support the old 104.78h Configuration allocation as a capacity-plausible historical model.

Do **not** replace the 135h tracker with the separate later `125.00h / 13 shifts` NTH reconstruction or the separate `147.00 net project hours` June 4 billing-thread record. Preserve those as distinct historical surfaces until an explicit reconciliation selects one for a different purpose.

## Implementation contract

The shared distribution implementation lives at:

```text
triage/neuron_task_hour_distribution_rules.py
```

The evidence-bounded calculator lives at:

```text
triage/nth_evidence_bounded_allocation.py
```

Generators should:

1. Resolve whether a roster row is in Neuron scope.
2. Determine which historical labor source governs the requested reconstruction.
3. Determine whether stronger dated evidence or a private/local day-role override applies.
4. When stronger bounded workload evidence applies, calculate the labor/workload ceilings before applying a generic percentage distribution.
5. Otherwise select the task-hour distribution using `choose_neuron_task_hour_distribution`.
6. Split hours using `distribute_task_hours` or the bounded allocation result, as appropriate.
7. Keep rule names, evidence references, selected historical authority, workload-envelope inputs, and override flags in an internal audit tab.
8. Keep the submission tab clean and PM-readable.

## Non-negotiables

- Do not distribute hours uniformly across all tasks.
- Do not infer technician-specific deployment duty from names in the public repo.
- Do not turn May support work into deployment by default.
- Do not fabricate event-level precision where the roster/event log does not contain it.
- Do not derive labor totals from device/workstation counts.
- Do not silently replace one historical hours surface with another.
- Do not preserve a later historical task ratio when stronger evidence supports a different bounded explanation for the requested artifact.
- Do use declared distributions when context is thin.
- Do use evidence-bounded workload attribution when stronger scope evidence exists.
