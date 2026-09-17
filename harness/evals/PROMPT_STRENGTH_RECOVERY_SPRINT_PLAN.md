# Prompt Strength Recovery Sprint Plan

**Canonical plan owner:** this file

**Repository:** `EndeavorEverlasting/web-excel-repair-triage`

**Original design floor:** `main@c99346be8269409ee5ecf24bdbbf33f9d6800bc1`

**Reconciled provider floor:** `main@80ead456dc6079997935105a77bf0690107aaf3a`

**State:** TRACKED / VALIDATING on PR #537; not yet integrated

**Mission:** restore and raise the semantic strength floor of operational prompts without duplicating active repair lanes, making hosted CI a single point of progress, or permitting an agent to stop silently at a tool/capability boundary.

## Completed floor

- PR #519 integrated Compute Mode and compiler-backed effective prompts.
- PR #534 integrated recurring-defect regression safety, including working/staged/exact-candidate patch hygiene.
- PR #536 integrated prompt-quality-history protection at `main@80ead456dc6079997935105a77bf0690107aaf3a`.
- The shared actionability policy carries compute, fixed-point, parallelism, evidence, convergence, durability, and recurring-defect doctrine.
- Registered upstream donor/reference sources include DeepSeek Harness, Matt Pocock skills, Michael Shimeles skills, and prompts.chat.
- `michaelshimeles/skills` was refreshed from audited `513f8a24...` to current `4b72f46b...`; only `README.md` changed, so the seven audited skill bodies remain semantically current.

## Active collision/dependency owners

| Owner | Reconciled state | Exact head / integration | Exclusive surfaces this plan will not steal |
| --- | --- | --- | --- |
| PR #533 | open external owner | `807af11f89f3253c676b79d7556f506a5fd890b5` | P07 effective-prompt identity focused repair/test |
| PR #535 | open external owner | `82d6d3ea55cfb408a93c60a2a229a2ab9c0f2b53` | local-proof continuity, repository actions, P07 compiler/build-context, shared actionability policy, generated Prompt Kit |
| PR #536 | integrated | head `79416fe...`; merge `80ead456...` | prompt-quality history contract, semantic migrations, validator/test/workflow |
| PR #524 | open external owner | refresh before collision-sensitive mutation | Compute Mode browser-observed proof lane; no Compute Mode semantic mutation here |

## Recovery principles

1. Prompt strength is a semantic repository invariant, not a prose-quality judgment.
2. Compiler/effective/profile representations preserve canonical obligations unless a governed semantic migration authorizes replacement.
3. Exhaustive mode increases useful depth; Efficient mode may reduce optional exploration but may not erase immutable evidence, ownership, continuation, integration, or truthful orchestration semantics.
4. Upstream skills contribute concrete mechanics with provenance; they do not replace Prompt Kit authority.
5. GitHub Actions and other hosted providers are adapters/proof surfaces, not the sole semantic or execution owner.
6. Shared contracts settle before parallel consumers.
7. Every legitimate stop states the exact completed fixed point, blocker, unsafe boundary, external gate, or exhausted authorized scope. Silent cessation is a regression while safe progress-bearing work remains.
8. Recurring whitespace/CRLF defects must be prevented by the smallest shared hook/check/validator owner, not repeatedly stripped from the latest diff.

## Phase map

### Phase 0 — Strength contract + adversarial matrix

**Owner:** strategic-harness owner / PR #537

**State:** IMPLEMENTED / VALIDATING

**Owned files:**
- `harness/contracts/prompt-strength.v1.json`
- `harness/evals/prompt-strength/adversarial-regression-matrix.v1.json`
- `scripts/validate_prompt_strength.py`
- `tests/test_prompt_strength_contract_prompt.py`
- `harness/test-floor.v1.json` registration
- validation receipt/template under `harness/evals/prompt-strength/`
- this plan and Phase-0 lane artifacts

**Implemented strengthening:**
- 21 typed strength dimensions with semantic evidence terms;
- 31 positive/negative adversarial cases, including PSA-031 silent-stop boundary regression;
- exact dependency revision/content anchors instead of PR-number-only claims;
- malformed dimension/profile/assertion structures fail closed;
- case profiles are restricted to supported execution profiles;
- adversarial dimension credits require matching semantic evidence;
- focused suite is registered through the deterministic prompt-semantic test convention.

**Acceptance:** exact-head focused validator/tests, deterministic floor, relevant harnesses, patch hygiene, and review reconciliation pass; no active external-owner surface is overwritten.

### Phase 1 — Reconcile active repair dependencies

**Hard dependencies:** #533 and #535 resolve or their exact surviving semantics are carried into the convergence candidate. #536 is already integrated.

**Mission:** refresh `main`, prove surviving P07 identity, local-proof continuity, and quality-history contracts; update this plan whenever their exact heads or integrated APIs materially change.

**Proof gate:** exact revision + current content + owning validators, not PR number or ancestry alone.

### Phase 2A — Upstream mechanics refresh

**State:** donor refresh performed; residual adoption remains successor work.

Refresh pinned identities for registered donor sources and maintain a provenance-rich residual map:
`source -> mechanic -> current owner -> existing coverage -> distinct residual -> disposition`.

Priority mechanics:
- real parallel/sub-agent dispatch and convergence;
- evidence-driven before/after proof;
- current-head review loops and multi-surface review freshness;
- orchestration-vs-reusable-mechanics separation;
- isolated writer dependency/resource hygiene;
- bounded review iteration with exact residuals.

No prompt identity creation merely because an upstream project has a separate skill.

### Phase 2B — Matrix-to-fixture implementation

**State:** Phase-0 mutation fixtures implemented for contract/schema/coverage/stopping defects; behavioral fixtures remain successor work.

Continue converting highest-risk matrix rows into executable negative fixtures and positive controls, reusing prompt-regression, compute-authority, prompt-parallel-dispatch, and compilation harnesses.

Priority: PSA-001/002/003/005/006/007/011/012/017/018/023/024/027/031.

### Phase 3 — Compiler/shared-policy wiring

**Canonical mutation owner:** PR #535 while it remains active.

Reconcile Phase-0 semantics into the smallest canonical shared owners and compiler policies through #535 rather than editing those surfaces from PR #537.

Required outcomes:
- profile-aware non-weakening rules;
- canonical/effective/detail/copy identity checks;
- local repository actions remain canonical and hosted CI remains an adapter;
- explicit stop/boundary reporting inherited by operational prompts;
- upstream residuals adopted only where distinct;
- no hosted-CI-only execution semantics.

### Phase 4 — Deterministic/local required-check integration

**State:** prompt-strength focused suite is registered in `harness/test-floor.v1.json`; the broader repository-local action owner is PR #535.

PR #535 must own the allow-listed repository action registry/runner and local merge-equivalent proof path, including recurring whitespace/CRLF prevention. Hosted workflows may call the same repository-owned command/profile but do not become the semantic owner.

### Phase 5 — Behavioral evaluation + publication

Use existing compute-authority/runtime evaluation to compare control vs strengthened prompts. Repository/static success is insufficient for OBSERVED downstream-agent-effectiveness.

After canonical shared-policy/compiler convergence, regenerate the Prompt Kit only through its registered builder and publish through the repository's active Pages contract. A stale release carrier must be refreshed rather than merged merely because it already exists.

## Current execution boundary

This ChatGPT runtime has provider mutation/review/CI access but its shell cannot resolve `github.com`, so it cannot truthfully claim a local clone/worktree or workstation-local action run. The observed boundary was `Could not resolve host: github.com`. That blocks only local-runtime proof; it does not block provider-side implementation, review repair, integration, or CI inspection.

## Proof ceiling

Phase 0 can prove repository/provider contract structure, adversarial semantic coverage, exact-head provider CI, and review reconciliation when those gates pass. It cannot prove local-workstation hooks/actions in this runtime, downstream model obedience, live sub-agent availability in another runtime, browser/device behavior beyond separately observed receipts, deployment until Pages is verified, or operator acceptance.

## Next transition

The exact local proof command remains repository-owned and must be resolved from current #535/main truth before operator guidance. On a capable local checkout, Phase-0 focused proof begins with:

```bash
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract_prompt -v
```

Then run the repository-owned deterministic/local-required-check action and patch-hygiene profile, reconcile #533/#535 exact heads, and advance integration/publication gates without silently stopping at a provider boundary.
