# 2026-05-20 Admin Billing Context Pipeline

This workflow was created after the April 2026 admin billing reconciliation push.

The core lesson: the workbook is not just arithmetic. It is chain-of-custody for
hours, exceptions, OOO rows, and Friday submission posture. Numbers can be right
while the framing is still wrong.

## Approved framing

Use this exact framing in admin-facing artifacts:

> Submission Posture: Updated April billing summary → hours-tracker-safe admin context. Built for consistent Friday reporting/submission review.

Do not use vague framing such as `Direction: cleaned April billing summary` when
the artifact is being submitted as a reviewed admin context package.

## Two-way scripts

The workflow needs two directions:

1. `scripts/billing_to_admin_context.py`
   - Input: reviewed billing/admin workbook.
   - Output: admin-facing context artifact.
   - Default export keeps only:
     - `01 Admin Summary`
     - `02 Tracker Import`
     - `03 Friday Batches`
   - Internal QC stays out of the admin submission unless explicitly requested.

2. `scripts/admin_context_to_billing.py`
   - Input: admin context workbook.
   - Output: billing-facing summary workbook.
   - Groups carried numeric hours by billing category, technician, and Friday batch.
   - Preserves blank-hour OOO/context-only rows as cleared context outside the numeric total.

## Friday reporting rule

Friday is the reporting/submission batch anchor.

- Monday through Friday work maps to that week's Friday.
- Saturday and Sunday work rolls into the next Friday unless explicitly assigned otherwise.
- This rule exists because Friday is the practical billing submission marker.

## Language guardrails

Admin-facing outputs must use calm operational language.

Approved summary language:

> Exception rows reconciled and cleared where applicable.

Approved blank-hour language:

> Blank-hour OOO/context-only rows reviewed and cleared where applicable.

Avoid defensive wording that makes the workbook sound suspect. The scripts treat
phrases like this as blocked admin-facing language:

- `no invented hours`
- `invented hours`
- `internal logic`
- `bridge logic`
- `confidence field`
- `inference language`
- `task evidence without attendance`

## OOO and context-only rule

OOO rows must not contain work-performed language.

Bad pattern:

> 04/01 confirmed OOO, but safe note still says configuration support or QA readiness.

Good pattern:

> Confirmed OOO for 04/01. No billable hours carried for this date.

Context-only rows should be explicit:

> 04/11 reviewed as context-only. No hours carried; no billing action required.

## Internal versus admin-facing posture

Keep internal proof work in `04 QC Pipeline` or similar tabs. Share tabs 1-3 with
admins. The shared workbook should explain the submitted hours without exposing
private bridge logic, inference fields, or forensic scratchwork.

## Validation gates

Before submission, check:

- total carried hours match expected reviewed total;
- no unresolved `REVIEW:` rows in admin-facing tabs;
- no internal-only tabs in the admin export;
- Friday batch totals equal tracker totals;
- blank-hour rows have OOO or context-only clearance language;
- OOO rows do not imply work was performed;
- suspicious language is absent from admin-facing cells.

Cold judge note: presentation is not garnish. If the framing is wrong, the
artifact looks less controlled even when the math is right.
