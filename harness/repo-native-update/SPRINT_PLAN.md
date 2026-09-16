# P104 Repository-Native Code Update Harness — Sprint Plan

## Mission
Build a bounded, repository-owned code generation seam that deterministically refreshes declared generated surfaces from canonical structured inputs. The mechanism coexists with human and agent developers without becoming unbounded self-modification or a competing codegen authority.

## Owned scope (this sprint)
- **Canary surface:** `canary-constants` — smallest real generator path from pinned JSON input to one committed Python module under `harness/repo-native-update/generated/`.
- **Local CLI trigger:** `python scripts/run_repo_native_update.py generate --surface canary-constants` (and `--check`). No new GitHub Actions workflows — Actions minutes are exhausted; local proof is the sprint ceiling.
- **Receipts:** ephemeral generation receipts under `Outputs/repo-native-update/receipt.json` with input identity, generator identity, outputs, validation result, and proof ceiling.
- **Path guards:** reject writes outside declared owned outputs; forbid `.github/`, `AGENTS.md`, `Candidates/`, `Active/`, and unscoped `Outputs/` (receipts only).
- **Idempotency:** same pinned inputs plus pinned generator version must produce byte-identical output; `--check` must pass immediately after `generate`.

## Forbidden scope
- `AGENTS.md` — governance contract is separately owned.
- `.github/workflows` — do not add Actions workflows in this sprint.
- Secrets or private evidence in generated or committed surfaces.
- Hand-editing generated output — repair canonical input or generator, then regenerate.
- A second competing codegen system — reuse or extend this harness entrypoint.
- Unbounded self-modification — only declared surfaces in the contract may be written.

## Phase map

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Static harness surfaces + `canary-constants` generator seam | **IMPLEMENTED in this sprint** (surfaces); coordinator wires root manifest/validators |
| **Phase 2** | Broaden owned surfaces beyond canary | **DEFERRED** — requires contract amendment and new inputs per surface |
| **Phase 3** | Optional provider delegate (schedule/PR bot) | **DEFERRED** — any provider workflow must delegate to the same CLI; no duplicated generator logic |

## Proof gates (local only)
1. `python -m unittest tests.test_repo_native_update -v`
2. `python scripts/validate_repo_native_update_harness.py --summary`
3. `python scripts/validate_harness.py --report Outputs/harness-completeness-report.json` (when root wiring lands)
4. First run: `python scripts/run_repo_native_update.py generate --surface canary-constants` produces expected bounded diff.
5. Repeat run: `python scripts/run_repo_native_update.py generate --surface canary-constants --check` exits zero with no tracked diff.

## Proof ceiling
Local deterministic generation from pinned inputs through the canonical CLI. No claim of GitHub Actions runtime proof, provider bot execution, or production deployment in this sprint.

## Deliverables split
| Owner | Artifact |
|-------|----------|
| **This sprint (static surfaces)** | `SPRINT_PLAN.md`, `manifest.v1.json`, `CODEBASE_MAP.md`, `WORKFLOW.md`, contract, inputs, `artifacts.v1.json`, `reports/CURRENT_STATE.md`, `generated/README.md` |
| **Coordinator / follow-on** | `scripts/run_repo_native_update.py`, `scripts/validate_repo_native_update_harness.py`, `tests/test_repo_native_update.py`, root `harness/manifest.v1.json` wiring |

## Stop condition
Phase 1 is complete when the canary surface is reproducible locally: first-run diff is reviewable, repeat `--check` is zero-diff, path guards reject undeclared output, and focused tests plus harness validation pass. Do not broaden surfaces or add provider triggers until Phase 1 proof is green.
