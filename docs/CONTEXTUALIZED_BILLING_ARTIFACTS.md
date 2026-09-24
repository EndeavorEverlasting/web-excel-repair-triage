# Contextualized Billing Artifacts

This document locks the May 29 sprint correction into the repo workflow.

## Rule

Billing artifacts must explain the work actually performed. Generic placeholder assignment labels are not acceptable when task-tracker, roster, timing, or operational context exists.

## Required outputs

Leadership-facing monthly billing outputs must include:

1. A clean monthly billing summary.
2. A row-level tracker/import tab with usable work context.
3. A reporting-batch tab.
4. At least one visual summary, preferably:
   - hours by work-context category,
   - top technician hours,
   - reporting-batch trend.

Project-hours exports must include row-level work context in the final visible context/assignment column.

## Context hierarchy

Use evidence in this order:

1. Task tracker context.
2. Roster/project assignment evidence.
3. Timing and day-pattern rules.
4. Explicit operator notes.
5. Last-resort generic category only when no better source exists.

## Current operating rules

For the April and May 2026 billing workflow:

- April Saturdays are deployment-heavy unless task evidence says otherwise.
- May Saturdays are configuration and inventory management.
- Evening hours are configuration and inventory management.
- Day hours are logistics, inventory management, incident response, ticket coordination, and client coordination.
- Warehouse movement, staging, stock delivery, and stock recovery should be treated as inventory management and logistics.
- Most hours should not be summarized as installation work unless there is direct evidence for installation.

## Leadership artifact boundary

Leadership-facing billing artifacts must not include employee pay-petition framing, private review scaffolding, confidence fields, or internal exception machinery.

Pay-difference analysis belongs in a separate comparison workbook or internal review artifact.

**Work context classification rules:** see [`BILLING_WORK_CONTEXT_RULES.md`](BILLING_WORK_CONTEXT_RULES.md).

## Failure modes

Stop and revise if any leadership-facing workbook:

- summarizes most work as a generic placeholder,
- lacks visual summaries,
- hides the operational context column,
- mixes pay-petition language into the billing summary,
- or exposes internal review machinery.
