# Prompt Strength / Execution Reliability Closeout Program

**Canonical plan owner:** this file  
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`  
**Refreshed main floor:** `33a2296426c018c6652b6d925a434274f39b1b33`  
**Planning owner:** PR #537 / `feat/prompt-strength-contract-matrix-20260917`  
**State:** TRACKED / OPEN CLOSEOUT PROGRAM

## Mission

Close the remaining Prompt Kit strength, execution-boundary, local-proof, line-ending, publication/release, and observed-behavior gaps with explicit owners and gates so a local agent can execute without reconstructing the architecture.

## Current proven floor

- #535 is merged: repository-local actions, exact-candidate hygiene, typed base/head context, restricted receipt paths, and path+blob proof fingerprints are on main.
- #539 is merged: provider-degraded merge policy exists on main without erasing local-proof requirements.
- #541 is merged at current main `33a22964...`: canonical P07 copy publication repair is on main.
- #542 advanced concurrently to `c6e330fe6676a974a79cf384dd279edfea4a9ab3`; all review threads are resolved on that head. Its remaining observed defect is deterministic external-resource projection drift: the live candidate differs from tracked `web/prompt-kit/resources.v1.json`. Several exact-head checks were still in progress at the last refresh.
- #543 remains open/draft at `a641a85e...` and owns effective-P07 repository-local-proof continuity. Its observed failing checks are consistent with stale generated Prompt Kit bytes.
- #537 remains open and stale relative to current main; its semantic core is valuable but final convergence waits for newer owners to integrate.
- #538 is the open Operant v0.9.0 release carrier and is downstream of accepted mainline semantics.
- No tracked root `.gitattributes` exists on current main. Working/staged/exact-candidate whitespace checks exist, but repository-wide line-ending normalization is not declared.
- P67 compute-authority runtime harness is integrated; observed external-agent effectiveness remains `UNPROVEN_RUNTIME`.
- P66/work-queue indexing is collision-blocked by open PR #524, which owns `.ai/WORK_QUEUE.md`. This file remains the complete plan owner until that ledger can be reconciled without a competing writer.

## Retired work discovered during planning

The original #542 core/privacy repair sublanes are **RETIRED / SUPERSEDED**. Concurrent work closed every #542 review thread before this plan reached dispatch. Do not launch Lane 02 or Lane 03 from older copies of the plan. Their only remaining value is historical/recovery context.

## Active ownership / collision map

| Surface | Owner | Rule |
|---|---|---|
| prompt-strength contract/matrix/validator | Lane 01 / #537 | semantic repair only; shared floor waits for Lane 07 |
| effective-P07 compiler/local-proof | Lane 04 / #543 | integrate before #542 final convergence |
| CRLF / repository line endings | Lane 05 | exclusive new `.gitattributes` owner |
| #542 current candidate + resource projection | Lane 06 / #542 | final repair/integration owner |
| #537 stale-branch/main reconciliation | Lane 07 / #537 | only after Lane 06 |
| generated Prompt Kit + release/Pages | Lane 08 | builders/workflows only |
| observed downstream agent behavior | Lane 09 / P67 | existing evaluation system only |

### Shared-file rules

- `harness/test-floor.v1.json`: current #542/main authority resolves before Lane 07. Lane 01 must not edit it.
- `registry/prompts/actionable-next-step-policy.v1.json`: current #542/main authority; #537 consumes rather than duplicates.
- `harness/repository-actions.v1.json`: #543 owns its active semantic delta.
- `web/prompt-kit/index.html`: generated only by `scripts/build_prompt_kit_registry.py`. Lane 04 integrates first; Lane 06 refreshes main and regenerates again if its sources require it.
- `web/prompt-kit/resources.v1.json` and `registry/resources/operant-external-resource-gaps.v1.json`: Lane 06 owns current donor projection drift using `scripts/sync_operant_external_resources.py`.
- `.gitattributes`: Lane 05 exclusive owner until integration.

## Launch order

### Wave A — graph width 3; launch concurrently when a real adapter exists

1. **Lane 01 — Repair #537 semantic core**
2. **Lane 04 — Close #543 effective-P07 local-proof continuity**
3. **Lane 05 — Add systemic CRLF / line-ending prevention**

### Wave B — #542 finalization

4. **Lane 06 — Repair donor projection drift and integrate #542**

Lane 06 depends on Lanes 04 and 05 for mutation/integration so it can refresh the newest main and avoid generated-artifact / checkout-policy proof churn. Read-only diagnosis of #542 may occur earlier.

### Wave C — prompt-strength convergence

5. **Lane 07 — Reconcile and merge #537** after Lane 01 + Lane 06.

### Wave D — publication/release

6. **Lane 08 — Verify final main Pages and refresh/merge #538** after Lane 07.

### Wave E — observed effectiveness

7. **Lane 09 — P67 external-agent pilot** after publication and treatment freeze.

## Active lane definitions

### Lane 01 — #537 semantic-core repair

**Owned:** prompt-strength contract, matrix, validator, focused test, plan artifacts.  
**Forbidden:** `harness/test-floor.v1.json`, shared actionable policy, P07 compiler/local actions, generated site, #542 files.  
**Known defect:** PSA-029 over-credits `fixed_point_continuation`. Repair the case, not the semantic-evidence validator.  
**Gate:** focused prompt-strength validator/tests + patch hygiene on exact #537 head. Do not merge; hand off to Lane 07.

### Lane 04 — #543 local-proof closure

**Owned:** compiler policy, P07 semantics, repository actions, prompt-compilation test; generated site only via builder.  
**Known defect family:** source/generated parity at `a641a85e...`; Prompt Quality History already passed while Pages/order-navigation/deterministic generated-site checks failed.  
**Gate:** compiler tests -> canonical generation -> `prompt-kit-proof` local action -> builder parity -> exact candidate checks -> merge #543 -> main containment.

### Lane 05 — line-ending systemic guard

**Owned:** new root `.gitattributes` plus minimum regression-safety contract/validator/test changes.  
**Forbidden:** whole-repo opportunistic renormalization, repository-action registry, generated Prompt Kit, active PR-owned files.  
**Gate:** inventory text/binary behavior, deterministic policy, CRLF negative fixture + positive control, regression-safety PASS, working/staged/exact-candidate hygiene, merge.

### Lane 06 — #542 finalization

**Depends on:** Lane 04 + Lane 05 integrated.  
**Current #542 state:** head `c6e330fe...`; zero unresolved review threads.  
**Current defect:** workflow built a live donor candidate that differs from tracked `web/prompt-kit/resources.v1.json`. This is candidate drift, not provider degradation.

Reproduce/update through the canonical producer:

```bash
mkdir -p Outputs/operant-external-resources
python scripts/sync_operant_external_resources.py \
  --output Outputs/operant-external-resources/resources.v1.json \
  --gaps-output Outputs/operant-external-resources/gaps.v1.json
cmp Outputs/operant-external-resources/resources.v1.json web/prompt-kit/resources.v1.json
cmp Outputs/operant-external-resources/gaps.v1.json registry/resources/operant-external-resource-gaps.v1.json
```

If drift is confirmed, run the canonical producer with its default tracked outputs rather than manually editing JSON:

```bash
python scripts/sync_operant_external_resources.py
```

Then validate external resources, builder parity, local required checks, exact-candidate hygiene, exact-head provider checks, merge #542, and prove current-main containment.

### Lane 07 — #537 convergence

**Depends on:** Lane 01 + Lane 06.  
Refresh stale #537 onto current main; resolve `test-floor` from current authority; re-evaluate and drop obsolete branch-only prompt-history/waiver edits if current main already proves P07 containment. Preserve prompt-strength evidence hardening and PSA-031 unless a stronger governed migration explicitly supersedes them.  
**Gate:** Prompt Quality History + prompt-strength + deterministic/local required checks + builder parity + review reconciliation + exact-candidate hygiene -> merge -> main containment.

### Lane 08 — Pages / Operant release

**Depends on:** Lane 07.  
Builder owns generated Prompt Kit; Pages workflow owns public deployment; Operant versioning workflow owns refresh of existing #538.  
**Gate:** final main builder parity -> successful main Pages deployment -> #538 refreshed in place -> release checks -> merge -> tag/GitHub Release exact identity.

### Lane 09 — P67 observed behavior

**Depends on:** Lane 08 and frozen treatment identity.  
Reuse `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`; run the real 16-run external-agent pilot through its adapter contract.  
**Gate:** 16 classified paired runs, same runtime identity per pair, zero hidden-gold leakage/forbidden mutation escape, pilot aggregate/fixture-validity disposition. No adapter/credential/quota means `UNPROVEN_RUNTIME`, not a fake PASS.

## Parallel capability / autonomy state

The active dependency graph width is **3**. This ChatGPT runtime has provider mutation/readback but no mounted local checkout or evidenced local autonomous-agent runner.

**PARALLEL EXECUTION: DEGRADED — graph width 3; no safe bound autonomous local-agent adapter in this runtime.**

**AUTONOMY_GAP:** a local strategic-harness runtime must bind the tracked `runtime_tool` lanes in `Outputs/prompt-parallel-dispatch/manifest.json` to its proven repo runner and preserve a compatible dispatch receipt. Human copy/paste is fallback only.

## Definition of done

1. #543 is integrated with current generated Prompt Kit parity.
2. repository line-ending policy/regression is integrated.
3. #542 donor projection drift is repaired and #542 integrated.
4. #537 semantic core is reconciled to strengthened main and integrated.
5. final main Prompt Kit is successfully deployed through Pages.
6. #538 is refreshed/merged/released under Operant authority.
7. P66/work-queue index is reconciled after #524 releases `.ai/WORK_QUEUE.md`.
8. P67 observed effectiveness is either completed at its exact runtime proof ceiling or remains explicitly `BLOCKED/UNPROVEN_RUNTIME` with its exact adapter/credential gate.

## Proof ceiling

This plan and repository gates can prove ownership, regression, integration, generation, and provider publication states when observed. They do not by themselves prove local workstation hook execution in an unavailable runtime, universal downstream model obedience, or operator acceptance.
