# Prompt Execution Evidence Spine — Current-Floor Sprint Map

**Status:** TRACKED / ACTIONABLE
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Current evidence floor:** `main@d8ef87ebb0f98fb49061429f9561ed3781556f44`
**Architecture owner:** `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`
**Runtime owner:** `scripts/evidence_spine_runtime.py` + `harness/contracts/evidence-spine-continuation.v1.json`
**Continuity index:** `.ai/WORK_QUEUE.md` / TRQ-008

This map records the whole Evidence Spine dependency horizon on the refreshed repository floor. It replaces the stale launch order carried by open PR #471; chat and historical PR prose are not canonical execution state.

## Mission

Keep recommendation, routing, dispatch, invocation, outcome, recovery, recurrence, continuation, and privacy as separate semantic owners connected only by thin adapters. Preserve zero-metadata human clipboard fallback while enabling deterministic agent continuation and recurrence-to-work behavior without a universal event bus or identity-bearing telemetry.

## Proven floor

| Wave | State | Durable proof | What is proven |
| --- | --- | --- | --- |
| Panel 1 — autonomous dispatch floor | **PROVEN / INTEGRATED** | PR #467 → `a1e9caa17c6a979a3747edb71632a66c9406af00`; PR #477 → `d8ef87ebb0f98fb49061429f9561ed3781556f44` | capability ladder, executable dispatch manifest/receipt path, observed parallelism derived from overlapping lane intervals, runner failures preserved as lane failures |
| Panel 2 — P95 architecture | **PROVEN / INTEGRATED** | PR #473 → `1583882c386ae41d3db87388a1f8e0c4026d0a81` | adapter-only/no-new-spine decision, provenance/owner matrix, #450/#431 donor dispositions, continuation-resolver admission |
| Panel 3A — collision ownership | **PROVEN / INTEGRATED** | PR #474 → `eaa35ef3e940aca229bd8a82a3f7ceebd9c44182` | lanes A/B/C writer boundaries and coordinator-serialized shared surfaces |
| Panel 3B — minimal runtime seam | **PROVEN / INTEGRATED** | PR #475 → `edb42410941f67285e5cda1e5b5b462a5da90578` | deterministic continuation, route provenance, bounded observation privacy, recurrence aggregation, P115-compatible work-request compilation |
| Provider-wide adoption / live destination observation | **UNPROVEN** | none | no claim beyond exact repository/static/runtime tests |

## Current owner boundaries

- **P07 / dispatch:** `prompt-parallel-dispatch/v1` and its runner/receipt path own dispatch attempts and observed concurrency.
- **P99:** owns outcome classification and outcome receipts; no donor lane may redefine success/failure semantics.
- **P115:** owns recovery/work-request coordination.
- **Evidence Spine runtime:** owns deterministic continuation disposition, destination provenance gating, recurrence aggregation, observation privacy admission, and work-request compilation gates.
- **Privacy/storage contracts:** own retention and identity exclusion; no raw prompt, response, clipboard, transcript, user, session, project, or device identity may leak into collective/observation evidence.
- **PR #450:** donor only for routing-control-plane concepts until reconciled; never wholesale merge stale branch state.
- **PR #431:** donor only for bounded observation concepts until reconciled; selection intent never proves terminal success.
- **Generated Prompt Kit:** builder-owned; this program does not hand-edit `web/prompt-kit/index.html`.

## Remaining execution waves

### Wave 3 — Donor reconciliation and retirement — READY

**Owner:** Prompt Topology / P95 runtime convergence coordinator.

**Dependency:** integrated Panel 1–3B floor above; refresh exact current heads/diffs of #450 and #431 before any mutation.

**Owned scope:** concept-by-concept comparison of donor diffs to current architecture/runtime; adapt only genuinely missing admitted semantics; close stale donor PRs once their useful concepts are either contained, salvaged, or explicitly rejected.

**Forbidden scope:** stale wholesale merges; new lifecycle/event envelope; competing route/outcome/recovery classifier; raw telemetry; identity-bearing observation; Phase D.

**Files to inspect:** `scripts/evidence_spine_runtime.py`, `harness/contracts/evidence-spine-continuation.v1.json`, `tests/test_evidence_spine_runtime.py`, exact #450/#431 changed files, P99/P115 contracts, privacy/storage contracts.

**Files likely to change:** only current runtime/contract/tests when a donor concept is proven missing; otherwise coordination/PR disposition only.

**Expected artifacts:** donor disposition matrix, any bounded adapter/test repair, exact validator/test receipts, PR closure or salvage integration evidence.

**Validation:** focused Evidence Spine architecture/collision/runtime tests; any donor-owner tests for salvaged behavior; root harness/affected CI; `git diff --check`; refreshed-main containment.

**Proof ceiling:** repository/static/runtime-test integration. No provider-wide adoption claim.

**Completion gate:** each #450/#431 admitted concept has exactly one terminal disposition (`already-contained`, `salvaged`, `rejected/superseded`), no duplicate semantic owner remains, any salvage is on refreshed main with green owning gates, and superseded PRs are closed with evidence.

### Wave 4 — External/runtime observation — BLOCKED UNTIL A REAL TARGET EXISTS

**Owner:** external launcher/provider integration owner selected by actual runtime evidence.

**Dependency:** Wave 3 closed plus a named accessible runtime/provider that can emit invocation/route/outcome evidence without violating privacy contracts.

**Owned scope:** thin provider/launcher adapter and observed receipts for exact runtime(s).

**Forbidden scope:** fabricated destination, hidden credentials, provider-wide generalization, mandatory metadata on human clipboard fallback.

**Expected proof:** invocation/route/outcome receipts tied to exact runtime version and tested conditions.

**Proof ceiling:** OBSERVED only for the exact runtime/provider tested.

### Deferred — Phase D / Collective Learning

Remains outside this map until a separate empirical/value/privacy gate admits it. Do not add behavioral topology ingestion, hosted telemetry, vector DB, or Collective Learning transport as a side effect of donor reconciliation.

## Independent adjacent program

Compute-authority evaluation is tracked separately in `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md` / TRQ-007. Sprint 1 is already integrated via PR #464; its next repository-safe transition is Sprint 2 runtime-harness implementation. Do not couple its study registry to Evidence Spine donor reconciliation merely because both concern agents.

## Validation and integration order

1. Refresh current `main`, donor PR heads, reviews, checks, and changed-file sets.
2. Re-run current architecture/collision/runtime tests before donor comparison.
3. Build a donor concept matrix against current main; no mutation until each candidate concept has a current owner.
4. Reproduce any missing admitted behavior with a failing focused test before repair when practical.
5. Apply the smallest adapter/contract repair; never transplant stale donor branches wholesale.
6. Run focused and affected repository gates plus `git diff --check`.
7. Re-fetch current main and reconcile any moved dependency floor.
8. Integrate validated authorized work; prove refreshed-main containment and affected push CI.
9. Close superseded donor PRs only after their concept disposition is recorded.

## Proof typing

Keep `PLANNED/DESIGNED`, `TRACKED`, `IMPLEMENTED`, `WIRED/REACHABLE`, `VALIDATED`, `INTEGRATED`, `DEPLOYED`, and `OBSERVED` distinct. A schema, branch, PR, unit test, or merge never silently proves live provider adoption.

## First executable continuation

**Inspect PR #450 and PR #431 against refreshed `main` and the integrated architecture/runtime; classify every architecture-admitted donor concept as already-contained, salvage, or retire before writing code.** If a missing concept is reproducible, repair it under the current owner with a failing regression first; otherwise close the donor as superseded with containment evidence.

## Durability rule

This file is the canonical Evidence Spine execution map. Update it before handoff whenever sequencing, owner boundaries, donor dispositions, proof ceilings, or the first executable continuation materially change. `.ai/WORK_QUEUE.md` indexes this map but does not replace it.
