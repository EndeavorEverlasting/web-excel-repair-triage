# Repository-Native Update

## Trigger
Use when a declared repo-native generated surface drifted from its pinned JSON input, when canonical generator/contract inputs changed, or when local Actions-free codegen proof is required.

## Required inputs
- Surface id declared in `harness/repo-native-update/contracts/repo-native-update.v1.json`.
- Canonical input JSON for that surface.
- Repository checkout with the generator CLI available.

## Outputs
- Declared owned generated file(s) only.
- Ephemeral receipt under `Outputs/repo-native-update/receipt.json`.
- Focused validator and unittest evidence.

## Procedure
1. Edit the canonical input, contract, or generator — never the generated file.
2. Run `python scripts/run_repo_native_update.py generate --surface <id>`.
3. Prove idempotency with `python scripts/run_repo_native_update.py generate --surface <id> --check`.
4. Run `python scripts/validate_repo_native_update_harness.py --summary` and `python -m unittest tests.test_repo_native_update -v`.
5. Review the diff and receipt; keep normal review/integration gates.

## Guardrails
- Reject path traversal, undeclared outputs, and forbidden prefixes (`.github/`, `AGENTS.md`, `Candidates/`, `Active/`).
- Do not add a new GitHub Actions workflow solely to run this generator while Actions minutes are exhausted.
- Do not auto-commit in a recursive generate-commit loop.
- One writer per owned surface; reconcile at the canonical input boundary.

## Validation
`python scripts/validate_repo_native_update_harness.py --summary`
`python -m unittest tests.test_repo_native_update -v`
`python scripts/run_repo_native_update.py generate --surface canary-constants --check`

## Proof ceiling
Local deterministic generation, static harness completeness, and focused unittest proof only. No Actions/provider bot runtime claim.
