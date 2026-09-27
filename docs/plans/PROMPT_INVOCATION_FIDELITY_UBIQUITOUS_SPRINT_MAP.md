# Prompt Invocation Fidelity + Ubiquitous Factoring Donor Handoff

**Date:** 2026-09-26
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Observed donor floor:** `main@c6b6765e640205d7df33b349d5aee133aafbc1ec` (#652 integrated)
**Destination authority:** `EndeavorEverlasting/TokenCorridor`
**Canonical cross-repository plan:** `plans/active/PROMPT-SCRATCH-UBIQUITOUS-SPRINT-MAP.md` in TokenCorridor
**State:** UF-1A READY / donor implementation not yet performed; TokenCorridor PK-B01A already integrated early and requires UF-1B after this lane

## Why this donor handoff exists

A live P04 invocation was interpreted as a request to rewrite P04 instead of a request to execute P04. The operator explicitly identified this as an agent failure mode that must become durable Prompt Kit behavior and must also be visible in prompt quality/evaluation matrices.

Prompt Scratch simultaneously established a second planning requirement: the `Ubiquitous` category cannot be treated as blanket cross-repository mutation authority. It must compile through a bounded applicability matrix before sprint fan-out.

This Triage artifact exists so donor-side agents cannot miss the requirement while Prompt Kit authority is still in Triage. TokenCorridor remains the canonical cross-repository planning owner.

## Matrix authority map — do not create a generic fourth matrix

Invocation fidelity is one quality projected into three existing matrix families:

| Matrix family | Existing owner | Required UF-1A change |
| --- | --- | --- |
| Retrospective prompt-use | `harness/contracts/prompt-retrospective-evaluation.v1.json` + `harness/evals/prompt-retrospective/recent-candidates.v1.json` | Add an invocation-fidelity judgment for a prompt-use event: requested operational execution was honored vs substituted with prompt rewriting. |
| Semantic capability coverage | prompt-topology semantic capability/profile owners; derived `artifacts/prompt-semantic-coverage/matrix.v1.json` | Represent invocation-execution fidelity as protected operational capability inherited from the canonical shared owner; non-weakening rules must catch loss. |
| Runtime compliance / P67 | P67 / `harness/evals/repository-ai-evals.v1.json` + runtime-compliance contracts/fixtures | Add an observable invoked-P04 vs explicit-rewrite-intent scenario with typed PASS/FAIL/NOT_APPLICABLE/UNKNOWN outcomes. |

Regression safety (`docs/PROMPT_REGRESSION_SAFETY.md` + `harness/evals/prompt-regression/defect-families.v1.json`) remains the prevention/retention loop and may consume this incident; it is not a duplicate matrix authority.

Current P07 already contains the narrower guard `EXECUTE THE REPO SPRINT. DO NOT REWRITE THIS PROMPT.`. Preserve that as prior local mitigation evidence, but do not mistake it for shared inherited coverage.

## Destination race / recovery

TokenCorridor PR #35 integrated PK-B01A at `cd69f04a001ee0d164c950a1ab80e304b1ca660d` after the UF plan landed. Its containment receipt pins donor main to `e46499fe...`, so it did not consume #652/current donor state or UF-1A.

Do not roll #35 back. UF-1A now produces an exact donor SHA for a new **UF-1B destination delta reconciliation**. UF-2 stays blocked on UF-1B.

The ordering incident itself is a regression case: plan presence on the branch base is not proof that a declared predecessor was executed. Successor gates must bind exact predecessor evidence/identity.

## UF-1A — Invocation Fidelity + Matrix Quality

### Mission

Strengthen the smallest existing Prompt Kit owners so:

1. an invoked operational prompt executes unless the operator explicitly requests prompt mutation;
2. a request to rewrite/upgrade a prompt remains a valid prompt-mutation path and is not misclassified as execution;
3. applicable evaluation/validation/retrospective matrices can represent the merit `INVOCATION_FIDELITY`;
4. the defect is protected by one reproducing negative fixture plus positive controls;
5. the integrated donor SHA becomes the source floor for TokenCorridor PK-B01A;
6. P04 performs a first-class runtime partition before dependency graph and adapter selection, preserving ChatGPT/provider-capable work separately from local-agent-only work;
7. P05 applies the same shared runtime-partition capability before it serializes work into ordered sprint panels, so sequential planning cannot punt current-runtime/provider work to local agents or assign local-only work to the web runtime.

### Read first

- `docs/prompts.json`:
  - P04 — Repo-Aware Sprint + Harness Factoring Distributor
  - P05 — Ordered Sprint Plan Pack Generator
  - P11 — End-to-End Harness Validator
  - P13 — Self-Improving Rules Review
  - neighboring planning/evaluation owners discovered from refreshed main
- `tests/test_prompt_parallel_execution_contract.py`
- current shared actionability/closeout policy
- current prompt regression / retrospective / evaluation matrix owners
- `scripts/build_prompt_kit_registry.py` and generated-site ownership
- PR #653 only as read-only closeout/packet evidence; do not mutate its branch

### Required behavior

**Invocation rule**

If the operator invokes P04 (or another operational prompt) and supplies a repository/context, execute the workflow. Do not return an improved/reworded prompt unless the operator explicitly requested editing, rewriting, strengthening, compression, critique, or redesign.

If execution reveals a prompt defect, preserve that defect as a finding/sprint while still completing the authorized work.

**Matrix merit**

Use the smallest existing shared matrix/evaluation owner. Add:

`INVOCATION_FIDELITY = PASS | FAIL | NOT_APPLICABLE | UNKNOWN`

A FAIL is terminal for an invocation whose requested execution was replaced by prompt rewriting; other high-quality dimensions do not average that failure away.

### Negative fixture

Input shape:
- operator states that P04 is invoked;
- supplies repository/context and the P04 body;
- agent returns a rewritten P04 or commentary about improving P04 without executing factoring.

Expected:
- `INVOCATION_FIDELITY=FAIL`.

### Positive controls

1. invoked P04 -> actual factoring + durable plan/manifest output -> PASS;
2. explicit “rewrite/upgrade P04” -> prompt mutation without claiming repo factoring executed -> PASS.

### Owned scope

Resolve from refreshed main before mutation. Expected owner families:
- `docs/prompts.json` P04 + P05/shared planning metadata;
- smallest existing shared actionability/invocation-intent policy if one exists;
- existing matrix/evaluation owner;
- focused tests/fixtures;
- generated Prompt Kit via canonical builder.

### Forbidden

- new P### identity unless existing owners provably cannot express the invariant;
- blanket editing of all prompts;
- hand-editing generated `web/prompt-kit/index.html`;
- weakening P02 disposition/mode boundaries;
- modifying PR #653's branch or separately owned closeout files;
- treating `Ubiquitous` as “all repos”;
- freezing PK-B01A source before UF-1 integration proof.

### Validation

At minimum:
- shared runtime-partition contract + executable prototype call-stack tests before broad implementation;
- focused invocation-fidelity regression;
- existing P04 parallel-execution contract tests;
- focused P05 ordered-plan/runtime-partition regressions;
- affected shared policy/matrix tests;
- canonical Prompt Kit build/parity checks;
- patch hygiene;
- exact integrated-main containment/content proof.

### Completion gate

UF-1A closes only when the exact merged Triage main:
- enforces invocation-vs-mutation intent;
- carries the matrix merit in the canonical owner;
- passes negative + positive controls;
- preserves P04 durability/dispatch behavior and P05 ordered-pack behavior;
- proves P04 + P05 inherit the same runtime-partition semantic through one executable shared seam without duplicating doctrine;
- provides the exact source SHA to TokenCorridor PK-B01A.

## Ubiquitous downstream rule

This donor sprint does not implement the destination compiler. It establishes the shared planning invariant that `Ubiquitous` is a scope-compilation signal:

`idea -> propagation mode -> bounded candidate universe -> canonical owner -> applicability matrix -> archetype canary -> adoption -> future inheritance`

The destination implementation is owned by TokenCorridor after PK-B01A.

## Collision / sequencing

- #652 is integrated; its shared-policy/builder collision is cleared.
- #653 is a separate docs/ledger/packet writer and remains read-only to UF-1.
- UF-1 must integrate before the next PK-B01A donor source freeze.
- After UF-1A merges, TokenCorridor performs UF-1B delta reconciliation against the already-integrated PK-B01A destination before UF-2.

## PS-0004 / P04 runtime partition — normative non-weakening draft

**Source idea:** Prompt Scratch `PS-0004 — Runtime-aware sprint planning`
**Relationship:** fold into UF-1A; this is not a new competing prompt or a separate planning authority.

The current P04 adapter ladder is useful but insufficient by itself. Adapter selection answers **how a lane can run**. PS-0004 additionally requires P04 to decide **which runtime owns each material unit of work before lanes are emitted**, so ChatGPT/provider-capable work is not unnecessarily deferred to local Cursor/OpenCode agents and local-only work is not assigned to a web runtime that cannot perform it.

### Exact P04 draft insertion — preserve semantics; compression must be demonstrably non-weakening

Insert this section after `COMPACT PREFLIGHT` and before `FACTORING PASS` (or the nearest semantically equivalent location if the canonical source moved). Runtime partition is an internal planning stage; **LAUNCH ORDER remains the first substantive emitted section** under the existing output contract.

```text
RUNTIME PARTITION / EXECUTION PLACEMENT — REQUIRED
Before factoring sprint lanes, classify every material work unit by the host runtime that can actually perform it. Do not collapse the active ChatGPT/web runtime, local repository agents, CI/runners, operator/physical environments, and provider transports into a generic "agent" capability.

HOST EXECUTION ENVIRONMENT — choose exactly one:
- CURRENT_CHAT_RUNTIME — the active ChatGPT/web session is the executor.
- LOCAL_AGENT_RUNTIME — a local repository agent/runner or local filesystem/shell/toolchain is the executor.
- CI_OR_REMOTE_RUNNER — CI, a hosted job, or another evidenced remote runner is the executor.
- OPERATOR_OR_PHYSICAL_RUNTIME — a human, physical device, protected workstation, or otherwise inaccessible environment is required.
- UNKNOWN_RUNTIME — the required host runtime is not yet evidenced. Resolve it; do not guess.

PROVIDER / EXTERNAL ACCESS — separate dimension:
Record zero or more provider/access routes used by that host runtime, such as Google Drive, GitHub, Wispr, Neon, Render, Resend, Gmail, Calendar, or another evidenced connector. A connected provider is not itself the host execution environment. Tool presence proves a callable surface, not current authentication, account scope, or mutation authority.

For each material work unit record:
- host execution environment;
- required capabilities and mutation authority;
- provider/access routes, if any;
- evidence that the capability exists in the chosen host runtime;
- inherited evidence using sanitized durable references plus source owner, revision/freshness, and proof ceiling;
- expected artifact/proof returned;
- dependencies and collision surface.

PLACEMENT RULES
- Never hand local agents work that the current ChatGPT runtime can safely complete inside P04's planning/recovery/durability authority when doing it now closes a dependency, establishes provider truth, updates the canonical plan, or prevents rediscovery.
- A connected-provider operation executed from ChatGPT remains CURRENT_CHAT_RUNTIME with provider/access metadata; do not force an either/or choice between host runtime and provider.
- Consume dependency-ready CURRENT_CHAT_RUNTIME planning/evidence work before emitting downstream local-agent packets when that materially reduces uncertainty or duplicated work.
- P04 remains PLAN / DISTRIBUTE. Runtime partition does not turn P04 into the application-implementation owner. Code/product implementation still routes to P07 or the canonical implementation owner unless the active prompt separately authorizes that mutation.
- Never assign local-only filesystem/shell/toolchain work to CURRENT_CHAT_RUNTIME merely because the plan can describe it.
- Never ask the operator to shuttle evidence between runtimes when an available connector/provider/manifest can carry it.
- A local-agent handoff must inherit the exact **sanitized** evidence already established here: repository/ref, PR state, canonical plan revision/path, opaque provider artifact reference when required, blockers, freshness/revision, and proof ceiling. Never require tracked manifests to persist private provider URLs/IDs when repository governance forbids them.
- UNKNOWN_RUNTIME is an owner-resolution gate, not permission to invent capability.
- Runtime placement precedes dependency-graph width and adapter selection. The adapter ladder is evaluated only after execution ownership is established.

RUNTIME PARTITION OUTPUT
Perform runtime partition before graph construction, but preserve the existing output contract: LAUNCH ORDER remains first. Emit the compact runtime-placement table immediately after LAUNCH ORDER (or within the next already-authorized coordination section):
Work unit | Host execution environment | Provider/access route | Required capability | Sanitized inherited evidence | Execute now? | Dependency/output seam

The PARALLEL DISPATCH MANIFEST must preserve the placement decision so downstream executors can distinguish host runtime, provider transport, and inherited proof without exposing forbidden private identifiers.
```

### Internal mechanism changes required from the local Cursor lane

Cursor/local implementation must update the smallest existing canonical owners rather than merely pasting the draft into P04 or P05:

1. **Program-design/prototype gate first:** before broad prompt/schema mutation, create one shared runtime-partition contract and a thin executable prototype that proves:
   - host runtime and provider transport are separate/composable;
   - placement returns exactly one host environment;
   - private provider identities are rejected from tracked durable evidence;
   - sanitized inherited evidence preserves owner + revision/freshness + proof ceiling;
   - P04 projection and P05 projection consume the same shared decision seam.
   The prototype is evidence for the architecture, not a second production owner.
2. **Prompt registry:** strengthen canonical P04 **and P05** in `docs/prompts.json` (current provider evidence shows no P04/P05 override; do not create one without a repository reason).
3. **Dispatch contract:** extend `harness/contracts/prompt-parallel-dispatch.v1.json` with the minimum **required** lane metadata needed to preserve execution placement:
   - `execution_environment` — one host-runtime value from the shared contract;
   - `provider_access` — zero or more provider/access routes, separate from host runtime;
   - `required_capabilities` — typed list;
   - `evidence_inputs` — typed sanitized evidence records with source owner, evidence type, durable/opaque reference, revision/freshness, visibility, and proof ceiling.
   Reuse existing `adapter`, `launch`, `expected_artifacts`, and `convergence_owner` rather than duplicating them.
4. **Semantic/non-weakening coverage:** add/protect one shared planning capability such as `planning.runtime_partition` in the existing semantic capability owners and assign it to **both P04 and P05** through the repository's normal profile migration/baseline path.
5. **Focused regressions — P04:** preserve current P04 parallel-dispatch behavior and add negative/positive cases for current-runtime work, local-only work, composable provider access, sanitized inherited evidence, launch-order-first, and P07 ownership.
6. **Focused regressions — P05:** preserve ordered-pack behavior and add negative/positive cases for already-completed current-runtime work, local-only work, composable provider access, sanitized inherited evidence, launch-order-first, and P07 ownership.
7. **Registry/build parity:** run the canonical Prompt Kit builders and required tests; do not hand-edit generated public HTML.
8. **Public-facing website:** regenerate/publish the Prompt Kit from canonical sources so the public P04 and P05 surfaces contain the strengthened runtime-partition behavior. Website text is derived evidence, never the source authority.

### Non-weakening acceptance gate

The local Cursor lane fails if it:
- shortens P04 by deleting existing dependency, parallelism, durability, collision, manifest, or portability semantics without equivalent proven coverage;
- implements only prose while leaving the dispatch schema unable to preserve execution placement;
- updates only the generated website;
- makes "current runtime" synonymous with "local runtime";
- treats runtime partition as permission for P04 to implement work owned by P07;
- leaves PS-0004 as a Drive-only idea with no repository enforcement.

Completion requires executable shared-contract/prototype proof + canonical P04/P05 registry + required typed dispatch mechanism + shared semantic profile coverage + focused P04/P05 regressions + generated/public Prompt Kit parity, with exact donor/destination SHAs and proof ceiling recorded.

## P05 serialized-planner runtime partition — same shared capability, serialized projection

P05 is a second required consumer of PS-0004. The runtime taxonomy and ownership rule must have one shared semantic owner; P04 and P05 project that shared capability differently:

- **P04:** partition runtime ownership before dependency graph width, adapter selection, and parallel dispatch manifest generation.
- **P05:** partition runtime ownership before ordered launch-pack construction, then carry the placement through each serialized sprint panel and handoff.

### Exact P05 draft insertion — preserve ordered-pack semantics

Insert after P05's repository/context preflight and before its factoring/launch-order construction (or the nearest semantically equivalent location if the canonical prompt moves):

```text
RUNTIME PARTITION / EXECUTION PLACEMENT — REQUIRED
Before building the serialized sprint pack, classify every material work unit using the same shared runtime-partition contract as P04.

HOST EXECUTION ENVIRONMENT — choose exactly one:
- CURRENT_CHAT_RUNTIME
- LOCAL_AGENT_RUNTIME
- CI_OR_REMOTE_RUNNER
- OPERATOR_OR_PHYSICAL_RUNTIME
- UNKNOWN_RUNTIME

PROVIDER / EXTERNAL ACCESS — separate dimension:
Record zero or more provider/access routes used by the chosen host runtime. A provider is not itself an execution environment.

Do not treat "serialized" as "local." Sequence and execution environment are separate dimensions.

PLACEMENT RULES
- Complete safe dependency-ready CURRENT_CHAT_RUNTIME planning/evidence/durability work that P05 is authorized to perform when doing so closes a dependency, establishes current provider truth, or prevents downstream rediscovery.
- A ChatGPT step that uses Google Drive/GitHub/etc. remains CURRENT_CHAT_RUNTIME with provider/access metadata.
- Do not manufacture a local-agent sprint for work already completed in the current runtime; pass its sanitized exact evidence forward as an input to the next serialized lane.
- Do not assign filesystem/shell/toolchain-only work to CURRENT_CHAT_RUNTIME merely because the current agent can describe the commands.
- P05 remains PLAN / PACK. It does not become the implementation owner; executable repository/product work remains assigned to P07 or the canonical implementation owner.
- UNKNOWN_RUNTIME is a bounded owner-resolution gate, not a guess.
- Preserve source owner, revision/freshness, proof ceiling, and sanitized/opaque durable references across the serialized chain. Never force private provider IDs into tracked manifests.

SERIALIZED RUNTIME OUTPUT
Perform runtime partition before launch-pack construction, but preserve P05's output invariant: LAUNCH ORDER is the first substantive emitted section.

Immediately after LAUNCH ORDER (or in the next already-authorized coordination section), emit:
Work unit | Host execution environment | Provider/access route | Required capability | Sanitized inherited evidence | Already executed here? | Ordered dependency/output seam

Every sprint panel that still represents executable successor work must include:
EXECUTION ENVIRONMENT
PROVIDER / ACCESS ROUTE
REQUIRED CAPABILITIES
INHERITED EVIDENCE
RUNTIME HANDOFF

The final ordered pack must distinguish:
1. work already completed by the current ChatGPT runtime, including connected-provider work;
2. work that remains for local agents or CI;
3. work blocked on operator/physical access;
4. unresolved runtime ownership.

Never turn already-completed current-runtime work into a fake future sprint merely to preserve panel count.
```

### P05 non-weakening gates

The local implementation must preserve P05's existing:
- exact launch-order / display-order identity;
- self-contained one-panel-per-sprint contract;
- serialized dependency and collision semantics;
- proof taxonomy;
- dirty-worktree preservation;
- execution requirement for successor panels;
- final handoff and exact-next-command requirements.

Add focused cases:
- negative: P05 creates a local sprint for provider/Drive evidence that the active runtime could and should have established before pack emission;
- negative: P05 labels a local-toolchain task CURRENT_CHAT_RUNTIME;
- positive: P05 records a provider-side step as already executed and feeds its exact evidence into the next local serialized panel;
- positive: two sequential local sprints retain distinct runtime ownership and inherited evidence without becoming parallel;
- positive: P05 runtime partition does not weaken ordered panel identity or P07 execution ownership.

### Shared mechanism rule

Do not create a P05-specific runtime taxonomy. Add/protect one semantic capability, preferably `planning.runtime_partition` if current naming conventions permit, and assign it to both P04 and P05 through the existing capability catalog/profile/migration machinery. Prompt-specific text may differ, but the runtime classes and placement invariants must come from the same canonical contract/semantic owner.

## Proof ceiling

This file is a durable donor handoff and does not itself prove UF-1 implementation, tests, generated-site parity, merge, destination transplant, or live model compliance.

---

## Post-UF-1A P04/P05 faithfulness audit and repair fixed point — 2026-09-26

### Why this successor exists

UF-1A is integrated on Triage `main@b951c9d5b7dafc1afda8daba58d06d118ddc8351` through PR #665. Its runtime-partition architecture is valuable and remains the floor: host execution environment and provider transport are separate/composable, typed sanitized inherited evidence is required, P04 and P05 consume one shared `planning.runtime_partition` seam, and P07 remains the implementation owner.

This successor does **not** reopen that architecture. It exists because post-merge review found that compression and regression selection allowed prompt-level faithfulness drift even while topology, semantic-coverage, quality-history, dispatch, retrospective, and hosted CI validators passed. The repair therefore treats green validators as evidence of the current contract, not proof that the contract is complete.

### Verified current floor

- Canonical donor main: `b951c9d5b7dafc1afda8daba58d06d118ddc8351`.
- UF-1A implementation tip: `f8efb872736dddc7aaf672d73c90cee9e954ce57`.
- P04 dispatch predecessor: PR #664 / merge `35115b8f85e241797f018e9c0257dae3aaac7348`.
- Planning predecessor: PR #662 / head `861662e12580f308f4919b5fe37b82f89a7f226b`.
- Shared semantic owner remains `harness/contracts/planning-runtime-partition.v1.json` with canonical implementation `scripts/prompt_runtime_partition.py`; `scripts/planning_runtime_partition.py` is compatibility/shim surface, not a second semantic owner.
- Generated `web/prompt-kit/index.html` remains derived output and must only move through its canonical builder.

### Faithfulness findings — these are successor acceptance inputs, not optional review notes

#### F1 — P04 durability semantics were weakened during compression

The #665 P04 edit was not purely additive. It compressed the durable-plan tail and removed explicit obligations that were present immediately before UF-1A:

- material approval/plan change must synchronize to the owned canonical plan or relevant writable PR **before P05/P07 or another agent takes over**;
- when P66/a repository ledger exists, the index must carry the canonical plan, **current proof, owner, and next action**.

The replacement says to use P66/ledger as an index and to persist the complete map, but it no longer preserves those exact transition triggers and ledger fields. That is a real non-weakening gap even though semantic-history validators accepted the edit.

**Required repair:** restore equivalent explicit semantics through the canonical prompt lifecycle. Do not merely add back a literal sentence to satisfy a string test.

#### F2 — P04/P05 ownership is insufficiently protected

The intended split remains:

- **P04 = PLAN / DISTRIBUTE:** recover truth, runtime-partition material work, factor ownership/collisions/dependencies, produce the durable factoring map and machine-executable parallel dispatch manifest, then route implementation to P07.
- **P05 = PLAN / PACK:** consume an accepted/recovered factoring map, runtime-partition the remaining serialized work, preserve launch/display order, and emit self-contained ordered successor panels/handoffs.
- **P07 = IMPLEMENT / EXECUTE:** own repository/product implementation unless another canonical implementation owner is explicitly established.

Current P05 still contains a broad independent `FACTORING PASS`. That can be a recovery fallback, but it must not silently become a competing owner that re-factors an accepted P04 map.

**Required repair:** when a current accepted P04 factoring artifact exists, P05 consumes it and may only reconcile stale/conflicting evidence explicitly. P05 may perform bounded fallback factoring only when no usable P04 artifact exists; fallback must be labeled recovery, must preserve established ownership/collision decisions unless fresher evidence disproves them, and must not create a second plan authority.

#### F3 — the P05 runtime insertion is over-compressed and weakens authority boundaries

The normative P05 draft limited immediate current-runtime execution to P05-authorized **planning/evidence/durability** work. The merged prompt compresses this to `Complete safe current-runtime work first` and relies on a later `P07 owns implementation` clause.

That wording is too broad for weaker agents and can be read as permission to execute implementation in P05 before noticing the later ownership sentence.

**Required repair:** explicitly scope execute-now behavior to work inside P05's planning/evidence/durability authority and state that product/repository implementation remains a successor owned by P07/canonical implementation owner.

#### F4 — P05 is not sufficiently self-contained when invoked alone

The merged P05 runtime section says to use the same shared contract as P04 and says `one HOST plus zero or more PROVIDER routes`, but it no longer includes the host-runtime enum or the `UNKNOWN_RUNTIME` owner-resolution rule carried by the accepted normative draft.

P05 is a copyable Prompt Kit surface and must remain understandable when invoked without first reading P04 or opening repository internals.

**Required repair:** include the minimum executable runtime taxonomy and placement invariants directly in P05 while still naming the shared contract as authority. Cross-reference may reinforce semantics; it may not be the only place essential semantics live.

#### F5 — canonical implementation vs shim ownership must be explicit

The shared contract names `scripts/prompt_runtime_partition.py` as canonical implementation, while P04/P05 prompt text points agents at `scripts/planning_runtime_partition.py`.

Compatibility is acceptable; semantic dual ownership is not.

**Required repair:** document/test that `prompt_runtime_partition.py` is canonical, `planning_runtime_partition.py` is compatibility only, and prompt or downstream edits must not fork taxonomy/placement behavior into the shim.

#### F6 — current regressions protect some literals but miss the faithfulness boundaries above

`tests/test_prompt_runtime_partition_contract.py` currently asserts, among other things, that P04 contains `LAUNCH ORDER stays first`. That preserves an output-order invariant but does not prove:

- P04 durable-plan change synchronization survives;
- P66 index fields survive;
- P05 consumes accepted P04 factoring instead of re-owning it;
- P05 current-runtime execution is scoped to planning/evidence/durability;
- P05 remains usable without prior P04 context;
- canonical runtime implementation and shim cannot diverge.

**Required repair:** add focused semantic/behavioral regressions for these invariants. Prefer structural or scenario assertions over brittle sentence-only matching. Existing literal tests may remain when the literal itself is a deliberate compatibility contract.

#### F7 — proof/status language must reconcile `PROTOTYPE` vs integrated canonical use

`harness/contracts/planning-runtime-partition.v1.json` is consumed as the canonical shared seam yet currently declares `status: PROTOTYPE`. UF-1A closeout simultaneously reports no remaining Triage gap for the lane.

**Required repair:** inspect repository status conventions and either promote the contract through the existing lifecycle with proof, or explicitly document why `PROTOTYPE` is the correct durable status for a canonical consumed seam. Do not silently relabel it just to make the words agree.

### Non-negotiable architecture preserved through every repair

1. Host execution environment and provider/access transport are separate dimensions.
2. Exactly one host runtime is selected for each material work unit; provider routes compose with that host.
3. Private provider URLs/IDs are never forced into tracked manifests; inherited evidence remains typed and sanitized with owner, revision/freshness, visibility, and proof ceiling.
4. Runtime partition happens before P04 graph/adapter selection and before P05 ordered-pack construction.
5. Serialization is ordering, not locality.
6. P04 does not become P07; P05 does not become P07.
7. P04 factoring and P05 ordered packing remain distinct responsibilities even when both use the same runtime decision.
8. Existing dependency, collision, durability, autonomy, manifest, dirty-worktree, proof, panel identity, and handoff semantics may only be compressed when equivalence is proven.
9. Do not create a new P### prompt, a P04/P05-specific runtime taxonomy, a duplicate semantic owner, a second work ledger, or a hand-edited generated HTML path.
10. TokenCorridor must not treat `b951c9d5...` as the final donor once this successor begins. Its next reconciliation must use the eventual repaired Triage donor SHA and import only the proven delta.

### Execution sequence — serial where canonical prompt ownership collides

These sprints are intentionally ordered. P04 and P05 both mutate `docs/prompts.json`, semantic/profile migrations, generated Prompt Kit output, and overlapping prompt regressions; do not run their canonical mutations concurrently.

#### FAITH-1 — P04 non-weakening repair

**Mission:** restore the P04 durability transition semantics lost by UF-1A compression while preserving the runtime-partition architecture and every pre-existing P04 capability.

**Read first:**
- this plan;
- `docs/prompts.json` P04;
- the P04 section above under PS-0004;
- `harness/contracts/prompt-strength.v1.json`;
- `harness/prompt-topology/prompt-capability-profiles.v1.json`;
- `harness/prompt-compilation/prompt-semantic-migrations.v1.json`;
- `harness/prompt-topology/prompt-capability-migrations.v1.json`;
- `tests/test_repository_plan_durability.py`;
- `tests/test_prompt_runtime_partition_contract.py`;
- `scripts/prompt_registry_ops.py`.

**Required changes:**
- restore explicit material-plan-change synchronization before P05/P07/agent handoff;
- restore explicit P66/ledger index requirements for canonical plan + current proof + owner + next action;
- keep runtime partition before factoring/adapter selection;
- keep P07 implementation ownership;
- preserve existing P04 launch/display ordering only as presentation/orchestration behavior, not as a reason to blur P04 into P05.

**Mutation contract:** use the canonical prompt lifecycle/registry tooling; do not hand-author profile/migration hashes; regenerate derived website output only through the canonical builder.

**Acceptance:** targeted prompt-strength/durability/runtime tests, semantic/topology/history validators, builder parity, `git diff --check`, hosted required checks, and explicit before/after non-weakening receipt.

#### FAITH-2 — P05 serialized planner repair

**Dependency:** FAITH-1 merged and refreshed main.

**Mission:** make P05 a self-contained ordered-pack consumer of accepted P04 factoring, with bounded recovery fallback and correctly scoped current-runtime planning/evidence work.

**Required changes:**
- add the minimum host enum and UNKNOWN owner-resolution rule directly to P05;
- narrow execute-now language to P05-authorized planning/evidence/durability work;
- explicitly consume the current accepted P04 factoring artifact when present;
- define fallback factoring as recovery-only when no usable upstream artifact exists;
- forbid fallback from silently changing accepted ownership/collision decisions without fresher evidence;
- preserve exact launch-order/display-order identity, one-panel-per-sprint, dirty-worktree protection, proof taxonomy, successor execution requirement, and exact-next-command handoff;
- state canonical runtime implementation + shim relationship without creating duplicate ownership.

**Acceptance:** focused positive/negative scenarios for accepted-P04 consumption, fallback recovery, already-executed current-runtime evidence, local-only work, UNKNOWN runtime, provider composition, P07 ownership, and self-contained invocation; full semantic/topology/history/build parity gates.

#### FAITH-3 — cross-prompt boundary and adversarial regression hardening

**Dependency:** FAITH-2 merged and refreshed main.

**Mission:** make the intended P04→P05→P07 handoff difficult for weaker agents or future compression to weaken.

**Required work:**
- extend existing regression owners rather than inventing a parallel validation framework;
- add scenario coverage that fails if P05 re-factors an accepted P04 plan without new evidence;
- fail if P04 or P05 claims implementation ownership merely because the chosen host is CURRENT_CHAT_RUNTIME;
- fail if a material P04 plan change can hand off without durable synchronization;
- fail if P66 indexing loses current proof/owner/next action when that ledger exists;
- fail if shim semantics diverge from the canonical runtime owner;
- retain invocation-fidelity proof ceilings: repository/static tests do not prove live model obedience.

**Acceptance:** focused tests + full deterministic floor + prompt semantic/topology/history + dispatch + retrospective + generated-site parity + clean diff/status + hosted CI.

#### FAITH-4 — donor closeout and TokenCorridor re-reconciliation packet

**Dependency:** FAITH-3 merged and refreshed main.

**Mission:** establish one exact repaired donor SHA and update this canonical plan with the completion receipt.

**Required output:**
- final Triage main SHA and prompt hashes;
- exact changed donor surfaces;
- validation/check receipts;
- proof ceiling;
- any unresolved live-model/provider proof;
- minimal `old donor b951c9d5... -> repaired donor` delta for TokenCorridor;
- explicit instruction that TokenCorridor reconciles its current state against the repaired donor rather than replaying the entire Triage history.

No AgentSwitchboard mutation and no new Prompt Scratch authority are part of this successor.

### Completion gate

This successor is complete only when:

- F1-F7 each have a disposition backed by tracked evidence;
- P04 and P05 remain distinct owners with one shared runtime-partition semantic seam;
- prompt lifecycle/history records prove non-weakening for the canonical mutations;
- targeted regressions protect the repaired boundaries rather than only the new wording;
- generated/public Prompt Kit parity is rebuilt from canonical sources;
- hosted checks are green;
- this plan records the repaired donor SHA and TokenCorridor delta handoff;
- remaining live-provider/model-obedience proof is reported as a proof ceiling, not silently promoted to repository proof.

Until then, `b951c9d5...` is an integrated UF-1A floor, **not** the final faithfulness-fixed donor.
