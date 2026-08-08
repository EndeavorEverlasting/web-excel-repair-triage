# Client Coordination Assignment Rules

This document records the assignment rules for client-coordination work in Neuron Track Hours, admin billing summaries, and related artifact engines.

## Rule

Only the following people should be classified as handling **Client Coordination** work:

- Richard Perez / Rich Perez
- Khadejah Harrison
- Alejandro Perales
- Geoff Gerber

No other technician should be auto-classified as `Client Coordination` without explicit manual review and written supporting evidence.

## Why this exists

Client coordination is not a generic midday support bucket. It represents client-facing coordination ownership, communication, scheduling, or project-facing coordination responsibilities.

For artifact generation, this means:

- Client Coordination rows for Richard/Rich Perez, Khadejah Harrison, Alejandro Perales, or Geoff Gerber may remain as `Client Coordination` when supported by source evidence.
- Client Coordination rows for any other technician must be removed from clean admin-ready time sheets or routed to an internal review artifact, depending on the artifact type.
- Generators should not infer Client Coordination from time-of-day slots alone.
- Existing historical rows outside the approved coordination group should not remain in submission-ready Neuron Track Hours rows.

## Engine behavior

Artifact engines should apply this rule as follows:

1. Preserve the original source evidence in internal sidecars when available.
2. If `assignment_type == "Client Coordination"` and the technician is not in the approved coordination group, remove the row from clean admin-ready Neuron Track Hours output.
3. For internal workbooks or sidecars, route the removed row to a review/audit artifact instead of silently accepting it.
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
    "Geoff Gerber",
}
```

## Spreadsheet artifact expectations

Neuron Track Hours and billing workbooks should make this visible:

- unauthorized Client Coordination rows should not remain in clean admin-ready time sheets;
- internal review outputs may list removed rows for audit, but submission workbooks should not preserve unauthorized coordination rows as visible work rows;
- review notes should explain that only Richard/Rich Perez, Khadejah Harrison, Alejandro Perales, and Geoff Gerber handle client coordination.

## Related Rezaul classification note

Rezaul Roman's April 2026 Neuron work should be treated as mixed **Inventory Management** and **Configurations** when the source evidence indicates mixed warehouse/inventory and configuration work. If a generator splits a punch into both categories, the split must be deterministic and reviewable, not hidden.
