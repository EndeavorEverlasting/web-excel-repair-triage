# Prompt Kit Serverless Runtime Lifecycle — Bounded Execution Prompt

This document is the durable successor plan to PR #460. It is both the source-requirement disposition ledger and the single bounded execution prompt for the immediate successor implementation. The machine-readable lifecycle authority is `harness/contracts/prompt-kit-serverless-runtime-lifecycle.v1.json`.

## MISSION

Execute **Phase 1 — Local Storage Separation and Lifecycle** for Prompt Kit on the latest `main` floor after refreshing provider truth.

The mission is to make local Prompt Kit usage safe for ordinary devices with limited storage before adding encrypted cross-device transport or Collective Learning ingestion. Build one repository-native local lifecycle owner that separates Personal State from disposable Local Journal / reducer / retry / polling state, applies the contract retention bounds automatically, and exposes reachable user-clear controls. Preserve user-created durable state during automatic cleanup.

The immediate Phase 1 implementation must satisfy these observable outcomes:

1. Personal State, Local Journal, PrivacyReducer buffer, sync retry state, polling state, and secrets have distinct logical ownership.
2. Local Journal, reducer buffer, retry queue, and polling state cannot grow without the age/size/count bounds in the lifecycle contract.
3. Cleanup runs at the required lifecycle points and can delete expired/acknowledged disposable state without deleting Personal State.
4. A user can clear usage/Local Journal data, collective buffer data, and sync retry/polling state; clearing Personal State is a separate confirmed action.
5. If cleanup cannot restore bounded storage, telemetry/sync writes stop before Personal State is deleted.
6. Existing or incoming runtime owners that persist usage state, including PR #242's `promptKit.usage.v1`, must expose a reachable clear/delete operation or delegate to the canonical lifecycle owner.
7. Generated Prompt Kit outputs remain generator-owned and are regenerated only through the canonical builder.

This phase does **not** implement `.pkenc` encryption, cross-device pairing, automatic cloud transport, hosted/serverless ingestion, or network-anonymity claims.

The durable capability IDs are deliberately explicit so future refactors cannot silently drop a use case:

- `local-storage-separation-and-lifecycle`
- `encrypted-pkenc-export-import`
- `cross-device-pairing`
- `serverless-sync-transport`
- `privacy-reducer-runtime`
- `collective-learning-ingestion`
- `network-anonymity`

## SOURCE PROMPT DISPOSITION

| ID | Source requirement | Disposition | Surviving requirement / reason |
| --- | --- | --- | --- |
| S01 | Previously skipped runtime capabilities must remain part of the repo so they cannot disappear from future work. | included | `runtime_capability_horizon` and `phase_map` in the lifecycle contract retain local persistence, `.pkenc`, pairing, serverless sync, reducer runtime, ingestion, and network-anonymity investigation. |
| S02 | Architecture should move serverless rather than require an always-on Prompt Kit backend. | included | Architecture invariant is `serverless-local-first`; no always-on Prompt Kit server is required. |
| S03 | Plan the phase and the local sprint now. | included | This document is the durable whole-phase map; the immediate bounded prompt is Phase 1 Local Storage Separation and Lifecycle. |
| S04 | Prevent telemetry drift from becoming a user storage problem. | included | Disposable stores have age plus size/count caps, mandatory cleanup run points, and storage-pressure fail-closed behavior. |
| S05 | Provide a mechanism for deleting polling / pooled telemetry state regularly. | merged | Survives as bounded `polling_state`, `sync_retry_queue`, reducer-buffer deletion, delete-on-success/ack/expiry, and manual clear controls. Both persistent polling history and unbounded telemetry pooling are forbidden. |
| S06 | Preserve useful durable user state while cleanup runs. | included | Automatic cleanup must never delete Personal State or required decryption/recovery material. |
| S07 | Consolidate source prompts into one bounded execution prompt rather than concatenate them. | included | This document is the single bounded successor prompt; overlapping operational rules are merged into the sections below. |
| S08 | Create a source-requirement ledger with one disposition per requirement. | included | This table is the canonical ledger for the consolidated source requirements. |
| S09 | Resolve conflicts using fresh repository evidence rather than remembered chat state. | included | `REPOSITORY EVIDENCE REQUIRED` mandates current `main`, open PRs, changed files, canonical contracts, validators, CI, and generated owners. |
| S10 | Prefer the smallest coherent immediate mission and keep future work out of the current sprint. | included | Immediate scope is Phase 1 only; phases 2–5 remain tracked but forbidden for Phase 1 mutation. |
| S11 | Carry forward compatible forbidden-scope rules and add collision boundaries. | included | NTH/Billing, unrelated Prompt Kit UX, hand-edited generated HTML, secrets/real user data, crypto/sync/ingestion phases, and PR #242's separately owned runtime surface remain outside this planning sprint. |
| S12 | Execute when the environment permits; do not stop at plan-only output. | included | This planning/contract sprint creates tracked contract, plan, validator, tests, workflow, PR review reconciliation, and mainline integration; Phase 1 runtime begins only after this gate is integrated. |
| S13 | Preserve strongest practical validation and evidence typing. | included | Focused validator/tests first, then existing privacy/cross-device validators, generated parity, CI, exact-head PR proof, and post-merge main proof. |
| S14 | Keep actionable plans durable in repo/provider state, not chat-only. | included | This plan plus the machine-readable lifecycle contract are canonical; PR body references both. |
| S15 | Mainline integration is the normal completion state when gates permit. | included | Exact validated head must merge to current default branch and be revalidated/contained there. |
| S16 | Use available parallel workers when real sub-agent slots exist. | merged | Preserve the execution rule, but provider/tool concurrency is not called sub-agent parallelism. If no delegated-agent facility exists, execute serially. |
| S17 | Generated outputs must be changed only through canonical generators. | included | Phase 1 must modify canonical runtime inputs and use `scripts/build_prompt_kit_registry.py`; `web/prompt-kit/index.html` is never hand-edited. |
| S18 | Artifact-generation instructions from the generic source prompt. | deferred-to-docs | No workbook/document/image artifact is the target of this sprint beyond tracked repository contracts/docs; the generic artifact branch is not applicable to Phase 1 runtime. |
| S19 | Deferred documentation branch should exist when useful documentation should not enter the immediate sprint. | superseded | All documentation needed to execute this phase is itself an acceptance dependency and therefore belongs with the lifecycle contract; unrelated documentation remains outside scope rather than being forced into a separate PR. |
| S20 | Final output must include a next-agent handoff. | superseded | The durable repo plan is the handoff authority. Chat may summarize it, but no separate mega-prompt should compete with this canonical document. |
| S21 | Earlier closeout language that prohibited a next-agent prompt. | merged | Survives as: do not create a second competing handoff prompt when the canonical tracked plan already provides the executable continuation. |
| S22 | Existing PR #460 successor phases: local storage separation; `.pkenc`; automatic transport only if warranted; PrivacyReducer runtime then ingestion. | merged | Expanded into five dependency-ordered phases so retention, polling/retry cleanup, pairing, and anonymity investigation cannot fall through the cracks. |
| S23 | PR #242 may maintain local preference/usage state. | included | It is a known collision/readiness dependency: its bounded usage store must gain a reachable clear/delete path before merge after this contract lands. |
| S24 | Do not silently claim network anonymity or live ingestion from static contracts. | included | Network anonymity remains `investigate-first`; runtime/deployment/observation evidence is required before promotion. |
| S25 | Current mainline strategy (#461) requires Prompt execution evidence-spine/state-ownership architecture to be resolved before Phase D Passive Learning / Collective Learning runtime work. | included | Phase 4 now depends on Phase 1 **plus** Prompt Topology Phase C closeout and the routed P95 evidence-spine/state-ownership investigation. Phase 1 local lifecycle and Phase 2/3 private sync remain separately executable because #461 explicitly treats Personal State + Private Sync as already bounded successor execution. |

## CONFLICT RESOLUTION

1. **Durable favorites vs aggressive cleanup.** Storage minimization does not authorize deleting Favorites, collections, saved variants, preferences, tags, notes, workflows, or required decryption material. Automatic purge applies only to disposable journal, reducer, retry, and polling state. Personal State requires an explicit user action and confirmation.
2. **Serverless direction vs earlier “no backend required” rule.** These are compatible. “Serverless” means no always-on Prompt Kit server is required; future automatic sync or Collective Learning may use bounded serverless transport/ingestion without turning the service into an identity or raw-history backend.
3. **Collective Learning usefulness vs privacy.** Rich behavior stays local. Only PrivacyReducer output may cross the network. Exact timestamps, stable identifiers, raw text, project/repository context, and session traces remain forbidden.
4. **Telemetry usefulness vs storage pressure.** Storage limits win. When cleanup cannot restore bounds, telemetry/sync writes stop. The product remains usable locally.
5. **PR #242 runtime ownership vs this lifecycle sprint.** This lifecycle lane does not rewrite #242's gameplay surface. It establishes the contract and gate that #242 must satisfy when reconciled with current main.
6. **Generic “FINAL HANDOFF” requirement vs avoiding prompt duplication.** The complete durable handoff is this file plus the lifecycle contract. Do not create another long-lived prompt with competing requirements.
7. **Phase 4 local Collective Learning vs current evidence-spine strategy.** Do not implement `privacy-reducer-runtime` as a new parallel event model merely because storage/privacy bounds now exist. Before Phase 4, integrate Prompt Topology Phase C closeout and resolve the P95 Prompt Execution Evidence Spine/state-ownership investigation so existing route/usage/outcome owners can be adapted rather than duplicated.

## IMMEDIATE OWNED SCOPE

**Repo:** `EndeavorEverlasting/web-excel-repair-triage`

**Successor sprint:** `Prompt Kit Phase 1 — Local Storage Separation and Lifecycle`

**Lane:** Prompt Kit privacy/storage runtime lifecycle.

**Dependencies:**
- PR #460 is integrated and validated on `main`.
- `harness/contracts/prompt-kit-cross-device-access.v1.json` remains the parent privacy/storage authority.
- `harness/contracts/prompt-kit-serverless-runtime-lifecycle.v1.json` defines the exact lifecycle limits.
- Phase 1 is independent of the P95 evidence-spine investigation; Phase 4 is not. Phase 4 may begin only after Prompt Topology Phase C closeout is integrated and the P95 evidence-spine/state-ownership investigation is resolved.

**Owned implementation surfaces for Phase 1:**
- one canonical local lifecycle/storage owner under the existing Prompt Kit source pattern;
- lifecycle integration at actual local usage/state write sites;
- user-clear controls for usage/journal, reducer buffer, and retry/poll state;
- retention/cleanup tests;
- canonical builder/template changes required to wire the runtime;
- generated Prompt Kit output only through the builder;
- lifecycle validator/test updates needed to prove the implementation.

**Expected Phase 1 artifacts:**
- repository-native lifecycle implementation;
- age/size/count retention enforcement;
- cleanup triggers at startup, local writes, network/export boundaries, acknowledgements, and manual clear;
- reachable clear/reset operation for existing `promptKit.usage.v1` or its canonical replacement;
- tests proving Personal State survives automatic cleanup;
- tests proving telemetry/sync writes stop when bounded cleanup fails;
- regenerated Prompt Kit parity and green existing privacy/cross-device checks.

## FORBIDDEN SCOPE

Phase 1 must not mutate or implement:

- NTH/Billing behavior or contracts;
- unrelated Prompt Kit visual/interaction redesign;
- `.pkenc` cryptography/import/export beyond interfaces needed to preserve future compatibility;
- cross-device pairing/recovery UX;
- automatic cloud/serverless sync transport;
- Collective Learning network ingestion;
- Phase 4 PrivacyReducer behavioral-event integration before the Phase C closeout + P95 evidence-spine/state-ownership gate is resolved;
- claims of network anonymity;
- identity-backed analytics;
- raw Local Journal upload;
- secrets, real user data, real recovery material, or production credentials;
- hand edits to `web/prompt-kit/index.html` or any other generator-owned output;
- unrelated open-PR surfaces except where a collision must be documented or reviewed.

## REPOSITORY EVIDENCE REQUIRED

Before Phase 1 mutation:

1. Refresh provider truth and resolve actual default branch/head.
2. Inspect current/open/recent Prompt Kit PRs and changed files, especially local state/usage owners and generator surfaces.
3. Read the parent privacy/storage contract and this lifecycle contract from current main.
4. Inspect `docs/PROMPT_KIT_PRIVACY_STORAGE.md`, privacy validators/tests/workflows, canonical Prompt Kit builder, and generated parity checks.
5. Inspect any current usage-state implementation such as PR #242 rather than assuming its storage shape.
6. Search for existing clear/reset helpers, storage adapters, IndexedDB/localStorage owners, retention logic, and UI controls before inventing another implementation.
7. Read `harness/prompt-topology/POST_PHASE_C_STRATEGIC_SCOUT.md` and preserve its P95 admission gate before any Phase 4/Passive Learning mutation.
8. Record the exact base SHA and any separately owned collision surfaces.

Fresh repository/provider truth outranks this document if filenames or owners move; update this plan and contract in the same owned lane when that happens.

## EXECUTION CONTRACT

1. Translate Phase 1 acceptance criteria into executable tests before broad mutation.
2. Reuse existing Prompt Kit JavaScript/module conventions and builder wiring.
3. Implement the smallest canonical lifecycle owner that can service all disposable stores; do not create one cleanup implementation per feature.
4. Cleanup must be idempotent and safe to run frequently.
5. Apply both **time bounds** and **size/count bounds** so offline or high-volume use cannot grow storage indefinitely.
6. Cleanup ordering must prefer disposable polling/retry/reducer/journal state and must never automatically delete Personal State.
7. Persist no poll request/response bodies, poll-cycle history, or exact polling timestamps merely for diagnostics.
8. Keep retry state operational, not historical: delete it on success, permanent failure, expiry, disabled transport, size pressure, or manual clear.
9. Delete reducer batches after a positive export/ingestion acknowledgement; if no transport exists, age/size expiry still applies.
10. If retention cannot restore bounds because the storage API fails or is unavailable, stop telemetry/sync writes and preserve core Prompt Kit use.
11. Expose user-facing clear controls that distinguish disposable usage/telemetry state from durable Personal State.
12. Reconcile PR #242 or its successor only after the lifecycle owner is canonical; do not duplicate lifecycle logic inside gameplay code.
13. Before Phase 4, honor the current P95 evidence-spine/state-ownership admission gate; do not invent a fourth route/usage/outcome event model.
14. Keep capability states typed: planned, implemented, wired, validated, integrated, deployed, observed.
15. Iterate through implementation → focused validation → diff review → gap repair until no safe in-scope improvement remains.
16. Commit/push and merge the exact validated head when review/CI/protection gates permit, then prove the current default branch contains it.

## VALIDATION

Order validation from cheap/focused to broad:

1. lifecycle unit tests for retention, oldest-first eviction, delete-on-ack/success/expiry, and manual clear;
2. adversarial tests proving Personal State is not automatically deleted;
3. tests proving unbounded localStorage/IndexedDB append-only usage is rejected or routed through the lifecycle owner;
4. `python scripts/validate_prompt_kit_serverless_runtime_lifecycle.py --summary`;
5. `python -m unittest tests.test_prompt_kit_serverless_runtime_lifecycle -v`;
6. existing privacy/storage validator and tests;
7. existing cross-device validator and tests;
8. canonical Prompt Kit build/check and generated parity;
9. JavaScript syntax/runtime tests for touched modules;
10. repository deterministic/web/harness CI gates;
11. exact-head PR review and post-merge mainline verification.

Static or CI proof does not become physical browser/device observation. Browser quota behavior, storage pressure, actual mobile/browser clear behavior, cross-device encryption, serverless transport, and network metadata remain unproven until their phases produce runtime evidence.

## DEFERRED DOCUMENTATION BRANCH

No separate documentation PR is required for the immediate lifecycle phase because this document and the machine-readable contract are execution dependencies and must evolve with the implementation.

If unrelated explanatory or tutorial material is later useful, derive its branch name from the then-current repository convention and keep it independent of Phase 1 code. Such a lane may explain user controls and storage behavior but may not redefine retention limits, privacy boundaries, or phase acceptance gates; those remain owned here and in the lifecycle contract.

## FINAL HANDOFF

**Proven floor:** PR #460 integrated the four-plane privacy/storage contract. Main later integrated PR #461, which adds the P95 evidence-spine/state-ownership admission gate before Phase D/Collective Learning runtime work. This successor document and `harness/contracts/prompt-kit-serverless-runtime-lifecycle.v1.json` add the durable serverless runtime horizon plus bounded retention/deletion obligations without bypassing that gate.

**First executable successor action after this planning/contract sprint is integrated:** refresh `main`, inspect the current local usage/state owner(s), and implement the Phase 1 canonical lifecycle owner with tests before wiring it into generated Prompt Kit output.

**Completion gate for Phase 1:** disposable state is provably bounded and self-cleaning; clear controls are reachable; Personal State survives automatic cleanup; existing Prompt Kit privacy/cross-device/build gates remain green; the exact validated implementation is integrated into current `main`.
