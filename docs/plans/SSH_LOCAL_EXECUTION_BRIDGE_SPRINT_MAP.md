# SSH + Local Execution Bridge Sprint Map

Status: TRACKED PLAN
Canonical repository: `EndeavorEverlasting/web-excel-repair-triage`
Planning floor: `main@29bf333309916740b6172247c5d93e5e76f9ea81`
Factoring date: 2026-09-18

## Mission

Remove GitHub Actions as a single point of execution failure without inventing a second CI system. Reuse the repository-owned parallel-dispatch and local-proof contracts, restore a current SSH transport prompt through the Prompt Kit admission path, and connect an authorized local agent host to reviewed repository action IDs. SSH is transport/authentication; it is not the scheduler, proof owner, or arbitrary remote-shell authority.

Target end state:

1. a current Prompt Kit SSH owner can configure and prove repository SSH transport safely;
2. a local host adapter can receive a bounded dispatch/work request without the operator acting as scheduler;
3. the adapter operates on an isolated, refreshed checkout and executes only reviewed repository-owned actions or explicitly admitted sprint commands;
4. `scripts/run_repository_action.py` remains the canonical local proof executor and `scripts/prompt_parallel_dispatch.py` remains the canonical dependency/parallel-dispatch owner;
5. an Actions-off canary can rebuild/validate Prompt Kit, commit the exact generated output, push over verified Git transport, and return typed proof that the coordinator can independently inspect;
6. hosted CI remains an optional independent proof adapter, not the semantic owner.

## Fresh evidence floor

- Current default branch: `main@29bf333309916740b6172247c5d93e5e76f9ea81` (`feat(runtime-compliance): add provider-neutral pilot runner`).
- P56 strengthening is already integrated on current main by PR #562 / merge commit `13c7f0204f0caacd3111f5864f80971830517921`; do not reopen that lane.
- PR #399 `feat(prompt-kit): add repository SSH setup completer` remains open at head `6f34ed4ca0db9fb367f45d0a3430703040305187` and was based on an obsolete floor. Its intended prompt identity `P139` is now occupied on current main by `Verified Job Opportunity Application Pack Builder` in `registry/prompts/management-operations-prompts.v1.json`. PR #399 is donor evidence, not merge-ready truth.
- `harness/contracts/repository-local-proof-continuity.v1.json` already defines hosted-provider degradation semantics and explicitly makes hosted CI non-exclusive.
- `harness/repository-actions.v1.json` + `scripts/run_repository_action.py` already own reviewed local action execution and typed repository-action receipts. `prompt-kit-build-proof`, `prompt-kit-proof`, `required-checks-proof`, `pre-push-proof`, and `repo-native-update-check` already exist.
- `harness/contracts/prompt-parallel-dispatch.v1.json` + `scripts/prompt_parallel_dispatch.py` already own machine-readable dependency waves and argv/runtime-tool dispatch receipts.
- Runtime-compliance Sprint 3A is now integrated on main. `harness/evals/runtime-compliance/runtime/adapter-contract.v1.json` is an evaluation-specific provider-neutral adapter/capture boundary; it must not silently become the operational repository worker.
- `harness/evals/PROMPT_RUNTIME_COMPLIANCE_PILOT_PLAN.md` still records the operational AUTONOMY_GAP: no evidenced autonomous mutating agent-worker adapter currently consumes P04/P59 lanes and returns verifiable receipts.
- AgentSwitchboard PR #311 is a clean draft plan for a concrete OpenCode V2 evaluation adapter. It assigns provider launch/readiness/subprocess boundaries to AgentSwitchboard and preserves FirstMate as canonical crew/session runtime. It is relevant prior art, but it is not yet the operational repository-action worker.
- Open PR #524 currently owns `.ai/WORK_QUEUE.md`; this plan deliberately does not mutate that shared ledger surface. The durable plan + this PR are the continuity owner until the ledger surface is free.

## Selected architecture

```text
coordinator / P04-P07
        |
        | typed prompt-parallel-dispatch manifest / bounded work request
        v
AgentSwitchboard / FirstMate local host adapter
        |
        | isolated checkout + reviewed action id
        v
scripts/run_repository_action.py
        |
        +--> deterministic tests / validators / generators
        |
        +--> repository-action-receipt/v1
        |
        v
Git remote using verified SSH transport when configured
        |
        v
GitHub branch / PR / merge provider
```

Authority boundaries:

- SSH owns repository transport/authentication only.
- FirstMate/AgentSwitchboard owns local agent launch/session/process boundaries; do not create a second scheduler in Triage.
- `prompt_parallel_dispatch.py` owns dependency waves and dispatch evidence.
- `run_repository_action.py` owns reviewed local proof actions; do not expose arbitrary shell as the normal remote contract.
- GitHub provider tooling owns remote repository/PR mutations and independent hosted proof when available.
- Runtime-compliance adapter/capture stays evaluation-only unless a later reviewed contract explicitly generalizes it.

### Control-plane wakeup gate

A local worker is not autonomous merely because an executable exists. Sprint 1B must resolve the machine-to-machine activation surface before Sprint 2B claims an operational bridge.

Preferred order:
1. reuse an already implemented AgentSwitchboard/FirstMate local invocation or connected runtime-tool surface when current evidence proves one;
2. otherwise use the smallest provider-backed bounded work-request inbox/wakeup that can carry only sanitized request identity, repository/ref, lane/action identity, and correlation metadata without GitHub Actions;
3. if inbound wakeup is unavailable, a bounded local poller may consume that provider queue with dedupe/idempotency and explicit cadence;
4. manual operator launch is portability/recovery fallback only and cannot satisfy the autonomous-worker completion gate.

The readiness sprint must choose among these from evidence. This plan does not invent a FirstMate webhook, daemon, or queue that current repository evidence has not proved.

## Viable path comparison

| Path | Disposition | Reason |
|---|---|---|
| GitHub self-hosted Actions runner | REFERENCE_ONLY / fallback | Restores hosted workflow execution but keeps Actions as the orchestration dependency and does not solve provider-independence. Useful later only as another adapter. |
| Arbitrary SSH remote shell | REJECT | Over-broad mutation surface, weak action provenance, duplicates repository-owned action policy, and turns SSH transport into execution authority. |
| Reuse runtime-compliance adapter directly | REJECT for operations | Its contract is evaluation/capture-specific and explicitly separates fake/real runtime evidence. Reusing it operationally would collapse proof domains. |
| Thin local host adapter -> P04/P59 manifest -> reviewed repository action IDs -> typed receipts | ADOPT | Reuses current contracts, minimizes new authority, supports Actions-off execution, and lets GitHub remain the integration/provider plane. |
| Provider-only GitHub mutations + hosted CI | KEEP as alternate | Works when provider execution is healthy; remains independent evidence, not the only path. |

## Dependency graph

```text
S0 Durable factoring + collision map (this plan)
   |
   +-------------------------+
   |                         |
S1A SSH Prompt Recovery   S1B Local Host Readiness
   |                         |
S2A Workstation SSH       S2B Thin Local Worker Adapter
   |                         |
   +------------+------------+
                |
      S3 Actions-Off Canary
                |
      S4 Integration/Hardening
                |
      S5 Cleanup + Generalization
```

Wave 1 graph width is 2. S1A and S1B own separate repositories/surfaces and are intentionally parallel. Wave 2 also has width 2 after its respective dependencies are satisfied.

## Sprint 0 — Durable factoring and collision map

Classification: floor / cleanup / planning durability.

Owned scope:
- this plan;
- the active `Outputs/prompt-parallel-dispatch/manifest.json` only for the initial evidence wave;
- PR description/coordination evidence.

Forbidden:
- `.ai/WORK_QUEUE.md` while PR #524 owns it;
- PR #399 prompt source or generated Prompt Kit output;
- AgentSwitchboard PR #311 files;
- runtime-compliance implementation.

Completion gate:
- plan and dispatch manifest are tracked on an isolated branch/PR from refreshed main;
- no stale identity is treated as merge-ready;
- current owners and proof ceilings are explicit.

Proof ceiling: TRACKED planning/control-plane evidence only.

## Sprint 1A — Re-admit Repository SSH Setup + Usage through current Prompt Kit authority

Classification: Prompt Kit owner recovery / floor repair.

Dependencies: Sprint 0.

Primary owner: P79 + `scripts/prompt_registry_ops.py`.

Mission:
- treat PR #399 as donor evidence;
- rerun current prior-art across all registered sources;
- compare P55, P61, current setup prompts, and any newly integrated owner by trigger/mission/closure;
- if the distinct SSH transport residual still survives, add through the helper and let current registry mechanics allocate the identity;
- never reuse stale `P139` manually.

Owned surfaces:
- the helper-selected canonical registry/profile;
- focused SSH semantic regression;
- test-floor registration when repository convention requires it;
- generated `web/prompt-kit/index.html` only through the canonical builder.

Forbidden:
- manual id/seq/copySheet allocation;
- P55/P61 role expansion unless current prior-art proves strengthening is the correct current owner;
- secrets/private keys;
- global workstation SSH policy;
- hand-editing generated HTML.

Acceptance gate:
- `prior-art` proves the owner disposition;
- current prompt identity is collision-free;
- preserved semantics include key reuse, private-key boundary, provider-neutral host trust, bounded `git ls-remote`, safe write proof, blocker typing, and HOW TO USE THIS SSH SETUP;
- focused prompt tests + registry validation + generated-site parity + deterministic floor pass;
- exact validated head integrates to main;
- PR #399 is then marked superseded/closed only after the replacement is safely integrated.

Proof ceiling: repository prompt semantics; no workstation SSH configuration yet.

## Sprint 1B — Prove the local host/backend readiness owner

Classification: agent harness / runtime integration preparation.

Repository owner: `EndeavorEverlasting/AgentSwitchboard`.

Dependencies: Sprint 0.

Starting evidence: draft PR #311 `plan(runtime): build concrete P67 OpenCode evaluation adapter` at head `b78e2fb0f4de8e290d60a3d64ebedcc9af9ae48a`; FirstMate remains canonical crew/session runtime.

Mission:
- refresh AgentSwitchboard current main and PR #311;
- execute the dependency-ready read-only OpenCode/provider readiness probe from the existing plan rather than creating another adapter program;
- determine the smallest reusable host invocation seam that can later receive a bounded Triage work request;
- preserve evaluation-adapter concerns separately from the future operational worker.

Forbidden:
- Triage registry mutation;
- replacing FirstMate scheduler;
- arbitrary remote shell endpoint;
- provider secrets in repository evidence;
- claiming mutating worker proof from a read-only readiness probe.

Acceptance gate:
- exact supported local backend(s), executable invocation, configuration/credential gate, isolation behavior, and proof ceiling are machine-verifiable;
- PR #311 is either integrated or its current blocking gate is exact;
- the next operational adapter implementation can bind to a proven host seam instead of an invented command.

Proof ceiling: host/backend readiness only.

## Sprint 2A — Configure and prove workstation SSH transport

Classification: environment/runtime setup.

Dependencies: Sprint 1A integrated SSH owner.

Mission:
- invoke the current SSH Prompt Kit owner on the actual workstation/repository;
- preserve existing keys/config/remotes;
- verify host fingerprint through authoritative provider evidence;
- register only a public key when needed;
- prove noninteractive repository read and safe write authorization for the intended repo/branch.

Required proof:
- exact repo/root/provider/remote;
- key decision REUSED or GENERATED without private material disclosure;
- bounded `git ls-remote` PASS;
- safe `git push --dry-run` PASS when read-write intent and branch state permit;
- exact blocker classification otherwise.

Proof ceiling: observed workstation Git transport/authentication. This does not prove local agent orchestration.

## Sprint 2B — Build the thin operational local worker adapter

Classification: agent harness / integration seam.

Primary owner: AgentSwitchboard/FirstMate.

Dependencies:
- Sprint 1B readiness;
- current Triage `prompt-parallel-dispatch` and `repository-actions` contracts refreshed and treated as read-only external authorities.

Mission:
- consume a bounded work request that identifies repository, exact base/head intent, lane/manifest identity, owned/forbidden surfaces, and reviewed action id or admitted P07 task;
- bind that request to the evidence-proven machine-to-machine wakeup/inbox surface from Sprint 1B; if no direct runtime-tool surface exists, implement the smallest provider-backed sanitized request carrier plus dedupe/idempotency rather than requiring operator launch;
- create/use an isolated checkout/worktree;
- refresh remote truth without destructive reset;
- invoke the repository-owned action/validator/generator through its canonical CLI;
- return typed execution/proof evidence and exact resulting commit identity;
- push only through an already verified Git transport path when write authority is present;
- never own merge/default-branch promotion independently.

First canary scope:
- support Triage `prompt-kit-build-proof` only;
- no arbitrary shell over the transport;
- no broad multi-repo generalization until the canary passes.

Security/guardrails:
- private SSH key/passphrase remains local;
- work request cannot inject an unregistered repository action command;
- environment/credential allowlist is explicit;
- unknown/partial mutation requires readback before retry;
- dirty/separately-owned work is preserved;
- every response pins exact repository/base/head/action/proof-relevance inputs.

Acceptance gate:
- a synthetic/local fixture proves request validation, isolation, allowlist rejection, nonzero-exit propagation, receipt production, and no unauthorized default-branch merge;
- an actual Triage checkout can be targeted without operator copy/paste scheduling.

Proof ceiling: operational adapter behavior in its tested local environment; not yet Actions-off end-to-end success.

## Sprint 3 — Actions-off Prompt Kit build/proof canary

Classification: end-to-end integration / runtime proof.

Dependencies:
- Sprint 2A verified SSH transport;
- Sprint 2B operational worker;
- current Triage local-action registry with `prompt-kit-build-proof`.

Mission:
Prove the exact failure mode that motivated this program: hosted Actions is unavailable or deliberately not used, yet the repository still advances safely.

Canary sequence:
1. coordinator produces a bounded lane/work request for an isolated feature branch;
2. local host refreshes/clones through the verified repository transport;
3. local worker invokes `python scripts/run_repository_action.py --action prompt-kit-build-proof ...` through the canonical interface;
4. canonical Prompt Kit generated output is produced by the tracked builder;
5. local proof receipt pins exact candidate/base/proof inputs and preserves hosted-only gates as unproven;
6. worker commits only the owned generated/source surfaces when a change exists;
7. worker pushes the exact validated branch through verified SSH;
8. coordinator independently reads back branch/PR state through GitHub provider tooling;
9. normal merge/protection rules apply; hosted CI may add independent proof if available but is not required for the local gates the contract says local proof can close.

Acceptance gate:
- no GitHub Actions execution is required to generate/validate the owned Prompt Kit surface;
- exact local receipt is valid;
- exact commit appears remotely;
- no private credential material crosses the boundary;
- coordinator can continue at the PR/integration gate without asking the operator to shuttle logs or commands.

Proof ceiling: observed Actions-off local execution + Git transport + remote readback for the canary. It does not automatically waive any truly hosted-only protection gate.

## Sprint 4 — Integrate the bridge into existing orchestration and regression owners

Classification: harness spine / regression safety / routing.

Dependencies: Sprint 3 observed canary.

Rule: strengthen only where the canary proves a real missing seam. Do not create speculative contracts before the observed trace exists.

Likely owners to inspect:
- `harness/contracts/prompt-parallel-dispatch.v1.json`;
- `scripts/prompt_parallel_dispatch.py`;
- `harness/contracts/repository-local-proof-continuity.v1.json`;
- `harness/repository-actions.v1.json`;
- P07 compiled semantics and regression tests;
- RTC01 provider-unavailable and RTC05 adapter-ladder runtime-compliance scenarios;
- AgentSwitchboard FirstMate/adapter registry and capability docs.

Possible outcomes:
- ALREADY COVERED: only registration/docs/adapter configuration needed;
- STRENGTHEN: add the smallest missing worker capability/trigger/receipt invariant;
- P13/P94 systemic repair only if the canary reproduces a recurring defect family.

Acceptance gate:
- P04/P07 can select the local worker at the repo-runner rung when available;
- Actions unavailability routes to the local path instead of terminal cessation;
- negative fixture fails when the runtime stops at provider loss while a local worker is available;
- positive control proves provider loss -> local action -> typed receipt -> continued integration;
- no duplicate scheduler/proof owner is introduced.

Proof ceiling: integrated orchestration/regression contract. Cross-machine generality remains unproven until separately observed.

## Sprint 5 — Cleanup and bounded generalization

Classification: release/PR hygiene + optional capability expansion.

Dependencies: Sprint 4.

Required cleanup:
- close/supersede stale PR #399 only after its accepted semantics are represented by integrated current truth;
- remove any temporary canary transport/config that is not canonical;
- preserve unique evidence/receipts according to repository artifact policy;
- update the work ledger only after its current owner releases the surface.

Generalization gate:
Only after the Prompt Kit canary passes, decide whether to expose additional reviewed `repository-actions.v1.json` action IDs or additional repositories through the same host adapter. Do not widen to arbitrary shell or universal remote execution by default.

## Skills / capabilities / triggers factoring

| Surface | Current owner | Disposition | Activation | Output / proof |
|---|---|---|---|---|
| SSH workflow guidance | stale PR #399 donor; current Prompt Kit admission via P79 | RECOVER / RE-ADMIT | existing repo needs SSH configure/repair/proof | verified transport setup + usage guide; repo semantics first, workstation proof later |
| Local proof capability | `repository-local-proof-continuity` + `repository-actions` | KEEP | provider unavailable or local proof explicitly selected | `repository-action-receipt/v1`; typed local proof ceiling |
| Parallel dispatch | `prompt-parallel-dispatch` + `prompt_parallel_dispatch.py` | KEEP | dependency graph/lane execution | manifest + receipt; observed parallelism only when actually dispatched |
| Runtime compliance evaluation adapter | runtime-compliance Sprint 3A | KEEP ISOLATED | evaluate runtime obedience | compliance capture/receipt; not operational mutation authority |
| Local agent host/scheduler | AgentSwitchboard / FirstMate | STRENGTHEN | bounded work request targets an available local backend | isolated agent/process execution + returned evidence |
| Provider-unavailable trigger | P07 local-proof continuity semantics | KEEP / validate observed route | hosted state QUOTA_EXHAUSTED/RATE_LIMITED/RUNNER_UNAVAILABLE/PERMISSION_DENIED | local continuation or exact typed blocker |

## Collision ledger

- `P139`: hard identity collision. Current main job-application owner wins; SSH must be re-admitted under current helper authority.
- `web/prompt-kit/index.html`: generated single-writer surface; only canonical builder may update it.
- `.ai/WORK_QUEUE.md`: currently owned by open PR #524; this plan does not write it.
- AgentSwitchboard `plans/plan-registry.json`: PR #311 already records a separate collision with PR #309; preserve that owner.
- FirstMate scheduling/session semantics: AgentSwitchboard authority; Triage must not create a competing scheduler.
- runtime-compliance adapter/capture: evaluation authority; operational bridge may reuse patterns, not the identity/receipt contract.
- SSH key/config: local credential boundary; no repository/chat artifact may persist private material.

## Proof taxonomy for this program

- TRACKED PLAN: this document/PR.
- VALIDATED PROMPT OWNER: current SSH prompt passes Prompt Kit registry/tests/build.
- HOST READINESS: local backend invocation/isolation is proven.
- WORKSTATION TRANSPORT OBSERVED: `git ls-remote` and applicable write dry-run observed on the real machine.
- LOCAL WORKER VALIDATED: adapter contract/tests/fixtures pass.
- ACTIONS-OFF CANARY OBSERVED: local worker executes real Triage action, pushes exact commit, provider readback confirms it.
- INTEGRATED: current main contains any required bridge/routing/regression changes.
- DEPLOYED/GENERALIZED: only when additional machines/repos are actually configured; never infer from canary proof.

## Initial dispatch posture

The dependency graph has two independent evidence lanes now: current-registry SSH prior-art and current local-proof floor verification. A repository-local runner is not available in the present coordinator runtime, and the isolated container cannot resolve GitHub, so those argv lanes are recorded as DEGRADED/BLOCKED in `Outputs/prompt-parallel-dispatch/manifest.json` rather than falsely reported as dispatched. This is the exact autonomy gap the later AgentSwitchboard worker sprint is intended to close.

## Definition of done for the whole program

The program is complete only when:
- a current SSH owner is integrated;
- a real workstation repository has verified SSH transport when SSH is selected;
- an autonomous local host adapter consumes bounded repository work without human scheduling;
- the Prompt Kit Actions-off canary executes through repository-native proof, pushes an exact validated commit, and is independently read back by the coordinator;
- required current-main routing/regression owners are strengthened only where the observed canary proves a gap;
- stale PR #399 is safely superseded/closed;
- all remaining hosted-only gates are explicitly typed rather than silently waived.
