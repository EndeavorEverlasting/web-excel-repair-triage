# Prompt Execution Evidence Spine — Architecture Decision

**Status:** DESIGNED / TRACKED (architecture decision; runtime not implemented here)
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Owner:** P95 — Program Design & Call-Stack Prototype Architect
**Evidence floor:** refreshed `main@a1e9caa17c6a979a3747edb71632a66c9406af00` (contains integrated Panel 1 / PR #467)
**Predecessor scout:** [`POST_PHASE_C_STRATEGIC_SCOUT.md`](./POST_PHASE_C_STRATEGIC_SCOUT.md)
**Phase C recovery floor:** [`PHASE_C_CLOSEOUT.md`](./PHASE_C_CLOSEOUT.md) + [`PHASE_C_HANDOFF.md`](./PHASE_C_HANDOFF.md)
**Canonical sprint map:** `harness/prompt-topology/EVIDENCE_SPINE_SPRINT_MAP.md` via planning PR #471 (TRACKED; not yet on this branch floor)
**Decision date:** 2026-09-14

## 1. Decision (one line)

**Accepted architecture:** keep intentionally separate semantic owners; compose them with **thin correlation adapters** and a deterministic **continuation resolver**. Do **not** introduce a universal lifecycle envelope, generic event bus, or new competing outcome/recovery classifier.

Decision rule outcome from the scout: **PREFER ADAPTER-ONLY / NO NEW SPINE**.

## 2. Why this decision (falsification summary)

| Alternative | Verdict | Discriminating evidence |
|---|---|---|
| A. Common lifecycle envelope + semantic payloads | **Rejected** | Existing owners already define receipt/event identity (`prompt-outcome-receipt/v1`, route receipts in #450, usage events in #431, dispatch receipt in #467). A shared envelope would become a second truth or a de-facto bus. Scout §3 Thesis A alternative explanation applies. |
| B. Adapters between separate owners | **Accepted** | All three required traces compose via stable correlation keys (`prompt_id`, `prompt_revision`, `invocation_id`, optional `mission_id`/`run_id`, `surface_id`) without merging payload semantics. Privacy plane (#460) already separates retention/reduction from semantic classification. |
| C. Intentional isolation / no composition | **Rejected for successor runtime** | Recommendation→route→invoke→outcome→recovery already needs deterministic continuation for agents (`next_action` / completion-candidate). Isolation would force prompt-prose or operator scheduling to bridge owners, violating P07/P115 autonomy contracts. Isolation remains valid only for Phase D behavioral channels until a later empirical gate. |

## 3. Non-goals (explicit)

- No Phase D topology mutation or Collective Learning ingestion.
- No generic analytics/event bus.
- No hosted telemetry; no raw prompt/response/clipboard/transcript/identity capture.
- No vector DB.
- No wholesale merge of stale #450/#431 branches.
- No duplicate P99 outcome classifier or P115 recovery queue.
- No application behavior owned only by prompt prose.
- Architecture integration does **not** prove runtime Evidence Spine implementation.

## 4. State-owner matrix

| Lifecycle state | Canonical semantic owner | Authoritative artifact / contract | Correlation keys produced | May infer? | Persistence / privacy plane |
|---|---|---|---|---|---|
| Recommendation | Prompt Finder / guided recommendations | Finder recommendation UI + topology advisory (Phase A/B/C) | `prompt_id`, `prompt_revision`, recommendation episode id (local) | No — recommendation ≠ selection | Device-local Personal State / Local Journal only if retained |
| Selection / open / copy | Prompt Kit local UI | Local usage/selection events (reconcile #431 concepts) | `prompt_id`, `surface_id`, local event id | No — copy ≠ invocation | Local Journal / privacy-bounded observation; never raw clipboard content |
| Dispatch attempt | P07 parallel dispatch (#467 integrated) | `prompt-parallel-dispatch/v1` + `scripts/prompt_parallel_dispatch.py` | `run_id`, lane_id, adapter rung | No — manifest ≠ observed parallelism | Repository/CI artifact or local Outputs/; not Collective Learning |
| Authoritative route receipt | Route control plane (salvage #450) | `prompt-route-receipt` (+ operant routing contract) | route_id, `prompt_id`, destination, confidence | Inferred destination must not promote to authoritative | Actor-neutral receipts; no user identity required |
| Execution / invocation | Launcher / agent runtime / observed surface | Invocation identity inside outcome receipt + optional runtime_tool receipts | **`invocation_id`** (stable), `surface_id`, `target_runtime` | Unknown destination allowed | Observed vs declared provenance required |
| Outcome | **P99** (merged #452) | `prompt-outcome-receipt/v1` + `prompt-outcome-classification.v1.json` | `receipt_id`, `invocation_id`, classification | Attribution enum already encodes PROVEN/CORRELATED/UNOBSERVED | Bounded append-only receipts; no raw content |
| Correction / recovery | **P115** + feedback AFK routing | P115 work-request / recovery coordination; `.ai/skills/prompt-kit-feedback-afk-routing` | links to `receipt_id` / finding id | Corrections are explicit events, not ordinary usage | Same privacy constraints as feedback skill |
| Recurrence / finding | Post-P95 Lane C (not this doc’s runtime) | Finding state machine consuming P99 evidence | finding_id ← receipt_ids | Thresholds remain P99-owner-specific where defined | Git-friendly finding records; dedupe by contract failure identity |
| Completion candidate | Deterministic continuation resolver (post-P95) | Resolver reads required/recovery gates + agent claim | mission/run/invocation ids | Agent terminal claim is candidate only | Ephemeral decision; may emit typed disposition only |
| `next_action` disposition | Same continuation resolver | Typed: `continue` \| `recover` \| `complete` \| `blocked` | inputs = correlated evidence set | Must not invent missing evidence | Deterministic function; no telemetry store |
| Retention / privacy | Merged #460 planes | `prompt-kit-cross-device-access` / privacy-storage contracts | N/A (plane placement) | PrivacyReducer has no network authority | Local Journal → PrivacyReducer → allowlisted aggregate only |

### Authority direction (forbidden flows)

- Recommendation must not prove route, invocation, or success.
- Dispatch attempt must not prove execution or observed parallelism without a receipt.
- Route receipt must not prove invocation occurred.
- Invocation must not prove SUCCESS.
- Ordinary open/copy must not create corrective/finding tickets.
- Inferred destination must not overwrite authoritative route destination.
- PrivacyReducer output must not carry user/session/project identity.

## 5. Identity and provenance model

Every correlated record MUST distinguish:

| Provenance class | Meaning | Example |
|---|---|---|
| **Observed** | Directly recorded by an owner that had the fact | Launcher emits authoritative destination; validator emits FAIL receipt |
| **Declared** | Agent/user claim without independent observation | Agent claims `complete` |
| **Inferred** | Derived from weak/partial signals | Guess destination from UI heuristics |
| **Unknown** | Explicit absence; preferred over fabrication | Human clipboard copy with no destination |

Required correlation vocabulary (shared *names*, not a shared envelope schema):

- `prompt_id` + `prompt_revision`
- `invocation_id` (created at true invocation; may be absent for copy-only)
- `surface_id`
- optional `mission_id` / dispatch `run_id`
- `receipt_id` / `route_id` / local `event_id` as owner-native ids
- `evidence_state` promotion remains typed (PLANNED…OBSERVED); never silent promotion

Human clipboard/hotkey path: **zero mandatory destination or metadata**. Destination may remain `unknown` indefinitely.

## 6. Three required traces

### Trace 1 — Recommendation path

1. Finder recommends prompts (topology/guidance) → advisory only.
2. User selects/open/copies → local selection event; clipboard content never stored.
3. Optional route decision → authoritative route receipt only if route owner observed destination; else destination `unknown`.
4. Invocation → assign `invocation_id` when a launcher/runtime actually invokes.
5. Outcome → P99 receipt keyed by `invocation_id`.
6. Eval/recovery candidate → only if classification.actionability warrants; P115 owns recovery work requests.

**Falsifier:** if any step’s artifact is treated as proof of a later step, the adapter is wrong.

### Trace 2 — Autonomous repair path

1. Deterministic repository failure observed → P99 FAILURE receipt (`attribution=PROVEN` when validator-backed).
2. P115 recovery selects repair owner / work request.
3. Reroute or repair runs → new invocation + new receipt; link via `related_receipt_ids` / supersession, **do not double-count** the original failure as a second independent defect.
4. Dispatch (#467) may parallelize independent repair lanes; dispatch receipt proves parallelism only when `observed_parallelism=true`.

### Trace 3 — Phase D candidate path (design only; not implemented)

1. Repeated local transition/co-use events accumulate in device-local journal.
2. PrivacyReducer emits allowlisted aggregates only.
3. Aggregate may *candidate* a topology behavioral channel (`CO_USAGE` / `TRANSITION` / …).
4. No identity escape; no production topology mutation in this architecture sprint; empirical value gate remains future P82.

## 7. Continuation resolver (agent-native seam)

**Owner (post-P95 runtime):** a deterministic service/module (not prompt prose) that:

**Inputs (read-only):** correlated P99 receipts, open P115 recovery/work items, optional route receipts, optional dispatch receipts, agent completion candidate.

**Outputs (typed disposition):**

| Disposition | When |
|---|---|
| `continue` | Required owned work remains; no blocking recovery supersession |
| `recover` | P115/required recovery gate supersedes agent completion candidate |
| `complete` | Required gates satisfied; no open recovery; evidence supports terminal claim |
| `blocked` | User-only / external gate named exactly |

**Completion-candidate rule:** an agent’s terminal claim is never authoritative while a required or recovery lifecycle gate remains open. The resolver owns that supersession decision.

## 8. Recurrence → finding boundary (design freeze for Lane C)

- One ordinary correction = evidence, not an automatic engineering ticket.
- Recurrence grouping keys on **underlying contract failure identity**, not similar free text.
- Generic threshold: three materially equivalent occurrences across multiple executions confirm recurrence, unless an owner-specific P99 threshold overrides (deterministic contradiction min 1; repeated local pattern min 3; manual context transfer min 2; correction-not-integrated min 2; premature terminal = terminal claim + safe successor observed).
- Duplicate findings accumulate evidence; they do not spam tickets.
- Post-fix recurrence reopens/escalates monitoring.
- Ticket/work-request compilation reuses **P115-compatible** coordination only when remediation owner, observed/expected behavior, linked evidence ids, acceptance criteria, and proof requirements exist.

## 9. Donor dispositions

### PR #450 (routing control plane)

**Disposition: ADAPT after interface freeze — do not wholesale merge.**

Keep/adapt:

- Actor-neutral route receipts
- Authoritative vs inferred destination semantics
- Idempotency / compare-and-set route-state ideas where still compatible with current main

Retire/supersede:

- Any overlap that redefines outcome/success (P99 owns outcome)
- Any telemetry or identity fields forbidden by #460

**Connection point:** route-receipt adapter → correlation keys → continuation resolver; never writes P99 classification.

### PR #431 (observation corpus)

**Disposition: ADAPT bounded observation — do not wholesale merge.**

Keep/adapt:

- Privacy-bounded selection/usage observation
- Explicit non-equivalence of selection intent to terminal success
- Session-identity stripping before any eval candidate export

Retire/supersede:

- Anything that stores raw query/prompt/clipboard/transcript
- Anything that creates a parallel outcome classifier

**Connection point:** local observation adapter → Local Journal / bounded events; feeds Phase D *candidates* only through PrivacyReducer later.

### PR #467 (autonomous dispatch) — INTEGRATED on this floor

**Disposition: KEEP as dispatch-attempt / observed-parallelism owner.**

Dispatch manifest/receipt remain separate from route and outcome. Required width≥2 claims need valid manifest + receipt with `observed_parallelism=true`.

### P99 / P115 / #460 — KEEP

Unchanged semantic authority. Architecture adds adapters and a resolver; it does not fork classifiers or privacy planes.

## 10. Adapter boundaries (minimal successor contracts)

Post-P95 implementation may add **thin** schemas only if needed:

1. `evidence-correlation/v1` — optional bag of foreign keys + provenance class (not a state machine).
2. `continuation-disposition/v1` — resolver input snapshot hash + typed disposition (not an event log).
3. Finding schema — only if Lane C cannot reuse an existing P115 work-request shape.

If static mapping + fixtures prove correlation keys suffice without (1), omit (1).

## 11. Thin prototype / falsification notes

Static mapping already discriminates alternatives for Traces 1–2 using existing contracts on `main` (`prompt-outcome-receipt/v1`, `prompt-parallel-dispatch/v1`, privacy planes).

Executable seam prototypes for failure propagation belong to Panel 3 once this decision is integrated; this architecture sprint does not ship production listeners.

Representative failure fixtures Panel 3 MUST cover (acceptance handoff):

- ordinary copy with `unknown` destination
- inferred destination not promoted
- premature terminal superseded by recovery
- duplicate evidence accumulation
- post-fix recurrence reopen
- privacy-rejected raw content

## 12. Proof ceiling

This document proves an **architecture decision** and ownership matrix against refreshed main + donor diffs + scout admission criteria.

It does **not** prove:

- Evidence Spine runtime integration
- provider-wide agent adoption
- live destination observation
- Phase D value
- #450/#431 mainline merge

## 13. Successor acceptance gates (Panel 3)

1. Collision matrix proves disjoint writers for lanes A/B/C vs coordinator-shared surfaces.
2. Lane A adapts only #450 concepts admitted here.
3. Lane B adapts only #431 concepts admitted here.
4. Lane C implements recurrence/finding/ticket per §8.
5. Continuation resolver implements §7 with fixtures.
6. Generated Prompt Kit remains builder-owned if UI consumers change.
7. Integrate dependency-first onto refreshed `main` with containment proof.

## 14. Sprint-map synchronization

Wave order remains: **#467 floor (done on this evidence floor) → P95 architecture (this artifact) → runtime convergence A/B/C**.

No sequencing change that would allow Phase D or donor wholesale merges before architecture integration. When PR #471’s sprint map lands on main, update its “architecture artifact absent” / P95 status rows to point at this file’s merged revision.
