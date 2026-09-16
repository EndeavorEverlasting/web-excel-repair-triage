# Harness Local-First Required Checks — Reference Architecture

Status: Phase 1 integrated on `main@5c39382c693cac4eb61df375e0128f63ff9d5698`; Phase 2 implementation active; root harness validator registry remains the canonical owner.

Fresh evidence floor: `main@5c39382c693cac4eb61df375e0128f63ff9d5698` (2026-09-15 local-first continuation).

## Capability slice

Make the repository-owned validator profile the executable source of truth for harness required checks. Operators and hooks must be able to run the same named profile without GitHub Actions. GitHub Actions may consume that runner, add provider-specific checkout/artifact transport, and publish evidence, but workflow YAML must not become the only definition of the checks.

This is not a request to replace the existing validator registry, introduce a task-runner dependency, or emulate GitHub Actions locally.

## Current repository floor

Already solved internally and now integrated:

- `harness/validators.v1.json` is the declared validator authority and records validator IDs, commands, blocking behavior, outputs, proof ceilings, named profiles, and hook bindings.
- `harness/test-floor.v1.json` selects the named `pre_push` validator profile.
- `scripts/run_deterministic_test_floor.py` resolves that profile, executes its registered commands locally, fails closed, and emits structured deterministic-floor evidence.
- `scripts/run_validator_profile.py` now provides the dependency-free generic `run <profile>` seam, preserves registry order/blocking/output/proof-ceiling metadata, emits a proof-relevance fingerprint, and requires no Actions runtime.
- `.github/workflows/validator-profile-runner.yml` is an Actions-optional thin consumer: provider setup and artifact transport wrap the same repository-owned profile runner rather than redefining the profile.
- `.github/workflows/deterministic-test-floor.yml` already demonstrates the same ownership direction for its specialized floor.
- Hooks are explicitly optional per-worktree local gates.

Remaining duplication on the current floor:

- `.githooks/pre-push` historically duplicated every command in the registered `pre_push` tail; Phase 2 removes only that duplicated tail while preserving out-of-profile coordination/safety checks.
- `.github/workflows/harness-contract.yml` still separately spells out overlapping harness checks and report transport.
- staged-tree `pre-commit` semantics remain intentionally separate until a profile runner can be proven against the staged checkout without weakening index isolation.

## External reference set

Evidence date: 2026-09-15. No external source code is copied by this work.

| Reference | Evidence identity | License | Observed implementation mechanism | Disposition |
| --- | --- | --- | --- | --- |
| `pre-commit/pre-commit` | `main@a9bba55a3f74068b53f4bd4d831d7e05e34eae6c` | MIT | Repository config owns hook definitions; local execution and CI invoke the same configuration. Local hooks can delegate to repository scripts. | ADAPT |
| `tox-dev/tox` | `main@a5a7ce622566ba4f018fb5d243483baca91a499a` | MIT | `tox.toml` owns named environments/tasks; Actions installs tox and invokes those environments instead of redefining the test commands. | ADAPT |
| `kubernetes/kubernetes` | `master@c028ba348dbaea5e8b0df94b2581e70d687a77c8` | Apache-2.0 | `hack/verify-all.sh` contains no real verification logic and redirects to the canonical `make verify` owner. Compatibility entrypoints stay thin. | ADOPT mechanism |
| `rust-lang/rust-analyzer` | `master@fa88768e772857f332bc8383e3a1c5a4212f9a6e` | Apache-2.0 repository metadata | Repo-owned `xtask` provides typed local developer/build tasks; CI and developer guidance point back to the same local commands, with actionable regeneration failures. | ADAPT |
| `nektos/act` | `master@4f411281417e88660bea1c1a1749aa71ae0bd60f` | MIT | Reads `.github/workflows` and emulates Actions locally via Docker, deliberately making Actions YAML the task graph. | REJECT as canonical owner |

### Evidence classification

- **OBSERVED_IMPLEMENTED** — pre-commit repository configuration drives hook execution and supports CI invocation; tox repository configuration owns named executable environments while GitHub Actions invokes tox; Kubernetes `verify-all.sh` delegates to `make verify`; rust-analyzer exposes repository-owned `xtask`; act reads Actions workflow YAML and executes it locally.
- **DOCUMENTED_UNVERIFIED** — performance claims, contributor productivity claims, and ecosystem-wide maintenance outcomes were not used to choose the local design.
- **ABSENT in inspected references** — none of the selected references carries this repository's validator-specific `proof_ceiling`, artifact ownership, protected-input, or evidence-state vocabulary. Those remain local contracts.

## Pattern ledger

### ADOPT

1. **One local command is the semantic owner.** Compatibility wrappers and provider workflows delegate rather than restate the task list.
2. **Stable named profiles/tasks.** Humans, hooks, and CI address a profile by identity instead of copying its command sequence.
3. **Fail-fast required checks.** A blocking failure terminates the required profile with a non-zero result.

### ADAPT

1. Preserve `harness/validators.v1.json` rather than adding tox, pre-commit, Make, or another task registry.
2. Preserve validator metadata (`blocking`, `output`, `proof_ceiling`) and proof-relevance inputs in execution receipts.
3. Keep provider setup, negative canaries, protected/private-input behavior, and CI artifact upload outside the portable profile when they depend on provider/runtime context.
4. Keep pre-commit staged-tree semantics separate from working-tree profile execution until staged-tree parity is proven.

### REJECT

1. **Actions-as-source-of-truth / local emulation (`act`)** — conflicts with Actions-optional ownership and introduces Docker/provider emulation as a prerequisite for local harness checks.
2. **Wholesale framework adoption** — duplicates an existing registry, adds dependencies, and weakens local proof metadata.
3. **Whole-hook/workflow replacement without parity proof** — unsafe when out-of-profile safety checks or provider-only artifact behavior would disappear.

## Solved baseline vs prioritized gap

| Capability | State | Evidence / disposition |
| --- | --- | --- |
| Versioned validator definitions | ALREADY_SOLVED_INTERNALLY | `harness/validators.v1.json` |
| Named profiles | ALREADY_SOLVED_INTERNALLY | `harness`, `pre_commit`, `pre_push`, `target-repository`, `artifact-engine` |
| Generic `run <profile>` CLI | ALREADY_SOLVED_INTERNALLY | Phase 1 merged via PR #504; `scripts/run_validator_profile.py` |
| Proof-ceiling-aware profile receipt | ALREADY_SOLVED_INTERNALLY | Phase 1 receipt carries validator metadata and proof-relevance fingerprint |
| Thin optional Actions consumer | ALREADY_SOLVED_INTERNALLY | `.github/workflows/validator-profile-runner.yml` |
| Thin pre-push delegation | AVAILABLE_TO_EMULATE_EXTERNALLY / ACTIVE | Kubernetes redirect + pre-commit delegation pattern; Phase 2 replaces only the duplicated registered tail |
| Thin harness-contract Actions delegation | AVAILABLE_TO_EMULATE_EXTERNALLY | tox-style CI wrapper; provider-specific setup/artifacts still require mapping |
| Staged-tree pre-commit parity | PROJECT_SPECIFIC_GAP | must preserve repository-specific staged checkout/index policy |
| CI canary/artifact parity during harness-workflow migration | PROJECT_SPECIFIC_GAP | provider-specific evidence transport must survive thin-wrapper conversion |

## Development phase map

Owner: root harness validator control plane (`harness/validators.v1.json` plus `scripts/run_validator_profile.py`).

### Phase 1 — INTEGRATED

Integrated via PR #504 at `main@5c39382c693cac4eb61df375e0128f63ff9d5698`.

Delivered:

- dependency-free `scripts/run_validator_profile.py`;
- profile resolution exclusively from `harness/validators.v1.json`;
- declared ordering, blocking behavior, outputs, and proof ceilings preserved;
- Python entrypoints normalized to the active interpreter;
- argument-vector execution without a shell;
- bounded structured receipt to `Outputs/` or explicit external/temp paths;
- registry/profile/validator proof-relevance fingerprint;
- focused fail-closed and execution regression tests;
- thin Actions consumer proving the repository-owned `target-repository` profile and transporting its receipt.

Observed Phase-1 proof at exact head `5a506766dabad73e5bb4963a6a6322bbd485af6f`:

- 10 focused runner tests PASS;
- `target-repository` profile PASS 3/3;
- validator-profile receipt artifact ID `10427380461`, digest `sha256:5d028df68ba537d889be84a8ea5c0273a0c7a020f0d6ba7fb3ebbefbeeffcf8b`;
- App harness, Artifact engine, Prompt Kit Pages, and deterministic repository floor all PASS before merge.

### Phase 2 — ACTIVE

Owned scope:

- convert only the duplicated registered tail of `.githooks/pre-push` to `run_validator_profile.py --profile pre_push`;
- preserve repository-work-ledger, cross-device, freshness, merge-gate, release-identity, order-navigation, artifact-handoff, and artifact-derivation checks verbatim because they are currently outside the profile;
- replace command-string duplication assertions with profile-delegation/parity assertions;
- fail the contract if any registered `pre_push` command is copied back into the hook.

Acceptance:

- harness contract tests prove all 16 out-of-profile commands remain;
- hook contains one `pre_push` profile invocation and a bounded temp receipt path;
- every registry-owned `pre_push` command is absent from hook source;
- executing the `pre_push` profile on the exact candidate remains green;
- deterministic repository floor remains green;
- merge only after refreshed main and review/check state preserve the proof-relevance fingerprint.

### Phase 3 — SUCCESSOR

- make `.github/workflows/harness-contract.yml` a thin consumer of the harness profile while retaining provider-only setup, PowerShell syntax proof, canaries, report uploads, and exact-candidate/patch evidence that cannot be expressed as portable validator commands;
- require profile identity and profile receipt in CI evidence;
- do not delete provider-only workflow logic merely to make YAML shorter.

### Phase 4 — OPTIONAL CONVERGENCE

- decide whether the out-of-profile pre-push checks belong in the root validator registry or are intentionally separate coordination/provider gates;
- only then consider making one required-check profile the complete pre-push/harness contract;
- separately evaluate staged-tree `pre_commit` delegation using its isolated checkout semantics.

## Non-goals

- no Actions emulator;
- no tox/pre-commit/Make/Task dependency;
- no change to protected/private input policy;
- no weakening or deletion of existing checks;
- no claim that a local profile pass proves provider integration, browser/runtime behavior, deployment, or production acceptance.

## Validation and invalidation criteria

Phase 1 is proven by the integrated exact-head evidence above.

Phase 2 is invalidated if fresh registry truth changes the `pre_push` profile so it no longer corresponds to the duplicated tail, if a preserved out-of-profile check becomes profile-owned without the hook/test contract being reconciled, or if delegation changes working-tree semantics.

The overall choice is invalidated if the validator registry ceases to be authoritative, registered commands require shell semantics that cannot be represented safely as argv, or a competing canonical generic profile runner supersedes `scripts/run_validator_profile.py`.

## Proof ceiling

Repository-local execution can prove deterministic profile selection/execution and receipt semantics for the checked-out source and available local dependencies. Hook static/CI proof can prove command preservation and delegation wiring. Neither proves GitHub branch protection, unavailable private inputs, browser/device behavior, deployment, or production acceptance. Phase 3 is still required before the legacy harness-contract workflow itself is thin-wrapper converged.
