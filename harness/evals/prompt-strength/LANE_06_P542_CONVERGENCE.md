# LANE 06 — Converge and Integrate #542

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**PR / branch:** #542 / `feat/execution-boundary-enforcement-architecture-20260918`  
**Wave:** B  
**Hard dependencies:** Lane 02 commit + Lane 03 commit; refresh after any Lane 04/05 mainline merges  
**Writer:** singular #542 convergence owner

## Mission

Combine the boundary-core and observatory repairs into #542, reconcile shared validator/test-floor/prompt-policy/generated-site surfaces once, close review, and integrate the exact candidate.

## Read first

- Lane 02 and Lane 03 handoffs/commit SHAs
- current #542 diff/review/checks
- current main after #543/line-ending merges that completed
- `harness/test-floor.v1.json`
- `harness/validators.v1.json`
- `registry/prompts/actionable-next-step-policy.v1.json`
- canonical Prompt Kit builder and Pages promotion docs

## Owned scope

All #542-owned files, plus conflict resolution required to integrate Lane 02/03 commits and refreshed main. No new feature scope.

## Forbidden scope

#537 prompt-strength semantics, #543 compiler/local-action source ownership, unrelated release/versioning changes.

## Tasks

1. Refresh main and #542.
2. Prove Lane-02 and Lane-03 commits are based on the expected #542 lineage and contain no forbidden-scope writes.
3. Merge/cherry-pick them into #542 without rewriting their evidence.
4. Merge/rebase refreshed main using repository policy; resolve `harness/test-floor.v1.json`, validator profile, and generated-site conflicts from current owners.
5. Regenerate Prompt Kit only via builder.
6. Re-fetch current #542 review threads; resolve each still-valid thread with current-head evidence.
7. Diagnose the current Operant external-resource-refresh failure. If it is external/provider-only and not required by the merge contract, type it accurately; if it reflects candidate behavior, repair it.
8. Run focused boundary/privacy suites, deterministic floor, local required checks, builder parity, and exact-candidate hygiene.
9. Push existing #542 branch.
10. Merge when green/authorized; refresh main and prove containment + current boundary/policy content.

## Validation order

```bash
python scripts/validate_execution_boundary_enforcement.py --summary
python -m unittest tests.test_execution_boundary_enforcement_prompt -v
python scripts/validate_privacy_preserving_failure_observatory.py --summary
python -m unittest tests.test_privacy_preserving_failure_observatory_prompt -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/run_repository_action.py --action required-checks-proof --base-ref origin/main --report Outputs/repository-actions/required-checks-proof.json
git diff --check
git diff --cached --check
```

## Safety

One convergence writer only. Preserve sibling branch/worktree commits until merge proof is complete. No force push. No manual generated HTML edits.

## Commit / push / merge contract

Commit conflict resolutions/regeneration separately when useful for auditability. Push #542 normally. Merge only at exact validated head.

## Proof level / ceiling

Target: VALIDATED + INTEGRATED execution-boundary and observatory controls.  
Ceiling: repository/provider integration; installed host-level supervisor behavior remains separately observed.

## Exact final response

Report dependency commit SHAs, pre/post main, conflicts and resolutions, review disposition, validation receipts, #542 head, merge SHA, post-merge containment/content proof, remaining runtime ceiling.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git switch feat/execution-boundary-enforcement-architecture-20260918 && git merge --no-edit origin/main
```
