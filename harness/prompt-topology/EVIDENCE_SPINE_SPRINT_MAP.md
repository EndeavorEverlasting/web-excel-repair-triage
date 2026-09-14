# Prompt Execution Evidence Spine — Canonical Sprint Map

**Status:** TRACKED / ACTIONABLE / NOT YET IMPLEMENTED  
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`  
**Planning floor:** `main@182cde18bf7fdc46f305039b5793eb33698cafa2` (2026-09-13 provider refresh)  
**Canonical strategic predecessor:** `harness/prompt-topology/POST_PHASE_C_STRATEGIC_SCOUT.md`  
**Required P95 architecture output:** `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`  
**Purpose of this file:** durable dependency map and execution order for the Prompt Execution Evidence Spine / frictionless prompt-dispatch work. This file does not replace the P95 architecture decision.

## Requested outcome

Move Prompt Kit from a human-only copy/paste helper toward a frictionless continuation system in which:

- human keyboard/hotkey/clipboard use remains a valid zero-ceremony fallback;
- agent-native execution can ask for the next applicable Prompt Kit action without browsing the catalog manually;
- an agent's terminal claim is treated as a completion candidate when lifecycle gates remain;
- dispatch destination/evidence is recorded only to the degree actually observable, with `unknown` remaining valid rather than forcing operator classification;
- repeated corrective behavior becomes durable, git-friendly evidence and can graduate into an agent-ready work item without turning ordinary prompt reuse into failure telemetry;
- route, usage, outcome, recovery, storage/privacy, and parallel-dispatch owners are reconciled rather than replaced by a new universal event bus.

## Fresh evidence floor

Current main already contains:

- Prompt Topology Phase C closeout and post-Phase-C strategic scout;
- merged outcome classification/receipt semantics (`P99` semantic owner, `P115` recovery/coordinator boundary);
- Prompt Kit privacy/storage contracts;
- bounded local storage lifecycle implementation from PR #466;
- existing feedback-to-AFK routing capability and trigger surfaces;
- current operational prompt contracts and generated Prompt Kit.

Provider refresh also shows three overlapping open lanes that must be treated as evidence/dependencies, not reimplemented from memory:

1. **PR #467 — autonomous parallel dispatch:** current-main based and directly relevant to frictionless agent dispatch, but not green. Current head observed during planning: `fff31c61e84282df2177107257829de0473f5ff5`. CI exposes at least two bounded P07 contract regressions, and two current review threads remain open around executable dispatch consumption and contradiction-resistant tests.
2. **PR #450 — routing control plane:** valuable route/receipt semantics, but the branch is substantially behind current `main`; reconcile only after the P95 ownership decision.
3. **PR #431 — Prompt Finder observation corpus / usage-feedback lane:** valuable bounded observation semantics, but the branch is substantially behind current `main` and currently unmergeable; reconcile only after the P95 ownership decision.

`harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md` did not exist on the planning floor. Phase C explicitly names P95 as the next approved owner and forbids substituting Phase D, a new event bus, hosted telemetry, or another competing evidence model for that investigation.

## Proof typing

Use these states without promotion:

`PLANNED/DESIGNED -> TRACKED -> IMPLEMENTED -> WIRED/REACHABLE -> VALIDATED -> INTEGRATED -> DEPLOYED -> OBSERVED`

A branch, PR, schema, passing local unit test, or static artifact never proves a stronger state by itself.

## Collision ownership

- **PR #467 owns its current parallel-dispatch branch/files until merged or explicitly superseded.** Do not duplicate its prompt-parallel-dispatch contract, launcher/adapter, tests, or Prompt Kit generated changes in another lane.
- **P95 architecture owns the state-owner/identity decision.** Until it lands, no successor may create a fourth route/usage/outcome event model or assert that one universal lifecycle envelope is required.
- **PR #450 remains the donor/owner for routing-control-plane concepts.** Do not independently recreate its route receipt/schema before P95 decides how it should adapt.
- **PR #431 remains the donor/owner for Prompt Finder observation concepts.** Do not independently recreate its observation corpus before P95 decides how it should adapt.
- **Merged outcome semantics remain authoritative on `main`.** Do not fork P99/P115 outcome and recovery classification into a competing classifier.
- **PR #466/main owns local retention/cleanup.** Evidence/feedback work must use the canonical bounded lifecycle rather than creating unbounded local history.
- **Generated `web/prompt-kit/index.html` is builder-owned.** Never hand-edit it.

## Launch order

### Wave 0 — Panel 1: Autonomous Dispatch Floor Repair & Mainline Convergence

**Goal:** repair PR #467's remaining regressions/review gaps, prove its dispatch artifact is actually consumable by a deterministic adapter/validator path, preserve all pre-existing P07 metadata contracts, then integrate the exact green head into current `main` when gates allow.

**Hard dependencies:** current `main`; PR #467 current head/reviews/checks.  
**Safe parallel work:** focused diagnosis/tests may run concurrently if they do not write the same registry/contract/generated surfaces.  
**Expected artifacts/proof:** repaired #467 head; focused regression tests; dispatch manifest/receipt consumer proof; generated parity where touched; required CI green; review disposition; merge/mainline containment proof.  
**Proof ceiling:** repository/CI/mainline integration. No claim that a third-party agent actually consumes Prompt Kit autonomously in production.

Current known repair gates from provider evidence:

- raw P07 `expectedOutput` must preserve explicit current-default-branch integration language;
- raw P07 `proofGate` must preserve the exact readability/editability-regression requirement;
- current review thread: “machine-executable” dispatch must be backed by an actual schema/launcher/validator consumer rather than prose-only compliance;
- current review thread: autonomous iteration regression tests must reject contradictory/no-dispatch instructions, not only assert substring presence.

### Wave 1 — Panel 2: P95 Evidence Spine Architecture & Lifecycle Ownership

**Goal:** execute the already-approved P95 investigation on the refreshed post-Panel-1 floor and write `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`.

**Hard dependency:** Panel 1 integrated or explicitly blocked with exact head/evidence incorporated read-only.  
**Safe parallel work:** read-only trace reconstruction for recommendation path, autonomous repair path, and Phase D candidate path may proceed concurrently; one architecture owner writes the final matrix/decision.  
**Expected artifacts:** state-owner/identity matrix; exact lifecycle identity/provenance rules; adapter boundaries; three required traces; thin non-production seam prototypes/failure tests when useful; explicit decision among common lifecycle envelope, adapters-only, or intentional isolation; named disposition for #450/#431; privacy/storage/dedupe/idempotency constraints; successor acceptance map.  
**Proof ceiling:** DESIGNED/TRACKED and, for thin prototypes, locally VALIDATED architecture evidence. No production Phase D, no hosted telemetry, no vector DB, no production migration of #450/#431.

The P95 design must explicitly cover the human and agent paths without adding workflow friction:

- human hotkey/copy/paste remains valid and may record destination as `unknown`;
- authoritative destination is recorded only when a launcher/route owner actually knows it;
- recommendation/dispatch and execution/outcome remain distinct evidence states;
- agent-native “what next?” resolution must consume existing lifecycle evidence rather than requiring the agent to browse the whole Prompt Kit;
- terminal claims become candidates subject to applicable lifecycle/acceptance gates, not unconditional global completion;
- ordinary use is not failure evidence;
- repeated corrective behavior must reuse outcome/recovery evidence and privacy bounds rather than raw transcript surveillance.

### Wave 2 — Panel 3: Evidence Spine Runtime & Feedback-to-Ticket Convergence

**Goal:** execute only the runtime/integration work admitted by the P95 architecture, reconcile stale donor PRs instead of duplicating them, and deliver the smallest end-to-end flow from bounded prompt execution evidence to deterministic continuation/recovery and git-friendly recurring-defect work.

**Hard dependencies:** Panel 2 architecture integrated; refreshed current main; exact donor heads for #450/#431; merged P99/P115 outcome semantics; local lifecycle owner.  
**Coordinator-owned collision surfaces:** any shared lifecycle adapter contract, shared evaluation registry entry, generated Prompt Kit rebuild, and integration order.  
**Parallel lanes after P95 freezes interfaces:**

- **Lane A — routing reconciliation:** salvage/adapt #450 semantics to the chosen lifecycle seam; do not redesign feedback/outcome semantics.
- **Lane B — observation reconciliation:** salvage/adapt #431 bounded observation semantics; do not create a new route or outcome classifier and do not store raw prompt/clipboard/transcript data.
- **Lane C — corrective recurrence / finding / ticket bridge:** consume authoritative normalized outcome/correction evidence and produce git-friendly findings plus P115-compatible agent-ready work requests; do not own Prompt Finder capture UI or route transport.

These lanes may execute in parallel only after exact file/schema ownership is rechecked against the integrated P95 design. If any lane needs the same contract/schema/registry/generated file, serialize that shared write under the coordinator.

**Minimum recurrence behavior for Lane C:**

- one ordinary correction is retained as evidence, not automatically ticketed;
- two materially equivalent occurrences may become a suspected recurrence;
- three materially equivalent occurrences across at least two executions normally confirm recurrence, subject to the existing outcome contract's stronger/owner-specific thresholds;
- severity overrides may escalate a single high-risk false-completion/destructive/security event;
- grouping is by underlying contract failure, not textual similarity alone;
- every finding links exact receipt/event/evidence identities and records observed vs inferred semantics;
- duplicate findings accumulate evidence rather than creating issue spam;
- ticket generation requires a bounded remediation surface, expected behavior, executable acceptance criteria, and proof requirements;
- acceptance criteria test behavior/regression, not merely wording presence;
- after remediation, recurrence returns the finding to monitoring/reopened state rather than silently declaring the systemic defect solved.

**Minimum continuation/dispatch behavior admitted for implementation:**

- expose one deterministic next-action seam only if P95 selects an owner for it;
- return `continue`, `recover`, `complete`, or equivalent typed disposition based on existing lifecycle/acceptance evidence;
- a required/recovery action supersedes a completion candidate;
- operator interaction is required only for a genuinely operator-only decision or unavailable evidence that cannot be resolved by the environment;
- human clipboard fallback remains usable with zero mandatory metadata entry;
- destination confidence is typed (`authoritative`, `bound/inferred`, `declared`, `unknown` or P95-selected equivalents) and never fabricated.

**Expected artifacts/proof:** admitted lifecycle adapter(s); reconciled donor behavior from #450/#431 or explicit retirement evidence; recurrence/finding schema or owner-specific extension as selected by P95; deterministic compiler/bridge to P115-compatible work requests; fixtures for ordinary use, repeated correction, premature terminal, dedupe, post-fix recurrence, and unknown destination; validation/CI; generated parity if UI/runtime wiring changes; exact mainline integration proof.  
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
- PR #467's prompt-parallel-dispatch mechanism after repair/integration.

### Reconcile after P95

- PR #450 routing control plane;
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
- recurrence aggregation and finding state transition logic;
- ticket/work-request compiler;
- persistence through existing bounded local lifecycle owners;
- Prompt Kit UI/hotkey surfaces only as thin consumers of those services;
- Agent/launcher integration only as thin consumers/producers of typed receipts.

Prompt text may instruct an agent to use these operations but must not be the only implementation of them.

## Validation / proof gates by wave

### Panel 1

1. Reproduce both current #467 CI failures against exact head.
2. Reconcile all current review threads; distinguish valid vs obsolete findings.
3. Run focused parallel-dispatch/P07 tests and validators.
4. Run Prompt Kit registry/generated parity for touched registry surfaces.
5. Run deterministic test floor and freshness/evidence workflow equivalents.
6. Push exact repaired head, require green PR checks/reviews, merge if authorized and safe.
7. Refresh `main`; prove merge containment and rerun affected owning validation.

### Panel 2

1. Refresh provider/repository truth after Panel 1.
2. Read Phase C closeout/handoff/scout and current outcome/privacy/storage/dispatch contracts.
3. Inspect exact #450/#431 donor diffs against current main.
4. Build the three required traces and state-owner/identity matrix.
5. Prototype only seams needed to falsify architecture choices.
6. Write P95 architecture with explicit accepted/rejected alternatives and successor admission gates.
7. Validate any prototype/tests/docs; open PR; reconcile review; merge architecture when green/authorized; prove main containment.

### Panel 3

1. Refresh post-P95 main and donor heads.
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
| Parallel/autonomous dispatch floor | PR #467 / prompt operations | IMPLEMENTED on branch, not green/integrated | repair CI/reviews -> validate -> integrate main |
| Evidence lifecycle ownership | P95 / Prompt Topology strategy | TRACKED, architecture artifact absent | design/prototype -> architecture PR -> integrate |
| Routing control plane | PR #450 donor | IMPLEMENTED on stale branch only | P95 disposition -> reconcile or retire -> validate/integrate |
| Prompt Finder observation lane | PR #431 donor | IMPLEMENTED on stale/unmergeable branch only | P95 disposition -> reconcile or retire -> validate/integrate |
| Outcome/correction semantics | P99/P115 on main | INTEGRATED | reuse; extend only through owned contracts |
| Local evidence retention/privacy | serverless lifecycle on main | INTEGRATED implementation | reuse and prove new writes remain bounded |
| Recurrence -> finding -> agent-ready work | not yet canonical | PLANNED | P95 owner decision -> implement/validate/integrate |
| Agent-native continuation / completion-candidate seam | not yet canonical | PLANNED | P95 owner decision -> implement/validate/integrate |
| Human clipboard/hotkey fallback | Prompt Kit existing UX | existing usable fallback; destination may be unobservable | preserve zero-metadata path while adding optional/authoritative receipts |
| Provider-wide autonomous adoption | external runtimes/providers | UNPROVEN | actual launcher/provider integrations + observed receipts |

## First executable continuation

**Owner:** Panel 1 / PR #467 repair lane.  
**Dependency:** refreshed current `main` and exact PR #467 head.  
**Action:** preserve the branch, reproduce the failing P07 metadata/proof tests and inspect current review threads; repair the existing owner rather than opening a duplicate parallel-dispatch implementation; then run its focused validator/tests and the repository deterministic/freshness gates.  
**Completion gate:** exact repaired #467 head is green, review gaps are dispositioned, and safe authorized mainline integration is completed and verified; otherwise the exact remaining review/check/protection blocker is recorded.

## Durability rule

This map is the canonical execution dependency map for the current Evidence Spine effort. If material sequencing, ownership, collision boundaries, acceptance gates, or proof ceilings change, update this tracked file (or the active PR carrying it) before handing execution to another agent. `POST_PHASE_C_STRATEGIC_SCOUT.md` remains the strategic predecessor; `EVIDENCE_SPINE_ARCHITECTURE.md` becomes the architecture authority once P95 integrates it. A repository work-ledger entry may index this map but must not duplicate or replace it.
