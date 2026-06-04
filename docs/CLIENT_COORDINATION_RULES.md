# Client Coordination Assignment Rules

This document records the assignment rules for client-coordination work in Neuron Track Hours, admin billing summaries, and related artifact engines.

## Rule

Only the following people should be classified as handling **Client Coordination** work:

- Richard Perez / Rich Perez
- Khadejah Harrison
- Alejandro Perales

No other technician should be auto-classified as `Client Coordination` without explicit manual review and written supporting evidence.

## Why this exists

Client coordination is not a generic midday support bucket. It represents client-facing coordination ownership, communication, scheduling, or project-facing coordination responsibilities.

For artifact generation, this means:

- Client Coordination rows for Richard/Rich Perez, Khadejah Harrison, or Alejandro Perales may remain as `Client Coordination` when supported by source evidence.
- Client Coordination rows for any other technician must be routed to review instead of silently accepted.
- Generators should not infer Client Coordination from time-of-day slots alone.
- Existing historical rows outside the approved coordination group should be flagged as review targets, not silently relabeled.

## Engine behavior

Artifact engines should apply this rule as follows:

1. Preserve the original source evidence.
2. If `assignment_type == "Client Coordination"` and the technician is not in the approved coordination group, emit a review item.
3. Do not include unauthorized Client Coordination as clean admin-ready classification unless the review is resolved.
4. If a replacement classification is required, it must come from source evidence or an explicit correction map.
5. Do not guess between Inventory Management, Configurations, Ticket Forwarding, or Deployment when the source only says Client Coordination.

## Approved coordinator set

Use this normalized set for rule checks:

```python
APPROVED_CLIENT_COORDINATORS = {
    "Richard Perez",
    "Rich Perez",
    "Khadejah Harrison",
    "Alejandro Perales",
}
```

## Spreadsheet artifact expectations

Neuron Track Hours and billing workbooks should make this visible:

- unauthorized Client Coordination rows should be highlighted or listed in a Review Queue;
- clean admin-ready outputs should not hide the review condition;
- review notes should explain that only Richard/Rich Perez, Khadejah Harrison, and Alejandro Perales handle client coordination.

## Related Rezaul classification note

Rezaul Roman's April 2026 Neuron work should be treated as mixed **Inventory Management** and **Configurations** when the source evidence indicates mixed warehouse/inventory and configuration work. If a generator splits a punch into both categories, the split must be deterministic and reviewable, not hidden.
