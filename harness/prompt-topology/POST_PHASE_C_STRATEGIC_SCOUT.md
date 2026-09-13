# Post-Phase-C Repository Strategic Scout

**Status:** STRATEGIC SCOUT COMPLETE — recommendation only; selected investigation is not implemented here
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Scout owner:** P141 — Repository Strategic Opportunity Scout
**Evidence floor:** refreshed `main@3e37127253c753a2e861f6171b4fa8aede43098e`
**Phase C hardened floor:** `b9cd839c4910402073e9e84476fb1b8d5e3060ef` via PR #459
**Latest strategic dependency:** PR #460, Prompt Kit privacy/storage planes, merged at `3e37127253c753a2e861f6171b4fa8aede43098e`
**Recommended next owner:** P95 — Program Design & Call-Stack Prototype Architect
**Recommended investigation:** Prompt execution evidence-spine/state-ownership architecture before Phase D Passive Learning

This document is the durable result of a repository-wide strategic scouting pass. It does **not** authorize implementation of Phase D, Phase E, Collective Learning ingestion, a shared event bus, AFK product extraction, Personal State runtime, Private Sync, or any other candidate described here. The operator has granted authority for future phases, but each successor still enters through its owning contract and proof boundary.

## 1. Repository situation model

### CURRENT FACTS

1. The repository now owns two substantial product domains: workbook/Web Excel compatibility tooling and the Prompt Kit / AFK Agent Flow ecosystem. `CODEBASE_MAP.md` and `harness/CONTEXT.md` route these through separate canonical owners rather than one undifferentiated application.
2. Prompt Kit infrastructure is mature at the repository/static-contract layer: registry ownership, deterministic generation, Pages publication, acquisition paths, prompt discovery/classification, eval orchestration, artifact/harness validation, product boundaries, release/versioning, and privacy/storage policy all have repository-owned contracts and tests.
3. Prompt Topology Phase A, Phase B, and the Phase C viewer are implemented on main. Phase C was additionally hardened through PR #459 before this scout.
4. Prompt Topology reserves `CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, and `COMPLEMENT` as behavioral channels, while Phase A excludes those channels from current canonical topology construction. This deliberately leaves room for a future behavioral evidence layer without letting current static semantics pretend that live evidence exists.
5. The Phase B projection contract already defines deterministic epoch identity, parent lineage, topology/projection hashes, rigid alignment, and displacement limits. Generated topology/projection artifacts are reproducible evidence outputs rather than a retained historical database.
6. PR #460 is now on main and defines four privacy/storage planes: Prompt Canon, Personal State, Private Sync, and Collective Learning. It also defines a device-only Local Journal and PrivacyReducer buffer. Collective Learning may receive only allowlisted, privacy-reduced aggregate evidence; the reducer itself has no network authority. Runtime browser/device persistence, reducer execution, encrypted `.pkenc` import/export, and network ingestion remain unimplemented/unobserved.
7. PR #431 is open and implements a privacy-bounded Prompt Finder observation corpus around `prompt_usage` / selection-intent events and candidate-only eval samples. It explicitly does not treat selection intent as terminal success and strips session identity before candidate-eval output.
8. PR #450 is open and implements a canonical prompt-routing control plane with actor-neutral route receipts, precedence, compare-and-set state, idempotency, headless routing, and autonomy-gap semantics.
9. PR #452 is merged on main (`fd3b3910e0ce80f3880ebd15426278354b065f48`) and implements prompt outcome receipts with invocation identity, multiple observers per invocation, evidence-state tracking, failure taxonomy, correction burden, and explicit UNKNOWN/environment behavior. Treat it as current-main outcome truth for P95, not as an open branch.
10. Those three open lanes are not present on current main and were authored against different earlier floors. Their semantics overlap around prompt identity, event/receipt identity, time, source/surface, causality, evidence, and progression, but they currently have separate schema ownership.
11. The merged repository AI eval framework already composes deterministic, synthetic, model-runtime, and human-review layers. Deterministic/synthetic evidence can block CI; live model-runtime and irreducible human judgment remain explicit proof ceilings rather than being inferred from static tests.
12. PR #454 made product ownership explicit and declared a future dedicated AFK Agent Flow cutover as a conditional successor. The current combined Prompt Kit remains an intentional compatibility surface.
13. `.ai/WORK_QUEUE.md` is a valid local coordination ledger but its visible task set currently ends in older DONE TRQ work while several substantial September PR lanes remain open. Provider PR state therefore carries materially newer unfinished-work evidence than the local queue.
14. At scout time, the tracked Prompt Topology directory contained `PHASE_C_HANDOFF.md` rather than a merged Phase C closeout. That recovery-floor dependency was later closed by integrating `PHASE_C_CLOSEOUT.md` beside the handoff on refreshed main. P95 may begin only after verifying that closeout/handoff pair is reachable from current main; this scout does not absorb the closeout lane's content.

### DERIVED PATTERNS

1. **Contract-rich, seam-poor convergence.** The repository is no longer primarily missing individual mechanisms. It increasingly has multiple strong mechanisms whose boundaries meet: recommendation, routing, invocation/usage observation, outcome classification, recovery coordination, eval candidate generation, privacy reduction, and topology behavior channels.
2. **Runtime-evidence blindness is the recurring proof ceiling.** Static/deterministic behavior is unusually well governed, but several important decisions still stop at “runtime/human unproven.” The open outcome/usage lanes are direct attempts to close that gap without pretending ordinary use is correctness evidence.
3. **Phase D has become technically feasible but architecturally ambiguous.** PR #460 resolves much of the prior privacy/storage uncertainty, and topology already reserves behavioral channels. What remains unclear is not whether the repository can collect *some* bounded behavior; it is which existing receipt/event owners should produce, correlate, reduce, and consume that evidence without creating another source of truth.
4. **A direct Phase D implementation now risks a fourth event model.** Implementing Passive Learning directly from the topology side would likely duplicate concepts already present in #431, #450, and #452 unless lifecycle identity, ownership, and adapter boundaries are resolved first.
5. **Phase E has semantic primitives before it has a durable corpus.** Epoch identity/lineage exists, but Historical Intelligence should not be built on the assumption that transient reproducible build artifacts are equivalent to accepted retained epochs.
6. **AFK extraction is strategically plausible but not currently blocking the strongest cross-system leverage.** Product boundaries now make extraction safer, yet the existing combined compatibility surface remains functional and explicitly supported.

### STRATEGIC HYPOTHESIS UNDER TEST

A minimal, privacy-respecting **Prompt Execution Evidence Spine** may be the missing architectural seam: not a monolithic event bus and not a new semantic owner, but a shared lifecycle identity/provenance boundary plus adapters that let existing owners interoperate without merging their payload semantics. This hypothesis requires architectural discrimination before any contract or runtime implementation.

## 2. Opportunity signals

- **Recurring contract gap:** route, usage, outcome, recovery, and eval evidence independently need prompt/revision/surface/causality identity, but no accepted current-main contract defines their lifecycle relationship.
- **Cross-cutting leverage:** one clean interoperability seam could improve runtime eval evidence, P99/P115 recovery, Phase D behavioral channels, candidate-eval generation, and later historical analysis.
- **Latent combination:** #431 usage observation + #450 routing receipts + #452 outcome receipts + #460 Local Journal/PrivacyReducer + existing feedback AFK routing + reserved topology behavior channels already contain most ingredients.
- **Skeleton with downstream importance:** the privacy contract names Local Journal and PrivacyReducer stores, but runtime ownership is intentionally not yet implemented.
- **Evaluation blindness:** repository AI evals deliberately preserve UNPROVEN model-runtime/human layers; usage alone does not close this, and outcome receipts are not integrated.
- **Architectural pressure:** integrating the three open evidence lanes independently can create duplicated identifiers, incompatible retention, or double-counted evidence before Phase D begins.
- **Strategic simplification:** a shared envelope may prove unnecessary; an adapter-only design that keeps each receipt schema independent could be the better outcome. The investigation must allow that conclusion.
- **Newly feasible capability:** PR #460 supplies a concrete privacy boundary and reducer allowlist that did not exist when Phase C originally prohibited telemetry.
- **User/operator pull encoded in repository trajectory:** recent work repeatedly invests in evidence-state discipline, runtime proof boundaries, routing authority, outcome classification, and privacy-bounded observation rather than only adding more prompt content.

## 3. Competing strategic theses

### Thesis A — Resolve a Prompt Execution Evidence Spine before Phase D

**THESIS**
Investigate whether routing, usage, outcome, recovery/eval, privacy reduction, and topology behavioral evidence need one minimal lifecycle identity/provenance seam with owner-specific payload adapters.

**EVIDENCE**
Three substantial open PRs independently define route, usage, and outcome evidence; current main defines Local Journal/PrivacyReducer ownership; topology reserves behavioral channels; repository AI evals have an explicit live-evidence ceiling.

**LEVERAGE**
Phase D, runtime evals, P99/P115 recovery, correction-burden analysis, candidate evals, future Collective Learning, and potentially Phase E provenance.

**TIMING**
Now. The privacy boundary just landed, but the event-producing lanes have not yet converged into main. Architecture can still be corrected before those contracts become harder to reconcile.

**COST / COMPLEXITY**
Medium architecture cost; potentially high downstream implementation cost. Main risk is inventing a central bus/authority that duplicates existing owners.

**UNLOCKS**
A principled Phase D contract, truthful end-to-end runtime evidence, cleaner integration order for #431/#450/#452, and a stable basis for privacy reduction.

**ALTERNATIVE EXPLANATION**
The separate schemas may already be correctly isolated. Simple adapters might be sufficient and any common envelope could add coupling with no benefit.

**IMMEDIATE REJECTION EVIDENCE**
Reject a shared-spine investment if an end-to-end trace shows every required lifecycle relationship can be expressed by existing owner-specific identifiers/adapters with no ambiguous causality, duplicate persistence, conflicting retention, or additional canonical truth.

### Thesis B — Execute Phase D Passive Learning directly

**THESIS**
Implement privacy-bounded behavioral channels (`CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, `COMPLEMENT`) so observed use can enrich topology recommendations.

**EVIDENCE**
Channels are already reserved; PR #460 defines a reducer output allowlist including prompt behavior and prompt-to-prompt transitions; #431 and #452 demonstrate bounded observation/outcome designs.

**LEVERAGE**
Could improve topology relationships, surface complementary/substitute prompts, and provide product-learning signals unavailable to semantic similarity alone.

**TIMING**
Newly feasible, but not yet cleanly owned.

**COST / COMPLEXITY**
High. Behavioral inference is noisy; privacy, retention, identity, causal interpretation, feedback loops, and recommendation quality all become live concerns.

**UNLOCKS**
Behavior-aware topology and potentially better recommendation/eval candidate generation.

**ALTERNATIVE EXPLANATION**
Static semantic/workflow relationships may already provide most useful topology value; real usage may be sparse, biased, or too context-dependent to justify this complexity.

**IMMEDIATE REJECTION EVIDENCE**
Reject or substantially narrow Phase D if an offline, privacy-safe replay cannot show incremental decision value over the existing static topology, or if useful signal requires fields forbidden by the privacy contract.

### Thesis C — Advance Phase E Historical Intelligence before behavioral learning

**THESIS**
Retain accepted topology/projection epochs and compare them for drift, split/merge behavior, lineage, and recurring opportunity patterns.

**EVIDENCE**
Phase B already has deterministic epoch IDs, parent lineage, topology/projection hashes, rigid alignment, and displacement bounds. Registry evolution already causes legitimate topology/projection changes.

**LEVERAGE**
Topology governance, regression diagnosis, visualization of system evolution, evidence for prompt consolidation/splitting, and later behavior-vs-semantics comparison.

**TIMING**
Conceptually attractive after A/B/C, but the required retained accepted-epoch corpus is not yet proven.

**COST / COMPLEXITY**
Medium. Requires authoritative retention semantics and reproducible reconstruction; storage itself is likely modest at current scale.

**UNLOCKS**
Historical drift dashboards, lineage explanations, and evidence-backed long-term prompt-system evolution.

**ALTERNATIVE EXPLANATION**
Git history plus deterministic rebuilds may be sufficient for occasional retrospective analysis; a permanent historical subsystem could be unnecessary at current scale.

**IMMEDIATE REJECTION EVIDENCE**
Reject present-tense implementation if fewer than two authoritative accepted epochs can be identified/reconstructed with stable ownership, or if the desired questions can be answered cheaply from existing Git/rebuild evidence without retained snapshots.

### Thesis D — Perform the dedicated AFK Agent Flow product cutover

**THESIS**
Use the now-explicit product-boundary contract to extract/build the dedicated AFK Agent Flow artifact/repository and stop relying on the combined Triage compatibility surface as the long-term product home.

**EVIDENCE**
PR #454 already made AFK vs Triage-local ownership machine-readable, identifies a target AFK repository, and explicitly names a governed AFK cutover as a successor.

**LEVERAGE**
Cleaner product identity, independent release/deployment lifecycle, reduced risk of shipping NTH/Triage-local behavior, easier portability and external reuse.

**TIMING**
Technically more feasible now than before #454.

**COST / COMPLEXITY**
High migration and release-governance cost. Dual-repo coordination, compatibility, release/versioning, documentation, Pages, and generated artifact parity all become migration surfaces.

**UNLOCKS**
A true standalone AFK product and cleaner repository responsibilities.

**ALTERNATIVE EXPLANATION**
The new product-boundary contract may already capture most maintenance benefit while the combined compatibility surface continues to work; extraction could create more coordination overhead than it removes.

**IMMEDIATE REJECTION EVIDENCE**
Reject near-term cutover if representative AFK changes now have one clear canonical owner and do not repeatedly collide with Triage-local surfaces, or if the target repository cannot preserve generated/runtime/release parity without duplicating authority.

### Thesis E — Prioritize Personal State + Private Sync runtime

**THESIS**
Implement local Personal State separation followed by encrypted `.pkenc` export/import to give Prompt Kit durable, portable user state before deeper learning/intelligence work.

**EVIDENCE**
PR #460 already defines logical stores, allowlisted Sync Capsule fields, transport rules, and an explicit successor sequence.

**LEVERAGE**
Favorites/collections/saved variants/preferences can become robust across local use and user-selected transfer without requiring a hosted backend.

**TIMING**
The governing privacy contract is already present on main.

**COST / COMPLEXITY**
Medium, with cryptographic UX/recovery and migration concerns.

**UNLOCKS**
Stronger personal product utility and a device-local substrate that later Local Journal/PrivacyReducer work can coexist with cleanly.

**ALTERNATIVE EXPLANATION**
This is important product execution but no longer a strategic uncertainty: #460 already selected and sequenced it. It may deserve P07 execution when prioritized rather than another repository-strategy investigation.

**IMMEDIATE REJECTION EVIDENCE**
Reject it as the *next strategic investigation* if existing contracts already make the next slice observable and bounded—which current evidence does. That does not reject the feature itself.

## 4. Falsification results

| Thesis | Result | Reason after challenge |
|---|---|---|
| A — Prompt Execution Evidence Spine | **SURVIVES** | Independent owners now overlap at lifecycle identity/provenance/retention boundaries, and the privacy contract makes the question timely. The architecture could still collapse to adapter-only; that is exactly what must be investigated. |
| B — Direct Phase D Passive Learning | **DEFERRED** | Valuable and newly feasible, but implementing now risks inventing a fourth evidence model before route/usage/outcome ownership is reconciled. Value also still needs later empirical proof. |
| C — Phase E Historical Intelligence | **DEFERRED** | Epoch semantics exist, but a durable accepted multi-epoch corpus is not yet demonstrated. Retention/admission should precede historical product work. |
| D — Dedicated AFK product cutover | **WEAKENED** | Product boundaries make it feasible, but the current compatibility surface remains intentional and working. The repository does not yet show stronger immediate leverage than the evidence convergence problem. |
| E — Personal State + Private Sync | **REJECTED as a scout target** | The strategic question is already resolved in #460; remaining work is bounded successor execution, not repository-level uncertainty. Preserve it for P07 prioritization rather than consuming P141/P95 discovery bandwidth. |

## 5. Strategic comparison

| Dimension | A Evidence Spine | B Direct D | C Historical E | D AFK Cutover |
|---|---|---|---|---|
| Evidence strength | Very high | High foundations, weak live value proof | Medium-high primitives, weak retained corpus | High ownership evidence |
| Recurrence / pressure | High across several lanes | Medium; future-facing | Medium; registry drift is real | Medium; portability intent is real |
| Cross-system leverage | **Very high** | High but topology-centered | Medium-high | High but product-boundary-centered |
| Downstream unlocks | **D + runtime eval + recovery + Collective Learning** | behavior-aware topology | historical drift/lineage | standalone AFK lifecycle |
| User/operator pull | High indirect evidence through repeated evidence/recovery contracts | Not yet measured | Low/medium | Medium |
| Architectural fit | Requires discrimination | Premature until A resolved | Good after retention owner | Good, already bounded by #454 |
| Implementation burden | Medium/high later; cheap design investigation now | High | Medium | High migration |
| Reversibility of next investigation | **Very high** | Low if runtime schema ships early | High | Medium |
| Dependency burden | Existing open PRs + #460 | A/privacy/runtime sources | retained epochs | target-repo/release/deploy |
| Measurability | High via compatibility/state-ownership criteria | Later via offline replay/quality metrics | High once epoch corpus exists | High via change sites/parity |
| Premature-abstraction risk | Medium, explicitly testable | **High** | Medium | Medium |
| Opportunity cost if delayed | **High** because open lanes may harden separately | Low/medium | Low | Medium |

## 6. Recommended thesis

**RECOMMENDED THESIS:** Resolve the minimal Prompt Execution Evidence Spine / lifecycle ownership architecture before implementing Phase D.

### Why this one

The strongest evidence is not that the repository needs “more telemetry.” It is that it already has several carefully bounded evidence mechanisms being built separately:

- recommendation/selection observation (#431),
- route-state truth (#450),
- outcome/evidence-state truth (#452),
- feedback/recovery routing already on main,
- repository AI eval orchestration already on main,
- device-local journal/privacy-reduction authority now on main (#460), and
- topology channels reserved for future behavioral evidence.

The architectural question is therefore both **timely and discriminable**: can these remain independent semantic owners while sharing enough lifecycle identity/provenance to compose safely? Answering that before integrating or extending them reduces the chance that Phase D creates another incompatible schema, leaks identifiers across privacy planes, or double-counts evidence.

### Why not the others

- **Not direct Phase D:** its source-of-evidence and lifecycle ownership are the unresolved part.
- **Not Phase E:** historical semantics outrun durable accepted-epoch retention.
- **Not AFK cutover:** valuable but does not address the current convergence of multiple live evidence/recovery/eval contracts.
- **Not Personal State/Private Sync strategy:** the strategy is already selected; it is an execution-priority decision, not an unresolved architectural thesis.

**CONFIDENCE:** HIGH. The recommendation is independently supported by current-main privacy/storage ownership, reserved topology behavior channels, the merged eval framework, and three mature open evidence/route/outcome lanes. Confidence is not certainty that a common spine should be built; P95 may correctly conclude that adapter-only composition is superior.

## 7. Cheapest discriminating investigation

### Route: P95 — Program Design & Call-Stack Prototype Architect

The unresolved uncertainty is **internal architecture/state ownership**, not external prior art and not yet an empirical behavior question. P82 therefore fails closed at this point.

### P95 admission dependency

P95 may start only after the Phase C closeout/handoff recovery floor required by `PHASE_C_HANDOFF.md` is reachable from refreshed main. That floor is [`PHASE_C_CLOSEOUT.md`](./PHASE_C_CLOSEOUT.md) beside the handoff: it records the integrated Phase C identity and strongest proof. The historical remote branch name `docs/prompt-topology-phase-c-closeout` pointed only at the Phase C hardening floor and must not be mistaken for that recovery pair.

### P95 mission

Determine whether current route, usage, outcome, recovery/eval, privacy-reduction, and topology behavior surfaces require:

1. a minimal common lifecycle envelope plus owner-specific payloads;
2. adapter-only interoperability with no common envelope; or
3. continued isolation with an explicit non-composition boundary.

Do not implement production feature behavior as part of this architecture investigation. P95 **may and should** create bounded non-production executable seam prototypes, representative call stacks, and explicit failure-propagation tests when needed to distinguish those alternatives. Prototype artifacts are evidence for the architecture decision; they are not authorization to ship Phase D or another production path.

### Required inputs

- integrated Phase C closeout/handoff pair on refreshed main;
- current `main` and `harness/contracts/prompt-kit-cross-device-access.v1.json`;
- current Phase A/B/C contracts;
- open PR #431 observation-corpus schema/runtime;
- open PR #450 prompt-routing receipt/control-plane contract;
- merged PR #452 outcome-receipt/classification contract on current main (`fd3b3910`);
- merged repository AI eval registry/framework;
- existing P99/P115 feedback/AFK routing capability and privacy restrictions;
- product-boundary contract only where lifecycle ownership crosses AFK/Triage surfaces.

### Required traces

Trace at least these three representative lifecycles and execute them through thin non-production seam prototypes where static mapping alone cannot prove ownership/failure semantics:

1. **Recommendation path:** Prompt Finder recommends prompts → user selects/open/copy → route decision → prompt invocation → later outcome observation → candidate eval/recovery.
2. **Autonomous repair path:** deterministic repository failure → outcome classification → recovery owner → reroute/repair decision → new receipt/outcome without double-counting the original failure.
3. **Phase D candidate path:** repeated local prompt transition/co-usage observations → device-local journal → PrivacyReducer → privacy-bounded aggregate → topology behavioral channel, with no user/session/project identity escaping the reducer.

### Required P95 artifact

Create one tracked design investigation beside the topology phase chain, proposed path:

`harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`

It must contain:

- state-owner/call-stack diagram or table;
- field-level identity/provenance/causality compatibility matrix for #431/#450/#452/#460;
- privacy-plane placement and retention for every field class;
- exact canonical owner for route truth, invocation/usage observation, outcome truth, recovery action, eval candidate, privacy-reduced aggregate, and topology advisory evidence;
- adapter boundaries and forbidden direction-of-authority flows;
- alternatives A/B/C above with concrete tradeoffs;
- collision/reconciliation implications for the three open PRs;
- executable prototype/test traces for representative success and failure propagation across every architecture alternative that survives static mapping;
- whether a new shared schema is actually necessary;
- minimal successor contract if one is necessary;
- explicit non-goals: no live collection, no production topology mutation, no network ingestion, no vector DB, no AFK extraction, no encrypted sync implementation.

### Decision rule

- **PROMOTE TO BOUNDED CONTRACT/IMPLEMENTATION:** exactly one architecture preserves all current semantic owners, maps all three traces without ambiguous lifecycle identity or duplicate persistence, obeys #460 privacy planes, survives representative executable seam/failure-propagation prototypes, and requires a bounded set of explicit adapters/contracts.
- **PREFER ADAPTER-ONLY / NO NEW SPINE:** existing schemas can compose through explicit adapters with no shared canonical envelope and no duplicated lifecycle truth, including through representative executable seam traces.
- **REJECT THE THESIS:** current owners should remain intentionally isolated and cross-linking adds more authority/coupling than useful evidence.
- **DEFER PHASE D:** any useful behavioral path requires prohibited data, undefined retention/consent, or an unimplemented prerequisite that dominates the architecture question.

### P82 admission disposition

**NOT ADMITTED YET.** The primary uncertainty is architecture/ownership. No single empirical metric can currently distinguish success because the lifecycle being measured is not yet canonically related across schemas. A Phase D prototype now would risk baking in the very ownership decision that P95 must discriminate. Thin P95 architecture prototypes do not count as P82 admission or Phase D implementation.

If P95 resolves the state model and the remaining question becomes “does privacy-bounded behavioral evidence materially improve recommendations/topology over the static baseline?”, then P82 becomes appropriate. That later P82 record must define an offline baseline, bounded fixture/replay corpus, measurable improvement criterion, and a REJECT outcome that can stop Phase D.

## 8. Successor phase horizon

| Phase / contract | State | Dependency / admission |
|---|---|---|
| Prompt Topology A | IMPLEMENTED / INTEGRATED | completed on main |
| Prompt Topology B | IMPLEMENTED / INTEGRATED | completed on main |
| Prompt Topology C viewer | IMPLEMENTED / VALIDATED / INTEGRATED | hardened through PR #459; recovery floor in `PHASE_C_CLOSEOUT.md` + `PHASE_C_HANDOFF.md` |
| Privacy/storage planes | DESIGNED / TRACKED / VALIDATED / INTEGRATED | PR #460 on main; runtime stores/reducer/sync not implemented |
| **P141 strategic scout** | **TRACKED by this document** | no production implementation |
| **Phase C closeout continuity** | **INTEGRATED RECOVERY FLOOR** | `PHASE_C_CLOSEOUT.md` + `PHASE_C_HANDOFF.md` on refreshed main; prerequisite for P95 |
| **P95 Evidence Spine architecture investigation** | **NEXT APPROVED OWNER** | integrated Phase C recovery floor + current main + evidence lanes + #460 + topology/evals |
| Open evidence lanes #431/#450 | IMPLEMENTED on branches, not integrated | reconcile only after P95 ownership decision |
| Outcome receipts #452 | IMPLEMENTED / INTEGRATED on main (`fd3b3910`) | current-main outcome truth for P95; do not re-analyze as an open branch |
| Phase D Passive Learning | AUTHORIZED FUTURE PHASE, DEFERRED BY STRATEGIC ORDER | evidence-spine ownership + later empirical value gate |
| Phase E Historical Intelligence | AUTHORIZED FUTURE PHASE, DEFERRED | authoritative accepted-epoch retention/corpus first |
| Personal State / Private Sync runtime | AUTHORIZED FUTURE BOUNDED EXECUTION | #460 already supplies strategy; prioritize separately under P07 when chosen |
| Dedicated AFK cutover | AUTHORIZED FUTURE MIGRATION, WEAKENED AS NEXT STRATEGIC BET | product-boundary parity + real extraction pressure |

## 9. Not now

- Do not add behavioral channels to canonical topology merely because their names are reserved.
- Do not merge #431 and #450 independently without checking their lifecycle/state ownership interactions against current main (including already-merged #452 outcome receipts).
- Do not create a generic analytics/event-bus abstraction as a demonstration of the evidence-spine thesis.
- Do not implement Local Journal, PrivacyReducer, Collective Learning ingestion, Private Sync, or hosted telemetry in this scout.
- Do not build a vector database.
- Do not turn transient Phase A/B generated artifacts into historical truth without a Phase E retention contract.
- Do not start the AFK repository cutover in this lane.
- Do not treat the stale local work queue as stronger evidence than provider PR/main truth; reconcile it only through its own owner if/when that becomes the selected work.

## 10. Proof ceiling

This scout proves repository/provider facts about current main contracts, merged/open PR state, declared schemas, phase boundaries, and existing proof ceilings. It supports a strategic judgment that architecture/state ownership is the highest-leverage next uncertainty.

It does **not** prove:

- that a common evidence-spine schema is necessary;
- that Phase D behavioral evidence improves recommendation or topology quality;
- that current users generate enough behavioral volume for learning;
- that any Collective Learning network design is anonymous in production;
- that Phase E history provides sufficient user/product value;
- that AFK extraction is economically preferable to continued compatibility composition;
- browser/device persistence, cryptographic sync, runtime model quality, or human acceptance.

Those unknowns belong to later owners and must not be promoted from this strategy document.

## 11. Continuation contract

**STRATEGIC ROUTE:** P95 — Program Design & Call-Stack Prototype Architect.
**ADMISSION DEPENDENCY:** verify the Phase C closeout/handoff recovery floor (`PHASE_C_CLOSEOUT.md` + `PHASE_C_HANDOFF.md`) is reachable on refreshed main before P95 begins.
**FIRST EXECUTABLE ACTION:** P95 owner refreshes current main, confirms the Phase C recovery pair, then traces Recommendation Path through routing, invocation, outcome, recovery/eval, privacy reduction, and topology-adjacent evidence into `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`.
**P95 FIRST ACTION AFTER DEPENDENCY:** refresh current main, confirm the Phase C closeout/handoff pair, resolve exact open #431/#450 heads plus merged #452 on main, trace the Recommendation Path across Prompt Finder/eval/privacy owners, and write the first state-owner/identity compatibility matrix plus the smallest representative executable seam trace in `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`.
**EXPECTED PROOF:** each lifecycle field has one semantic owner, one persistence/privacy plane, and explicit adapters or an explicit non-composition boundary; all three required traces are resolved; surviving alternatives are exercised through bounded non-production seam prototypes including failure propagation; no production feature implementation is present in the diff.
**P95 COMPLETION GATE:** architecture recommendation is durable, falsification-friendly, compatible with current privacy/topology/eval contracts, executable-prototype-backed where ambiguity remains, and specific enough to route the next bounded owner without reopening repository-wide strategy.