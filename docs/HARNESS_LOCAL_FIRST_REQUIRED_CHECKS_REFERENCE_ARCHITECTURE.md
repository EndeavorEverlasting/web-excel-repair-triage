# Harness Local-First Required Checks — Reference Architecture

Status: executable phase map; implementation owner is the root harness validator registry.

Fresh evidence floor: `main@017f78369f22e13a54f5992c683c30b1b6013a9f` (2026-09-15 research pass).

## Capability slice

Make the repository-owned validator profile the executable source of truth for harness required checks. Operators and hooks must be able to run the same named profile without GitHub Actions. GitHub Actions may consume that runner, add provider-specific checkout/artifact transport, and publish evidence, but workflow YAML must not become the only definition of the checks.

This is not a request to replace the existing validator registry, introduce a task-runner dependency, or emulate GitHub Actions locally.

## Current repository floor

Already solved internally:

- `harness/validators.v1.json` is the declared validator authority and already records validator IDs, commands, blocking behavior, outputs, proof ceilings, named profiles, and hook bindings.
- `harness/test-floor.v1.json` already selects a named validator profile (`pre_push`).
- `scripts/run_deterministic_test_floor.py` already resolves that profile, executes its registered commands locally, fails closed, and emits structured evidence for the deterministic floor.
- `.github/workflows/deterministic-test-floor.yml` already demonstrates the desired ownership direction: Actions performs provider setup/canaries/artifact upload while invoking the repository-owned deterministic runner for the actual clean floor.
- Hooks are explicitly optional per-worktree local gates.

Gap observed on the fresh floor:

- no general CLI executes an arbitrary profile from `harness/validators.v1.json`;
- `.githooks/pre-push` duplicates every command in the registered `pre_push` tail instead of delegating to the registry;
- `.github/workflows/harness-contract.yml` separately spells out overlapping harness checks and report transport;
- `tests/test_harness_contract.py` currently protects the duplicated pre-push command strings, so migration must change the contract deliberately rather than silently deleting checks.

## External reference set

Evidence date: 2026-09-15. No external source code is copied by this work.

| Reference | Evidence identity | License | Observed implementation mechanism | Disposition |
| --- | --- | --- | --- | --- |
| `pre-commit/pre-commit` | `main@a9bba55a3f74068b53f4bd4d831d7e05e34eae6c` | MIT | Repository config owns hook definitions; local execution and CI invoke the same configuration. Local hooks can delegate to repository scripts. | ADAPT |
| `tox-dev/tox` | `main@a5a7ce622566ba4f018fb5d243483baca91a499a` | MIT | `tox.toml` owns named environments/tasks (`fast`, `fix`, `type`, release, Python matrices); Actions installs tox and invokes those environments instead of redefining the test commands. | ADAPT |
| `kubernetes/kubernetes` | `master@c028ba348dbaea5e8b0df94b2581e70d687a77c8` | Apache-2.0 | `hack/verify-all.sh` explicitly contains no real verification logic and redirects to the canonical `make verify` owner. Compatibility entrypoints stay thin. | ADOPT mechanism |
| `rust-lang/rust-analyzer` | `master@fa88768e772857f332bc8383e3a1c5a4212f9a6e` | Apache-2.0 repository metadata | Repo-owned `xtask` provides typed local developer/build tasks; CI and developer guidance point back to the same local commands, with actionable regeneration failures. | ADAPT |
| `nektos/act` | `master@4f411281417e88660bea1c1a1749aa71ae0bd60f` | MIT | Reads `.github/workflows` and emulates Actions locally via Docker. This deliberately makes Actions YAML the task graph. | REJECT as canonical owner |

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
2. Preserve validator metadata (`blocking`, `output`, `proof_ceiling`) in the execution receipt.
3. Keep provider setup, negative canaries, protected/private-input behavior, and CI artifact upload outside the portable profile when they depend on provider/runtime context.
4. Keep pre-commit staged-tree semantics separate from working-tree profile execution.

### REJECT

1. **Actions-as-source-of-truth / local emulation (`act`)** — conflicts with Actions-optional ownership and introduces Docker/provider emulation as a prerequisite for local harness checks.
2. **Wholesale framework adoption** — duplicates an existing registry, adds dependencies, and weakens local proof metadata.
3. **Immediate full hook/workflow replacement** — unsafe until every existing out-of-profile check and CI artifact behavior is dispositioned.

## Solved baseline vs prioritized gap

| Capability | State | Evidence / disposition |
| --- | --- | --- |
| Versioned validator definitions | ALREADY_SOLVED_INTERNALLY | `harness/validators.v1.json` |
| Named profiles | ALREADY_SOLVED_INTERNALLY | `harness`, `pre_commit`, `pre_push`, `target-repository`, `artifact-engine` |
| Local profile resolution/execution inside deterministic floor | ALREADY_SOLVED_INTERNALLY | `scripts/run_deterministic_test_floor.py` |
| Structured deterministic-floor receipt | ALREADY_SOLVED_INTERNALLY | `Outputs/deterministic-test-floor-report.json` contract |
| Generic `run <profile>` CLI | AVAILABLE_TO_EMULATE_EXTERNALLY | tox/xtask/pre-commit mechanism; missing generic local entrypoint here |
| Thin hook delegation | AVAILABLE_TO_EMULATE_EXTERNALLY | Kubernetes redirect/pre-commit pattern; current pre-push duplicates commands |
| Thin Actions delegation | AVAILABLE_TO_EMULATE_EXTERNALLY | tox GitHub workflow pattern; current harness workflow duplicates commands and provider transport |
| Proof-ceiling-aware profile receipt | PROJECT_SPECIFIC_GAP | external references do not carry this repo's evidence semantics |
| Staged-tree pre-commit parity | PROJECT_SPECIFIC_GAP | must preserve repository-specific staged checkout/index policy |
| CI canary/artifact parity during migration | PROJECT_SPECIFIC_GAP | provider-specific evidence transport must survive thin-wrapper conversion |

## Selected development target

Owner: root harness validator control plane (`harness/validators.v1.json` plus a repository-owned runner under `scripts/`).

Phase 1 — **implement now**:

- add a dependency-free `scripts/run_validator_profile.py`;
- resolve profiles exclusively from `harness/validators.v1.json`;
- preserve declared ordering, blocking behavior, outputs, and proof ceilings;
- rewrite `python`/`python3`/`py` entrypoints to the current interpreter as the deterministic floor already does;
- use argument-vector execution rather than a shell;
- optionally emit a bounded structured receipt to `Outputs/` or an explicit external/temp path;
- add focused tests for ordering, fail-closed contract errors, blocking failure, non-blocking continuation, command parsing, and report-path safety.

Phase 2 — **successor**:

- convert only the duplicated registered tail of `.githooks/pre-push` to `run_validator_profile.py --profile pre_push`;
- preserve repository-work-ledger, cross-device, freshness, merge-gate, release-identity, order-navigation, artifact-handoff, and artifact-derivation checks until each is deliberately registered or explicitly kept outside the profile;
- replace command-string duplication assertions with profile-delegation/parity assertions.

Phase 3 — **successor**:

- make `.github/workflows/harness-contract.yml` a thin consumer of the harness profile while retaining provider-only setup, PowerShell syntax proof, canaries, report uploads, and exact-candidate/patch evidence that cannot be expressed as portable validator commands;
- require profile identity and profile receipt in CI evidence.

Phase 4 — **optional convergence**:

- decide whether the out-of-profile pre-push checks belong in the root validator registry or are intentionally separate coordination/provider gates;
- only then consider making one required-check profile the complete pre-push/harness contract.

## Non-goals

- no Actions emulator;
- no tox/pre-commit/Make/Task dependency;
- no change to protected/private input policy;
- no weakening or deletion of existing checks;
- no claim that a local profile pass proves provider integration, browser/runtime behavior, deployment, or production acceptance.

## Validation and invalidation criteria

Phase 1 is proven when focused unit tests pass, the real registry can resolve at least one existing profile without shell interpretation, a generated receipt preserves validator identity/order/blocking/proof ceilings, and patch hygiene is clean.

The choice is invalidated if current repository truth reveals an existing generic profile runner with equivalent behavior, if registered commands require shell semantics that cannot be represented safely as argv, or if the validator registry is no longer the authoritative owner.

## Proof ceiling

Repository-local execution can prove deterministic command selection/execution and receipt semantics for the checked-out source and available local dependencies. It cannot prove GitHub branch protection, provider check attribution, CI artifact retention, unavailable private inputs, platform-specific commands absent on the host, browser/device behavior, deployment, or production acceptance.
