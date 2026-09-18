# Prompt Strength / Execution Reliability Closeout Program

**Canonical plan owner:** this file  
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`  
**Refreshed main floor:** `33a2296426c018c6652b6d925a434274f39b1b33`  
**Planning owner:** PR #537 / `feat/prompt-strength-contract-matrix-20260917`  
**State:** TRACKED / OPEN CLOSEOUT PROGRAM

## Mission

Close the remaining Prompt Kit strength, execution-boundary, local-proof, line-ending, publication, and observed-behavior gaps without asking each local agent to rediscover ownership. Every lane below has one primary mutation owner, explicit forbidden surfaces, deterministic gates, and a proof ceiling.

## Current proven floor

- #535 is merged: repository-local actions, exact-candidate hygiene, typed base/head context, safe receipt paths, and path+blob proof-relevance inputs are on main.
- #539 is merged: provider-degraded merge policy exists on main and does not erase local-proof requirements.
- #541 is merged at current main `33a22964...`: canonical P07 copy publication repair is on main.
- #542 is open and owns the execution-boundary control plane plus privacy-preserving failure observatory.
- #543 is open/draft and owns effective-P07 repository-local-proof continuity.
- #537 remains open and stale relative to current main; its semantic core is valuable but must not carry superseded dependency assumptions.
- #538 is the open Operant v0.9.0 release carrier; it is downstream of accepted mainline semantics and must be refreshed, not hand-edited around newer work.
- No tracked root `.gitattributes` exists on current main. Exact-candidate `git diff --check` exists, but repository-wide line-ending policy is not yet canonical.
- P67 compute-authority evaluation is integrated through its runtime harness; observed external-agent effectiveness remains `UNPROVEN_RUNTIME`.

## Ownership / collision map

| Surface | Owner | Rule |
|---|---|---|
| prompt-strength contract/matrix/validator | #537 | Lane 01 only until final #537 convergence |
| execution-boundary contract/taxonomy/engine | #542 core | Lane 02 |
| privacy failure observatory | #542 observatory | Lane 03 |
| effective P07 local-proof compiler semantics | #543 | Lane 04 |
| line-ending normalization / CRLF prevention | new isolated lane | Lane 05 |
| #542 shared branch convergence | #542 coordinator | Lane 06 |
| #537 stale-branch/main reconciliation | #537 coordinator | Lane 07 |
| generated Prompt Kit + release/Pages | existing builders + #538 | Lane 08 |
| observed downstream agent behavior | P67 / skill-evaluation | Lane 09 |

### Shared-file rules

- `harness/test-floor.v1.json`: #542/Lane 06 owns final reconciliation before #537 rebases. Lane 01 must not edit it merely to get green.
- `registry/prompts/actionable-next-step-policy.v1.json`: #542 owns current boundary-accountability strengthening. #537 must consume, not duplicate it.
- `web/prompt-kit/index.html`: generated only by `scripts/build_prompt_kit_registry.py`; never hand-edit. #543 may regenerate only when it is the next integration candidate; #542 and #537 must regenerate again after rebasing on newer main.
- `harness/repository-actions.v1.json`: #543 owns its active semantic delta. Lane 05 must not alter it.
- `.gitattributes`: Lane 05 exclusive owner until merged.

## Launch order

### Wave A — start concurrently

1. **Lane 01 — Repair #537 semantic core**
2. **Lane 02 — Close #542 execution-boundary core review**
3. **Lane 03 — Close #542 privacy-observatory review**
4. **Lane 04 — Close #543 effective-P07 local-proof continuity**
5. **Lane 05 — Add systemic line-ending / CRLF prevention**

These lanes have disjoint owned mutation surfaces when their forbidden scopes are respected.

### Wave B — converge and integrate low-collision lanes

6. **Lane 06 — Converge #542** after Lanes 02–03 and after current main includes any already-merged Lane 04/05 work.
7. Lane 04 and Lane 05 may integrate as soon as their exact candidates are green and mergeable; after either merges, every still-open downstream branch refreshes main before proof.

### Wave C — prompt-strength convergence

8. **Lane 07 — Reconcile and merge #537** only after #542 is integrated. Rebase/merge current main, drop superseded history-waiver edits, resolve `test-floor` against current main, rerun prompt-strength + quality-history + local required checks, then merge.

### Wave D — publication/release

9. **Lane 08 — Refresh #538 and verify public Pages** only after Lane 07 lands. Use Operant versioning automation to refresh the existing release branch/PR; do not manually create a second release workspace.

### Wave E — observed effectiveness

10. **Lane 09 — P67 external-agent pilot** only after strengthened prompts are integrated/published and treatment identity is frozen for a new evaluation generation.

## Lane definitions

### Lane 01 — #537 semantic-core repair

**Mission:** make the prompt-strength contract/matrix internally correct without touching shared owners currently held by #542/#543.

**Owned:** `harness/contracts/prompt-strength.v1.json`, `harness/evals/prompt-strength/adversarial-regression-matrix.v1.json`, `scripts/validate_prompt_strength.py`, `tests/test_prompt_strength_contract_prompt.py`, prompt-strength plan artifacts.

**Forbidden:** `harness/test-floor.v1.json` until Lane 07; shared actionable policy; P07 compiler semantics; generated HTML.

**Known defect:** PSA-029 currently over-credits `fixed_point_continuation`. Remove unsupported credit or strengthen the case only if the case truly tests that dimension. Do not weaken semantic-evidence validation.

**Gate:** focused validator/tests green on exact #537 head; no new review finding; branch may remain unmerged until Lane 07.

### Lane 02 — #542 execution-boundary core

**Mission:** close all still-valid core review findings in #542's boundary contract/validator/state-machine path.

**Owned:** execution-boundary contracts/taxonomy, boundary matrix, `scripts/execution_boundary_engine.py`, `scripts/validate_execution_boundary_enforcement.py`, focused boundary tests, final validator-profile registration needed by this feature.

**Forbidden:** failure-observatory implementation; #543 compiler/local-action files; #537 strength files.

**Known review obligations:** validate full layer shapes/responsibilities; derive required case IDs from the contract rather than a divergent hard-coded set; ensure blocking boundary validators are actually present in normal required/harness/pre-push profiles.

**Gate:** all core review threads resolved by current-head evidence; deterministic floor and affected validator profiles pass.

### Lane 03 — #542 privacy observatory

**Mission:** close privacy/stability findings without redesigning the execution-boundary core.

**Owned:** `scripts/failure_observatory.py`, `scripts/cursor_failure_sentinel.py`, privacy observatory contract/spec/validator/tests and its example hook config.

**Forbidden:** `harness/test-floor.v1.json`, shared prompt policy, core boundary taxonomy unless a failing test proves an unavoidable dependency.

**Known review obligations:** owner-only correlation-secret creation; sticky explicit interrupt; reject or reconcile invalid terminal receipts; validate persisted state before capsule emission; fail closed on malformed hook document/container shapes.

**Gate:** privacy negative canaries + focused tests pass; every unresolved review thread has repair/disposition evidence.

### Lane 04 — #543 effective-P07 local proof

**Mission:** finish the four-file P07 compiler/local-action delta, regenerate through the canonical builder when ready to integrate, and merge before #542/#537 final convergence if green.

**Owned:** `harness/contracts/prompt-language-compiler-policy.v1.json`, `harness/prompt-compilation/semantics/P07.json`, `harness/repository-actions.v1.json`, `tests/test_prompt_compilation.py`; generated Prompt Kit only at integration step.

**Known failures at `a641a85e...`:** Pages reports stale generated Prompt Kit; operational/order-navigation baseline detects the same product drift; deterministic canary fails because source/generated state is inconsistent. Diagnose before mutation, regenerate via builder, rerun `prompt-kit-proof`.

**Gate:** `python scripts/run_repository_action.py --action prompt-kit-proof --base-ref origin/main --report Outputs/repository-actions/prompt-kit-proof.json` PASS on exact candidate; affected hosted gates green or separately typed provider-only blocker; merge and verify containment on refreshed main.

### Lane 05 — CRLF / line-ending systemic prevention

**Mission:** close the recurring line-ending defect family at repository policy level instead of cleaning individual diffs.

**Owned:** new root `.gitattributes`; smallest existing regression-safety contract/validator/test changes needed to enforce it. Reuse existing `tests/test_prompt_regression_safety_prompt.py` when possible so no new test-floor registration is needed.

**Forbidden:** repository-action registry, generated Prompt Kit, #542/#543/#537 owned files, opportunistic whole-repo renormalization.

**Tasks:** inventory tracked text/binary extensions and current byte endings; define deterministic LF policy for cross-platform source/config/docs and explicit exceptions only where tool/runtime compatibility requires them; add negative fixture/mutation proving CRLF/attribute drift is caught plus positive control; prove no binary corruption; do not run `git add --renormalize .` across unrelated files unless a separately reviewed migration is required.

**Gate:** policy regression passes, existing regression-safety validator passes, working/staged/exact-candidate hygiene passes.

### Lane 06 — #542 convergence

**Depends on:** Lanes 02–03 complete; refreshed main contains any integrated Lane 04/05 work.

**Mission:** integrate the two #542 sublanes into one candidate, resolve shared `test-floor`/prompt-policy/generated-site surfaces once, rerun review, then merge.

**Gate:** no unresolved blocking review thread, all required checks green or honestly provider-blocked under current merge policy, builder parity, local required checks, exact-candidate hygiene, merge, post-merge containment/content proof.

### Lane 07 — #537 convergence

**Depends on:** Lane 01 + Lane 06 integrated.

**Mission:** refresh the stale prompt-strength branch onto current main and remove superseded assumptions.

**Required reconciliation:** current main already contains #535/#539/#541 and should contain #542/#543/CRLF by this stage. Re-evaluate whether #537 still needs any `prompt-quality-history` edit; delete branch-only waiver/history changes that are no longer necessary. Resolve `harness/test-floor.v1.json` from current main rather than replaying the old snapshot.

**Gate:** prompt-strength validator/tests, Prompt Quality History, deterministic floor, local required checks, builder parity, review reconciliation, exact-candidate hygiene, merge and post-merge containment.

### Lane 08 — website + Operant release

**Depends on:** Lane 07 integrated.

**Mission:** publish only accepted mainline Prompt Kit bytes and refresh the existing #538 release carrier.

**Authority:** `scripts/build_prompt_kit_registry.py` owns generated site; `.github/workflows/prompt-kit-pages.yml` owns Pages promotion; `.github/workflows/operant-versioning.yml` owns refresh of an already-open Operant release PR.

**Gate:** main builder parity -> main Pages deploy success -> #538 refreshed from current main by existing Operant automation -> exact release candidate checks -> merge release PR -> tag/release workflow proof. A PR preview is not production publication.

### Lane 09 — observed downstream behavior

**Depends on:** Lane 08 publication and a frozen treatment identity.

**Canonical owner:** P67 / `skill-evaluation`; reuse `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`.

**Mission:** execute the real 16-run external-agent pilot through a provider adapter satisfying `runtime/adapter-contract.v1.json`; do not create a second eval framework.

**Gate:** 16 classified paired runs, same provider/model identity per pair, no hidden-gold leakage, zero forbidden-mutation escape, pilot aggregate and fixture-validity disposition. Only then may Sprint 3/main study advance.

## Parallel capability / autonomy state

The dependency graph width is five in Wave A. This ChatGPT runtime has provider mutation and CI/readback access but no mounted local checkout and no evidenced autonomous local-agent runner, so it cannot prove local parallel dispatch itself.

**PARALLEL EXECUTION: DEGRADED** — graph width >= 2; local agent/runtime adapter is not bound in this environment.

**AUTONOMY_GAP:** a local strategic-harness runtime must bind the tracked manifest lanes to its evidenced agent runner. Human copy/paste is fallback only.

## Definition of done

The closeout program is complete only when:

1. #543 local-proof semantics are integrated.
2. #542 boundary/observatory semantics are integrated.
3. the line-ending systemic guard is integrated.
4. #537 prompt-strength semantics are reconciled to current main and integrated.
5. canonical Prompt Kit bytes from final main are deployed by Pages.
6. #538 is refreshed/merged/released under Operant authority.
7. P67 observed effectiveness is either completed at its exact runtime proof ceiling or remains explicitly `BLOCKED/UNPROVEN_RUNTIME` with adapter/credential gate; it may not be relabeled repository-complete.

## Proof ceiling

This plan and its deterministic repository gates can prove ownership, regression, integration, generation, and provider publication states when observed. They cannot by themselves prove local workstation hook execution in an unavailable runtime, universal downstream model obedience, or operator acceptance.
