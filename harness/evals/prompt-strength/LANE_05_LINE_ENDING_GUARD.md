# LANE 05 — Systemic CRLF / Line-Ending Guard

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**Base:** refreshed `origin/main`  
**Wave:** A  
**Suggested branch:** `fix/line-ending-policy-20260918`  
**Hard dependencies:** none  
**Safe parallel work:** Lanes 01–04  
**Convergence owner:** this lane; merge independently when green

## Mission

Make recurring CRLF/line-ending drift impossible to treat as per-diff cleanup by establishing one canonical repository normalization policy plus regression proof.

## Read first

- `AGENTS.md`
- `harness/contracts/prompt-regression-safety.v1.json`
- `scripts/validate_prompt_regression_safety.py`
- `tests/test_prompt_regression_safety_prompt.py`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `harness/validators.v1.json`
- `harness/promotion/required-checks.v1.json`
- `harness/prompt-topology/config.v1.json` for existing Prompt Kit LF normalization
- current tracked file extensions / binary artifacts

## Current evidence

Current main has working/staged/exact-candidate whitespace checks, but no root `.gitattributes`. Therefore trailing whitespace/conflict markers are guarded while repository-wide checkout/commit line-ending normalization is not canonically declared.

## Owned scope

- new root `.gitattributes`
- smallest existing regression-safety contract/validator/test changes required to enforce the policy

Prefer extending the already-registered regression-safety test instead of adding another test-floor identity.

## Forbidden scope

- mass opportunistic file rewrites
- `git add --renormalize .` without a separately reviewed migration
- `harness/repository-actions.v1.json`
- #542/#543/#537 owned files
- generated Prompt Kit HTML
- binary content conversion

## Tasks

1. Refresh main and create an isolated branch/worktree.
2. Inventory tracked text/binary extensions and sample current endings before choosing policy.
3. Add `.gitattributes` with `text=auto` baseline plus explicit deterministic eol rules for source/config/docs. Use exceptions only when a concrete runtime/tool requirement demands them; document that evidence in the test/contract.
4. Add a negative regression that mutates the policy or feeds a CRLF-owned LF surface and proves rejection.
5. Add a positive control for allowed normalized content and any justified exception.
6. Extend `validate_prompt_regression_safety.py` only if needed to make policy presence/critical rules fail closed.
7. Prove existing patch-hygiene contracts still pass.
8. Do not renormalize the whole repository in this sprint.
9. Commit, push, open/reuse the smallest PR, validate, merge if green, then verify main contains the policy.

## Validation order

```bash
python scripts/validate_prompt_regression_safety.py --summary
python -m unittest tests.test_prompt_regression_safety_prompt -v
git check-attr --all -- .gitattributes '*.py' '*.json' '*.md' '*.sh' '*.ps1' '*.cmd'
git diff --check
git diff --cached --check
```

After commit, run the repository-owned exact-candidate action against `origin/main`.

## Safety

Do not assume every Windows-oriented file requires CRLF. Do not assume every file is text. Prove binary exclusions and explicit exceptions. Avoid giant normalization diffs.

## Commit / push / PR contract

One branch, one coherent policy+regression commit set. Merge as soon as exact candidate is green; downstream lanes refresh afterward.

## Proof level / ceiling

Target: VALIDATED + INTEGRATED repository line-ending policy.  
Ceiling: does not prove every developer's global Git config or editor settings; proves repository-enforced checkout/index expectations and regression policy.

## Exact final response

Report inventory, selected policy, exceptions and evidence, negative/positive fixtures, commands/results, changed paths, commit/PR/merge, main containment, and any unrenormalized legacy files that remain.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git worktree add ../wetr-line-endings -b fix/line-ending-policy-20260918 origin/main
```
