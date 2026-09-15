# Repository-Native Code Update Harness — Codebase Map

## Purpose
This overlay owns the **source → generator → generated surface** boundary for bounded repository-native code updates (P104). Canonical JSON inputs and one CLI runner produce declared outputs; humans and agents repair inputs or the generator, not hand-edited generated files.

## Key surfaces
| Surface | Role |
|---------|------|
| `harness/repo-native-update/contracts/repo-native-update.v1.json` | Generator contract: surfaces, owned/forbidden paths, fail-closed rules, idempotency |
| `harness/repo-native-update/inputs/canary-constants.v1.json` | Phase 1 canary canonical input |
| `harness/repo-native-update/generated/canary_constants.py` | Phase 1 committed generated output (created by runner) |
| `scripts/run_repo_native_update.py` | Authoritative generator CLI (`generate`, `--check`, `--surface`) |
| `scripts/validate_repo_native_update_harness.py` | Static harness completeness and contract alignment |
| `tests/test_repo_native_update.py` | Focused unit/contract tests for generation guards |
| `harness/repo-native-update/artifacts.v1.json` | Machine-readable artifact registry |
| `Outputs/repo-native-update/receipt.json` | Ephemeral generation receipt (gitignored runtime proof) |

## Entry points
1. Read `harness/CONTEXT.md` and this map before changing generation scope.
2. Inspect `harness/repo-native-update/manifest.v1.json` for commands and component paths.
3. Edit canonical inputs under `harness/repo-native-update/inputs/` — never patch generated output directly.
4. Run generation locally: `python scripts/run_repo_native_update.py generate --surface canary-constants`.
5. Prove idempotency: `python scripts/run_repo_native_update.py generate --surface canary-constants --check`.

## Build / test commands (local only)
```bash
# Harness static validation
python scripts/validate_repo_native_update_harness.py --summary

# Focused tests (when present)
python -m unittest tests.test_repo_native_update -v

# Generate canary surface
python scripts/run_repo_native_update.py generate --surface canary-constants

# Zero-diff repeat proof
python scripts/run_repo_native_update.py generate --surface canary-constants --check

# Root harness completeness (after coordinator wiring)
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json

# Whitespace / conflict marker hygiene
git diff --check
```

No GitHub Actions workflow is required or planned for Phase 1 — Actions minutes are exhausted; local CLI proof is the sprint ceiling.

## Traps
- **Hand-editing `generated/`** — violates one-writer policy; regenerate from input.
- **Undeclared output paths** — runner must fail closed; do not write `.github/`, `AGENTS.md`, or protected prefixes.
- **Competing generators** — do not add a second script that writes the same owned path.
- **Timestamp or locale leakage** — breaks idempotency and `--check`; normalize in the runner.
- **Treating receipt as source of truth** — receipts are ephemeral proof under `Outputs/`; canonical truth is input + committed generated output.
- **Provider workflow without CLI delegation** — Phase 3 workflows must shell out to the same CLI, not duplicate logic.
