# Lane 03 — Dependency Reconciliation

**Authority:** research-design contributor  
**Owned output:** `harness/evals/prompt-strength/dependency-reconciliation.v1.json`  
**Forbidden:** mutation of PR #533, #535, #536 owned files.

## Mission
Refresh exact provider/default-branch truth and determine which semantics from the three active repair dependencies survive into the current repository floor before any shared-policy/compiler convergence begins.

## Read first
- `AGENTS.md`
- `harness/evals/PROMPT_STRENGTH_RECOVERY_SPRINT_PLAN.md`
- `harness/evals/prompt-strength/dependency-reconciliation.template.v1.json`
- PR #533, #535, #536 metadata, changed files, current heads, checks, reviews, and merge state

## Tasks
1. Fetch/refresh default branch and exact PR heads without force.
2. For each PR, distinguish open/merged/superseded state from actual current-content survival.
3. Inspect the governing contract/content that the PR owns.
4. Run the owning validator/tests when executable locally; record exact command, head, and result.
5. Enumerate collisions with the future Phase-3 convergence surfaces.
6. Produce the reconciliation artifact with exact evidence and the next allowed transition.

## Validation
The artifact must not mark a dependency reconciled from ancestry or PR state alone. Current content plus owning proof is required.

## Proof ceiling
Dependency/integration evidence only; no authorization to mutate sibling-owned surfaces and no downstream model-obedience claim.
