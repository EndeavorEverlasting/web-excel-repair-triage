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
- proves P04 + P05 inherit the same runtime-partition semantic without duplicating doctrine;
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

Insert this section after `COMPACT PREFLIGHT` and before `FACTORING PASS` (or the nearest semantically equivalent location if the canonical source moved):

```text
RUNTIME PARTITION / EXECUTION PLACEMENT — REQUIRED
Before factoring sprint lanes, classify every material work unit by the runtime that can actually perform it. Do not collapse the active ChatGPT/web runtime, connected providers, local repository agents, CI/runners, and operator/physical environments into a generic "agent" capability.

Use these execution-environment classes:
- CURRENT_CHAT_RUNTIME — work the active ChatGPT/web session can perform with its presently evidenced tools and mutation authority.
- CONNECTED_PROVIDER — work executable through a connected API/connector/provider from the active runtime.
- LOCAL_AGENT_RUNTIME — work requiring local filesystem, shell, repository toolchain, local browser/runtime, or repo-proven runners such as Cursor/OpenCode/AgentSwitchboard/Codex/Claude wrappers.
- CI_OR_REMOTE_RUNNER — deterministic work owned by CI, matrix jobs, hosted runners, or another evidenced remote execution surface.
- OPERATOR_OR_PHYSICAL_RUNTIME — work that genuinely requires a human, physical device, protected workstation, credential boundary, or environment unavailable to agents.
- UNKNOWN_RUNTIME — required capability or authority is not yet evidenced. Resolve it; do not guess.

For each material work unit record:
- required capability and mutation authority;
- evidence that the capability exists in the chosen runtime;
- preferred execution environment and fallback environment;
- exact inputs/evidence inherited from prior lanes;
- expected artifact/proof returned;
- dependencies and collision surface.

PLACEMENT RULES
- Never hand local agents work that the current ChatGPT/provider runtime can safely complete inside P04's planning/recovery/durability authority when doing it now closes a dependency, establishes provider truth, updates the canonical plan, or prevents rediscovery.
- Consume dependency-ready CURRENT_CHAT_RUNTIME and CONNECTED_PROVIDER planning/evidence work before emitting downstream local-agent packets when that materially reduces uncertainty or duplicated work.
- P04 remains PLAN / DISTRIBUTE. Runtime partition does not turn P04 into the application-implementation owner. Code/product implementation still routes to P07 or the canonical implementation owner unless the active prompt separately authorizes that mutation.
- Never assign local-only filesystem/shell/toolchain work to the ChatGPT/web runtime merely because the plan can describe it.
- Never ask the operator to shuttle evidence between runtimes when an available connector/provider/manifest can carry it.
- A local-agent handoff must inherit exact provider/repository/Drive evidence already established here: repository, branch/default head, PR state, canonical plan revision/path, artifact/provider identity, relevant URLs/IDs, blockers, and proof ceiling. Do not require the local agent to rediscover known facts unless freshness rules require revalidation.
- UNKNOWN_RUNTIME is an owner-resolution gate, not permission to invent capability.
- Runtime placement precedes dependency-graph width and adapter selection. The adapter ladder is evaluated only after execution ownership is established.

RUNTIME PARTITION OUTPUT
Before LAUNCH ORDER, emit one compact table:
Work unit | Execution environment | Required capability | Evidence | Execute now? | Dependency/output seam

The PARALLEL DISPATCH MANIFEST must preserve the placement decision so downstream executors can distinguish current-runtime/provider work from local-agent work and cannot silently reassign it.
```

### Internal mechanism changes required from the local Cursor lane

Cursor/local implementation must update the smallest existing canonical owners rather than merely pasting the draft into P04:

1. **Prompt registry:** strengthen canonical P04 in `docs/prompts.json` (P04 currently has no override in `registry/prompts/prompt-overrides.v1.json`; do not create one without a repository reason).
2. **Dispatch contract:** extend `harness/contracts/prompt-parallel-dispatch.v1.json` with the minimum typed lane metadata needed to preserve execution placement. Preferred minimal fields:
   - `execution_environment` using the six classes above;
   - `required_capabilities` as a typed list;
   - `evidence_inputs` as durable references already established upstream.
   Reuse existing `adapter`, `launch`, `expected_artifacts`, and `convergence_owner` rather than duplicating them.
3. **Semantic/non-weakening coverage:** add/protect a P04 planning capability such as `planning.runtime_partition` in the existing semantic capability owners and update P04's accepted capability profile through the repository's normal migration/baseline path.
4. **Focused regressions:** preserve current P04 parallel-dispatch behavior and add:
   - negative: ChatGPT/provider evidence is available, but P04 punts that inspection/durability work to a local agent without consuming it;
   - negative: local filesystem/toolchain-only work is assigned to the ChatGPT/web runtime;
   - positive: current runtime establishes provider/Drive truth and persists plan evidence, then a local lane inherits those exact refs;
   - positive: P04 performs runtime partition without stealing P07's implementation ownership.
5. **Registry/build parity:** run the canonical Prompt Kit builders and required tests; do not hand-edit generated public HTML.
6. **Public-facing website:** regenerate/publish the Prompt Kit from canonical sources so the public P04 surface contains the strengthened runtime-partition behavior. Website text is derived evidence, never the source authority.

### Non-weakening acceptance gate

The local Cursor lane fails if it:
- shortens P04 by deleting existing dependency, parallelism, durability, collision, manifest, or portability semantics without equivalent proven coverage;
- implements only prose while leaving the dispatch schema unable to preserve execution placement;
- updates only the generated website;
- makes "current runtime" synonymous with "local runtime";
- treats runtime partition as permission for P04 to implement work owned by P07;
- leaves PS-0004 as a Drive-only idea with no repository enforcement.

Completion requires canonical registry + internal typed mechanism + focused regression + generated/public Prompt Kit parity, with exact donor/destination SHAs and proof ceiling recorded.

## P05 serialized-planner runtime partition — same shared capability, serialized projection

P05 is a second required consumer of PS-0004. The runtime taxonomy and ownership rule must have one shared semantic owner; P04 and P05 project that shared capability differently:

- **P04:** partition runtime ownership before dependency graph width, adapter selection, and parallel dispatch manifest generation.
- **P05:** partition runtime ownership before ordered launch-pack construction, then carry the placement through each serialized sprint panel and handoff.

### Exact P05 draft insertion — preserve ordered-pack semantics

Insert after P05's repository/context preflight and before its factoring/launch-order construction (or the nearest semantically equivalent location if the canonical prompt moves):

```text
RUNTIME PARTITION / EXECUTION PLACEMENT — REQUIRED
Before building the serialized sprint pack, classify every material work unit by the runtime that can actually perform it. Use the shared planning runtime classes:

- CURRENT_CHAT_RUNTIME
- CONNECTED_PROVIDER
- LOCAL_AGENT_RUNTIME
- CI_OR_REMOTE_RUNNER
- OPERATOR_OR_PHYSICAL_RUNTIME
- UNKNOWN_RUNTIME

Do not treat "serialized" as "local." Sequence and execution environment are separate dimensions.

PLACEMENT RULES
- Complete safe dependency-ready CURRENT_CHAT_RUNTIME and CONNECTED_PROVIDER planning/evidence/durability work that P05 is authorized to perform when doing so closes a dependency, establishes current provider truth, or prevents downstream rediscovery.
- Do not manufacture a local-agent sprint for work already completed in the current runtime; instead pass its exact artifact/evidence forward as an input to the next serialized lane.
- Do not assign filesystem/shell/toolchain-only work to CURRENT_CHAT_RUNTIME merely because the current agent can describe the commands.
- P05 remains PLAN / PACK. It does not become the implementation owner; executable repository/product work remains assigned to P07 or the canonical implementation owner.
- UNKNOWN_RUNTIME is a bounded owner-resolution gate, not a guess.
- Preserve exact provider/repository/Drive evidence across the serialized chain so later panels consume prior proof instead of restarting discovery.

SERIALIZED RUNTIME OUTPUT
Before LAUNCH ORDER, emit:
Work unit | Execution environment | Required capability | Evidence | Already executed here? | Ordered dependency/output seam

Every sprint panel that still represents executable successor work must include:
EXECUTION ENVIRONMENT
REQUIRED CAPABILITIES
INHERITED EVIDENCE
RUNTIME HANDOFF

The final ordered pack must distinguish:
1. work already completed by the current ChatGPT/provider runtime;
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
