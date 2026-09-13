# Prompt Kit Compute-Authority External-Agent Evaluation Sprint Map

**Status:** Sprint 1 IMPLEMENTATION COMPLETE on harness floor — empirical effectiveness remains unproven; Sprint 2+ not started
**Canonical owner:** P67 Repository Eval Framework Builder + existing `skill-evaluation` capability
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Evidence floor at plan creation:** `main@fd3b3910e0ce80f3880ebd15426278354b065f48`
**Floor proof:** PR #452 merged at `fd3b3910...`; exact-main push workflows observed 12/12 completed successfully
**Primary target:** measure whether external agents spend more *useful* compute under the strengthened shared Prompt Kit compute-authority contract
**Plan owner path:** `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`
**Sprint 1 implementation path:** `harness/evals/compute-authority/`

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
- PR #461's strategic recommendation to resolve evidence-spine/state ownership before Phase D Passive Learning.

Reuse these owners. Do not create a second generic eval framework, second skill-evaluation identity, second evidence-state vocabulary, or second prompt-outcome model.

### Active collision owners

| Surface | Current owner | Disposition for this program |
| --- | --- | --- |
| `harness/evals/repository-ai-evals.v1.json` | P67; also modified by open PR #450 | **Final convergence owner only.** Sprints 1–2 must not edit it. |
| `tests/test_repository_ai_eval_framework.py` | P67; also modified by open PR #450 | **Final convergence owner only.** Reconcile #450 first. |
| route receipts / routing control plane | open PR #450 | Read-only evidence/dependency; do not absorb. |
| Prompt Finder usage candidates | open PR #431 | Read-only candidate evidence; do not treat selection intent as terminal success. |
| serverless/local lifecycle phase map | open PR #462 | Independent product/runtime owner; do not edit its five owned files. |
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
- modifying PR #450/#431/#462/#242 owned surfaces unless a later explicit reconciliation sprint authorizes it;
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

### Sprint 2 — External-Agent Paired Runtime Harness + 16-Run Pilot

**Owner:** P67 model-runtime lane + `skill-evaluation`
**Lane:** agent harness + runtime proof
**Depends on:** Sprint 1 integrated into refreshed default branch
**Owned:** exact control/treatment snapshot resolver, disposable-run isolation, generic provider/agent adapter seam, sanitized capture, metric extraction, paired-order randomization, pilot runner, pilot evidence artifacts
**Forbidden:** treatment prompt mutation after freeze; shared P67 registry files still owned by #450 convergence; provider secrets in repo; product runtime edits
**Expected artifacts:** immutable condition manifest, run/capture pipeline, 16-run pilot receipts when a runtime is accessible, pilot aggregate and fixture-validity disposition
**Gate:** same-case A/B reproducibility, no gold leakage, zero forbidden-mutation escape, invalid/incomplete runs classified rather than silently scored, model-runtime absence remains `UNPROVEN_RUNTIME` rather than fake PASS
**Proof ceiling:** harness integration plus whatever exact external-runtime observations actually execute

### Sprint 3 — P67 Convergence + 48-Run Main Study + Effectiveness Decision

**Owner:** P67 shared registry/convergence owner
**Lane:** integration + runtime proof + reporting
**Depends on:** Sprint 2 pilot valid; refresh/reconcile PR #450 before touching shared registry/tests; current main contains predecessors
**Owned:** reconcile shared `harness/evals/repository-ai-evals.v1.json`, `tests/test_repository_ai_eval_framework.py`, repository AI eval workflow if needed; blinded scoring/aggregation; run remaining repetitions to reach 48 valid runs; emit final decision and outcome/evidence receipts; update P66/plan state
**Forbidden:** weakening thresholds after observing treatment results; silently relabeling usage as success; product/prompt tuning inside the frozen study; claiming deployment/operator behavior not observed
**Expected artifacts:** integrated P67 suite, exact 48-run paired dataset or explicit runtime blocker, blinded score set, aggregate report, failure taxonomy, final verdict, typed proof-state update
**Gate:** deterministic + synthetic floor green, exact shared-registry reconciliation green, valid run count/condition balance proven, blinded scoring complete, thresholds mechanically evaluated, exact-main containment and affected CI green
**Proof ceiling:** `OBSERVED` only for exact tested external-agent/runtime population and study conditions; no universal model/provider generalization

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
- Once Sprint 2 freezes Control/Treatment, do not tune treatment wording during the same study. A discovered prompt weakness becomes a separately versioned repair followed by a fresh evaluation generation.

## 14. Current state and exact next action

**Completed/proven:** strengthened contract is repository-integrated; PR #452 outcome-receipt vocabulary is mainline-integrated; current main floor is green at provider level; P67 and `skill-evaluation` owners already exist.

**Remaining:** all external-agent compute-authority empirical evaluation work described above.

**Risks:** evaluator overfitting; provider nondeterminism; hidden-gold leakage; transcript privacy; raw token/tool volume being mistaken for usefulness; #450 collision on shared P67 registry; cost/credential limits in live model runs.

**Blockers:** none for Sprint 1. Live-runtime credentials/provider availability may block only the runtime execution portion of Sprints 2–3 and must be reported as such.

**Proof ceiling now:** TRACKED/DESIGNED plan on a green repository floor; external-agent behavioral effectiveness remains UNPROVEN.

**NEXT ACTION:** Sprint 1 owner P67/`skill-evaluation` — create the versioned compute-authority eval contract, schemas, eight hidden gold fixtures, deterministic fixture/metric validator and focused tests under `harness/evals/compute-authority/`, without touching the #450-shared repository-AI registry files; integrate that floor before starting runtime pilot work.
