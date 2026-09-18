# LANE 01 — Repair #537 Prompt-Strength Semantic Core

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**PR / branch:** #537 / `feat/prompt-strength-contract-matrix-20260917`  
**Wave:** A  
**Primary ownership:** prompt-strength semantic contract/matrix/validator/tests  
**Hard dependencies:** none beyond refreshed main/provider truth  
**Safe parallel work:** Lanes 02, 03, 04, 05  
**Convergence owner:** Lane 07

## Mission

Repair #537's semantic defects while avoiding shared files now owned by #542/#543. The immediate known defect is PSA-029 over-crediting `fixed_point_continuation`.

## Read first

- `AGENTS.md`
- `harness/evals/PROMPT_STRENGTH_RECOVERY_SPRINT_PLAN.md`
- `harness/contracts/prompt-strength.v1.json`
- `harness/evals/prompt-strength/adversarial-regression-matrix.v1.json`
- `scripts/validate_prompt_strength.py`
- `tests/test_prompt_strength_contract_prompt.py`
- current PR #537 reviews/checks
- current `main` history contract after #541

## Compact preflight

Record current main SHA, #537 head, ahead/behind, dirty state, worktrees, open overlapping PRs, unresolved #537 review threads, exact failing checks.

## Owned scope

- prompt-strength contract
- prompt-strength adversarial matrix
- prompt-strength validator
- focused prompt-strength test
- prompt-strength planning/handoff artifacts

## Forbidden scope

- `harness/test-floor.v1.json` until Lane 07
- `registry/prompts/actionable-next-step-policy.v1.json`
- P07 compiler semantics/policy
- `harness/repository-actions.v1.json`
- hand-edited `web/prompt-kit/index.html`
- #542 boundary/observatory files

## Tasks

1. Refresh `origin/main` and PR #537 provider state.
2. Reproduce the current focused failure before editing.
3. Repair PSA-029: remove `fixed_point_continuation` unless its stimulus/assertions genuinely exercise fixed-point continuation. Do not weaken semantic-evidence matching.
4. Re-read every unresolved #537 review thread against the current branch; implement still-valid findings only.
5. Re-run focused prompt-strength validation.
6. Do not rebase/merge current main if doing so would force resolution of #542-owned `test-floor`; leave that for Lane 07.
7. Commit only owned files and push the existing #537 branch.

## Validation order

```bash
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract_prompt -v
git diff --check
git diff --cached --check
```

If local repository actions are usable, also run the smallest relevant read-only action without regenerating the site.

## Safety

Preserve unrelated dirty work. No force push. No new prompt identity. No waiver deletion/addition merely to satisfy history checks. A current-main P07/history discrepancy is Lane 07 evidence, not license to mutate history here.

## Commit / push contract

Commit one coherent semantic repair to the existing #537 branch. Push normally. Do not merge #537 in this lane.

## Proof level / ceiling

Target: IMPLEMENTED + LOCALLY VALIDATED focused semantic core.  
Ceiling: no shared-floor reconciliation, mainline integration, Pages deployment, or downstream model-obedience proof.

## Exact final response

Report: refreshed main/head; changed files; reproduced defect; repair; focused command results; unresolved review/checks; commit SHA; push state; preserved git/worktree state; exact handoff to Lane 07.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git switch feat/prompt-strength-contract-matrix-20260917 && python scripts/validate_prompt_strength.py --summary
```
