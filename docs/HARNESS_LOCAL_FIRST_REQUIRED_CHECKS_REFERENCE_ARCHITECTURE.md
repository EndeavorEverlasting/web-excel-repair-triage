# Harness Local-First Required Checks — Reference Architecture and Program Design

Status: Phase 1 and Phase 2 integrated; Phase 3 design/prototype active on `feat/harness-actions-profile-delegation-20260915`.

Fresh evidence floor: `main@29bbf707974d43bfbd966855a3cc5b9172988db3` (2026-09-16). Phase 2 integration commit `e2c077ebaa438cdde0d4942f97bfee8d5bf2a6a2` is contained by this floor. The active Phase 3 branch was reconciled non-destructively onto that floor before further design work.

## User outcomes and invariants

Primary user outcomes:

1. A developer can run a named required-check profile locally without GitHub Actions and receive a deterministic pass/fail decision plus bounded evidence.
2. Git hooks and CI consume the same repository-owned profile rather than becoming second semantic owners of the command list.
3. A failing blocking validator stops the profile, identifies the failing validator, propagates a nonzero exit, and preserves enough evidence to diagnose the failure.
4. Provider-only proof such as exact PR diff checks, PowerShell syntax checks, checkout identity, and artifact upload remains owned by the provider adapter; a local profile pass must never be promoted into provider proof.
5. Staged pre-commit validation must continue to validate the staged index snapshot rather than accidentally validating unstaged working-tree content.

Program invariants:

- `harness/validators.v1.json` is the semantic authority for validator definitions and portable profile membership/order.
- `scripts/run_validator_profile.py` is the generic local execution seam; Actions is optional.
- registered commands execute as argument vectors without a shell;
- Python commands use the active interpreter;
- blocking failures fail fast; nonblocking failures may only produce `PASS_WITH_WARNINGS`;
- repository-local profile receipts live under `Outputs/`; explicit external/temp receipt paths are allowed for adapters;
- proof state is versioned by registry/profile/validator fingerprint rather than by repository HEAD alone;
- provider artifacts and diagnostics are evidence, not durable business state;
- staged-index and working-tree state are distinct execution contexts and must not share ownership implicitly.

## Governance vs harness vs program

- **Governance**: `AGENTS.md`, workflow doctrine, integration/freshness rules, and proof-state language define how repository work is performed.
- **Harness**: registries, validators, hooks, workflows, artifact metadata, CI, reports, and tests provide control/evidence infrastructure.
- **Program design**: the required-check runtime described below owns profile resolution, execution policy, adapter boundaries, state transitions, and failure propagation.
- **Implementation**: broad convergence of every hook/workflow onto the program is intentionally deferred until the executable seams are proven.

The harness is therefore an input and execution environment for this program, not a substitute for its runtime architecture.

## External reference baseline

Evidence date: 2026-09-15. No external source code is copied.

| Reference | Evidence identity | License | Mechanism | Disposition |
| --- | --- | --- | --- | --- |
| `pre-commit/pre-commit` | `main@a9bba55a3f74068b53f4bd4d831d7e05e34eae6c` | MIT | Repository config owns hook definitions; local and CI consumers share it. | ADAPT |
| `tox-dev/tox` | `main@a5a7ce622566ba4f018fb5d243483baca91a499a` | MIT | Named repo-owned task environments; CI invokes rather than restates them. | ADAPT |
| `kubernetes/kubernetes` | `master@c028ba348dbaea5e8b0df94b2581e70d687a77c8` | Apache-2.0 | Thin compatibility entrypoint redirects to canonical local verification owner. | ADOPT mechanism |
| `rust-lang/rust-analyzer` | `master@fa88768e772857f332bc8383e3a1c5a4212f9a6e` | Apache-2.0 metadata | Repo-owned typed task entrypoint reused by developers and CI. | ADAPT |
| `nektos/act` | `master@4f411281417e88660bea1c1a1749aa71ae0bd60f` | MIT | Actions YAML is the task graph and is emulated locally. | REJECT as owner |

## Design-space comparison

### Candidate A — shell/YAML orchestration owns commands

Hooks and workflows spell out required commands directly.

- correctness: currently works but ownership is duplicated;
- change leverage: poor; one command change can require several consumers to move together;
- failure ownership: fragmented;
- testability: mostly string/parity assertions;
- disposition: **REJECT** as canonical design.

### Candidate B — registry + deep profile executor + thin adapters

The registry owns semantic profile state. One executor resolves and runs it. CLI, hooks, staged-snapshot orchestration, and Actions are adapters that add only context-specific behavior.

- correctness: one command/profile authority;
- interface: small (`profile`, optional registry, optional report path -> exit/result receipt);
- state locality: strong;
- failure handling: explicit contract failure vs validator failure;
- change leverage: high;
- dependency cost: none beyond stdlib/Git already present;
- disposition: **SELECTED**.

### Candidate C — new task/plugin framework

Introduce tox/pre-commit/Make/Task or a new typed plugin framework as the runtime owner.

- interface could be clean, but duplicates the existing registry;
- adds dependency and migration cost before a demonstrated need;
- would weaken repository-specific proof-ceiling/fingerprint vocabulary unless reimplemented;
- disposition: **REJECT FOR NOW**. Revisit only if command heterogeneity or extension pressure exceeds the present executor.

### Candidate D — Actions-centric local emulation

Use workflow YAML as canonical state and emulate GitHub locally.

- violates Actions-optional requirement;
- makes Docker/provider semantics a local prerequisite;
- confuses portable validation with provider evidence;
- disposition: **REJECT**.

## Domain vocabulary

- **ValidatorSpec** — one registered check: identity, class, command, blocking policy, declared output, proof ceiling.
- **ProfileSpec** — ordered validator identities defining one portable required-check contract.
- **ProfileRun** — one execution of a ProfileSpec against one repository/snapshot state.
- **ProfileReceipt** — structured result for a ProfileRun: profile identity, source/fingerprint, observed steps, exit status, failure identity, bounded stdout/stderr tails.
- **ExecutionContext** — the state against which commands run: working tree, materialized staged snapshot, or provider checkout.
- **ConsumerAdapter** — CLI, pre-push, pre-commit, or Actions surface that selects an execution context/profile and propagates the result.
- **ProviderEvidence** — CI-only evidence such as exact candidate diff, checkout identity, syntax checks, and uploaded artifacts.
- **IndexGate** — check whose truth depends on Git index metadata (`validate_staged_artifacts.py`, `git diff --cached --check`).
- **SnapshotGate** — check that can execute against a materialized staged-tree filesystem without Git index metadata.

## Program module / interface map

### Validator registry — canonical durable state owner

Path: `harness/validators.v1.json`

Owns validator definitions, portable profile ordering, blocking policy, declared outputs/proof ceilings, and hook/profile bindings. It does not own provider setup, staged materialization, artifact upload, retries, or process execution.

### Profile contract compiler — pure-ish domain seam

Current functions in `scripts/run_validator_profile.py`:

- `read_registry(path)` -> validated payload + registry digest;
- `resolve_profile(payload, profile_name)` -> ordered ValidatorSpecs;
- `command_argv(command)` -> executable argv;
- `profile_fingerprint(...)` -> canonical proof-relevance identities/revisions.

Failure contract: raises `ProfileContractError`; no validator process is started.

### Profile orchestrator — application owner

Current interface: `execute_profile(profile_name, registry_path, report_path) -> (exit_code, report)`.

Hidden behavior: contract compilation, step ordering, fail-fast policy, warning accounting, Git metadata observation, receipt assembly/persistence.

This is intentionally the deep module boundary. Consumers should not learn individual validator commands.

### Process adapter — external side-effect boundary

Current function: `run_command(validator)`.

Owns subprocess invocation, working directory, stdout/stderr capture, return code, and duration observation. It does not classify profile-level success beyond returning the observed step result.

### Evidence adapter

Current receipt writing remains inside `execute_profile` because the interface is small and there is no demonstrated second persistence implementation. Extract only if another evidence sink appears.

Runtime receipts are diagnostics/evidence, not durable product state. Retention/upload is consumer/provider policy.

### Git metadata adapter

Current function: `git_value(...)`.

Provides optional commit/branch observation. Its failure does not redefine validator truth. Exact PR candidate/base truth remains provider-owned.

### Consumer adapters

- CLI: `scripts/run_validator_profile.py` argument parsing and exit propagation.
- Pre-push: `.githooks/pre-push`; working-tree coordination checks plus one `pre_push` profile call.
- Actions: `.github/workflows/harness-contract.yml`; exact checkout/provider proof + one `harness` profile call + evidence transport.
- Pre-commit: `.githooks/pre-commit`; currently owns staged index gates, snapshot materialization, and snapshot-safe checks. Broad convergence is deferred until prototype evidence selects the exact boundary.

## Dependency direction

`CLI / hook / Actions adapter`
-> `execute_profile`
-> `read_registry + resolve_profile + profile_fingerprint`
-> `run_command`
-> `subprocess / filesystem / Git process`
-> `step result`
-> `profile state transition`
-> `ProfileReceipt`
-> `adapter exit / upload / Git allow-block decision`

Allowed dependencies point inward toward the profile program. The registry never depends on hooks or CI. The executor never imports workflow/provider logic. Provider wrappers may consume a receipt but may not rewrite the profile command list.

## State and ownership

| State | Canonical owner | Mutation boundary | Invalidation / lifecycle |
| --- | --- | --- | --- |
| Validator definitions/profile order | `harness/validators.v1.json` | tracked review/merge | any semantic registry change invalidates affected profile proof |
| Working-tree source | Git checkout/operator | ordinary repository mutation | current local state |
| Staged index | Git | `git add`/index mutation | commit/reset/index change |
| Materialized staged snapshot | pre-commit adapter | temp directory only | destroyed after hook/prototype run |
| Profile execution state | `execute_profile` | in-memory per run | ends at PASS/WARN/FAIL |
| Profile receipt | profile executor | temp/`Outputs/` | per-run evidence; may be uploaded by CI |
| Provider artifact | Actions adapter | GitHub run artifact store | provider retention policy |
| Provider exact-candidate identity/diff | Actions/provider checkout | read-only observation | invalid when PR head/base changes |

No cache, queue, database, daemon, server, container runtime, or deployment tier is required. This subsystem is a repo-local CLI/hook program plus ephemeral CI consumers, so managed PaaS/container/Kubernetes selection is **not applicable** on current evidence.

## Profile-run state machine

`REQUESTED`
-> `CONTRACT_RESOLVED`
-> `RUNNING(step n)`
-> one of:

- `PASS` when all required steps succeed;
- `PASS_WITH_WARNINGS` when only explicitly nonblocking steps fail;
- `FAIL_VALIDATOR` when a blocking step fails; remaining steps are not started;
- `FAIL_CONTRACT` when registry/profile/report-path compilation fails before execution.

Exit mapping:

- `0`: PASS or PASS_WITH_WARNINGS;
- `1`: blocking validator failure;
- `2`: profile/registry/report contract failure.

Provider/adapters may fail independently after a local PASS (for example exact candidate diff or artifact upload). That produces provider failure, not retroactive mutation of the local receipt.

## Representative executable call stacks

### Journey A — local required-check execution

Terminal user value: developer gets a trustworthy allow/block result and a diagnostic receipt without Actions.

`developer command`
-> CLI parser
-> `execute_profile(profile)`
-> `read_registry`
-> `resolve_profile`
-> `profile_fingerprint`
-> `run_command` for each validator
-> validator subprocesses
-> step results
-> fail-fast/warning policy
-> ProfileReceipt write
-> process exit code
-> terminal feedback.

Failure stack:

unknown/malformed profile
-> `resolve_profile` / report-path validation
-> `ProfileContractError`
-> FAIL contract receipt when the destination itself is valid
-> exit 2
-> no validator starts.

Blocking validator failure
-> `run_command`
-> nonzero return
-> orchestrator classifies validator as blocking
-> remaining validators are not started
-> failed validator recorded
-> exit 1.

### Journey B — pre-push working-tree gate

Terminal user value: push proceeds only after coordination/safety gates and the canonical `pre_push` profile pass.

`git push`
-> `.githooks/pre-push`
-> separately owned coordination/safety checks
-> `run_validator_profile.py --profile pre_push`
-> ProfileRun
-> temp receipt
-> hook exit
-> Git push allow/block.

Phase 2 proved this design and integrated it on main.

### Journey C — Actions provider wrapper

Terminal user value: exact candidate gets one provider-visible CI decision plus preserved evidence artifacts without Actions becoming profile owner.

`pull_request/push event`
-> exact-head checkout
-> provider/runtime setup
-> provider-only syntax/coordination checks
-> focused required-check program call-stack prototype
-> `run_validator_profile.py --profile harness`
-> local ProfileReceipt
-> artifact upload of receipt + registered reports
-> provider-only staged-artifact regression
-> `git diff --check origin/main...HEAD`
-> Actions job conclusion.

Failure ownership:

- profile failure: runner exits nonzero; CI step/job fails; receipt upload uses `always()`;
- upload failure/missing artifact: provider adapter fails even if profile passed;
- exact-candidate diff failure: provider adapter fails; local working-tree receipt remains truth only for its own context.

### Journey D — staged pre-commit snapshot candidate

Terminal user value: commit decision is based on staged content, not unstaged working-tree content.

Current production hook:

`git commit`
-> index-aware artifact gate
-> `git checkout-index` materializes isolated snapshot
-> snapshot-safe checks execute inside snapshot
-> return to source checkout
-> `git diff --cached --check`
-> commit allow/block.

Prototype candidate:

`git commit / prototype test`
-> materialize real Git index snapshot
-> build a temporary prototype ProfileSpec from the **canonical ValidatorSpecs** `harness-completeness` + `harness-contract-tests`
-> execute the snapshot copy of `run_validator_profile.py` against that snapshot
-> receipt outside snapshot
-> PASS.

Failure prototype:

same staged snapshot
-> mutate only snapshot `harness/manifest.v1.json` to an invalid `default_branch`
-> same real runner + same prototype profile
-> `harness-completeness` fails
-> orchestrator stops before `harness-contract-tests`
-> failed validator receipt
-> exit 1.

This prototype deliberately does **not** replace the production pre-commit hook. It tests whether a snapshot-safe profile seam is viable before assigning permanent profile state.

## Executable prototype owner

`tests/test_required_check_program_call_stacks.py`

Prototype acceptance:

1. Actions wrapper contains exactly one portable `harness` profile invocation.
2. Provider-only checkout, PowerShell, artifact upload, profile artifact, and exact-candidate diff markers remain.
3. No harness-profile command is copied into workflow YAML except the intentionally different provider exact-candidate patch check.
4. A real Git index snapshot can execute the snapshot-safe validator pair through the real snapshot copy of `run_validator_profile.py`.
5. The staged-snapshot success receipt observes both expected validators.
6. Corrupting the snapshot manifest fails at `harness-completeness`, records one observed step of two, and returns exit 1.

The prototype fakes no executor seam and no validator behavior. The only synthetic element is the temporary prototype profile grouping; it reuses the actual canonical validator definitions and is intentionally not persisted into the production registry until evidence selects it.

## Alternatives for staged pre-commit convergence

### S1 — delegate the existing `pre_commit` profile unchanged

**Rejected by design inspection.** The current profile mixes index-aware commands (`validate_staged_artifacts.py`, `git diff --cached --check`) with snapshot-safe commands. A materialized snapshot has no canonical Git index owner, so whole-profile execution inside it would collapse two execution contexts.

### S2 — teach the generic runner about Git-index phases

Possible, but adds index orchestration and phase semantics to a currently portable executor. This makes the core know too much about one adapter.

Disposition: **DEFER / likely reject** unless prototypes prove a genuine cross-consumer need.

### S3 — keep index gates in the pre-commit adapter and introduce one snapshot-safe profile

Smallest coherent boundary. The hook remains owner of materialization/index state; the existing generic executor owns snapshot-safe portable checks.

Disposition: **PREFERRED CANDIDATE**, pending executable prototype proof.

## Testability and observability

Unit/contract proof:

- `tests/test_validator_profile_runner.py` verifies profile compilation, exit/fail-fast policy, report containment, warning handling, and fingerprints.
- `tests/test_harness_contract.py` verifies hook/registry ownership and anti-duplication.

Integration/prototype proof:

- `tests/test_required_check_program_call_stacks.py` crosses real Git snapshot materialization -> real runner -> real validator subprocesses -> real receipt and exercises both success/failure stacks.
- Phase 3 Actions job runs the same prototype test before running the full canonical harness profile.

Observability owner:

- profile executor: bounded step stdout/stderr tails, duration, return code, validator/proof metadata, observed/required step counts, fingerprint;
- provider adapter: workflow step conclusion and uploaded artifacts.

No semantic product telemetry is needed; these are operational developer checks. Diagnostic volume remains bounded by receipt tail limits and CI retention policy.

## Second-pass architecture critique gate

After the executable prototype runs, reassess:

1. Did staged snapshot execution require the executor to know Git-index details? If yes, the seam is wrong.
2. Did the snapshot need copied validator logic rather than canonical ValidatorSpecs? If yes, the profile-state design is wrong.
3. Did Actions need to know individual portable validator commands? If yes, the wrapper is still too thick.
4. Did provider evidence disappear or become falsely represented as local proof? If yes, Phase 3 is invalid.
5. Does `execute_profile` now expose too many caller-specific arguments? If no, keep the current single-file deep module; do not split it for aesthetics.
6. Is the temporary snapshot profile grouping sufficient? If proven, broad implementation may persist a named snapshot-safe profile; otherwise retire the prototype without changing production pre-commit.

## Development phase map

Owner: `harness/validators.v1.json` + `scripts/run_validator_profile.py`.

### Phase 1 — INTEGRATED

PR #504 introduced and proved the generic local-first profile runner and thin optional Actions consumer. Mainline integration occurred at `5c39382c693cac4eb61df375e0128f63ff9d5698`.

### Phase 2 — INTEGRATED

PR #505 converged the duplicated registered pre-push tail onto the `pre_push` profile, preserved separately owned safety/coordination gates, and moved anti-duplication enforcement into the canonical harness validator. Integration commit: `e2c077ebaa438cdde0d4942f97bfee8d5bf2a6a2`.

### Phase 3 — DESIGN / PROTOTYPE ACTIVE

Owned scope:

- `.github/workflows/harness-contract.yml`: portable profile delegation plus preserved provider-only behavior;
- `tests/test_required_check_program_call_stacks.py`: provider-wrapper and staged-snapshot executable prototypes;
- this document: canonical program design, phase map, proof boundary.

Forbidden scope:

- changing validator membership/order merely to satisfy CI;
- production pre-commit convergence before prototype evidence;
- weakening provider exact-candidate/artifact proof;
- provider/promotion policy outside the operational harness workflow;
- unrelated Prompt Kit/application behavior.

Phase 3 acceptance:

- prototype tests PASS on exact branch head;
- full `harness` profile PASS on exact branch head;
- Operational harness workflow uploads profile/harness/interaction/language artifacts and preserves exact-candidate diff proof;
- deterministic repository floor remains green;
- second-pass critique records any seam change before merge;
- refreshed default branch contains the exact validated implementation after merge.

### Phase 4 — BOUNDED BUILD, only after Phase 3 evidence

If staged snapshot prototype succeeds without core leakage:

- add one durable snapshot-safe profile using the proven validator set/boundary;
- change only the staged-tree inner portion of `.githooks/pre-commit` to delegate to it;
- retain index artifact/path gate before materialization and `git diff --cached --check` after snapshot validation;
- preserve currently out-of-profile coordination checks unless separately dispositioned;
- add anti-duplication regression analogous to pre-push.

If the prototype fails or requires index semantics inside the core runner, do not implement Phase 4 from this design; revise the seam first.

## Non-goals

- no Actions emulator;
- no new task framework dependency;
- no daemon/API/database/container/Kubernetes service;
- no production pre-commit rewrite during design/prototype phase;
- no deletion of provider-only proof to shorten YAML;
- no claim that local/CI repository proof equals browser, device, deployment, protected-runtime, or production proof.

## Proof ceiling and invalidation

Repository/local/CI prototypes can prove profile selection/execution, staged snapshot viability, fail-fast behavior, consumer delegation, receipt semantics, and provider workflow wiring for the exact tested commit.

They do not prove branch-protection configuration, unavailable private inputs, browser/device behavior, deployment, or production acceptance.

The selected architecture is invalidated if:

- the validator registry ceases to be authoritative;
- required commands need shell semantics the argv executor cannot represent safely;
- staged snapshot execution requires the generic executor to own Git-index state;
- provider-only evidence cannot survive thin-wrapper conversion;
- a competing canonical generic profile executor is integrated;
- the prototype reveals split ownership or failure classification that cannot be repaired without caller-specific knowledge in the core.
