# Repository-Native Code Update — Workflow

## Pick up a task
1. Confirm the target surface is declared in `harness/repo-native-update/contracts/repo-native-update.v1.json`.
2. Read `harness/repo-native-update/reports/CURRENT_STATE.md` for Working/Broken/Missing status.
3. Identify the canonical input for the surface (Phase 1: `harness/repo-native-update/inputs/canary-constants.v1.json`).
4. If changing behavior, edit the input or generator — not files under `generated/`.
5. Note proof ceiling: local CLI only; no Actions runtime claim this sprint.

## Generate
```bash
python scripts/run_repo_native_update.py generate --surface canary-constants
```
- Validates input schema and surface ownership before write.
- Writes only declared owned outputs (atomic/fail-closed).
- Emits receipt to `Outputs/repo-native-update/receipt.json` (ephemeral).

Review the diff. First run after input or generator change may produce a bounded tracked diff in `harness/repo-native-update/generated/canary_constants.py`.

## Validate
```bash
python scripts/validate_repo_native_update_harness.py --summary
python -m unittest tests.test_repo_native_update -v
python scripts/run_repo_native_update.py generate --surface canary-constants --check
git diff --check
```

`--check` must exit zero with no tracked diff when inputs and generator are unchanged.

## Failure handling
| Failure | Action |
|---------|--------|
| Malformed input JSON | Fix input; do not partial-write output |
| Undeclared output path | Reject run; amend contract before expanding scope |
| Path traversal / symlink escape | Fail closed; inspect runner path normalization |
| Partial write / interrupted generation | Restore from last good generated file or regenerate |
| `--check` diff after clean generate | Fix ordering/normalization in generator; verify `ordered_keys` |
| Collision with human/agent edit on generated file | Reconcile at canonical input; regenerate |
| Missing runner/validator/tests | Static surfaces only — coordinator or follow-on worker implements scripts |

## Actions-exhausted local proof path
GitHub Actions minutes are exhausted. Phase 1 proof is entirely local:
1. Run unit tests.
2. Run harness validator `--summary`.
3. Run `generate` then `generate --check` for zero-diff idempotency.
4. Commit generated output with input/generator changes in the same change set when appropriate.

Do **not** add `.github/workflows` for this harness in Phase 1. Any future provider trigger (Phase 3) must delegate to `scripts/run_repo_native_update.py` without duplicating generation logic.

## Handoff
Record in receipt or operator notes:
- Surface id and input path/hash
- Generator id and version
- Owned outputs written
- Validation and `--check` results
- Proof ceiling (local deterministic only)
- Exact next command or blocker

For Phase 1 completion, explicitly state whether `canary-constants` first-run diff and repeat zero-diff proof were observed locally.
