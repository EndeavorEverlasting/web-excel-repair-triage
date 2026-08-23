# Neuron Work Context Rules

These rules prevent Neuron Track Hours generation from flattening all included Neuron work into one generic assignment label or carrying unsupported high-risk labels forward from legacy trackers.

## Purpose

The roster determines who worked, when they worked, and whether the staff/date belongs to Neuron work. Once a row is in Neuron scope, the assignment/task label must be context-aware and evidence-bounded.

The clean submission tracker should contain only the selected task label. Rule names, confidence, source authority, and review explanations belong in internal audit artifacts.

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
| Inventory lane | `Inventory Management` is a low-profile lane for stock, reconciliation, staging, counts, kits, and shortages. |
| Ticket lane | `Ticket Forwarding` captures request routing, queue handling, RITM/REQ activity, and morning admin processing. |
| Client lane | `Client Coordination` captures meetings, calls, emails, status updates, and coordination work. |
| Deployment evidence gate | `Deployments` is a high-risk person/date label. Outside an explicitly registered historical month rule, require direct row evidence describing deployment/install/go-live/cutover execution. A bare `Deployment` label, resolved project name, legacy monthly Deployment bucket, deployment tracker, deployment planning/information, package-level field/deployment-support wording, or device count is insufficient. |
| April historical lane | April is the registered deployment exception month: Saturdays usually classify as `Deployments`; April Monday/Wednesday evening windows may also classify as `Deployments`. These month-specific rules do not silently carry into June or later months. |
| May weekend lane | May weekends are mostly `Configurations` and `Inventory Management`, not deployments by default. |
| Unsupported high-risk fallback | When Deployment is not directly supported, use only a lower-profile category supported by the row/current evidence or the deterministic fallback. Do not replace one unsupported high-risk label with another and do not manufacture task hours or percentages. |
| Evening lane | Evening Neuron work skews toward `Configurations`. |
| Logistics lane | `Logistics` is daytime material movement, relay, delivery, pickup, shipment handling, and cleanup only. Do not classify evening work as logistics. |
| Explicit signals | Strong lower-risk text signals from notes, worked-project labels, or resolved project context may override time heuristics. Deployment has its own stronger gate and may not be inferred from resolved-project text. |

## June 2026 guardrail

The legacy June source includes a monthly `Deployment` bucket, and June billing correspondence mentions field/deployment support at the package level. Neither source is literal person/date deployment truth. A June detail row may say `Deployments` only when dated evidence ties deployment execution to that shift.

When that evidence is absent, the qualitative admin surface should use lower-profile supported context such as Configuration/Validation, Inventory/Reconciliation, Survey/Recon, Logistics/Staging, Readiness/Field Support, Documentation/Coordination, or Troubleshooting/Support. The fallback describes service context only and does not redistribute paid hours.

## Implementation contract

The shared implementation lives at:

```text
triage/neuron_work_context_rules.py
```

The Bonita/NTH resolver must call the shared classifier and must not hardcode all rows to `Neuron Installation` or trust a generic `Deployment` noun as shift-level evidence.

Expected behavior:

- Submission tracker: clean supported task category only.
- Internal audit: rule name, confidence, source authority, and review flags.
- No internal explanation text in the submission workbook.
- No generic `Bonita-friendly` wording in the tracker.
- No person/date `Deployments` solely because a project name, legacy category, tracker, or monthly package contains the word deployment.

## Test target

```powershell
python -m pytest tests/test_neuron_work_context_rules.py tests/test_nw_prj_neuron_track_hours_bonita.py -q
```