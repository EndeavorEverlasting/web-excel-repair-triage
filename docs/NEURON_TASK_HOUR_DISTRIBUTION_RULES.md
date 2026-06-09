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

## Implementation contract

The shared implementation lives at:

```text
triage/neuron_task_hour_distribution_rules.py
```

Generators should:

1. Resolve whether a roster row is in Neuron scope.
2. Determine whether a private/local day-role override applies.
3. Select the task-hour distribution using `choose_neuron_task_hour_distribution`.
4. Split net hours using `distribute_task_hours`.
5. Keep rule names and override flags in an internal audit tab.
6. Keep the submission tab clean and PM-readable.

## Non-negotiables

- Do not distribute hours uniformly across all tasks.
- Do not infer technician-specific deployment duty from names in the public repo.
- Do not turn May support work into deployment by default.
- Do not fabricate event-level precision where the roster/event log does not contain it.
- Do use declared distributions when context is thin.
