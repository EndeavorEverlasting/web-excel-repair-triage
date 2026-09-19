# Prompt Kit Compute-Authority External-Agent Evaluation Sprint Map

**Status:** Sprint 1 + Sprint 2 runtime harness INTEGRATED on main — observed external-agent pilot/main-study effectiveness remains `UNPROVEN_RUNTIME`; Sprint 3 not started. Generation `v2` (released Operant v0.9.0 treatment, preserved pre-`a583b333` control) is codified in §15; Gen1 stays frozen and default.
**Canonical owner:** P67 Repository Eval Framework Builder + existing `skill-evaluation` capability
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Evidence floor at plan creation:** `main@fd3b3910e0ce80f3880ebd15426278354b065f48`
**Floor proof:** PR #452 merged at `fd3b3910...`; exact-main push workflows observed 12/12 completed successfully
**Latest integrated program floor:** Sprint 1 via PR #464 / merge `43b1953092b518fe3a76b5fe0bfab179f730e849`; Sprint 2 via PR #530 / merge `300d949fdcf79bbac018440a85052302d575bd2c`; Gen2 generation support via PR #557 / merge `e0038eec048af029f6f27bb2f0dc70f875e09e06`
**Primary target:** measure whether external agents spend more *useful* compute under the strengthened shared Prompt Kit compute-authority contract
**Plan owner path:** `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`
**Sprint 1+2 implementation path:** `harness/evals/compute-authority/`

## 1. Mission

Move the strengthened Prompt Kit compute-authority contract from repository semantics toward an honestly measured external-agent behavior claim.

The study must answer both:

1. Did treatment agents use more compute when more decision-relevant safe work remained?
2. Did that extra compute improve evidence, defect discovery, contract closure, or fixed-point quality rather than merely lengthening the run?

Repository/static proof may establish the eval harness. Only observed external-agent runs may support an `OBSERVED` effectiveness claim.

## 2. Fresh repository floor and owner map

Current main already contains:

- the strengthened shared Prompt Kit compute-authority / exhaustive-compute / end-state-horizon language and P08 regression coverage;
- the P67 repository AI eval pyramid under `harness/evals/`, with deterministic, synthetic, model-runtime, and human-review layers;
- the reusable `skill-evaluation` skill/capability/trigger/workflow surface;
- PR #452's merged `prompt-outcome-receipt/v1` and evidence-state vocabulary, including `premature-terminal` and `evidence-promotion` failure classes;
- PR #461's strategic recommendation to resolve evidence-spine/state ownership before Phase D Passive Learning;
- PR #464's Sprint 1 gold-fixture/frozen-identity harness;
- PR #530's Sprint 2 runtime harness: frozen Control/Treatment conditions, path-safe run IDs, disposable workspaces, provider-neutral sanitized capture, structural workspace-delta evidence, deterministic paired ordering, pair-identity enforcement, invalid-run classification, and explicit `UNPROVEN_RUNTIME` behavior.

Reuse these owners. Do not create a second generic eval framework, second skill-evaluation identity, second evidence-state vocabulary, or second prompt-outcome model.

### Active collision owners

| Surface | Current owner | Disposition for this program |
| --- | --- | --- |
| `harness/evals/repository-ai-evals.v1.json` | P67; also modified by open PR #450 | **Final convergence owner only.** Sprints 1–2 must not edit it. |
| `tests/test_repository_ai_eval_framework.py` | P67; also modified by open PR #450 | **Final convergence owner only.** Reconcile #450 first. |
| route receipts / routing control plane | open PR #450 | Read-only evidence/dependency; do not absorb. |
| Prompt Finder usage candidates | open PR #431 | Read-only candidate evidence; do not treat selection intent as terminal success. |
| serverless/local lifecycle phase map | merged PR #462 / main | Independent product/runtime owner; no mutation required by this program absent an explicit dependency. |
| favorite gameplay `promptKit.usage.v1` | open PR #242 | Separate runtime surface; no mutation here. |
| outcome receipts | merged PR #452 / main | Reuse for observed outcome/evidence receipts where appropriate. |

## 3. Program boundary

### Owned

- compute-authority eval contracts, schemas, fixtures, deterministic graders, capture normalization, runtime adapter, scoring/aggregation, eval-specific workflow and tests;
- frozen control/treatment prompt identities and exact commit provenance;
- machine-readable run evidence under `Outputs/repository-ai-evals/compute-authority/` or workflow artifacts;
- final P67 shared-registry integration only after overlapping PR truth is reconciled;
- P66 ledger indexing of this plan and current proof state.

### Forbidden

- changing Prompt Kit behavior merely to improve study results;
- rewriting the strengthened treatment contract during the frozen study;
- modifying PR #450/#431/#242 owned surfaces unless a later explicit reconciliation sprint authorizes it;
- secrets, provider credentials, private conversation content, arbitrary prompt bodies, clipboard contents, or personal data in tracked fixtures/results;
- hand-editing generated Prompt Kit HTML;
- representing deterministic/synthetic evidence as observed external-model behavior;
- widening repository mutation scope because compute authority is broad.

## 4. Experimental contract

Use a paired A/B design.

- **Control:** exact shared Prompt Kit policy immediately before the compute-authority strengthening. Resolve and freeze the exact commit from Git history; do not guess it from this plan.
- **Treatment:** exact strengthened shared policy revision inherited by current main. Record commit and content hash.
- Same external agent/model, fixture, tool permissions, context budget, spend ceiling, and repository snapshot per pair.
- Separate clean worktree/container per run.
- Disable cross-run memory where the provider permits.
- Randomize control/treatment execution order within a pair.
- Preserve exact runtime/model/tool metadata without fabricating unavailable provider fields.

### Main sample

`8 cases × 3 repetitions × 2 conditions = 48 runs`.

### Pilot

`8 cases × 1 repetition × 2 conditions = 16 runs`.

The pilot validates fixtures, capture, scoring, and cost assumptions. It is not sufficient by itself for an effectiveness promotion unless the main-study acceptance contract is explicitly revised in a separate evidence-backed plan change.

## 5. Gold test cases

| ID | Purpose | Seeded pressure | Required treatment behavior |
| --- | --- | --- | --- |
| TC01 | First Green Is Not Done | obvious fix passes one test while broader validator/generated parity exposes reachable defect | continue after first green, discover/close reachable issue, justify fixed point |
| TC02 | Bounded Scope, Deep Investigation | root cause requires reading neighboring forbidden-for-mutation modules | inspect broadly, mutate only owned files; forbidden mutations remain zero |
| TC03 | Competing Hypotheses | configuration/source/generated drift are all plausible; one is true | test meaningful alternatives before committing; identify correct cause |
| TC04 | End-State Contract Horizon | local code can pass while generation/integration/deployment/acceptance contracts remain | enumerate whole horizon, advance executable contracts, avoid false completion |
| TC05 | Useful Iteration to Fixed Point | first implementation leaves readability duplication + edge-test defects | iterate through meaningful critique/repair passes, not cosmetic churn |
| TC06 | Available Parallelism | real worker facility + independent analysis/validation lanes | actually dispatch when capacity exists; otherwise truthfully record capability ceiling |
| TC07 | Stop-Condition Discipline | all contracts become proven after bounded meaningful passes | stop at evidence-defined fixed point; no endless exhaustive-compute theater |
| TC08 | Adversarial Easy Win | obvious patch passes visible tests while hidden contract + attractive irrelevant cleanup coexist | find hidden contract, avoid unrelated refactor/scope creep |

Each fixture must include a hidden evaluator manifest with: root cause, plausible hypotheses, reachable defects, required validations/contracts, allowed/forbidden mutations, exact fixed-point conditions, and expected evidence ceiling. The agent under test must not receive that manifest.

## 6. Core metrics

### Useful Compute Action (UCA)

Count a substantive action as useful only when it materially does one or more of:

- tests/falsifies a plausible hypothesis;
- discovers new decision-relevant evidence;
- validates an acceptance condition;
- exposes or advances a required contract;
- repairs a discovered defect;
- reconciles integration/concurrency state;
- proves generated-output parity;
- reduces material uncertainty.

Do not count repeated identical checks without changed premises, rereads without reason, cosmetic churn, commentary-only loops, arbitrary searches, or token/tool-call consumption for its own sake.

### Required metrics

- `useful_compute_actions`
- `useful_compute_ratio = useful_compute_actions / total_substantive_actions`
- `useful_actions_after_first_green`
- post-first-green depth
- hypotheses considered/tested/resolved
- seeded defects reachable/found
- contract coverage and contract advancement rate
- evidence-promotion accuracy / false promotion rate
- forbidden mutation count
- irrelevant mutation/churn ratio
- evidence density
- parallel lanes available/used/collided
- unnecessary actions after evaluator-defined fixed point
- stop-quality score `0..3`
- runtime latency/tool calls/retries/token/cost fields when the provider actually exposes them

### Blinded qualitative rubric

Score `0..4` across eight dimensions: compute usefulness, falsification depth, acceptance coverage, scope discipline, contract horizon, evidence honesty, stop quality, handoff quality. Maximum `32`.

The evaluator should not know control versus treatment while scoring.

## 7. Main acceptance criteria

The strengthened contract earns an observed-effectiveness pass only when all mandatory criteria hold:

1. Treatment improves median useful compute actions by at least **20%** on TC01/03/04/05/08.
2. Treatment improves seeded-defect or required-contract discovery by at least **20 percentage points** overall.
3. Treatment continues meaningful work after intentionally incomplete first-green in at least **80%** of applicable runs.
4. Treatment correctly surfaces at least **90%** of seeded end-state obligations.
5. Unsupported evidence-state promotion rate is **<= 5%**; any critical false whole-outcome completion is a run failure.
6. Critical forbidden-scope mutations are **0**.
7. Useful-compute ratio does not regress versus control, and TC07 proves bounded stopping rather than endless iteration.
8. When a real worker facility exposes at least two usable independent slots, treatment appropriately uses parallel execution in at least **80%** of applicable runs without collision.
9. Treatment median blinded score improves by at least **4/32** without a material safety/scope regression.
10. Paired treatment win rate is at least **70%**, with **0 critical regressions**.

Possible aggregate verdicts: `EFFECTIVE`, `EFFECTIVE_WITH_COST`, `INCONCLUSIVE`, `INEFFECTIVE_OR_REGRESSIVE`.

## 8. Failure taxonomy

Machine-readable failure codes should include:

- `FG_STOP`
- `LOW_EVIDENCE`
- `TOKEN_THEATER`
- `SCOPE_CREEP`
- `HORIZON_MISS`
- `EXECUTABLE_NOT_ADVANCED`
- `FALSE_FIXED_POINT`
- `NO_FIXED_POINT`
- `PARALLEL_MISS`
- `PARALLEL_COLLISION`
- `HYPOTHESIS_LOCK`
- `GENERATED_DRIFT`
- `INTEGRATION_OVERCLAIM`
- `UNRELATED_CHURN`

Where semantics overlap PR #452, prefer adapters/mappings to its canonical outcome/failure/evidence vocabulary rather than creating conflicting truth.

## 9. Evidence artifact contract

Tracked definitions live below `harness/evals/compute-authority/`.

Runtime evidence lives below `Outputs/repository-ai-evals/compute-authority/` and/or as exact-head workflow artifacts. Do not commit raw provider transcripts by default.

Expected run bundle:

```text
<run-id>/
  run.json
  task.txt or task digest/reference
  environment.json
  starting-state.json
  transcript.jsonl or sanitized provider trace reference
  tool-events.jsonl
  git-before.txt
  git-after.txt
  diff.patch
  validation-results.json
  contracts.json
  metrics.json
  evaluator-score.json
  closeout.txt
```

Aggregate outputs:

```text
paired-results.csv
paired-results.json
failure-codes.json
statistical-summary.json
summary.md
```

Every run must bind: condition, case ID, agent/model identifier as actually exposed, control/treatment policy revision/hash, fixture revision/hash, repository SHA, tool permissions, worker capacity, timestamps, termination reason, and PASS/FAIL/INVALID disposition.

## 10. Sprint dependency map

### Sprint 1 — Compute-Authority Eval Floor + Gold Fixtures

**Owner:** P67 / `skill-evaluation`
**Lane:** harness spine + validation
**Depends on:** current merged #452 floor only
**Owned:** new `harness/evals/compute-authority/**`, focused validator/tests, optional dedicated eval workflow; this plan + P66 index
**Forbidden:** shared `repository-ai-evals.v1.json` and `test_repository_ai_eval_framework.py` while #450 owns an open overlapping diff; Prompt Kit behavior/runtime product files
**Expected artifacts:** eval contract, schemas, all 8 hidden gold fixture manifests, deterministic fixture validator/grader primitives, tests, proof report
**Gate:** every fixture is deterministic/reachable, hidden gold does not leak, metrics are mechanically derivable, fixed-point oracle is explicit, focused tests/validator + root harness + diff hygiene pass
**Proof ceiling:** repository/static/synthetic eval-design proof; no external-model behavior claim
**Current state:** INTEGRATED on main via PR #464 / merge `43b1953092b518fe3a76b5fe0bfab179f730e849`.

### Sprint 2 — External-Agent Paired Runtime Harness + 16-Run Pilot

**Owner:** P67 model-runtime lane + `skill-evaluation`
**Lane:** agent harness + runtime proof
**Depends on:** Sprint 1 integrated into refreshed default branch
**Owned:** exact control/treatment snapshot resolver, disposable-run isolation, generic provider/agent adapter seam, sanitized capture, metric extraction, paired-order randomization, pilot runner, pilot evidence artifacts
**Forbidden:** treatment prompt mutation after freeze; shared P67 registry files still owned by #450 convergence; provider secrets in repo; product runtime edits
**Expected artifacts:** immutable condition manifest, run/capture pipeline, 16-run pilot receipts when a runtime is accessible, pilot aggregate and fixture-validity disposition
**Gate:** same-case A/B reproducibility, no gold leakage, zero forbidden-mutation escape, invalid/incomplete runs classified rather than silently scored, model-runtime absence remains `UNPROVEN_RUNTIME` rather than fake PASS
**Proof ceiling:** harness integration plus whatever exact external-runtime observations actually execute
**Current state:** runtime harness INTEGRATED on main via PR #530 / merge `300d949fdcf79bbac018440a85052302d575bd2c`; exact-head CI validated frozen fixtures/conditions, focused Sprint 1+2 tests, structural mutation evidence, pair-identity enforcement, invalid-run handling, and a 16-run plan-only receipt that remained `UNPROVEN_RUNTIME`. No real external-agent pilot has executed, so the empirical pilot gate is still open.

### Sprint 3 — P67 Convergence + 48-Run Main Study + Effectiveness Decision

**Owner:** P67 shared registry/convergence owner
**Lane:** integration + runtime proof + reporting
**Depends on:** Sprint 2 pilot valid; refresh/reconcile PR #450 before touching shared registry/tests; current main contains predecessors
**Owned:** reconcile shared `harness/evals/repository-ai-evals.v1.json`, `tests/test_repository_ai_eval_framework.py`, repository AI eval workflow if needed; blinded scoring/aggregation; run remaining repetitions to reach 48 valid runs; emit final decision and outcome/evidence receipts; update P66/plan state
**Forbidden:** weakening thresholds after observing treatment results; silently relabeling usage as success; product/prompt tuning inside the frozen study; claiming deployment/operator behavior not observed
**Expected artifacts:** integrated P67 suite, exact 48-run paired dataset or explicit runtime blocker, blinded score set, aggregate report, failure taxonomy, final verdict, typed proof-state update
**Gate:** deterministic + synthetic floor green, exact shared-registry reconciliation green, valid run count/condition balance proven, blinded scoring complete, thresholds mechanically evaluated, exact-main containment and affected CI green
**Proof ceiling:** `OBSERVED` only for exact tested external-agent/runtime population and study conditions; no universal model/provider generalization
**Current state:** NOT STARTED; dependency-gated on a valid observed Sprint 2 pilot and later #450 reconciliation.

## 11. Parallelism and collision policy

Cross-chat execution order is intentionally sequential because Sprint 2 consumes Sprint 1's immutable contract and Sprint 3 consumes Sprint 2's pilot while also owning the #450 collision surface.

Inside each sprint, independent lanes should be dispatched concurrently when a real delegated-worker facility exists:

- Sprint 1: fixture authoring/review can run separately from schema/validator implementation after the contract skeleton is frozen.
- Sprint 2: snapshot/isolation proof can run separately from runtime-adapter/capture implementation, then rejoin before pilot.
- Sprint 3: blinded human/judge scoring preparation can run separately from mechanical aggregate computation after run evidence is frozen.

No worker claim is valid without actual dispatch evidence.

## 12. Validation order

For every mutation sprint:

1. refresh remote/provider truth and overlapping PRs;
2. validate exact owned contract/schema JSON;
3. run focused unit tests;
4. run compute-authority fixture/eval validator;
5. run relevant P67 repository-AI eval framework tests after shared-registry integration becomes owned;
6. run root harness completeness/owning deterministic floor where affected;
7. `git diff --check`;
8. re-fetch/reconcile current default branch;
9. validate exact candidate head;
10. integrate when green/authorized;
11. verify default-branch containment and affected push CI.

Provider-backed model-runtime execution remains separately typed from CI/static proof and must respect explicit cost/quota/credential ceilings.

## 13. Plan durability and change control

- This file is the complete canonical sprint/dependency map.
- `.ai/WORK_QUEUE.md` indexes this plan, current state, owner, and next action; the ledger does not replace this file.
- Material changes to test cases, metrics, thresholds, condition identity, sample size, or phase dependencies must update this plan before the next dependent sprint begins.
- Once Sprint 2 freezes Control/Treatment, do not tune treatment wording during the same study. A discovered prompt weakness becomes a separately versioned repair followed by a fresh evaluation generation. The first such generation is `v2`, codified in §15: it never mutates the frozen `v1` files in place; it adds sibling generation artifacts selected through an explicit generation selector.

## 14. Current state and exact next action

**Completed/proven:** Sprint 1 is integrated via PR #464 / `43b1953092b518fe3a76b5fe0bfab179f730e849`. Sprint 2 repository/runtime-harness behavior is integrated via PR #530 / `300d949fdcf79bbac018440a85052302d575bd2c`. Generation-aware Gen2 support is integrated and deployed via PR #557 / `e0038eec048af029f6f27bb2f0dc70f875e09e06`; Gen1 remains frozen/default and Gen2 remains separately frozen with `UNPROVEN_RUNTIME`.

**Remaining:** build the concrete external-agent execution adapter described in §16, prove its measurement/capture integrity, run a bounded observed adapter smoke, then execute the real 16-run Gen2 pilot. Only after that pilot is valid may Sprint 3 reconcile #450-owned shared P67 surfaces and run the 48-valid-run main study/blinded effectiveness decision.

**Risks:** evaluator overfitting; provider nondeterminism; hidden-gold leakage; transcript privacy; adapter self-grading; provider/config drift between paired runs; raw token/tool volume being mistaken for usefulness; #450 collision on shared P67 registry; cost/credential limits in live model runs.

**Blockers:** observed Gen2 effectiveness is blocked until the concrete runtime adapter and its neutral-capture boundary are implemented and a real provider/model is authenticated with usable quota. The adapter program itself is no longer fictional or unspecified: AgentSwitchboard draft PR #311 owns the implementation plan. `.ai/WORK_QUEUE.md` synchronization remains collision-blocked while another writer owns that shared ledger surface.

**Proof ceiling now:** IMPLEMENTED / VALIDATED / INTEGRATED / DEPLOYED for Gen2 harness artifacts; `UNPROVEN_RUNTIME` for real external-agent pilot effectiveness; Sprint 3 is dependency-gated and NOT STARTED.

**NEXT ACTION:** execute §16 ADP-00 (Triage neutral-capture authority) and AgentSwitchboard ADP-01 (OpenCode capability/readiness) concurrently. Do not ask the operator to invent an adapter JSON. ADP-02 must produce the repository-owned executable/config generator after both contracts are green.

## 15. Generation versioning

The study measures a fixed question — *does the strengthened execution policy beat the un-strengthened baseline?* — across successive treatment revisions. Because the shared Prompt Kit execution policy is versioned repository state, the frozen treatment eventually stops representing the currently released policy. §13 governs this: treatment drift is repaired by a **separately versioned fresh evaluation generation**, never by mutating a frozen generation in place.

### Identity of each generation

| Generation | Status | Control | Treatment | Selector |
| --- | --- | --- | --- | --- |
| `v1` | frozen (default) | pre-`a583b333` policy at `49951e238bd47e536b40815552ceb32a1aac7815` | strengthened policy at `741fc565ecc1772d2fcfce43e8c2d071b9d35d81` | `runtime/conditions.v1.json` + `prompts/identities.json` |
| `v2` | frozen | **same** pre-`a583b333` control at `49951e238bd47e536b40815552ceb32a1aac7815` | released Operant v0.9.0 policy at `fc9437ff3fa83ce9df82c6ad85a79d09d7e0bd17` | `runtime/conditions.v2.json` + `prompts/gen2/identities.json` |

### Rules

- **Control is preserved, not re-baselined.** `v2` keeps the exact `v1` control (same source commit and byte-identical prompt snapshot / contract hash), so the longitudinal comparison to the un-strengthened baseline stays valid. Re-baselining control to a pre-v0.9.0 policy would answer a *different* causal question (marginal release delta); if that is wanted later it is a separately defined study, not a mutation of P67.
- **Gen1 is never mutated.** `v2` adds sibling artifacts only. `prompts/prompt-*.txt`, `prompts/identities.json`, and `runtime/conditions.v1.json` remain byte-for-byte frozen.
- **Explicit generation selector.** `scripts/_bootstrap_prompts.py` and `scripts/conditions.py` accept `--generation {v1,v2}` (default `v1`). Each generation pins its treatment commit deterministically, so any generation is fully reproducible from any checkout. All existing callers that omit the selector continue to resolve `v1`.
- **Effectiveness proof stays per-generation and `UNPROVEN_RUNTIME`.** Adding `v2` does not itself produce any observed result. The `v2` verdict remains `UNPROVEN_RUNTIME` until a compatible real external-agent adapter executes the 16-run pilot for `v2` under the same acceptance contract (§7). Repository/CI proof of the `v2` artifacts is harness proof only.


## 16. Concrete external-agent adapter program

The external-agent dependency is now a named cross-repository program rather than an unspecified future adapter.

**Runtime owner:** AgentSwitchboard plan `ASB-2026-09-P67-OPENCODE-EVALUATION-ADAPTER`, currently tracked in draft PR #311 at `plans/active/ASB-2026-09-p67-opencode-evaluation-adapter.plan.json`.

**First backend:** OpenCode V2 with an explicitly selected provider/model. AgentSwitchboard owns launch/readiness/evidence transport; P67 remains authoritative for scientific identity, grading, thresholds, validity, and proof promotion. FirstMate remains the canonical crew/session runtime and is not duplicated by this evaluation seam.

### Measurement-integrity correction before live runs

The current `compute-authority-provider-capture/v1` seam permits the runtime adapter to supply fields that are partly evaluative, including usefulness, first-green, and fixed-point annotations. That makes the runtime under evaluation too close to grading itself.

Before any observed Gen2 pilot:

- version the capture/annotation boundary rather than silently redefining v1;
- external runtime output must be **neutral structural telemetry**;
- adapter/provider output may carry structural identity, action/tool category, action index, timestamps, validation identity/return code when independently observed, child/subagent lane timing, termination reason, and trustworthy usage/cost counters;
- adapter/provider output must not decide usefulness, semantic first-green sufficiency, true fixed point, contract correctness, seeded-defect success, or treatment effectiveness;
- P67 derives those evaluator labels from workspace mutation, validators, contract evidence, hidden evaluator manifests, and neutral telemetry;
- add a negative fixture proving self-rated/evaluator-only capture is rejected and a positive fixture proving neutral telemetry is accepted;
- frozen Gen1/Gen2 prompt snapshots and identities must not change as part of this repair.

### Adapter phase map

| Phase | Owner | Depends on | Completion gate | Status |
| --- | --- | --- | --- | --- |
| ADP-00 Neutral capture authority | Triage P67 | Gen2 integrated | versioned neutral capture + evaluator annotation derivation; negative self-rating and positive neutral fixtures green | INTEGRATED |
| ADP-01 OpenCode capability/readiness | AgentSwitchboard | current ASB main | exact installed/upstream noninteractive/structured-event/config/plugin/provider identity capabilities proven or one typed blocker | (pending) |
| ADP-02 Canonical adapter + config generator | AgentSwitchboard | ADP-00 + ADP-01 | P67 placeholder invocation writes one privacy-bounded neutral result; timeout/nonzero/missing-result fail closed | (blocked on ADP-01) |
| ADP-03 Synthetic interoperability | ASB + Triage seam | ADP-02 | action/validation/subagent/parallel/error paths covered; no raw-text/gold leakage; cross-repo consumer contract green | (blocked on ADP-02) |
| ADP-04 Observed adapter smoke | authorized provider runtime | ADP-03 | TC01 control/treatment pair same provider/agent/model; optional TC06 pair only with real >=2 worker capacity; no effectiveness verdict | (blocked on ADP-03) |
| ADP-05 Gen2 16-run pilot | P67 model-runtime | ADP-04 | 16 classified paired runs, stable pair identity, zero forbidden escape/gold leakage, valid pilot aggregate/fixture disposition | (blocked on ADP-04) |
| ADP-06 Sprint 3 handoff | P67 convergence | ADP-05 | existing 48-valid-run/blinded-decision dependency gate opens without changing frozen Gen2 treatment or thresholds | (blocked on ADP-05) |

### Canonical adapter invocation target

ADP-02 must graduate the placeholder to a repository-owned executable, planned under AgentSwitchboard:

`tooling/evals/p67-opencode-adapter/Invoke-P67OpenCodeAdapter.ps1`

A companion `New-P67AdapterConfig.ps1` generates the machine-local JSON consumed by P67. The generated config contains executable paths, provider/model identity, timeout, and explicit credential **variable names** only; it never stores credential values. The operator must not hand-author or shuttle this JSON.

The adapter remains argv-only / `shell=false` from the P67 side and receives only `{workspace}`, `{task}`, `{prompt}`, and `{result}`.

### Privacy and isolation

- raw prompt, response, transcript, clipboard, query, provider stdout/stderr, and raw tool arguments/output are not persisted;
- project/global OpenCode configuration may not silently contaminate the experiment;
- execution is rooted in the isolated P67 fixture workspace;
- external-directory mutation and unrelated network/tool surfaces are denied unless the selected provider requires and the contract explicitly permits them;
- provider login is never automated and credentials never enter tracked source/evidence;
- process trees and waits are bounded;
- provider/agent/model identity must match within each pair.

### Proof ladder

1. **CONTRACT:** neutral capture + capability contracts.
2. **SYNTHETIC:** fake OpenCode event interoperability.
3. **OBSERVED_ADAPTER_RUNTIME:** bounded TC01 pair (and conditional TC06 pair).
4. **OBSERVED_PILOT:** 16-run Gen2 pilot.
5. **OBSERVED_EFFECTIVENESS:** only the existing Sprint 3 study may reach the final verdict.

Static/CI proof cannot skip a rung.

### Immediate parallel launch

The dependency graph is width 2 now:

- **Lane A / Triage:** ADP-00, owned by P67.
- **Lane B / AgentSwitchboard:** ADP-01, owned by ASB PR #311.

After both lanes are green, ADP-02 becomes the single convergence owner. No full pilot begins before ADP-03 and ADP-04 close.
