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

`Warehouse Maintenance` and `Survey` should only be used when explicit evidence or a private/local override identifies them. Otherwise, warehouse maintenance generally falls under Inventory Management or Logistics, and survey work generally falls under Documentation, Inventory Management, or Troubleshooting depending on context.

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

For known May deployment days, the public repo stores the rule only. Private workbooks or local config should identify applicable rows with a role/cohort label such as `may_deployment_field_team`.

## May 6 rule

May 6, 2026 is a confirmed May deployment day for a limited field team.

The private/local layer should mark applicable rows with:

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

## Stronger-evidence override: bounded Configuration attribution

Generic percentage distributions are a fallback for thin context. They must not override stronger dated evidence.

Use the evidence-bounded contract in:

```text
docs/NTH_EVIDENCE_BOUNDED_ATTRIBUTION.md
triage/nth_evidence_bounded_allocation.py
```

Core rules:

1. Select the correct historical labor record for the question being answered; do not silently substitute a later reconstruction.
2. **Only a confirmed Configuration count may be multiplied by Configuration timing.**
3. Testing / IDT counts, target counts, installation counts/dates, and generic remaining-work counts are not Configuration multipliers.
4. The bounded helper requires `scope_kind="configuration_count"`; all other scope types fail closed.
5. Reserve hours required by stronger dated non-Configuration evidence before assigning remaining defensible labor to Configuration.
6. Configuration may not exceed either remaining selected labor or confirmed-population workload capacity.
7. The result is a ceiling, not a quota.
8. Keep Configuration and Deployment distinct even when they support the same device population.
9. Installation dates establish chronology, not exact Configuration timestamps or labor.
10. Do not automatically add a failure/rework contingency; actual rework requires dated evidence inside the selected labor control.

## Packet M May 26–29 correction

Historical tracker state is preserved for audit:

```text
Historical tracker total: 135.00h
Configuration label:       104.78h
Inventory Management:       20.65h
Deployments:                  5.24h
Logistics:                    4.33h
```

The old 104.78h / 77.61% Configuration share is **not** the target for the next packet.

### The `38 remaining` total

The All-Wave / Risk Summary `38 remaining` is **device-testing / IDT remaining scope**.

Do not use either historical chain:

```text
38 × 2h = 76h
```

or

```text
38 workstations × 2 devices × 2h = 152h
```

Both are invalid active Configuration models because the multiplier is a testing count.

### Installation chronology

The Risk Summary separately carries installation dates including 05/06, 05/11–05/12, 05/13, 05/22, 05/22 and **05/26**.

The 05/26 CCMC anchor supports continuing production into the questioned May 26–29 window. It does not tell the generator how many devices were configured that day.

### Device-specific timing

For a **confirmed** configuration count:

- Neuron normalized allocation: **1.50h / device**;
- Neuron detailed process: **56–88 min**;
- optional separate Neuron rename: **+5–10 min**, for **61–98 min** detailed total;
- Cybernet detailed process: **118–156 min**, approximately **1.97–2.60h**;
- confirmed Cybernet+Neuron pair: **3.47–4.10h direct Configuration**.

Scenario translations may be shown internally when the exact count is open, but no row may be selected as fact without device-level Configuration evidence.

## Implementation contract

The shared distribution implementation lives at:

```text
triage/neuron_task_hour_distribution_rules.py
```

The evidence-bounded calculator and device-specific timing model live at:

```text
triage/nth_evidence_bounded_allocation.py
```

Generators should:

1. Resolve whether a roster row is in Neuron scope.
2. Determine which historical labor source governs the requested reconstruction.
3. Determine whether stronger dated evidence or a private/local day-role override applies.
4. Classify every workload count by authority before multiplying it.
5. Reject testing/IDT, target, install, or generic remaining counts as Configuration multipliers.
6. When a confirmed Configuration count exists, use the device-specific timing model and labor ceilings.
7. When the count is not confirmed, keep Configuration scenario-bounded rather than ratio-first.
8. Otherwise select the generic task-hour distribution using `choose_neuron_task_hour_distribution`.
9. Keep rule names, evidence references, historical authority, scope kind, timing inputs, and override flags in an internal audit tab.
10. Keep the submission tab clean and PM-readable.

## Non-negotiables

- Do not distribute hours uniformly across all tasks.
- Do not infer technician-specific deployment duty from names in the public repo.
- Do not turn May support work into deployment by default.
- Do not fabricate event-level precision where the roster/event log does not contain it.
- Do not derive labor totals from device/workstation counts.
- Do not convert device-testing / IDT remaining scope into Configuration labor.
- Do not silently replace one historical hours surface with another.
- Do not preserve the historical 104.78h Configuration label by inertia.
- Do use declared distributions when context is thin.
- Do use confirmed-count evidence-bounded attribution when stronger Configuration evidence exists.
