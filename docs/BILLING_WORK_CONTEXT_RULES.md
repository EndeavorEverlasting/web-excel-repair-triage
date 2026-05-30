# Billing Work Context Rules

**Canonical classification spec.** When classification logic changes, update this document in the same PR as code. Tests in `tests/test_billing_context_rules.py` must cover every rule below.

Related docs:

- Output quality and leadership boundaries: [`CONTEXTUALIZED_BILLING_ARTIFACTS.md`](CONTEXTUALIZED_BILLING_ARTIFACTS.md)
- CLI and exporter usage: [`BILLING_CONTEXT_EXPORTER.md`](BILLING_CONTEXT_EXPORTER.md)
- Admin posture, Friday batch, language guardrails: [`2026-05-20-admin-billing-context-pipeline.md`](2026-05-20-admin-billing-context-pipeline.md)

Implementation: [`triage/billing_context/context_rules.py`](../triage/billing_context/context_rules.py)

---

## 1. Placeholder labels (suspect by default)

These assignment labels are **placeholders**, not acceptable final work context when better evidence exists:

- `Neuron Installation`
- `installation` / `install`
- `neuron install` / `neuron installation`

Most hours must **not** be summarized as installation work unless task evidence directly supports installation activity.

When a placeholder is replaced, record an internal mismatch (`placeholder_assignment_replaced`); leadership exports show the resolved context only.

---

## 2. Context hierarchy (evidence order)

Apply evidence in this order. Stop at the first decisive source:

1. **Task tracker text** — highest priority; keyword classification from admin billing context submission.
2. **Non-placeholder roster/project assignment** — retain when task text is absent or inconclusive.
3. **Timing and day-pattern rules** — see §3; used when steps 1–2 do not resolve context.
4. **Explicit operator notes** — free-text fields in tracker or roster rows.
5. **Last-resort generic category** — `Unknown / Needs Review` only when no better source exists.

---

## 3. Timing and day-pattern rules

These are **rules**, not suggestions. They reflect April–May 2026 operational reality.

| When | Default work context | Notes |
|------|---------------------|-------|
| **April Saturdays** | `Deployment Support` | April billing was deployment-heavy on Saturdays unless task evidence says otherwise |
| **May+ Saturdays** | `Inventory Management` (default) or `Configuration` | May onward: configuration and inventory work — **not** deployment-first, **not** logistics-first |
| **Evening hours** (start ≥ 16:00 or end ≥ 18:00) | `Inventory Management` (default) or `Configuration` | Evenings are configuration/inventory work — **not** `Logistics` |
| **Sundays** | `Logistics` | Cleanup operations, stock movement, warehouse recovery |
| **Weekday daytime** | `Mixed Operational Support` | Hospital stock delivery, logistics runs, inventory management, incident response, ticket coordination, client coordination |
| **Warehouse / staging / stock** (in task text) | `Inventory Management & Logistics` | When text mentions warehouse, staging, stock, delivery, pickup |

### Anti-patterns

- Do **not** classify May+ Saturday or evening hours as `Logistics` unless task text explicitly describes delivery or cleanup.
- Do **not** use `Inventory Management & Logistics` as a lazy timing fallback for May evenings or Saturdays.
- April vs May **Saturday behavior differs by design** (deployment-heavy April vs config/inventory May+).

### Configuration vs Inventory Management (May+ timing fallback)

When timing rules apply but task text does not decide:

- Default to **`Inventory Management`**.
- Use **`Configuration`** when assignment or notes hint at build, imaging, setup, or device configuration language.

---

## 4. Task-text keyword buckets

When task tracker text is present, classify by keywords (first match wins):

| Keywords (case-insensitive) | Work context |
|----------------------------|--------------|
| configure, configuration, imaged, image, setup, build | `Configuration` |
| inventory, warehouse, stock, staging, deliver, delivery, pickup, logistics | `Inventory Management & Logistics` |
| deploy, deployment, go live, go-live, floor support | `Deployment Support` |
| incident, break/fix, outage, urgent, support issue | `Incident Response` |
| ticket, servicenow, ritm, req | `Ticket Coordination` |
| client, pm, coordination, coordinate, follow up, follow-up | `Client Coordination` |

If no keyword matches, fall through to hierarchy steps 2–5.

---

## 5. Allowed work-context labels

| Label | Meaning |
|-------|---------|
| `Configuration` | Device imaging, build, setup, configuration work |
| `Inventory Management` | Stock control, staging, warehouse operations without primary delivery |
| `Inventory Management & Logistics` | Combined inventory and stock movement / delivery |
| `Deployment Support` | Go-live, floor support, deployment activity |
| `Incident Response` | Break/fix, outage, urgent support |
| `Ticket Coordination` | ServiceNow / RITM / REQ coordination |
| `Client Coordination` | PM follow-up, client-facing coordination |
| `Logistics` | Delivery runs, cleanup, stock movement (especially Sundays) |
| `Mixed Operational Support` | Weekday daytime blend when no single category dominates |
| `Unknown / Needs Review` | No decisive evidence — internal review required |

---

## 6. Leadership vs internal surfaces

### Leadership artifacts (contextualized `.xlsx`)

Include: `Date`, `Tech`, `Hours`, `Work Context`, optional `Original Assignment`, `Start Time`, `End Time`.

**Exclude:** confidence, context-reason, raw task notes, pay-petition framing, internal exception machinery, draft reasoning, review scaffolding.

Scan all string cells for blocked language per [`admin_billing_context_rules.py`](../triage/admin_billing_context_rules.py) before export.

### Internal artifacts (HTML dashboard, mismatch JSON/CSV)

May include: context reason, confidence, full notes, cross-source hour deltas, partial-hour flags, dashboard unresolved rows.

---

## 7. Maintenance rule

> Classification changes require **both** an update to this document **and** matching tests. Do not change `context_rules.py` behavior without updating §3–§4 here.
