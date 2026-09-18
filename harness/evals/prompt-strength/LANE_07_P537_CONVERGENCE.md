# LANE 07 — Reconcile and Integrate #537

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**PR / branch:** #537 / `feat/prompt-strength-contract-matrix-20260917`  
**Wave:** C  
**Hard dependencies:** Lane 01 complete; Lane 06/#542 integrated; refresh current main  
**Writer:** singular #537 convergence owner

## Mission

Bring #537 onto the fully strengthened mainline, discard stale dependency-era edits, resolve shared-floor conflicts from current authority, and merge the prompt-strength semantic floor.

## Read first

- Lane 01 handoff/commit
- canonical closeout plan
- current main after #542/#543/line-ending work
- #537 changed files and unresolved reviews
- current-main `harness/contracts/prompt-quality-history.v1.json`
- current-main `harness/test-floor.v1.json`
- current shared actionable policy
- `harness/contracts/prompt-strength.v1.json`
- prompt-strength matrix/validator/test

## Required reconciliation

1. Prove #535/#539/#541 semantics survive on current main; do not carry historical PR-state assumptions.
2. Prove #542's boundary-accountability shared policy is present; #537 must consume rather than duplicate it.
3. Re-evaluate every #537 edit to `prompt-quality-history.v1.json`. If current main already closes P07 containment, drop branch-only waiver/history edits that no longer strengthen the contract.
4. Resolve `harness/test-floor.v1.json` from current main plus the prompt-strength test registration. Never restore the older whole-file snapshot.
5. Preserve Lane 01's semantic-evidence hardening and PSA-031 silent-stop regression unless current shared boundary contract supersedes it with strictly stronger equivalent coverage; if superseded, record the migration rather than silently deleting it.

## Tasks

1. Refresh and merge/rebase current main into #537.
2. Resolve collisions by canonical owner, not by “ours/theirs” convenience.
3. Run Prompt Quality History before and after any history-file edit.
4. Run prompt-strength validator/tests.
5. Run deterministic floor and local required checks.
6. Regenerate Prompt Kit only if current #537 source changes affect it; prove parity.
7. Re-fetch all #537 review threads and close only with exact-head evidence.
8. Push #537; merge when exact candidate is green and no dependency/review conflict remains.
9. Refresh main and prove merge containment plus presence of prompt-strength contract/matrix/test.

## Validation order

```bash
python scripts/validate_prompt_quality_history.py --summary
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract_prompt -v
python scripts/run_repository_action.py --action required-checks-proof --base-ref origin/main --report Outputs/repository-actions/required-checks-proof.json
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
git diff --check
git diff --cached --check
```

## Safety

No wholesale branch reset. No stale waiver restoration just to get green. No shared-policy duplication. No proof promotion from PR state alone.

## Commit / push / merge contract

Existing #537 branch. Preserve Lane 01 commits. Commit reconciliation separately when possible. Merge only after exact-head validation.

## Proof level / ceiling

Target: VALIDATED + INTEGRATED prompt-strength semantic floor on current main.  
Ceiling: not Pages production or observed model behavior until Lanes 08–09.

## Exact final response

Report old/new base, dropped/surviving stale edits, conflict owners, all validator/action receipts, exact #537 head, merge SHA, current-main containment/content proof, next publication gate.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git switch feat/prompt-strength-contract-matrix-20260917 && git merge --no-edit origin/main
```
