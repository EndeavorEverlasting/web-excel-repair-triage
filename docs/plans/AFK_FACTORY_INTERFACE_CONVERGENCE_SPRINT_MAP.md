# AFK Factory Interface Convergence Sprint Map

**Shared convergence ID:** `AFK-FACTORY-CONVERGENCE-2026-09-22`
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Repository role:** Prompt Kit / AFK Agent Flow — human↔AFK interface foundation
**Planning floor:** `main@5aca914e8026702844201fb9026b28ee54fbb08d`
**Canonical cross-repository plan:** `EndeavorEverlasting/TokenCorridor` → `plans/active/AFK-FACTORY-CONVERGENCE.md` + `plans/active/AFK-FACTORY-CONVERGENCE.plan.json` (material floor `afbc796f6292d13888975699329ad188b86d3ee5`, current observed `main@4d20a69f3f3e518ec9ccb401555ec6ee2cc2a661`)
**AgentSwitchboard companion plan:** `ASB-2026-09-TOKEN-CORRIDOR-COMPETITIVE-ARCHITECTURE` (PR #347 integrated; current observed `main@2b2d5dfc9aa11ca8bab44137984a97fea4bd12db`)
**Destination invariant (canonical):** **TokenCorridor is the destination product and canonical convergence repository for Prompt Kit / AFKAF and AgentSwitchboard; the current three-repository split is migration topology, not permanent product boundary.** Logical ownership survives physical consolidation. See canonical plan for M0–M5 phases, authority-transfer gates, and donor dispositions.
**Local AFK identity authority:** `harness/contracts/operant-product-identity.v1.json` on `main@5aca914e8026702844201fb9026b28ee54fbb08d` now targets `EndeavorEverlasting/TokenCorridor` with state `created-convergence-authority-cutover-unproven`; this repository remains current donor authority until per-capability cutover gates pass.
**Floor freshness semantics:** pinned SHAs are material integration floors; later `main` descendants remain current when they contain the floor and governing content is present. This companion file cannot certify another repository's freshness: every execution must refresh TokenCorridor/AgentSwitchboard provider truth and use ancestry plus current-content checks before relying on their plans.

## 0. Destination product and repository-convergence invariant (canonical)

**TokenCorridor is the destination product and canonical convergence repository for Prompt Kit / AFKAF and AgentSwitchboard.** The current three-repository layout is **migration topology**, not permanent product boundary.

Logical boundaries survive physical consolidation:

- **Prompt Kit / AFKAF** — human↔AFK interface semantics, prompt/workflow meaning, continuation semantics, evidence/authority presentation, operator-facing topology behavior (remains front door; not hidden or discarded).
- **TokenCorridor** — unified product identity, convergence program, bounded decision/successor-transition seam, destination packaging/integration boundary.
- **AgentSwitchboard** — execution readiness, adapter selection, authority enforcement at dispatch, normalized receipts, validation/integration evidence, proof ceilings (preserved logical ownership; physical ASB capabilities migrate into TokenCorridor per M3; compatibility repo/package retained only while callers/installers require it).
- **FirstMate / FrontierAgent / other runtimes** — runtime substrates/adapters behind pinned upstream/fork + adapter boundaries by default; selective extraction requires measured evidence.

The accepted FirstMate ↔ AgentSwitchboard ↔ Prompt Kit protocol remains an **internal contract boundary**; it must not be interpreted as requiring Prompt Kit and AgentSwitchboard to remain separate Git repositories or separate end-user products. Repository consolidation changes packaging/authority, not semantic contracts.

### Donor disposition (canonical pointer)

- **web-excel-repair-triage:** extract Prompt Kit/AFKAF product capabilities into TokenCorridor; retain Excel/OOXML repair-specific application behavior in Triage. Do not move Excel functionality merely because Prompt Kit currently lives beside it.
- **AgentSwitchboard:** migrate execution/proof control-plane capabilities into TokenCorridor behind preserved contracts/module boundaries; retain standalone compatibility repository/package only while external callers/installers/migration proof require it.
- **Runtimes:** keep FirstMate, FrontierAgent, etc. as pinned upstream/fork + adapter integrations by default.

### Migration phases — M0–M5 (canonical pointer)

Canonical `repositoryConvergencePhases` lives in `EndeavorEverlasting/TokenCorridor` → `plans/active/AFK-FACTORY-CONVERGENCE.plan.json`:

- **M0 — Inventory and authority map:** enumerate Prompt Kit/ASB capability owners, schemas, generators, tests, workflows, release/install surfaces, external callers with dispositions (`MIGRATE_TO_TOKENCORRIDOR` / `RETAIN_IN_DONOR` / `COMPATIBILITY_FACADE` / `ADAPTER_ONLY` / `RETIRE_AFTER_CUTOVER` / `DEFER_WITH_OWNER`).
- **M1 — Destination package skeleton:** explicit TokenCorridor module/package boundaries for interface / decision / execution-proof without duplicated authority.
- **M2 — Prompt Kit extraction:** non-Excel Prompt Kit/AFKAF capabilities run from TokenCorridor with parity proof; Triage retains Excel/OOXML domain.
- **M3 — AgentSwitchboard convergence:** ASB execution/proof capabilities run from TokenCorridor with contract/adapter/installer/runtime/receipt parity.
- **M4 — Authority cutover:** TokenCorridor canonical for migrated capabilities; donors downgraded to retained-domain/compatibility/archive.
- **M5 — Transitional cleanup:** retire sync/mirroring/cross-repo transport only when no compatibility need remains.

### Authority-transfer gate (canonical pointer)

A donor capability remains authoritative until **all** are proven (see canonical `destinationContract.authorityTransferGate`):

1. exact capability/source inventory;
2. explicit TokenCorridor destination module/package owner;
3. deterministic behavior and protected regression parity;
4. caller rewiring or compatibility facade;
5. integration into TokenCorridor `main`;
6. explicit donor authority downgrade.

Until then: **integration by protocol is the migration mechanism; it is not the final packaging decision.**

### Canonical plan path

`EndeavorEverlasting/TokenCorridor` → `plans/active/AFK-FACTORY-CONVERGENCE.md` and `plans/active/AFK-FACTORY-CONVERGENCE.plan.json` (material floor `afbc796f6292d13888975699329ad188b86d3ee5`). TokenCorridor is the canonical cross-repository convergence authority. This repository's identity contract remains authoritative for current Prompt Kit/AFK Agent Flow donor status until cutover. This companion is a pointer/coordination surface and never certifies external-plan freshness without a provider refresh.

## 1. Product boundary

Prompt Kit is the **front door of the software factory**.

It owns the boundary where a human goal becomes AFK-operable structure:

- prompt/workflow discovery and identity;
- intent routing and prompt selection;
- work-item progression;
- evidence-state and proof language;
- authority/user-only gate presentation;
- continuation semantics;
- machine-readable handoff to the next execution owner;
- operator-facing topology/visual interaction semantics.

The factory is not AFK when Prompt Kit finishes a step by making the operator:

- choose the obvious next prompt;
- create another chat;
- paste a lane prompt or manifest;
- shuttle artifacts/receipts between agents;
- schedule a known successor worker;
- reapprove an unchanged action that already carries explicit authority.

True user-only decisions remain visible, typed, durable, and resumable.

## 2. Current closeout floor

Prompt Kit can close current work independently of AgentSwitchboard and TokenCorridor implementation.

Current integrated mainline owners:

- **P55 repository bootstrap:** PR #623 merged; PR #638 closed the recovery ledger. Treat current `main` as authority, not the historical feature branch.
- **P143 Repository Convergence Planner:** PR #640 integrated the reviewed contracts; PR #632 is closed/superseded donor evidence.

Current active convergence lanes to refresh before mutation:

- **PR #626** — issue-centered AFK/P66 progression;
- **PR #600** — routing decision / Evidence Spine continuation;
- **PR #630** — prompt findability and agent readability.

Adjacent active writers **#636** and **#641** must be collision-checked before any M2 registry/generator/test-floor mutation. They are not substitutes for the canonical integrated P55/P143 owners.

Older predecessor writers are floor-clearing candidates, not parallel authorities. The closeout owner must reconcile unique behavior into one refreshed floor rather than independently fixing every historical PR forever.

### Prompt Kit closeout output

Publish an exact integrated `main` identity proving:

1. one current P55 repository-creation owner;
2. one current P66/work-progression owner;
3. one unambiguous Repository Convergence Planner identity;
4. current Evidence Spine continuation/routing semantics;
5. prompt discovery/findability points at current identities;
6. generated Prompt Kit parity and deterministic floor pass;
7. predecessor writers are contained, transferred, deliberately preserved, or closed.

That integrated floor becomes Prompt Kit's input to the shared convergence program.

## 3. Cross-repository interface contract

Prompt Kit emits interface truth; it does not directly own TokenCorridor judgment logic or AgentSwitchboard execution.

Minimum machine-readable handoff semantics:

```text
interface_state
work_item / invocation identity
current prompt/workflow owner
evidence state
authority state + provenance
candidate successor / unresolved judgment
required payload/artifact references
proof ceiling
stable correlation identity
```

### State dimensions must remain orthogonal

**Evidence:** how a fact/value is known.
**Authority:** whether an action is permitted and by what grant/policy.
**Execution:** what happened when an action was attempted.

No downstream requirement may silently promote one dimension into another.

Examples:

- `visibility=public / INFERRED` ≠ authorization to create a public repository;
- namespace availability ≠ product-name approval;
- valid prompt routing ≠ execution success;
- high model confidence ≠ permission.

## 4. Successor behavior

The intended AFK route is:

```text
Prompt Kit interface resolution
        ↓
typed continuation / bounded-decision request
        ↓
TokenCorridor
        ↓
typed successor transition
        ↓
AgentSwitchboard execution request
        ↓
runtime / adapter / worker
        ↓
execution + validation receipt
        ↓
Prompt Kit Evidence Spine
        ↓
continue / recover / user-only / complete
```

Prompt Kit remains the semantic owner of what continuation means. TokenCorridor and AgentSwitchboard are execution collaborators, not replacements for that interface contract.

## 5. Visual frontier — Prompt Topology → Factory Topology

Prompt Kit already has an integrated visual substrate that should be **extended, not restarted**:

- Phase A: renderer-neutral semantic topology;
- Phase B: deterministic 3D projection and spatial stability;
- Phase C: immersive read-only viewer.

Durable owners include:

- `artifacts/prompt-topology/topology.v1.json`;
- `artifacts/prompt-topology/projection-3d.json`;
- `artifacts/prompt-topology/projection-state.v1.json`;
- `harness/prompt-topology/phase-c-viewer.v1.json`;
- `Outputs/prompt-topology-viewer/index.html` as generated runtime artifact.

### Existing visual doctrine remains binding

Semantic graph/state is canonical.
Projection coordinates are derived.
The viewer is read-only presentation.

Do not infer semantic relations from 3D proximity or mutate canonical state because a visual layout looks better.

### Next visual frontier

Generalize the same doctrine into **Factory Topology**.

The viewer should eventually project four typed planes:

1. **Interface — Prompt Kit**
   - prompt;
   - workflow;
   - work item;
   - route;
   - evidence state;
   - authority gate;
   - continuation.

2. **Decision — TokenCorridor**
   - decision request;
   - decision receipt;
   - engine selection;
   - confidence/abstention;
   - action fingerprint;
   - successor transition.

3. **Execution — AgentSwitchboard**
   - execution request;
   - adapter;
   - run;
   - worker/worktree;
   - runtime receipt.

4. **Proof**
   - validator;
   - artifact;
   - check;
   - blocker;
   - integration;
   - main containment;
   - proof ceiling.

Candidate cross-plane relations:

`ROUTES_TO`, `COMPILES_TO`, `REQUIRES`, `AUTHORIZED_BY`, `DISPATCHES`, `EXECUTES`, `PRODUCES`, `VALIDATED_BY`, `CONTINUES_TO`, `BLOCKED_BY`, `SUPERSEDES`, `CORRELATES_WITH`.

## 6. Interaction language to preserve

The user's existing Prompt Universe / factory visualizer intent remains the target interaction language:

- sector/plane hover and focus;
- camera drill-down;
- selection with exact evidence inspection;
- neighbor and path highlighting;
- search as spatial navigation;
- stable identity across refreshes;
- cross-plane route tracing;
- filters for evidence / authority / execution / blocker / proof;
- opportunity/gap highlighting;
- accessible non-3D fallback.

The visualizer must never become the only way to understand or operate the factory.

## 7. First cross-repository tracer slice

Choose one Prompt Kit work item whose continuation reaches outside Prompt Kit.

Prove:

1. Prompt Kit emits typed interface/authority state.
2. TokenCorridor receives the state under the same correlation identity.
3. TokenCorridor returns a deterministic or bounded successor transition.
4. AgentSwitchboard receives/executes the transition through an existing execution contract.
5. the execution/validation receipt returns to Prompt Kit;
6. Evidence Spine resolves the next state;
7. Factory Topology can render the same path from typed artifacts without special-case prose parsing.

The visual rendering may follow the contract proof; correlation/schema decisions must anticipate it from the beginning.

## 8. Parallel closeout and floor clearing

Three lanes may run concurrently:

- **Prompt Kit closeout** — this repository;
- **AgentSwitchboard closeout** — its OSS-first architecture plan;
- **floor clearing** — retire superseded writers without mutating active closeout owners.

The floor lane may report unique predecessor behavior into this closeout lane. It must not independently rebase, rewrite, or close the canonical current writer.

## 9. Non-goals

This plan does not:

- create another crew scheduler;
- make Prompt Kit an execution-adapter runtime;
- move Prompt Kit semantic truth into TokenCorridor;
- turn the visualizer into a source of authorization;
- reopen Prompt Topology Phase A/B/C;
- introduce behavioral telemetry without its existing privacy/admission gates;
- force NodeWeaver into the visualizer;
- require paid Jev, Not Diamond, LangSmith, Vercel, Factory, Cursor Cloud Agents, or another managed product.

## 9A. Unresolved prompt-product continuity — Private Tutor and Repository Grill

These two operator intents are material Prompt Kit successor work and must survive PK-C0 floor clearing. They are **not** satisfied merely because adjacent grilling or teaching behavior exists.

### Private Tutor continuity

Current registry truth:

- **P96 — Stateful Socratic Technical Tutor Workspace** exists and owns stateful Socratic technical teaching, active retrieval, practical exercises, verified mastery, and a repository data-structure learning grill.
- **P98 — Teach Workspace Protocol Bootstrapper** establishes repository-local `.teach/` state and explicitly permits version-controlled learning state when repository policy/data sensitivity permit.
- The current P96/P98 persistence model therefore does **not** by itself satisfy a private/local tutor requirement where learner state, mistakes, uncertainty, reasoning history, mastery records, and learning progress must remain non-public and non-repository-tracked.

Required boundary:

- preserve P96's useful teaching mechanics and evidence-grounded instruction;
- do not silently promote private learner state into Git/GitHub or shared project truth;
- resolve the canonical private/local persistence owner before changing P96/P98 identity or storage behavior;
- keep repository facts/resources separable from learner-specific state so a technical lesson can be grounded in repo truth without turning the repo into the learner diary.

The existing `conversation_repository_promotion_contract` in `harness/contracts/prompt-kit-cross-device-access.v1.json` is the mandatory graduation gate for any conversation-derived repository change. It forbids raw learning state from becoming repository truth, but it is **not** proof that the current `.teach/` storage model is private/local.

### Repository Grill continuity

The intended Repository Grill is distinct from all of these existing surfaces:

- **P65** grilling selects the right Prompt Kit route.
- **P96** Grill-Me-style mode teaches repository data structures to the learner.
- the tracked external **Matt Pocock `grill-me`** resource supplies a one-question-at-a-time interrogation discipline.

The unresolved Repository Grill product behavior is:

1. inspect current repository/provider evidence before asking the operator factual questions;
2. interrogate one unresolved feature/architecture/product decision at a time;
3. use the external Grill-Me discipline when available, without making that external skill the canonical Prompt Kit identity;
4. derive candidate repository upgrades from the interview;
5. keep operator knowledge state, uncertainty, misconceptions, reasoning history, preferences unrelated to the repository, and raw dialogue private;
6. promote only repo-specific, impersonal requirements/decisions/invariants/acceptance gates through the existing conversation→repository promotion contract;
7. write accepted upgrades into the smallest canonical repository owner rather than a parallel diary/report;
8. leave rejected, unresolved, or user-only decisions explicitly typed instead of manufacturing repository truth.

### Identity decision gate

This is a **blocking PK-C0.5 phase**, not optional follow-up. Do **not** allocate a new prompt ID merely from this plan. After PK-C0 establishes the refreshed Prompt Kit registry floor, the Prompt Kit product-identity/privacy lane must run prompt-identity/overlap review against P04/P14/P65/P95/P96/P98 and current external-skill routing before PK-C1 begins. The result must either:

- strengthen an existing canonical owner without breaking its established job; or
- register one distinct Repository Grill identity with focused routing/privacy/promotion regression tests.

For the Private Tutor requirement, the same review must decide whether private/local persistence is a mode of P96/P98 or requires a separate identity. The decision must be driven by ownership and storage semantics, not prompt-count convenience.

## 10. Local execution phases

### PK-C0 — close current Prompt Kit floor
Reconcile the active P55/P66/P143/Evidence-Spine/findability owners and integrate one current floor.

### PK-C0.5 — resolve Private Tutor + Repository Grill identity/storage contract

**Owner:** Prompt Kit product-identity/privacy lane.
**Dependency:** PK-C0 exact integrated Prompt Kit main floor.
**Canonical output:** `docs/plans/PROMPT_TUTOR_GRILL_IDENTITY_DECISION.md`.

Execute:

1. run current prior-art/identity review for **private local Socratic tutor** against P96/P98 plus P04/P14/P95 and current upstream teaching resources;
2. run current prior-art/identity review for **Repository Grill → repo upgrade** against P65/P96 plus P04/P14/P95 and the tracked external `grill-me` resource;
3. decide for each requirement whether to STRENGTHEN an existing owner or ADD a distinct identity, with exact ownership rationale;
4. for the Tutor, choose a private/local persistence owner that keeps learner state, mistakes, mastery history, and reasoning outside repository-tracked truth;
5. for Repository Grill, bind candidate-upgrade promotion to `conversation_repository_promotion_contract` and name the smallest canonical repository targets it may update;
6. write the decision artifact above with routing changes, owned/forbidden scope, focused privacy/promotion/search regressions, lifecycle disposition, and exact implementation successor.

**Validation/exit gate:** the decision artifact is tracked on the refreshed floor; both operator intents have one unambiguous canonical owner/route and storage/promotion boundary; no unresolved overlap with P65/P96/P98 remains; any ADD/STRENGTHEN implementation is explicitly queued with focused regressions; and PK-C1 remains blocked until this decision is integrated.

### PK-C1 — freeze interface-transition contract
**Dependency:** PK-C0.5 integrated. On that resolved prompt-identity floor, define the minimal typed interface state that TokenCorridor consumes.

### PK-C2 — machine continuation proof
Prove a non-user-only successor can leave Prompt Kit without operator prompt/chat/payload scheduling.

### PK-C3 — cross-repository receipt return
Consume a real AgentSwitchboard execution/validation receipt and resolve continuation.

### PK-C4 — Factory Topology adapter
Add a renderer-neutral adapter that converts the cross-repository typed artifacts into a factory-topology view model while preserving Prompt Topology's read-only projection doctrine.

## 11. Acceptance

Prompt Kit's repository-local convergence is ready to join TokenCorridor when:

- current active prompt identities are unambiguous, including an integrated PK-C0.5 decision for Private Tutor and Repository Grill ownership/routing;
- the deterministic floor passes at the exact integrated head;
- interface/evidence/authority/execution dimensions are mechanically distinct;
- successor transitions are machine-addressable;
- the ordinary route does not require human scheduling;
- the visual projection consumes typed artifacts rather than parsing agent prose;
- this plan points to the exact integrated Prompt Kit floor.

## Proof ceiling

This plan is repository-local convergence intent. It does not prove TokenCorridor or AgentSwitchboard runtime integration, live AFK continuation, or Factory Topology runtime behavior.

## Next action

Owner: Prompt Kit closeout lane.

Refresh current provider/main truth; treat integrated P55 (#623/#638) and P143 (#640; #632 superseded) as mainline floor, reconcile the still-active #626/#600/#630 lanes plus collisions from #636/#641, and publish one integrated Prompt Kit floor. Then execute PK-C0.5: run prior-art/identity review for the Private Tutor and Repository Grill, write and integrate `docs/plans/PROMPT_TUTOR_GRILL_IDENTITY_DECISION.md`, and only then begin PK-C1.
