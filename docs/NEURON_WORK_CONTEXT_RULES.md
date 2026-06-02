# Neuron Work Context Rules

These rules prevent Neuron Track Hours generation from flattening all included Neuron work into one generic assignment label.

## Purpose

The roster determines who worked, when they worked, and whether the staff/date belongs to Neuron work. Once a row is in Neuron scope, the assignment/task label must be context-aware.

The clean submission tracker should contain only the selected task label. Rule names, confidence, and review explanations belong in internal audit artifacts.

## Allowed task categories

```text
Configurations
Inventory Management
Logistics
Deployments
Ticket Forwarding
Client Coordination
Documentation
Troubleshooting / Incident Response
```

## Durable rules

| Rule | Requirement |
| --- | --- |
| Dominant lane | Most Neuron hours classify as `Configurations` unless stronger evidence says otherwise. |
| Inventory lane | `Inventory Management` is the second-most common lane and includes stock, recon, staging, counts, kits, and shortages. |
| Ticket lane | `Ticket Forwarding` captures request routing, queue handling, RITM/REQ activity, and morning admin processing. |
| Client lane | `Client Coordination` captures meetings, calls, emails, status updates, and coordination work. |
| Deployment lane | April is the main deployment exception month: Saturdays usually classify as `Deployments`; April Monday/Wednesday evening windows may also classify as `Deployments`. |
| May weekend lane | May weekends are mostly `Configurations` and `Inventory Management`, not deployments by default. |
| Evening lane | Evening Neuron work skews toward `Configurations`. |
| Logistics lane | `Logistics` is daytime material movement, relay, delivery, pickup, shipment handling, and cleanup only. Do not classify evening work as logistics. |
| Explicit signals | Strong text signals from notes, worked-project labels, or resolved project context override time heuristics when safe. |

## Implementation contract

The shared implementation lives at:

```text
triage/neuron_work_context_rules.py
```

The Bonita/NTH resolver must call the shared classifier and must not hardcode all rows to `Neuron Installation`.

Expected behavior:

- Submission tracker: clean task category only.
- Internal audit: rule name, confidence, and review flags.
- No internal explanation text in the submission workbook.
- No generic `Bonita-friendly` wording in the tracker.

## Test target

```powershell
python -m pytest tests/test_neuron_work_context_rules.py tests/test_nw_prj_neuron_track_hours_bonita.py -q
```
