# Prompt Kit audit of `michaelshimeles/skills`

**Status:** implementation audit / donor intake hardening

**Upstream:** `michaelshimeles/skills`

**Pinned source reviewed:** `513f8a24aae6383b00356fa285144b1bc3730dc1`

## Decision

Prompt Kit should not copy Michael Shimeles' seven skills wholesale or create seven new prompt identities. His repository is most useful as a continuously refreshed donor plus a set of concrete mechanics to compare against existing canonical owners. The correct system change is to register the donor in the external-resource intake plane, make root-level skill repositories enumerable, let P79's existing all-registered-source prior-art gate search it automatically, and strengthen existing owners only where a distinct residual remains.

The existing `ISOLATED WRITER / CONVERGENCE CONTRACT` is already stronger than `new-feature` on dependency-floor proof, sibling preservation, local convergence, provider-only fallback, and cleanup preservation. The upstream still exposes several useful concrete invariants that Prompt Kit should preserve as follow-on hardening rather than duplicate across prompts.

## Whole-repository skill audit

| Upstream skill | What the upstream contributes | Existing Prompt Kit coverage | Residual worth adopting | Canonical owner / disposition |
| --- | --- | --- | --- | --- |
| `new-feature` | Fresh task lane from current default, open-PR overlap check before writing, one worktree/branch per task, fresh dependency install, shared-resource warning, lockfile regeneration, cleanup after PR resolution. | Shared isolated-writer/convergence contract already requires refreshed provider truth, overlap inspection, dedicated writer lanes, sibling preservation, separate shared resources, dependency-order convergence, and preservation-gated cleanup. | Make fresh per-lane dependency installation explicit when the toolchain requires it; forbid hand-merging generated lockfiles when regeneration is canonical; keep task/worktree paths disposable and gitignored; distinguish harness-managed worktrees from manually created ones. | Strengthen the shared isolated-writer contract and its focused validator; no new prompt identity. |
| `code-structure` | Actions own why/when and domain policy; shared services own reusable how; explicit parameters, structured returns, no hidden DB reach-through, extract repeated operations rather than one-off logic, migrate caller-by-caller. | P95 already owns program architecture, canonical ownership, seams, deep modules, call stacks, and bounded prototypes. | Add an explicit orchestration-vs-mechanics test when repeated operational logic appears: domain state transitions/auth/error classification remain with orchestration; reusable provider/SDK/command mechanics use explicit inputs and structured results; extraction begins from real repetition, not speculative abstraction. | Strengthen P95 when this residual is confirmed against its current prompt; no new prompt identity. |
| `evidence-driven-testing` | Capture the failure before fixing it, bind evidence to exact revision/environment, annotate assertions, record passed/failed/untested rather than silently skipping, preserve crash-safe/repeatable artifacts, verify evidence after capture, and keep runtime evidence complementary to repository checks. | P94 and the shared evidence-state contracts already distinguish static vs live proof, protect accepted behavior, require current runtime evidence for runtime claims, and prevent evidence promotion. | Make before-state capture a default bug-fix gate when safely reproducible; require evidence receipts to name revision/environment and explicit untested reasons; verify captured media/output before citing it; keep the evidence artifact reproducible and separate from source. | Strengthen P94/evidence owners; no new prompt identity. |
| `before-and-after` | A narrow visual proof adapter with preflight, protected-preview detection, viewport-aware capture, existing-image reuse, and PR-ready comparison output. | Prompt Kit has live/browser proof owners and generated artifact parity, but no universal rule that every visual change needs this exact CLI. | Prefer a reusable before/after adapter for visible UI deltas; reuse evidence captured during development; do not let the adapter switch branches/start servers or invent the before state; treat protected preview/auth as a real gate. | Reference/adapt under P94 or the owning UX/browser proof workflow when a visible surface changes; no global prompt copy. |
| `greploop` | Bounded review-fix-push-review loop, fresh head binding, poll until the review for the current head completes, gather findings from multiple provider surfaces, fix actionable findings, resolve addressed threads, stop at explicit success or iteration ceiling. | Shared progress/retry/non-progress contracts already bound retries, invalidate stale proof, require exact-head evidence, and continue through review/integration. | Review freshness should be tied to the current head and latest updated review artifact; review aggregation should inspect all canonical provider surfaces before declaring zero findings; capped review loops should produce an exact residual instead of silently stopping. | Strengthen review/integration owners only where current provider logic lacks these checks. |
| `greploop-apps` | Same review loop plus a fallback for oversized PRs where the normal check run never appears and the bot edits an existing summary comment instead. | Prompt Kit already rejects stale/missing proof and requires current provider truth. | Treat "expected check never materialized but authoritative review surface updated" as a supported provider-specific fallback with freshness evidence, not an excuse to use stale review state. Large-PR fallback belongs in provider adapter logic rather than general prompt prose. | Provider/review adapter hardening; no new prompt identity. |
| `unslop` | A concrete cleanup pass for human-facing prose: remove filler, chatbot phrases, puffery, vague attribution, synthetic rhythm, and dense/passive wording while preserving intended tone. | Correspondence/document prompts already optimize human-facing writing, while repository prompts prioritize evidence semantics over house style. | Keep this as an optional/reusable writing-quality skill rather than a universal engineering policy. Applying its stylistic rules globally would conflict with domain-specific voice and existing output contracts. Use it for text the agent authored for humans, not untouched source prose. | Keep as registered external resource; adapt selectively through correspondence/document owners if a real gap appears. |

## Cross-skill workflow comparison

The upstream `AGENTS.md` composes the collection as `isolate -> build -> prove -> ship`, with prose cleanup applied to human-facing artifacts. Prompt Kit's stronger convergence model is `refresh -> select executable gate -> act -> validate -> critique -> integrate green slice -> refresh -> continue`.

These models are compatible. Prompt Kit should keep its stronger progress-state, freshness, recovery, proof-ceiling, and mainline-convergence semantics while borrowing the upstream's concrete adapters and narrow operational invariants. The donor should remain reference evidence, not Operant authority.

## Implemented in this slice

1. Register `michaelshimeles/skills` in `harness/contracts/operant-external-resource-intake.v1.json`.
2. Support `resource_root: "."` for repositories whose skill directories live at repository root.
3. Extend focused external-resource tests so the donor is mandatory in contract, tracked source floor, and P79's all-registered-source prior-art search.
4. Add a regression fixture proving root-level skill enumeration respects `max_depth`.
5. Generate the tracked resource index and gap ledger through the existing sync producer, never by hand, then require the normal external-resource workflow to prove exact parity.

## Follow-on residuals

These are not permission to add new prompt identities. Each must first be compared against its current canonical owner after the donor is part of the automated prior-art floor.

- Shared isolated-writer contract: fresh dependency install, canonical lockfile regeneration, disposable/gitignored lane paths, and harness-managed worktree deltas.
- P95: explicit orchestration-layer vs reusable-service-layer decision test for repeated operational mechanics.
- P94/evidence owners: before-state capture, exact revision/environment evidence receipts, explicit `untested` reasons, and post-capture evidence verification.
- Provider review adapters: current-head multi-surface review freshness and oversized-PR edited-summary fallback.
- Human-writing owners: optional `unslop`-style cleanup only where it does not conflict with a domain-specific voice contract.

## Proof ceiling

This audit proves that all seven upstream skills and the repository-level workflow were inspected at the pinned source revision and that the adoption decisions above are durably recorded. Repository tests and generated sidecar parity can prove donor registration/enumeration/search wiring. They cannot prove model obedience to the upstream skills, browser/video capture behavior that was not executed, Greptile availability, or the quality of future upstream changes.
