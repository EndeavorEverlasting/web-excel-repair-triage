# PR Merge-Gate Operator Report

**As of:** 2026-08-15
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Workflow owner:** `pr-floor-integration`
**Focused contract:** `harness/contracts/pr-merge-gate.v1.json`
**Validator:** `scripts/validate_pr_merge_gate.py`

## Failure that triggered this contract

PR #181 had an exact validated head, was open, non-draft, mergeable, and had successful final-head CI. Merge intent and authority were present. The agent nevertheless reported the unmerged PR as a blocker and handed the operator a feature-branch retrieval command.

That was the wrong state transition. An actionable authorized merge gate is not a blocker.

PR #181 was subsequently merged with expected-head protection. The merge commit is `913645482c2f0f214665ee04be712abc5f46a052`, and `main` was verified at that commit before this harness repair branch was created.

## Required decision rule

The `pr-floor-integration` workflow must classify the exact live PR state before reporting a blocker.

Return `merge_now` when all of these are true:

- the PR is open and not already merged;
- it is not a draft;
- provider mergeability is `true`;
- every repository-required check is successful;
- unresolved required review findings are zero;
- the current head SHA equals the expected validated head SHA;
- merge intent exists;
- merge authority exists.

`merge_now` is explicitly **not** a blocker outcome. The required action is to merge immediately using expected-head protection and then verify the canonical default branch advanced.

## True blocker classes

A PR may be reported as blocked only when the focused gate identifies a real unresolved condition, including:

- closed without merge;
- head moved after validation;
- draft state;
- mergeability is unknown or false;
- a repository-required check is not successful;
- unresolved required review findings remain;
- merge intent exists but the current actor lacks merge authority.

Conflict repair, check repair, review resolution, or authority handoff should name the exact blocker rather than using the existence of an open PR as the blocker.

## Post-merge consumption rule

After provider merge success:

1. Verify the repository default branch advanced to a commit containing the merged head.
2. Record the merge/default-branch commit as integration proof.
3. Route normal `use`, `update`, `pull`, `acquire`, `open`, and `install` intents to `main` or the registered public artifact.
4. Do not tell normal consumers to fetch, pin, or create a worktree from the merged feature branch.
5. Feature-branch retrieval remains valid only for explicit historical, forensic, or branch-specific debugging intent.

## Regression coverage

`harness/evals/fixtures/pr-merge-gate-cases.v1.json` contains positive and negative cases for:

- green + mergeable + authorized => `merge_now`;
- missing authority;
- failed required checks;
- unresolved review findings;
- merge conflict;
- unknown mergeability;
- expected-head movement;
- draft PRs;
- already-merged PRs;
- post-merge normal-consumer routing to `main`;
- rejection of post-merge feature-branch guidance;
- required verification that the default branch advanced;
- explicit historical branch-debugging exceptions.

Focused proof:

```bash
python -m py_compile scripts/validate_pr_merge_gate.py tests/test_pr_merge_gate.py
python scripts/validate_pr_merge_gate.py --summary
python -m unittest tests.test_pr_merge_gate -v
```

The focused gate also runs in the tracked pre-commit hook, pre-push hook, and operational-harness GitHub Actions workflow.

## Proof ceiling

The contract, fixtures, validator, hooks, and CI prove deterministic classification and handoff semantics on the tested commit. They cannot themselves perform or prove a provider merge. Actual merge success and canonical-default-branch advancement require observed Git/GitHub evidence, as recorded above for PR #181.