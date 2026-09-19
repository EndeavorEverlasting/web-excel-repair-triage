# Prompt Execution Evidence Spine — Canonical Sprint Map

**Status:** TRACKED / WAVES 0–2 INTEGRATED ON MAIN / PLANNING MAP INTEGRATED VIA #471
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Planning floor:** refreshed `main@3644dd3bdf2f89dccfb07f554f753c93c917e65e` (provider refresh 2026-09-19)
**Canonical strategic predecessor:** `harness/prompt-topology/POST_PHASE_C_STRATEGIC_SCOUT.md`
**Required P95 architecture output:** `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md` (INTEGRATED via #473)

This file is the durable dependency map for the Prompt Execution Evidence Spine and frictionless Prompt Kit continuation work. It does not replace the P95 architecture decision.

## Requested outcome

Move Prompt Kit from a human-only copy/paste helper toward a frictionless continuation system in which:

- human keyboard/hotkey/clipboard use remains a valid zero-ceremony fallback;
- agent-native execution can ask for the next applicable Prompt Kit action without manually browsing the catalog;
- an agent terminal claim is treated as a completion candidate when lifecycle gates remain;
- dispatch destination/evidence is recorded only to the degree actually observable, with `unknown` valid rather than forcing operator classification;
- repeated corrective behavior becomes durable, git-friendly evidence and can graduate into agent-ready work without turning ordinary prompt reuse into failure telemetry;
- route, usage, outcome, recovery, storage/privacy, and parallel-dispatch owners are reconciled rather than replaced by a new universal event bus.

## Fresh evidence floor

Current `main` already contains:

- Prompt Topology Phase C closeout and the post-Phase-C strategic scout;
- merged outcome classification/receipt semantics (`P99` semantic owner, `P115` recovery/coordinator boundary);
- Prompt Kit privacy/storage contracts;
- bounded local storage lifecycle implementation from PR #466;
- the Operant v0.8.0 release merge from PR #469;
- existing feedback-to-AFK routing capability and trigger surfaces;
- current operational prompt contracts and generated Prompt Kit;
- **Wave 0 / Panel 1:** autonomous parallel dispatch floor from PR #467 (`a1e9caa1`) plus observed-interval repair PR #477 (`d8ef87eb`);
- **Wave 1 / Panel 2:** `EVIDENCE_SPINE_ARCHITECTURE.md` from PR #473;
- **Wave 2 / Panel 3:** runtime collision matrix (#474) and minimal Evidence Spine runtime adapters (#475).

Provider refresh also identifies two remaining donor lanes that stay evidence/dependencies until architecture-bounded salvage:

1. **PR #450 — routing control plane.** Valuable route/receipt semantics; reconcile only where P95 preserves ownership.
2. **PR #431 — Prompt Finder observation corpus / usage-feedback lane.** Valuable bounded observation semantics; reconcile only where P95 preserves ownership.

`harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md` is present on current `main`. Phase D, a new event bus, hosted telemetry, and competing evidence models remain forbidden.

## Proof typing

Use these states without promotion:

`PLANNED/DESIGNED -> TRACKED -> IMPLEMENTED -> WIRED/REACHABLE -> VALIDATED -> INTEGRATED -> DEPLOYED -> OBSERVED`

A branch, PR, schema, passing local unit test, or static artifact never proves a stronger state by itself.

## Collision ownership

- **PR #467/#477 own the integrated parallel-dispatch floor on `main`.** Do not duplicate its prompt-parallel-dispatch contract, launcher/adapter, tests, or generated Prompt Kit changes in another lane.
- **P95 architecture owns the state-owner/identity decision** via integrated `EVIDENCE_SPINE_ARCHITECTURE.md`. Successors must not create a fourth route/usage/outcome event model or assert that one universal lifecycle envelope is required.
- **PR #450 is historical donor evidence for routing-control-plane concepts.** The current Lane A implementation owner is the thin route-receipt seam in `scripts/evidence_spine_runtime.py`; PR #596 is the bounded salvage/integration carrier. Do not revive #450's mutable router/state/eval-registry implementation.
- **PR #431 remains the donor/owner for Prompt Finder observation concepts.** Do not independently recreate its observation corpus before adapting only P95-preserved concepts.
- **Merged outcome semantics remain authoritative on `main`.** Do not fork P99/P115 outcome and recovery classification into a competing classifier.
- **PR #466/current `main` owns local retention/cleanup.** Evidence/feedback work must use the canonical bounded lifecycle rather than create unbounded local history.
- **Generated `web/prompt-kit/index.html` is builder-owned.** Never hand-edit it.

## Launch order

### Wave 0 — Panel 1: Autonomous Dispatch Floor Repair & Mainline Convergence

**Status:** INTEGRATED on `main` via #467 (`a1e9caa1`) and post-merge review repair #477 (`d8ef87eb`).

**Goal:** repair PR #467's remaining regressions/review gaps, prove its dispatch artifact is actually consumed by a deterministic adapter/validator path, preserve pre-existing P07 metadata contracts, and integrate the exact green head into current `main` when gates allow.

**Hard dependencies:** refreshed current `main`; exact refreshed PR #467 head, checks, and current review threads.

**Safe parallel work:** focused diagnosis/tests may run concurrently only when they do not write the same registry, contract, generated, workflow, or PR-owned surfaces.

**Expected artifacts/proof:** repaired #467 head; focused regression tests; dispatch manifest/receipt consumer proof; generated parity where touched; required CI green; review disposition; merge/mainline containment proof.

**Proof ceiling:** repository/CI/mainline integration. No claim that a third-party agent actually consumes Prompt Kit autonomously in production.

Proven repair gates:

- raw P07 `expectedOutput` preserves explicit current-default-branch integration language;
- raw P07 `proofGate` preserves the exact readability/editability-regression guarantee;
- machine-executable dispatch is consumed by `harness/contracts/prompt-parallel-dispatch.v1.json` + `scripts/prompt_parallel_dispatch.py` (`validate|run|verify-receipt`);
- autonomous iteration regressions reject contradictory/no-dispatch instructions;
- `observed_parallelism` is derived from overlapping lane wall-clock intervals, not submission intent.

### Wave 1 — Panel 2: P95 Evidence Spine Architecture & Lifecycle Ownership

**Status:** INTEGRATED on `main` via #473.

**Goal:** execute the already-approved P95 investigation on the refreshed post-Panel-1 floor and write `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`.

**Hard dependency:** Panel 1 integrated, or explicitly blocked with the exact blocked head/evidence incorporated read-only.

**Safe parallel work:** read-only trace reconstruction for the recommendation path, autonomous-repair path, and Phase-D-candidate path may proceed concurrently; one architecture owner writes the final matrix/decision.

**Expected artifacts:** state-owner/identity matrix; lifecycle identity/provenance rules; adapter boundaries; three required traces; thin non-production seam prototypes/failure tests when useful; explicit decision among common lifecycle envelope, adapters-only, or intentional isolation; named disposition for #450/#431; privacy/storage/dedupe/idempotency constraints; successor acceptance map.

**Proof ceiling:** DESIGNED/TRACKED and, for thin prototypes, locally VALIDATED architecture evidence. No production Phase D, hosted telemetry, vector DB, or production migration of #450/#431.

The P95 design must explicitly cover the human and agent paths without adding workflow friction:

- human hotkey/copy/paste remains valid and may record destination as `unknown`;
- authoritative destination is recorded only when a launcher/route owner actually knows it;
- recommendation/dispatch and execution/outcome remain distinct evidence states;
- agent-native “what next?” resolution consumes existing lifecycle evidence rather than requiring the agent to browse the whole Prompt Kit;
- terminal claims become candidates subject to applicable lifecycle/acceptance gates, not unconditional global completion;
- ordinary use is not failure evidence;
- repeated corrective behavior reuses outcome/recovery evidence and privacy bounds rather than raw transcript surveillance.

### Wave 2 — Panel 3: Evidence Spine Runtime & Feedback-to-Ticket Convergence

**Status:** INTEGRATED minimal runtime on `main` via #474 (collision matrix) and #475 (runtime adapters). Lane A route-receipt salvage is implemented through PR #596 using the existing runtime seam; #431 observation salvage remains architecture-bounded.

**Goal:** execute only runtime/integration work admitted by P95, reconcile stale donor PRs instead of duplicating them, and deliver the smallest end-to-end flow from bounded prompt execution evidence to deterministic continuation/recovery and git-friendly recurring-defect work.

**Hard dependencies:** Panel 2 architecture integrated; refreshed current `main`; exact donor heads for #450/#431; merged P99/P115 outcome semantics; local lifecycle owner.

**Coordinator-owned collision surfaces:** any shared lifecycle adapter contract, shared evaluation registry entry, generated Prompt Kit rebuild, and integration order.

**Parallel lanes after P95 freezes interfaces:**

- **Lane A — routing reconciliation:** route receipt ownership is integrated on `main` through PR #596 as `scripts/evidence_spine_runtime.py::build_route_receipt`; it salvages only actor-neutral receipts, destination provenance, and deterministic idempotent identity from #450. The RRB-03 decision successor is `scripts/prompt_routing_decision.py`, which consumes a verified current-revision route receipt plus the canonical merged Prompt Kit registry and emits `prompt-kit.routing-decision/v1` without mutable route state. Prompt dispatch remains an AgentSwitchboard producer responsibility after this decision seam integrates.
- **Lane B — observation reconciliation:** salvage/adapt #431 bounded observation semantics; do not create a new route or outcome classifier and do not store raw prompt/clipboard/transcript data.
- **Lane C — corrective recurrence / finding / ticket bridge:** consume authoritative normalized outcome/correction evidence and produce git-friendly findings plus P115-compatible agent-ready work requests; do not own Prompt Finder capture UI or route transport.

These lanes may run concurrently only after exact file/schema ownership is rechecked against the integrated P95 design. If lanes need the same contract, schema, registry, generated file, workflow, branch, or PR, serialize that shared write under the coordinator.

**Minimum recurrence behavior for Lane C:**

- one ordinary correction is retained as evidence, not automatically ticketed;
- two materially equivalent occurrences may become a suspected recurrence;
- three materially equivalent occurrences across at least two executions normally confirm recurrence, subject to existing outcome-contract owner thresholds;
- canonical P99/P115 thresholds remain authoritative where they are more specific: deterministic contradiction `min=1`, repeated local pattern `min=3`, manual context transfer `min=2`, correction-not-integrated `min=2`, and premature terminal based on terminal claim plus observed safe successor;
- severity overrides may escalate a single high-risk false-completion, destructive, or security event;
- grouping is by underlying contract failure, not textual similarity alone;
- every finding links exact receipt/event/evidence identities and records observed versus inferred semantics;
- duplicate findings accumulate evidence rather than create issue spam;
- ticket generation requires a bounded remediation surface, expected behavior, executable acceptance criteria, and proof requirements;
- acceptance criteria test behavior/regression, not merely wording presence;
- after remediation, recurrence returns the finding to monitoring/reopened state rather than silently declaring the systemic defect solved.

**Minimum continuation/dispatch behavior admitted for implementation:**

- expose one deterministic next-action seam only if P95 selects an owner for it;
- return `continue`, `recover`, `complete`, or equivalent typed disposition based on existing lifecycle/acceptance evidence;
- a required/recovery action supersedes a completion candidate;
- operator interaction is required only for a genuinely operator-only decision or unavailable evidence that cannot be resolved by the environment;
- human clipboard fallback remains usable with zero mandatory metadata entry;
- destination confidence is typed (`authoritative`, `bound/inferred`, `declared`, `unknown`, or P95-selected equivalents) and never fabricated.

**Expected artifacts/proof:** admitted lifecycle adapter(s); reconciled donor behavior from #450/#431 or explicit retirement evidence; recurrence/finding schema or owner-specific extension selected by P95; deterministic compiler/bridge to P115-compatible work requests; fixtures for ordinary use, repeated correction, premature terminal, dedupe, post-fix recurrence, and unknown destination; validation/CI; generated parity if UI/runtime wiring changes; exact mainline integration proof.

**Proof ceiling:** repository/static/runtime tests and observed browser/local evidence only where actually executed. No claim of provider-wide agent adoption, production cross-device sync, hosted Collective Learning, or autonomous real-world destination observation without direct runtime receipts.

## Harness factoring

### Keep / reuse

- `P99` outcome semantics and privacy-bounded classification;
- `P115` work-request/recovery coordination;
- `prompt-kit-feedback-afk-routing` skill/capability/trigger path;
- Prompt Kit local lifecycle/storage owner from PR #466;
- Prompt topology strategic owner and Phase C artifacts;
- existing registry/generator/parity machinery;
- existing repository AI eval framework;
- PR #467 prompt-parallel-dispatch mechanism after repair/integration.

### Reconcile after P95

- PR #450 routing control plane — historical donor only after Lane A salvage; do not wholesale merge;
- PR #431 Prompt Finder observation corpus/usage-feedback work.

### Create only if P95 proves necessary

- minimal lifecycle identity/provenance adapter contract;
- deterministic next-action/continuation resolver;
- git-friendly recurring-correction finding representation;
- finding-to-P115 work-request/ticket bridge;
- focused validators/fixtures for those seams.

### Explicitly do not create yet

- generic universal event bus;
- raw transcript/clipboard telemetry collector;
- hosted telemetry backend;
- Phase D behavioral topology ingestion;
- vector database;
- duplicate Prompt Finder/outcome/recovery classifiers;
- product logic implemented only as prompt prose.

## Application-logic factoring

Application/domain behavior, if admitted after P95, belongs in deterministic code/contracts:

- lifecycle state resolution / completion-candidate state machine;
- next-action decision service;
- routing adapter(s);
- recurrence aggregation and finding state-transition logic;
- ticket/work-request compiler;
- persistence through existing bounded local lifecycle owners;
- Prompt Kit UI/hotkey surfaces only as thin consumers of those services;
- agent/launcher integration only as thin consumers/producers of typed receipts.

Prompt text may instruct an agent to use these operations but must not be the only implementation of them.

## Validation and proof gates by wave

### Panel 1

1. Refresh current `main` and exact #467 head/reviews/checks; reconcile its branch to the required floor without destructive reset.
2. Reproduce current #467 failures against the exact head.
3. Reconcile current review threads; distinguish valid from obsolete findings.
4. Run focused parallel-dispatch/P07 tests and validators.
5. Run Prompt Kit registry/generated parity for touched registry surfaces.
6. Run deterministic test floor and freshness/evidence workflow equivalents.
7. Push exact repaired head, require green PR checks/reviews, merge if authorized and safe.
8. Refresh `main`; prove merge containment and rerun affected owning validation.

### Panel 2

1. Refresh provider/repository truth after Panel 1.
2. Read Phase C closeout/handoff/scout and current outcome/privacy/storage/dispatch contracts.
3. Inspect exact #450/#431 donor diffs against current `main`.
4. Build the three required traces and state-owner/identity matrix.
5. Prototype only seams needed to falsify architecture choices.
6. Write P95 architecture with explicit accepted/rejected alternatives and successor admission gates.
7. Validate any prototype/tests/docs; open PR; reconcile review; merge architecture when green/authorized; prove main containment.

### Panel 3

1. Refresh post-P95 `main` and donor heads.
2. Freeze collision map before writes.
3. Dispatch independent implementation lanes only where file/schema ownership is disjoint.
4. Reconcile donor work onto current owners; never force-carry stale branches wholesale.
5. Implement recurrence/finding/ticket and continuation seams only as admitted by P95.
6. Run focused validators/fixtures, privacy/storage checks, outcome/recovery tests, generated parity, deterministic test floor, and browser/runtime proof where applicable.
7. Integrate dependency-related PRs in dependency order; refresh/revalidate downstream heads after each base move.
8. Prove refreshed default branch contains the exact accepted changes.

## Deferred work

The following remain outside this three-panel map unless the P95 architecture or a later explicit request admits them:

- Phase D Passive Learning / topology behavioral channels;
- Phase E Historical Intelligence;
- serverless cross-device sync phases not required by this evidence-spine seam;
- hosted Collective Learning ingestion;
- network-anonymity claims;
- vector database / NodeWeaver expansion;
- AFK Agent Flow repository extraction/cutover;
- unrelated Prompt Kit visual redesign;
- NTH/Billing or spreadsheet product behavior.

## Contract horizon

| Contract | Owner | Current planning status | Required transition |
| --- | --- | --- | --- |
| Parallel/autonomous dispatch floor | PR #467/#477 / prompt operations | INTEGRATED on main | reuse; do not duplicate in RRB-03 |
| Evidence lifecycle ownership | P95 / Prompt Topology strategy | INTEGRATED via #473 | preserve adapter-only ownership; no universal event bus |
| Routing control plane | Evidence Spine Lane A + RRB-03 decision seam | Route receipts INTEGRATED via #596 / `2d26e7e`; registry-bound decision compiler IMPLEMENTED on `feat/rrb03-routing-decision-r3-20260919` | focused regression + deterministic floor -> exact-head review -> integrate decision seam -> hand off `asb.prompt-dispatch/v1` production to AgentSwitchboard |
| Prompt Finder observation lane | PR #431 donor | IMPLEMENTED on stale/unmergeable branch only | P95 disposition -> reconcile or retire -> validate/integrate |
| Outcome/correction semantics | P99/P115 on main | INTEGRATED | reuse; extend only through owned contracts |
| Local evidence retention/privacy | serverless lifecycle on main | INTEGRATED implementation | reuse and prove new writes remain bounded |
| Recurrence -> finding -> agent-ready work | not yet canonical | PLANNED | P95 owner decision -> implement/validate/integrate |
| Agent-native continuation / completion-candidate seam | not yet canonical | PLANNED | P95 owner decision -> implement/validate/integrate |
| Human clipboard/hotkey fallback | Prompt Kit existing UX | existing usable fallback; destination may be unobservable | preserve zero-metadata path while adding optional/authoritative receipts |
| Provider-wide autonomous adoption | external runtimes/providers | UNPROVEN | actual launcher/provider integrations + observed receipts |

## First executable continuation

**Owner:** RRB-03 Prompt Kit routing-decision lane.

**Dependency:** current `main` contains PR #596 / `2d26e7e` route-receipt salvage and the canonical merged Prompt Kit registry remains loadable through `scripts/build_prompt_kit_registry.py::load_prompt_kit_registry`.

**Action:** validate `scripts/prompt_routing_decision.py` with `tests/test_prompt_routing_decision_prompt.py` and the registered deterministic floor, reconcile exact-head review/CI, and integrate the registry-bound decision seam. Then refresh AgentSwitchboard and compile `asb.prompt-dispatch/v1` only from the integrated decision; Prompt Kit must not impersonate the AgentSwitchboard dispatch producer.

**Completion gate:** the exact decision candidate is green, review-complete, merged to current `main`, and current-main content proves current-registry binding plus route-receipt verification; the successor AgentSwitchboard dispatch phase then owns durable-inbox message construction without crew scheduling or automatic rollover.

## Durability rule

This map is the canonical execution dependency map for the current Evidence Spine effort. If material sequencing, ownership, collision boundaries, acceptance gates, or proof ceilings change, update this tracked file (or the active PR carrying it) before handing execution to another agent. `POST_PHASE_C_STRATEGIC_SCOUT.md` remains the strategic predecessor; `EVIDENCE_SPINE_ARCHITECTURE.md` becomes the architecture authority once P95 integrates it. A repository work-ledger entry may index this map but must not duplicate or replace it.