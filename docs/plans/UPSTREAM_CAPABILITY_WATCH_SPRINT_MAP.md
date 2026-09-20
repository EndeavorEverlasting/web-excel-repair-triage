# Upstream Capability Watch + Prompt Impact Sprint Map

**Canonical repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Planning floor:** `main@70178017ffa5c27f4428d6aae733a61113a6f4ad`
**Planning branch:** `plan/upstream-capability-watch-20260920`
**Owner:** Prompt Kit upstream capability watch / P102 + P115 integration
**Status:** TRACKED PLAN — U0A forensics and U0B source research PROVEN; U1 implementation is active on PR #619; U1 integration and U2+ runtime/visibility remain unproven.

## Mission

Close the defect exposed by the missed Matt Pocock `teach` update path: registered external capabilities may refresh as donor metadata, yet Prompt Kit has no capability-level identity ledger, source→local impact graph, durable change event, or guaranteed P115/user-visible routing. Extend the existing external-resource/P102/P115 spine rather than creating a second polling system.

Separately, route Claude/Anthropic design and skill-authoring prior art through the same intake mechanism after authoritative source research. UX-oriented donor mechanics belong with current UX owners; prompt/skill-authoring mechanics belong with P79 and prompt operations. Donor authority never implies local mutation authority.

## Fresh evidence floor

- Matt Pocock is already registered in `harness/contracts/operant-external-resource-intake.v1.json` as `mattpocock-skills` with repository `mattpocock/skills`, root `skills`, and nested `SKILL.md` enumeration.
- The registered refresh cadence is daily at `37 5 * * *`; canonical command is `python scripts/sync_operant_external_resources.py`.
- `.github/workflows/operant-external-resource-refresh.yml` is a read-only drift-proof workflow: build candidate, validate, `cmp` candidate against tracked projection, upload artifacts. It does not route drift to P115 and cannot mutate main.
- The current public resource projection pins Matt repo floor `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`; `mattpocock-skills:productivity/teach` exists and currently has `target_id: null`, `POINT_TO_EXTERNAL`, `REVIEW_ADD_PROMPT`.
- The `teach` file blob identity at current Matt main is `c679eeccd48ca720c8196e5d9a9e58223abf213b`. That same blob was present at the September 10, September 16, and September 18 donor floors even while Matt's repository SHA moved. This proves repository-floor identity is too coarse for capability-specific impact routing.
- P102 already requires observed identity to remain distinct from last successfully applied identity when that distinction matters.
- P79 already requires all registered upstream prior-art search before plausible ADD identity allocation.
- P115 is the semantic AFK coordination owner. `scripts/prompt_kit_afk_signal_router.py` explicitly does not own scheduling or promotion.
- The historical /teach workspace implementation and P96/P98 strengthening live in `registry/prompts/tutorial-discovery-prompts.v1.json`.
- Current open PR collision floor: #600 touches `harness/prompt-topology/EVIDENCE_SPINE_SPRINT_MAP.md`; #606 touches semantic/capability profile floors; #561 touches `registry/prompts/tutorial-discovery-prompts.v1.json` and generated Prompt Kit; #431 touches feedback workflow/runtime UI and generated Prompt Kit. No inspected open PR owns this new plan path or the active dispatch manifest.

## U0A forensic classification — PROVEN

Canonical evidence: `harness/reports/UPSTREAM_CAPABILITY_WATCH_FORENSICS.md` and `harness/reports/upstream-capability-watch-forensics.v1.json`.

| Disposition | Proven result | Consequence |
|---|---|---|
| `SOURCE_UNWATCHED` | FALSE — Matt source and `productivity/teach` are registered. | Registration was not the incident cause. |
| `POLL_NOT_SCHEDULED` | FALSE — daily scheduled runs are observed. | Scheduler absence was not the incident cause. |
| `IDENTITY_DETECTION_GAP` | CONFIRMED DEFECT — resource rows use donor repo SHA rather than per-resource blob identity. | Capability-specific change attribution is noisy/imprecise. |
| `IMPACT_EDGE_MISSING` | CONFIRMED DEFECT — current `teach` target is null. | No deterministic P96/P98/P65 evaluation route exists. |
| `VISIBILITY_GAP` | CONFIRMED DEFECT — earliest proven post-detection break. | Run `35332457839` detected drift and uploaded evidence but emitted no P115/user signal. |

Incident correction: the inspected September upstream delta did **not** modify `skills/productivity/teach/SKILL.md`; it added and then refined `skills/in-progress/pr/SKILL.md`. The local teaching lane may still be semantically behind broader upstream practice, but that is U2B work and is not promoted to fact by U0A.

## Non-negotiable data invariants

1. `last_observed_identity` and `last_processed_identity` are separate. Observing a new capability identity must not consume it before a durable event/routing checkpoint succeeds.
2. Capability identity is the smallest stable upstream unit that can meaningfully change (Git blob/content SHA for `SKILL.md` where available), while repository revision remains provenance.
3. One identity transition produces at most one canonical change event. Deduplication key is source/capability + previous identity + current identity.
4. Missing impact edges do not erase source-change events.
5. Upstream observation is evidence, never local adoption or promotion authority.
6. Promotion is policy-controlled; default external capability policy is review-required.
7. The existing external-resource intake remains discovery/catalog authority. Do not create a competing donor registry.

## Ownership / factoring

### Harness spine
- Keep: `harness/contracts/operant-external-resource-intake.v1.json` as donor-source/catalog authority.
- Create: one bounded upstream-capability-watch contract/schema only if current contracts cannot express capability identity, processing state, dedupe, impact edges, and promotion policy without conflating discovery with execution state.
- Keep/extend: deterministic test floor and fixtures.
- Keep: `Outputs/prompt-parallel-dispatch/manifest.json` as orchestration artifact.

### Agent harness
- Keep P102: polling/scheduled-sync builder; strengthen only if implementation reveals a reusable missing invariant.
- Keep P115: AFK semantic coordinator.
- Keep P79: prompt registry contribution/promotion gate.
- Rewire trigger path: accepted `upstream_capability.changed` → impact resolver → P115 bounded review work.
- Do not put provider polling inside browser feedback telemetry.

### Conventional application logic
- External resource sync continues to enumerate donor sources.
- New watch state machine owns capability observation/processed state and change receipts.
- P115 router accepts a bounded upstream-capability event class without gaining scheduler or merge authority.
- UI/Prompt Kit status consumes receipts; it does not become the state owner.

## Dependency graph / waves

### Wave 0 — parallel research/forensics
**Lane U0A — Missed teach forensic classification**
Owns forensic report/receipts only. Proves the five dispositions against current source, workflow, artifacts, and history.

**Lane U0B — Design + skill-authoring authoritative-source research**
Read/research lane. Establishes the authoritative Claude/Anthropic `/design` and skill-authoring surfaces, versionability, license/usage boundaries, and candidate local owners. No registry mutation.

These lanes are write-collision free.

### Wave 1 — shared contract floor
**Lane U1 — Capability watch contract + fixtures**
Depends U0A. Defines minimal persisted source/capability identity, poll state, `last_observed_identity`, `last_processed_identity`, append-only poll receipt, impact-edge shape, dedupe transition key, promotion policy, and canonical change event. Adds negative/positive fixtures.

This lane owns any new shared schema/registry shape. Later lanes must not redefine it.

### Wave 2 — parallel implementation
**Lane U2A — Runtime detection + P115 visibility routing**
Depends U1. Extends the current external-resource refresh/watch seam to calculate capability-level identities, persist/process transitions safely, emit deduped change events, and route accepted actionable events to P115. Preserve read-only schedule semantics unless an existing strategic owner already owns candidate PR creation. No prompt body mutation.

**Lane U2B — Teach impact edges + Socratic reconciliation**
Depends U1. Adds explicit `mattpocock-skills:productivity/teach` impact mappings to the current teaching owners after refreshed overlap review, then semantically compares current upstream `teach` with P96/P98/P65 and changes only proven stale/missing behavior. P79 remains promotion gate. Do not rewrite P96 merely because a donor changed.

U2A and U2B are parallel-safe if U1 owns shared schema and U2B alone owns canonical impact-edge data.

### Wave 3 — donor intake
**Lane U3 — Design/skill-creator intake**
Depends U0B, U1, U2B. Register only authoritative, maintainable donor surfaces established by U0B. Add impact mappings: authoring/evaluation mechanics toward P79/prompt operations; design/UX mechanics toward current UX architecture/design-system/certification owners after refreshed owner resolution. Do not treat `/design` as universal prompt-authoring authority.

### Wave 4 — user-facing status
**Lane U4 — Capability Radar / visibility UX**
Depends U2A and U3. Expose receipt-derived states such as CURRENT, UPSTREAM_CHANGED, EVALUATING, CANDIDATE, DECLINED, INTEGRATED without becoming a second state store. Reconcile current open PRs #431 and #561 before touching their UI/generated-output surfaces.

### Wave 5 — convergence proof
**Lane U5 — Synthetic A→B replay + integration**
Depends U2A, U2B, U3, U4. Run end-to-end fixture:
A observed/processed → B observed → durable change event → impact resolution → P115 review item/user-visible state → processed advances to B only after durable routing. Re-poll B produces no duplicate. B→C produces exactly one new event. Validate promotion remains review-required and converge exact green owners to refreshed main.

## Collision ledger

- `registry/prompts/tutorial-discovery-prompts.v1.json`: U2B owner; open PR #561 currently overlaps. Reconcile or wait before mutation.
- `web/prompt-kit/index.html`: generated only; multiple open PRs overlap. Never use as source.
- `docs/prompt-kit-feedback-production.js` / guided recommendations / feedback workflow: #431 currently overlaps. U4 must refresh/reconcile before mutation.
- `harness/prompt-topology/EVIDENCE_SPINE_SPRINT_MAP.md`: #600 owner; this plan must not mutate it.
- semantic/capability profile floors: #606 owner; avoid unless a later prompt semantic change requires refreshed integration.
- `scripts/prompt_kit_afk_signal_router.py`: U2A owner for this sprint family; no inspected open PR currently overlaps that exact path.
- external-resource contract/sync/workflow: U1/U2A shared family; U1 defines schema, U2A consumes it. Serialize writes.

## Sprint definitions

### U0A — Missed teach forensic classification
**Status:** PROVEN on provider/runtime-history evidence.
**Primary surface:** research/runtime proof.
**Read first:** external-resource contract/index/sync/workflow; workflow evidence if accessible; P102 history; P115 routing contract/router; teaching prompt registry; P79 prior-art gate.
**Outputs:** `harness/reports/UPSTREAM_CAPABILITY_WATCH_FORENSICS.md` plus machine-readable receipt `harness/reports/upstream-capability-watch-forensics.v1.json`.
**Validation:** every disposition has PASS/FAIL/UNKNOWN evidence; no unsupported claim that scheduled runs occurred.
**Proof ceiling:** repository/provider forensics only unless scheduled-run evidence is available.

### U0B — Design/skill-authoring authoritative-source research
**Primary surface:** research/design.
**Outputs:** bounded donor-source disposition with authoritative location/version signal, usage/license boundary, local owner map, and recommendation REGISTER / REFERENCE_ONLY / REJECT.
**Forbidden:** editing Prompt Kit registry or adopting donor wording wholesale.
**Proof ceiling:** authoritative-source research.

### U1 — Capability watch contract + fixtures
**Primary surface:** harness spine.
**Expected contract:** watched source/capability locator; immutable identity; repository revision provenance; poll state; append-only receipt; impact edge; dedupe transition; promotion policy; event schema. U1 also owns the deterministic state-transition kernel at `scripts/upstream_capability_watch.py`, the capability-watch checks inside `scripts/validate_operant_external_resources.py`, and focused-suite wiring in `.github/workflows/operant-external-resource-refresh.yml`; U2A later owns provider polling, durable runtime persistence, and P115 routing around that proven kernel.
**Required tests:** initial observation; unchanged; A→B; replay B; B→C; routing failure leaves processed=A; missing impact edge retains event; promotion cannot jump changed→integrated.
**Proof ceiling:** deterministic repository proof.

### U2A — Runtime detection + P115 visibility routing
**Primary surface:** integration seam + agent harness.
**Expected behavior:** existing daily refresh detects per-capability changes, produces durable typed events, routes actionable impacted events to P115, and exposes bounded status.
**Forbidden:** automatic prompt rewrite, scheduler-owned merge, credentials in receipts, raw donor bodies in tracked state.
**Proof ceiling:** deterministic + provider workflow proof; due-time observation only if actually observed.

### U2B — Teach impact + Socratic reconciliation
**Primary surface:** Prompt Kit registry/semantic validation.
**Expected behavior:** explicit impact mapping and evidence-backed P96/P98/P65 disposition. Current file blob identity must be pinned in the review receipt.
**Forbidden:** donor-copy rewrite, P79 bypass, hand-editing generated HTML.
**Proof ceiling:** Prompt Kit semantic/regression proof; no claim of teaching efficacy without user/runtime observation.

### U3 — Design/skill-creator intake
**Primary surface:** external donor registration + impact graph.
**Expected behavior:** authoritative donor surfaces become watchable prior art only where source/version semantics are stable; mappings point to existing owners.
**Forbidden:** new universal design owner when current UX owners suffice.
**Proof ceiling:** repository integration + source provenance.

### U4 — Capability Radar
**Primary surface:** conventional UI + UX prompts only where required.
**Expected behavior:** receipt-derived state with provenance and no duplicate state authority. Keyboard/mouse/phone interaction follows current UX owners; generated site rebuilt only from canonical sources.
**Proof ceiling:** automated/browser proof available in repo; physical-device proof remains separate.

### U5 — Synthetic replay + convergence
**Primary surface:** validation/runtime proof/integration.
**Expected artifact:** exact transition receipt chain proving no silent consumption between observed and processed identity.
**Proof ceiling:** exact environment actually exercised.

## Skill / capability / trigger inventory

| Surface | Decision | Activation | Input | Output | Guardrail |
|---|---|---|---|---|---|
| P102 polling builder | KEEP / possibly strengthen | repo/product needs permissioned upstream polling | authoritative source + consumer boundary | safe polling implementation | no silent recurring mutation |
| external-resource intake skill | KEEP | donor catalog refresh/review | registered sources | metadata-only pinned projection | no donor body copying |
| P79 prompt adder/prior-art | KEEP | reusable prompt insight / plausible ADD | chat + all registered donor prior art | strengthen/add decision | donor evidence ≠ authoring authority |
| P115 AFK coordinator | KEEP / REWIRE input | accepted actionable signal | typed bounded event | bounded work request | no scheduler/merge authority |
| upstream-capability change trigger | CREATE | processed identity differs from observed and durable transition event exists | event + impact edges | P115 review routing | dedupe + promotion policy |
| impact resolver | CREATE as capability/application seam | upstream capability event | source/capability id + edge registry | affected local owner ids | zero-edge must remain diagnosable |
| capability radar UI | CREATE as consumer | persisted watch/review state changes | read-only receipts/state | user-visible status | never state authority |

## Validation / proof gates

1. Existing external-resource tests remain green.
2. New watch contract/schema validation passes.
3. Negative fixture proves routing crash cannot advance `last_processed_identity`.
4. Positive fixture proves one A→B event and dedupe on repeated B.
5. Missing-edge fixture yields retained change event + diagnosable no-impact state.
6. P115 router rejects sensitive/raw donor bodies and preserves promotion boundary.
7. Teaching prompt semantic tests pass after any U2B change.
8. Generated Prompt Kit parity is exact when canonical prompt sources change.
9. Patch hygiene and deterministic floor pass before integration.
10. Mainline integration is containment/content proven after refreshed default branch.

## Parallel capability / autonomy state

### Current executable graph

After U0A and U0B integration, the active executable graph contains only U1. Current graph width is **1**, so parallel execution is **NOT_APPLICABLE** for the active wave. The machine-readable manifest is `Outputs/prompt-parallel-dispatch/manifest.json`, run id `upstream-capability-watch-20260920-u1`, and it is pinned to existing writer PR #619 / branch `feat/upstream-capability-watch-contract-floor-20260920`.

### Historical wave

The prior U0B/U1 successor wave had graph width 2 and ran under DEGRADED coordination because no autonomous worker adapter was exposed. That historical autonomy gap is preserved by the merged U0A/U0B evidence; it is not the current dispatch posture.

## Contract horizon

| Contract | Owner | Status | Next transition |
|---|---|---|---|
| forensic classification | U0A | PROVEN | closed by `harness/reports/UPSTREAM_CAPABILITY_WATCH_FORENSICS.md` + `harness/reports/upstream-capability-watch-forensics.v1.json` |
| design-source authority research | U0B | PROVEN | `harness/reports/UPSTREAM_DESIGN_AUTHORING_SOURCE_RESEARCH.md` integrated by PR #618 |
| watch data/event contract | U1 | REQUIRED SUCCESSOR WORK | implement schema + fixtures |
| runtime detection/routing | U2A | REQUIRED SUCCESSOR WORK | emit durable capability events + P115 routing |
| teach reconciliation | U2B | REQUIRED SUCCESSOR WORK | add impact mapping and semantic disposition |
| design/authoring intake | U3 | REQUIRED SUCCESSOR WORK | register/adapt only authoritative donors |
| user-visible capability state | U4 | REQUIRED SUCCESSOR WORK; collision-gated | reconcile #431/#561, then implement |
| end-to-end replay | U5 | REQUIRED SUCCESSOR WORK | prove A→B→visible→processed and dedupe |
| deployment/live AFK due-time proof | runtime/operator environment | UNPROVEN/UNKNOWN | observe actual scheduled execution after integration |

## First executable continuation

Owner: U1 capability-watch contract-floor lane.
Dependency: U0A forensics and U0B source research are PROVEN. Graph width is now 1, so parallel execution is NOT_APPLICABLE. The executable manifest is `Outputs/prompt-parallel-dispatch/manifest.json` with run id `upstream-capability-watch-20260920-u1`.
Action: continue PR #619 on refreshed main: repair the `UNSEEN -> CURRENT` baseline transition, implement the deterministic state kernel in `scripts/upstream_capability_watch.py`, validate the contract/impact-edge invariants through `scripts/validate_operant_external_resources.py`, make the refresh workflow execute the focused capability-watch suite, make the routing-failure fixture exercise the kernel, and wire the focused suite into the external-resource refresh workflow now; deterministic-floor registration remains BLOCKED by active #606 ownership of `harness/test-floor.v1.json` and must be converged by that owner before U1 can reach its full acceptance ceiling.
Completion gate: deterministic A→B/replay/B→C fixtures plus routing-failure preservation prove that a new observed identity cannot be silently consumed before durable routing.

Coordination note: `.ai/WORK_QUEUE.md` is temporarily owned by open PR #615, so U0A ledger synchronization is deferred to convergence rather than racing that shared file.
