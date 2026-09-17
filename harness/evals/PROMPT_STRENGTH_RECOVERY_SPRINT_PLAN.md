# Prompt Strength Recovery Sprint Plan

**Canonical plan owner:** this file  
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`  
**Provider floor at design time:** `main@c99346be8269409ee5ecf24bdbbf33f9d6800bc1`  
**State:** DESIGNED / TRACKED, not yet integrated  
**Mission:** restore and then raise the semantic strength floor of operational prompts without duplicating active repair lanes or making hosted CI a single point of progress.

## Completed floor

- PR #519 integrated Compute Mode and compiler-backed effective prompts.
- PR #534 integrated recurring-defect regression safety.
- Current `main` is `c99346be8269409ee5ecf24bdbbf33f9d6800bc1`.
- The shared actionability policy already carries compute, fixed-point, parallelism, evidence, convergence, and durability doctrine.
- Registered upstream donor/reference sources include DeepSeek Harness, Matt Pocock skills, Michael Shimeles skills, and prompts.chat.

## Active collision/dependency owners

| Owner | Status at plan creation | Exclusive surfaces this plan will not edit |
| --- | --- | --- |
| PR #533 | open | P07 effective-prompt identity repair carrier/test |
| PR #535 | open | local-proof continuity, repository actions, P07 compiler/build-context, shared actionability policy, generated Prompt Kit |
| PR #536 | open | prompt-quality history contract, semantic migrations, validator/test/workflow |
| PR #524 | open | Compute Mode browser-observed proof lane; no Compute Mode semantic mutation here |

## Recovery principles

1. Prompt strength is a semantic repository invariant, not a prose-quality judgment.
2. Compiler/effective/profile representations preserve canonical obligations unless a governed semantic migration authorizes replacement.
3. Exhaustive mode increases useful depth; Efficient mode may reduce optional exploration but may not erase immutable evidence, ownership, continuation, integration, or truthful orchestration semantics.
4. Upstream skills contribute concrete mechanics with provenance; they do not replace Prompt Kit authority.
5. GitHub Actions and other hosted providers are adapters/proof surfaces, not the sole semantic or execution owner.
6. Shared contracts settle before parallel consumers.

## Phase map

### Phase 0 — Strength contract + adversarial matrix

**Owner:** strategic-harness owner  
**State:** current plan slice  
**Owned files:**
- `harness/contracts/prompt-strength.v1.json`
- `harness/evals/prompt-strength/adversarial-regression-matrix.v1.json`
- `scripts/validate_prompt_strength.py`
- `tests/test_prompt_strength_contract.py`
- this plan

**Acceptance:** validator and focused tests pass; every strength dimension has adversarial coverage; no active PR owned surface is modified.

### Phase 1 — Reconcile active repair dependencies

**Hard dependencies:** #533, #535, #536 resolve or their exact surviving semantics are carried into the convergence candidate.  
**Mission:** refresh `main`, prove surviving P07 identity, local-proof continuity, and quality-history contracts; update this plan only if their integrated APIs differ from the design assumptions.

**Proof gate:** current-content + owning validators, not ancestry alone.

### Phase 2A — Upstream mechanics refresh

**Parallel-safe after Phase 0; read-only until owner mapping is settled.**  
Refresh pinned identities for the registered donor sources. Produce a provenance-rich residual map:
`source -> mechanic -> current owner -> existing coverage -> distinct residual -> disposition`.

Priority mechanics:
- real parallel/sub-agent dispatch and convergence;
- evidence-driven before/after proof;
- current-head review loops and multi-surface review freshness;
- orchestration-vs-reusable-mechanics separation;
- isolated writer dependency/resource hygiene;
- bounded review iteration with exact residuals.

No prompt identity creation.

### Phase 2B — Matrix-to-fixture implementation

**Parallel-safe with Phase 2A after Phase 0.**  
Convert the highest-risk matrix rows into executable negative fixtures and positive controls, reusing the existing prompt-regression, compute-authority, prompt-parallel-dispatch, and compilation harnesses.

Start with: PSA-001/002/003/005/006/007/011/012/017/018/023/024/027.

### Phase 3 — Compiler/shared-policy wiring

**Depends on Phases 1, 2A, 2B.**  
Strengthen the smallest canonical shared owners and compiler policies. Do not bulk edit prompt bodies when a shared owner can carry the invariant. Reconcile with #535/#536 instead of overwriting them.

Required outcomes:
- profile-aware non-weakening rules;
- canonical/effective/detail/copy identity checks;
- upstream residuals adopted only where distinct;
- no hosted-CI-only execution semantics.

### Phase 4 — Deterministic floor integration

Register the focused prompt-strength validator/tests and selected adversarial fixtures with the repository-owned local required-check/test floor. Hosted workflows, when available, call the same repository-owned commands.

### Phase 5 — Behavioral evaluation

Use the existing compute-authority/runtime evaluation harness to compare control vs strengthened prompts. Repository/static success remains insufficient for an OBSERVED downstream-agent-effectiveness claim.

## Parallel groups

After Phase 0 is integrated or pinned as a dependency:
- **Group A:** Phase 2A upstream read-only refresh.
- **Group B:** Phase 2B adversarial fixture implementation.
- **Group C:** local-proof/test-floor compatibility analysis against the eventual #535/#536 integration result, read-only until those dependencies settle.

Phase 3 is the singular convergence owner for shared policy/compiler mutation.

## Proof ceiling

This plan plus Phase 0 can prove a durable semantic contract, adversarial coverage design, and focused validator behavior. It cannot prove downstream model obedience, actual sub-agent availability in another runtime, hosted CI, live browser/device behavior, deployment, or operator acceptance.

## Next transition

A local strategic-harness agent should first refresh provider/default-branch truth, verify this plan/contract branch or merged commit still applies, run:

```bash
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract -v
```

Then reconcile the exact surviving semantics of PRs #533, #535, and #536 before any shared-policy/compiler mutation.
