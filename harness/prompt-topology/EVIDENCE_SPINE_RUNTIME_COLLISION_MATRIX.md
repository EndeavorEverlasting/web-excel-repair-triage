# Evidence Spine Runtime — Write Collision Matrix

**Status:** TRACKED coordinator preflight (Panel 3)
**Floor:** `main@1583882c386ae41d3db87388a1f8e0c4026d0a81` (contains P95 architecture PR #473 + dispatch floor PR #467)
**Architecture authority:** `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`
**Rule:** A/B/C may run in parallel only on disjoint write sets below. Shared surfaces are coordinator-serialized.

## 1. Shared surfaces (coordinator-only writers)

| Surface | Why serialized | Current owner on main |
|---|---|---|
| `harness/contracts/*` shared lifecycle / correlation / continuation schemas | One writer per schema | Coordinator creates only if architecture §10 requires |
| `harness/evals/repository-ai-evals.v1.json` | Eval registry collision | Coordinator |
| Artifact / capability registries touching Evidence Spine | Shared registration | Coordinator |
| `web/prompt-kit/index.html` | Builder-owned generated | Coordinator via `scripts/build_prompt_kit_registry.py` only |
| Shared GitHub workflows that gate multiple lanes | Workflow ownership | Coordinator |
| Integration branch / mainline merge sequencing | Single integrator | Coordinator |

## 2. Lane write ownership (disjoint)

### Lane A — routing reconciliation (#450 adapt)

**Allowed writes (adapt onto current architecture; do not wholesale merge branch):**

- New/adapted route-receipt adapter modules under a dedicated path (prefer extending existing scripts only when equivalent on main)
- Fixtures/tests scoped to route receipts / destination confidence
- Donor concepts only: actor-neutral receipts, authoritative vs inferred destination, idempotency

**Forbidden writes:** P99 outcome schemas; P115 recovery queues; observation corpus; generated Prompt Kit by hand; privacy plane contracts.

**Donor evidence (read-only):** `origin/pr/450-head` files
`harness/contracts/operant-prompt-routing.v1.json`, `harness/schemas/prompt-route-receipt.v1.schema.json`, `scripts/operant_prompt_route.py`, `scripts/evaluate_prompt_route_receipts.py`, related fixtures/tests.

### Lane B — bounded observation (#431 adapt)

**Allowed writes:**

- Privacy-bounded observation adapter / local event helpers
- Tests proving ordinary open/copy ≠ success and raw content rejected
- Donor concepts only: bounded selection/usage observation, identity stripping

**Forbidden writes:** route control plane; outcome classification; ticket compiler; raw clipboard/prompt storage; generated HTML hand-edits.

**Donor evidence (read-only):** `origin/pr/431-head` observation/feedback pipeline files (reconcile against current main privacy lifecycle; do not resurrect superseded feedback designs blindly).

### Lane C — recurrence → finding → P115 work

**Allowed writes:**

- Recurrence aggregator + finding state representation
- Finding→P115-compatible work-request compiler
- Fixtures for thresholds, dedupe, post-fix reopen

**Forbidden writes:** route receipts; observation storage schema; P99 classifier fork; Prompt Kit UI redesign.

### Coordinator — continuation + integration

**Allowed writes:**

- Continuation resolver (`next_action` / completion-candidate supersession)
- Optional thin `evidence-correlation/v1` / `continuation-disposition/v1` if still required after lane seams land
- Combined integration tests
- Generated Prompt Kit rebuild if a lane legitimately changes consumer inputs
- Mainline merge sequencing

## 3. Parallel safety verdict

| Pair | Disjoint? | Notes |
|---|---|---|
| A × B | Yes | Different adapter domains |
| A × C | Yes | Route vs finding/ticket |
| B × C | Yes | Observation vs recurrence (C consumes P99, not raw B events, for tickets) |
| Any × Coordinator shared schemas/registries/HTML/workflows | No | Serialize |

**Dispatch rule:** After this matrix is on the integration floor, launch A/B/C concurrently only with pinned owned paths; coordinator holds shared contracts until lane PRs are dependency-ready.

## 4. Acceptance before lane mutation

1. Architecture revision is ancestor of current `main` (proven at matrix authoring).
2. Each lane PR lists exact file paths in its description matching this matrix.
3. Any path not listed requires coordinator amendment of this matrix first.
