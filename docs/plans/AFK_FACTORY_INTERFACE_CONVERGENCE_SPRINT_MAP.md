# AFK Factory Interface Convergence Sprint Map

**Shared convergence ID:** `AFK-FACTORY-CONVERGENCE-2026-09-22`
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Repository role:** Prompt Kit / AFK Agent Flow — human↔AFK interface foundation
**Planning floor:** `main@c97718247e7b14544d198035dd3cdc07725545a8`
**Canonical cross-repository plan:** `EndeavorEverlasting/TokenCorridor` → `plans/active/AFK-FACTORY-CONVERGENCE.plan.json` (TokenCorridor PR #1)
**AgentSwitchboard companion plan:** `ASB-2026-09-TOKEN-CORRIDOR-COMPETITIVE-ARCHITECTURE` (AgentSwitchboard PR #346)

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

Current active convergence owners to refresh before mutation:

- **PR #632** — Repository Convergence Planner / P143;
- **PR #623** — P55 repository bootstrap;
- **PR #626** — issue-centered AFK/P66 progression;
- **PR #600** — routing decision / Evidence Spine continuation;
- **PR #630** — prompt findability and agent readability.

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

## 10. Local execution phases

### PK-C0 — close current Prompt Kit floor
Reconcile the active P55/P66/P143/Evidence-Spine/findability owners and integrate one current floor.

### PK-C1 — freeze interface-transition contract
On the integrated floor, define the minimal typed interface state that TokenCorridor consumes.

### PK-C2 — machine continuation proof
Prove a non-user-only successor can leave Prompt Kit without operator prompt/chat/payload scheduling.

### PK-C3 — cross-repository receipt return
Consume a real AgentSwitchboard execution/validation receipt and resolve continuation.

### PK-C4 — Factory Topology adapter
Add a renderer-neutral adapter that converts the cross-repository typed artifacts into a factory-topology view model while preserving Prompt Topology's read-only projection doctrine.

## 11. Acceptance

Prompt Kit's repository-local convergence is ready to join TokenCorridor when:

- current active prompt identities are unambiguous;
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

Refresh current provider/main truth, reconcile the active #623/#626/#632/#600/#630 ownership stack, and publish one integrated Prompt Kit floor. Then update this plan with that exact main SHA before PK-C1 begins.
