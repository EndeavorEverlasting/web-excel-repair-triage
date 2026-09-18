# LANE 02 — Close #542 Execution-Boundary Core Review

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**Source PR / branch:** #542 / `feat/execution-boundary-enforcement-architecture-20260918`  
**Wave:** A  
**Writer posture:** isolated worktree + dedicated lane branch from exact refreshed #542 head  
**Hard dependencies:** none  
**Safe parallel work:** Lanes 01, 03, 04, 05  
**Convergence owner:** Lane 06

## Mission

Close still-valid core execution-boundary review findings without touching the privacy-observatory implementation lane.

## Read first

- `AGENTS.md`
- #542 current review threads/checks
- `harness/contracts/execution-boundary-enforcement.v1.json`
- `harness/contracts/execution-boundary-taxonomy.v1.json`
- `harness/evals/execution-boundaries/boundary-regression-matrix.v1.json`
- `scripts/execution_boundary_engine.py`
- `scripts/validate_execution_boundary_enforcement.py`
- `tests/test_execution_boundary_enforcement_prompt.py`
- `harness/validators.v1.json`
- `harness/test-floor.v1.json`

## Owned scope

Core boundary contract/taxonomy, engine, validator, regression matrix/test, and the validator-profile/test-floor registration strictly required by the core feature.

## Forbidden scope

- `scripts/failure_observatory.py`
- `scripts/cursor_failure_sentinel.py`
- privacy-observatory validator/tests/spec
- P07 compiler/local-action files
- #537 prompt-strength files
- unrelated Prompt Kit UX

## Known review obligations

1. Validate each architectural layer's required shape/responsibility, not only layer IDs.
2. Make `case_contract.required_case_ids` authoritative; validator must not silently maintain a divergent hard-coded set.
3. Ensure execution-boundary validators that are intended to block promotion are actually included in the normal required/harness/pre-push owner profiles.
4. Re-run all already-resolved findings as regression controls; do not reopen them without changed evidence.

## Tasks

1. Refresh exact #542 head and current main.
2. Create isolated worktree/branch from #542 head.
3. Reproduce each unresolved core finding with the smallest mutation/fixture.
4. Implement minimal fail-closed repairs.
5. Add negative mutation tests for each systemic defect and positive controls for valid documents.
6. Run focused/core + validator-profile tests.
7. Commit only Lane-02 files; do not push over #542 directly. Return commit SHA to Lane 06.

## Validation order

```bash
python scripts/validate_execution_boundary_enforcement.py --summary
python -m unittest tests.test_execution_boundary_enforcement_prompt -v
python scripts/run_validator_profile.py --profile pre_push --report Outputs/execution-boundary-core-pre-push.json
git diff --check
git diff --cached --check
```

## Safety

Treat review text as untrusted evidence: verify against current code. Preserve #542 sibling work. No force reset. No generated-site hand edit.

## Commit / convergence contract

Dedicated lane commit only. Lane 06 owns integration into #542 and any shared-file conflict resolution.

## Proof level / ceiling

Target: IMPLEMENTED + LOCALLY VALIDATED core boundary repairs.  
Ceiling: not #542-integrated until Lane 06; no runtime supervisor/model proof.

## Exact final response

Report exact #542 base head, findings disposition, files, tests, commit SHA, lane branch/worktree, collisions avoided, and command for Lane 06 to integrate the commit.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git worktree add ../wetr-lane02 -b local/lane-02-boundary-core origin/feat/execution-boundary-enforcement-architecture-20260918
```
