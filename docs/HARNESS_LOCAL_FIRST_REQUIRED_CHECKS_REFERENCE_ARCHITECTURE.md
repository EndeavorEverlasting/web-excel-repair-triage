# Harness Local-First Required Checks — Reference Architecture and Program Design

Status: Phases 1–3 are integrated. Phase 4 is the next bounded build seam; it must preserve staged-index isolation while moving the snapshot-safe inner pre-commit checks behind the repository-owned profile executor.

Fresh integrated floor: `main@dc9099f8e9442567439d3cb2d85808d981cb0f67` (2026-09-16). Phase 3 merged through PR #507. The exact validated Phase 3 head was `3ea443fde432d5453f486ec6727aeb6cf369b635`; the merge commit has that tested head as a parent and the same tree `746b9c4a0938b963e2d693751a9bfb2182060b57`.

## User outcomes and invariants

Primary user outcomes:

1. A developer can run a named required-check profile locally without GitHub Actions and receive a deterministic pass/fail decision plus bounded evidence.
2. Git hooks and CI consume repository-owned profiles rather than becoming second semantic owners of portable command lists.
3. A failing blocking validator stops the profile, identifies the failing validator, propagates a nonzero exit, and preserves bounded diagnostic evidence.
4. Provider-only proof such as exact PR diff checks, PowerShell syntax checks, checkout identity, and artifact upload remains owned by the provider adapter; a local profile pass is never promoted into provider proof.
5. Staged pre-commit validation validates the staged index snapshot rather than unstaged working-tree content.

Program invariants:

- `harness/validators.v1.json` is the semantic authority for ValidatorSpecs and portable ProfileSpecs.
- `scripts/run_validator_profile.py` is the generic local execution seam; Actions is optional.
- registered commands execute as argument vectors without a shell;
- Python commands use the active interpreter;
- blocking failures fail fast; nonblocking failures may only produce `PASS_WITH_WARNINGS`;
- repository-local receipts live under `Outputs/`; adapters may use explicit external/temp receipt paths;
- proof state is versioned by registry/profile/validator fingerprint rather than repository HEAD alone;
- provider artifacts and diagnostics are evidence, not durable product state;
- working-tree, staged-index, materialized-snapshot, and provider-checkout state have separate owners.

## Governance vs harness vs program vs implementation

- **Governance**: `AGENTS.md`, workflow doctrine, integration/freshness rules, and evidence-state language define how work is performed.
- **Harness**: registries, validators, hooks, workflows, artifacts, reports, tests, and CI provide control/evidence infrastructure.
- **Program design**: the required-check runtime owns profile resolution, execution policy, state transitions, adapter boundaries, and failure propagation.
- **Implementation**: consumers are converged onto those seams in bounded phases; no harness document substitutes for runtime ownership.

## External reference baseline

Evidence date: 2026-09-15. No external source code was copied.

| Reference | Evidence identity | License | Relevant mechanism | Disposition |
| --- | --- | --- | --- | --- |
| `pre-commit/pre-commit` | `main@a9bba55a3f74068b53f4bd4d831d7e05e34eae6c` | MIT | Repository config owns hook definitions; local and CI consumers share it. | ADAPT |
| `tox-dev/tox` | `main@a5a7ce622566ba4f018fb5d243483baca91a499a` | MIT | Named repo-owned task environments; CI invokes rather than restates them. | ADAPT |
| `kubernetes/kubernetes` | `master@c028ba348dbaea5e8b0df94b2581e70d687a77c8` | Apache-2.0 | Thin compatibility entrypoint redirects to canonical local verification. | ADOPT mechanism |
| `rust-lang/rust-analyzer` | `master@fa88768e772857f332bc8383e3a1c5a4212f9a6e` | Apache-2.0 metadata | Repo-owned typed task entrypoint reused by developers and CI. | ADAPT |
| `nektos/act` | `master@4f411281417e88660bea1c1a1749aa71ae0bd60f` | MIT | Actions YAML becomes the task graph and is emulated locally. | REJECT as owner |

Selected pattern: **registry + deep profile executor + thin context adapters**. A new task framework or Actions emulator would duplicate existing ownership and add dependencies without proven need.

## Domain vocabulary

- **ValidatorSpec** — one registered check: identity, class, command, blocking policy, declared output, proof ceiling.
- **ProfileSpec** — ordered ValidatorSpec identities defining a portable required-check contract.
- **ProfileRun** — one execution of a ProfileSpec against one execution context.
- **ProfileReceipt** — structured result containing profile identity, fingerprint, observed steps, status, failure identity, bounded output, and timing.
- **ExecutionContext** — working tree, materialized staged snapshot, or provider checkout.
- **ConsumerAdapter** — CLI, hook, or Actions surface selecting an execution context/profile and propagating the result.
- **ProviderEvidence** — provider-only exact-candidate, syntax, or artifact-transport proof.
- **IndexGate** — check whose truth depends on Git index metadata.
- **SnapshotGate** — check that can execute against the materialized staged filesystem without owning Git index metadata.

## Program module and interface map

### Validator registry — durable semantic state owner

Path: `harness/validators.v1.json`.

Owns validator definitions, portable profile order, blocking policy, declared outputs/proof ceilings, and hook/profile bindings. It does not own subprocess execution, staged materialization, provider setup, or artifact upload.

### Profile contract compiler — domain seam

Current functions in `scripts/run_validator_profile.py`:

- `read_registry(path)` -> validated payload + registry digest;
- `resolve_profile(payload, profile_name)` -> ordered ValidatorSpecs;
- `command_argv(command)` -> executable argv;
- `profile_fingerprint(...)` -> proof-relevance identities/revisions.

Contract errors are classified as `ProfileContractError` before validator execution.

### Profile orchestrator — application owner

Interface: `execute_profile(profile_name, registry_path, report_path) -> (exit_code, report)`.

It hides profile compilation, step ordering, fail-fast/warning policy, Git metadata observation, receipt assembly, and receipt persistence. Consumers must not learn portable validator commands.

### Process adapter — external side-effect boundary

`run_command(validator)` owns subprocess invocation, repository working directory, bounded stdout/stderr capture, return code, and duration. It returns observed step data to the orchestrator; it does not own profile-level state.

### Evidence persistence

Receipt persistence remains inside the orchestrator because no second persistence implementation has been demonstrated. Provider adapters may transport receipts but do not redefine them.

### Consumer adapters

- CLI: argument parsing and exit propagation in `scripts/run_validator_profile.py`.
- Pre-push: `.githooks/pre-push`; separate safety/coordination gates plus one `pre_push` profile invocation.
- Actions: `.github/workflows/harness-contract.yml`; exact checkout/provider proof + one `harness` profile invocation + artifact transport.
- Pre-commit: `.githooks/pre-commit`; owns Git-index gates and snapshot materialization. Its snapshot-safe inner sequence is the Phase 4 convergence target.

## Dependency direction

`CLI / hook / Actions adapter`
-> `execute_profile`
-> `read_registry + resolve_profile + profile_fingerprint`
-> `run_command`
-> `subprocess / filesystem / optional Git observation`
-> `step result`
-> `profile state transition`
-> `ProfileReceipt`
-> `adapter exit / upload / Git allow-block decision`

Dependencies point inward toward the profile program. Registry and executor never depend on workflow/provider logic.

## State and ownership

| State | Canonical owner | Mutation boundary | Invalidation / lifecycle |
| --- | --- | --- | --- |
| Validator definitions/profile order | `harness/validators.v1.json` | tracked review/merge | semantic registry change invalidates affected proof |
| Working tree | Git checkout/operator | ordinary repository mutation | current local state |
| Staged index | Git | index mutation | `git add`, reset, commit, index change |
| Materialized staged snapshot | pre-commit adapter | temporary directory | destroyed after run |
| Profile execution state | `execute_profile` | in-memory | terminates PASS/WARN/FAIL |
| Profile receipt | profile executor | temp/`Outputs/` | per-run evidence |
| Provider artifact | Actions adapter | provider artifact store | provider retention policy |
| Provider candidate identity/diff | Actions/provider checkout | read-only | invalidated by PR head/base movement |

No database, queue, daemon, service, container runtime, PaaS, or Kubernetes tier is needed. This subsystem is repository-local CLI/hook code plus ephemeral CI consumers.

## Profile-run state machine

`REQUESTED -> CONTRACT_RESOLVED -> RUNNING(step n)` then:

- `PASS`: all required steps pass;
- `PASS_WITH_WARNINGS`: only explicitly nonblocking steps fail;
- `FAIL_VALIDATOR`: a blocking validator fails and successors are not started;
- `FAIL_CONTRACT`: registry/profile/report-path contract fails before execution.

Exit mapping: `0` = PASS/WARN, `1` = blocking validator failure, `2` = contract failure.

Provider adapters may fail after local PASS (artifact upload, exact candidate diff, provider syntax). That does not rewrite the local receipt.

## Representative call stacks

### Local profile execution

`developer command -> CLI -> execute_profile -> registry/profile resolution -> validator subprocesses -> profile policy -> receipt -> exit/terminal feedback`

Failure: malformed/unknown profile -> contract error -> exit 2 without validator execution. Blocking validator -> nonzero step -> failed-validator receipt -> exit 1 -> no successor validator.

### Pre-push

`git push -> pre-push adapter -> preserved safety/coordination checks -> run pre_push profile -> receipt -> hook exit -> Git allow/block`

Phase 2 proved and integrated this seam.

### Actions provider wrapper

`PR/push event -> exact-head checkout -> provider-only setup/checks -> call-stack prototype -> run harness profile -> upload receipt/reports -> exact candidate diff -> job conclusion`

Phase 3 proved the wrapper can stay thin without losing provider-only evidence.

### Staged pre-commit

`git commit -> index path gate -> materialize index snapshot -> snapshot-safe profile -> leave snapshot -> cached-diff gate -> Git allow/block`

Git/pre-commit owns the staged index and materialization; the generic executor owns only the snapshot-safe profile. This is the selected Phase 4 seam.

## Executable prototype and observed proof

Prototype owner: `tests/test_required_check_program_call_stacks.py`.

Exact tested head: `3ea443fde432d5453f486ec6727aeb6cf369b635`.

Observed in Operational harness run `35103556125`:

- Actions delegation prototype: PASS;
- real staged-index materialization + real snapshot executor success path: PASS;
- snapshot manifest corruption failure path: PASS, failed at `harness-completeness`, one observed step of two, exit 1;
- full canonical `harness` profile: PASS, 29/29 steps observed;
- exact candidate `git diff --check origin/main...HEAD`: PASS;
- staged artifact contract: PASS;
- expected provider report uploads: PASS.

Selected receipt artifacts include:

- `harness-validator-profile` artifact `10449301845`, digest `sha256:f1d9ab6b49e55622f194e552dfb60bc64d657edf5ad8d20b11cbfe74dcc62a78`;
- `harness-completeness-report` artifact `10449455989`, digest `sha256:6f60a72025683ad53d5351becdd83789e6681103cec61467da9d2b64fe8b15fd`.

All six exact-head PR workflows completed successfully: Operational harness, Deterministic repository floor, Validator profile runner, App harness, Artifact engine, and Prompt Kit Pages.

## Second-pass architecture critique

Prototype evidence selected candidate S3: keep index phases in the pre-commit adapter and execute snapshot-safe checks through the existing generic runner.

Findings:

- **Interface leakage:** none observed. The runner needed no Git-index or Actions-specific arguments.
- **State ownership:** singular. Git/pre-commit owns index/snapshot; registry owns portable profile state; executor owns ProfileRun; Actions owns provider transport/proof.
- **Failure ownership:** sound. Invalid snapshot state failed at the first blocking validator and stopped the next validator with a precise receipt.
- **Mock pressure:** none at the evaluated seam. Git index materialization, runner, validators, and subprocesses were real. Only the temporary prototype profile grouping was synthetic.
- **Adapter value:** justified. Actions preserves provider proof; the staged adapter preserves index isolation.
- **Core depth:** sufficient. Splitting `run_validator_profile.py` now would add ceremony without another implementation owner.

Decision: **keep the core executor unchanged**.

## Solved baseline and remaining gap

| Capability | Status / owner |
| --- | --- |
| Versioned validator definitions | INTEGRATED — `harness/validators.v1.json` |
| Generic local profile execution | INTEGRATED — `scripts/run_validator_profile.py` |
| Thin optional Actions consumer | INTEGRATED — validator-profile workflow |
| Thin pre-push profile consumer | INTEGRATED — `.githooks/pre-push` |
| Canonical anti-duplication for pre-push | INTEGRATED — `validate_harness.py` + tests |
| Operational Actions harness delegation | INTEGRATED — PR #507 / `main@dc9099f8...` |
| Staged snapshot seam | PROTOTYPE PROVEN — production convergence remains Phase 4 |
| Browser/device/deployment runtime | OUT OF SCOPE for this subsystem |

## Development phase map

### Phase 1 — INTEGRATED

PR #504 introduced the generic local-first profile runner and thin optional Actions consumer. Integration commit: `5c39382c693cac4eb61df375e0128f63ff9d5698`.

### Phase 2 — INTEGRATED

PR #505 converged the registered pre-push tail onto the profile runner and moved anti-duplication ownership into the canonical harness validator. Integration commit: `e2c077ebaa438cdde0d4942f97bfee8d5bf2a6a2`.

### Phase 3 — INTEGRATED

PR #507 integrated the program design, provider-wrapper delegation, success/failure call-stack prototypes, and preserved provider proof. Exact tested head `3ea443fde432d5453f486ec6727aeb6cf369b635`; mainline merge `dc9099f8e9442567439d3cb2d85808d981cb0f67`.

### Phase 4 — NEXT BOUNDED BUILD: staged pre-commit convergence

Current `.githooks/pre-commit` has two **index-aware adapter gates** that must remain outside the snapshot profile:

1. before materialization: `python scripts/validate_staged_artifacts.py`;
2. after snapshot validation: `git diff --cached --check`.

The hook materializes the index with `git checkout-index --all --prefix="$staged_tree/"`. Inside that snapshot it currently executes **14 snapshot-safe commands**:

1. `python scripts/validate_repository_work_ledger.py --summary`
2. `python -m unittest tests.test_repository_work_ledger -v`
3. `python scripts/validate_prompt_kit_cross_device_access.py --summary`
4. `python -m unittest tests.test_prompt_kit_cross_device_access -v`
5. `python scripts/validate_prompt_kit_freshness_guidance.py --summary`
6. `python -m unittest tests.test_prompt_kit_freshness_guidance -v`
7. `python scripts/validate_pr_merge_gate.py --summary`
8. `python -m unittest tests.test_pr_merge_gate -v`
9. `python scripts/validate_artifact_handoff_harness.py --summary`
10. `python -m unittest tests.test_artifact_handoff_harness -v`
11. `python scripts/validate_artifact_derivation_harness.py --summary`
12. `python -m unittest tests.test_artifact_derivation_harness -v`
13. `python scripts/validate_harness.py --report "$HARNESS_REPORT"`
14. `python -m unittest tests.test_harness_contract -v`

Commands 13–14 already map to canonical ValidatorSpecs `harness-completeness` and `harness-contract-tests`. Commands 1–12 are intentionally preserved by current hooks but are not yet ValidatorSpecs in `harness/validators.v1.json`; they are the exact registry gap to close before replacing the inner sequence.

#### Phase 4 owned surfaces

- `harness/validators.v1.json`: register the 12 missing snapshot-safe audit/test commands with explicit class, output, blocking policy, and proof ceiling; define one named snapshot-safe profile containing those 12 plus `harness-completeness` and `harness-contract-tests` in existing hook order.
- `.githooks/pre-commit`: keep the outer index path gate, `git checkout-index`, temp cleanup, and final cached-diff gate; replace only the 14-command inner block with one profile-runner call from inside the staged snapshot.
- `scripts/validate_harness.py`: update required validator/profile ownership and enforce the pre-commit delegation boundary; reject reintroduction of profile-owned command copies while requiring the two index-aware adapter gates.
- `tests/test_harness_contract.py`: prove registry/hook ownership, order, delegation, and anti-duplication.
- `tests/test_staged_artifact_hygiene.py`: preserve the ordering invariant that the path-only index gate runs before materialization and cached-diff proof remains after snapshot validation.
- `tests/test_required_check_program_call_stacks.py`: replace the temporary prototype grouping with the durable snapshot profile and retain success + corrupted-snapshot fail-fast journeys.

#### Phase 4 acceptance

- every current inner pre-commit command is dispositioned exactly once; none is silently dropped;
- the durable snapshot profile executes all 14 snapshot-safe checks in existing order against a real materialized Git index;
- the two index-aware gates remain adapter-owned and are not moved into the generic executor;
- corrupted staged snapshot fails at the responsible blocking validator and stops successors;
- working-tree-only unstaged mutations cannot change the staged-snapshot decision;
- canonical harness validation rejects copied profile commands in `.githooks/pre-commit`;
- focused staged-hook tests, the relevant named profile, Operational harness, and deterministic repository floor pass on exact head;
- validated work is integrated to refreshed default branch before closeout.

#### Phase 4 naming decision

The semantic boundary should be named for the execution context, not the Git lifecycle event. Preferred profile ID: `pre_commit_snapshot`.

Before mutation, search current consumers of the existing `pre_commit` profile. Current evidence shows the root validator and root harness tests depend on that identity, so the build lane must migrate or preserve compatibility deliberately rather than silently renaming it. Do not teach the generic executor phased/index semantics merely to preserve the old name.

## Non-goals

- no Actions emulator;
- no new task framework dependency;
- no daemon/API/database/container/Kubernetes service;
- no deletion of provider-only evidence to shorten YAML;
- no Git-index phase logic inside the generic profile executor unless future evidence proves a cross-consumer requirement;
- no claim that repository/CI proof equals browser, device, deployment, protected-runtime, or production proof.

## Proof ceiling and invalidation

Current repository/CI proof establishes profile selection/execution, Actions delegation, receipt semantics, staged-snapshot seam viability, and failure propagation for the tested tree. It does not prove branch-protection configuration, unavailable private inputs, browser/device behavior, deployment, or production acceptance.

The architecture must be revisited if:

- the validator registry ceases to be authoritative;
- required commands need unsafe/unrepresentable shell semantics;
- staged snapshot execution requires the generic executor to own Git-index state;
- provider-only evidence cannot survive thin-wrapper ownership;
- a competing canonical generic executor is integrated;
- Phase 4 reveals a current inner check cannot actually execute as a snapshot-safe ValidatorSpec without caller-specific knowledge leaking into the core.
