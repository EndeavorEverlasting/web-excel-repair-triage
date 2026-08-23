# Billing Artifact and Operator-Input Safety Contract

Binding for billing, Neuron Track Hours, roster/task reconciliation, operator-provided workbooks, and management evidence.

## Direction and source authority

- The current operator instruction controls within its authority unless it conflicts with higher repository law or a registered source-of-truth contract.
- Do not resurrect stale plans, abandoned sequences, old management targets, or remembered precedence when current tracked contracts exist.
- For the same artifact, the newest concrete compatible constraints control. If current authoritative sources materially disagree, surface the contradiction instead of inventing reconciliation.
- Billing quality is not arithmetic alone: preserve source provenance, evidence boundaries, required wording/abstraction, and artifact contracts.

## Operator-input immutability

`Candidates/` and `Active/` are read-only operator inputs unless an explicit contract authorizes mutation. Scripts must treat inputs as source-of-truth evidence, not convenient scratch space.

Never silently edit, normalize, deduplicate, repair, re-save, rename, or overwrite an operator input to make a downstream check pass. Never set `--output` equal to `--input`. Generated artifacts and machine evidence belong under the registered `Outputs/` family or another explicitly registered output path.

When evidence is missing or inconsistent, report the exact mismatch and use the registered review/unresolved mechanism. Do not fabricate hours, dates, workers, sites, devices, tickets, task detail, allocation, or incidents.

## Neuron Track Hours output profiles

Select the output family before loading deeper rules. The older `triage.nth_monthly_artifact` path is a working/review artifact. For the current June-completed / August-MTD **admin-management qualitative** family, demand-load `docs/NTH_QUALITATIVE_ADMIN_PROFILE.md` and `configs/artifact_profiles/nth_qualitative_admin.v1.json`, then use `scripts/build_nth_qualitative_admin.py`. Do not use a reference workbook as attendance truth or reconstruct its styling/language from memory.

## Cross-artifact reconciliation

Honor registered source direction such as **Roster Log to Admin Sheet**, **Roster Log to Task Tracker**, and **Task Tracker to Roster Log** only where the current domain contract defines it. Do not treat dashboard totals, capacity, device counts, prior totals, or management expectations as labor evidence unless a current authority explicitly does so.

## Proof boundary

A generated workbook is not accepted merely because it opens or balances mathematically. Run the strongest current generator, reconciliation, schema, Web Excel, package, and downstream acceptance gates assigned by the active contract, and distinguish producer proof from downstream/management acceptance.
