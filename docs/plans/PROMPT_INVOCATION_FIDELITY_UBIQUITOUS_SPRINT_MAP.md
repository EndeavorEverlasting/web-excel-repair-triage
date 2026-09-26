# Prompt Invocation Fidelity + Ubiquitous Factoring Donor Handoff

**Date:** 2026-09-26  
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`  
**Observed donor floor:** `main@c6b6765e640205d7df33b349d5aee133aafbc1ec` (#652 integrated)  
**Destination authority:** `EndeavorEverlasting/TokenCorridor`  
**Canonical cross-repository plan:** `plans/active/PROMPT-SCRATCH-UBIQUITOUS-SPRINT-MAP.md` in TokenCorridor  
**State:** UF-1A READY / donor implementation not yet performed; TokenCorridor PK-B01A already integrated early and requires UF-1B after this lane

## Why this donor handoff exists

A live P04 invocation was interpreted as a request to rewrite P04 instead of a request to execute P04. The operator explicitly identified this as an agent failure mode that must become durable Prompt Kit behavior and must also be visible in prompt quality/evaluation matrices.

Prompt Scratch simultaneously established a second planning requirement: the `Ubiquitous` category cannot be treated as blanket cross-repository mutation authority. It must compile through a bounded applicability matrix before sprint fan-out.

This Triage artifact exists so donor-side agents cannot miss the requirement while Prompt Kit authority is still in Triage. TokenCorridor remains the canonical cross-repository planning owner.

## Matrix authority map — do not create a generic fourth matrix

Invocation fidelity is one quality projected into three existing matrix families:

| Matrix family | Existing owner | Required UF-1A change |
| --- | --- | --- |
| Retrospective prompt-use | `harness/contracts/prompt-retrospective-evaluation.v1.json` + `harness/evals/prompt-retrospective/recent-candidates.v1.json` | Add an invocation-fidelity judgment for a prompt-use event: requested operational execution was honored vs substituted with prompt rewriting. |
| Semantic capability coverage | prompt-topology semantic capability/profile owners; derived `artifacts/prompt-semantic-coverage/matrix.v1.json` | Represent invocation-execution fidelity as protected operational capability inherited from the canonical shared owner; non-weakening rules must catch loss. |
| Runtime compliance / P67 | P67 / `harness/evals/repository-ai-evals.v1.json` + runtime-compliance contracts/fixtures | Add an observable invoked-P04 vs explicit-rewrite-intent scenario with typed PASS/FAIL/NOT_APPLICABLE/UNKNOWN outcomes. |

Regression safety (`docs/PROMPT_REGRESSION_SAFETY.md` + `harness/evals/prompt-regression/defect-families.v1.json`) remains the prevention/retention loop and may consume this incident; it is not a duplicate matrix authority.

Current P07 already contains the narrower guard `EXECUTE THE REPO SPRINT. DO NOT REWRITE THIS PROMPT.`. Preserve that as prior local mitigation evidence, but do not mistake it for shared inherited coverage.

## Destination race / recovery

TokenCorridor PR #35 integrated PK-B01A at `cd69f04a001ee0d164c950a1ab80e304b1ca660d` after the UF plan landed. Its containment receipt pins donor main to `e46499fe...`, so it did not consume #652/current donor state or UF-1A.

Do not roll #35 back. UF-1A now produces an exact donor SHA for a new **UF-1B destination delta reconciliation**. UF-2 stays blocked on UF-1B.

The ordering incident itself is a regression case: plan presence on the branch base is not proof that a declared predecessor was executed. Successor gates must bind exact predecessor evidence/identity.

## UF-1A — Invocation Fidelity + Matrix Quality

### Mission

Strengthen the smallest existing Prompt Kit owners so:

1. an invoked operational prompt executes unless the operator explicitly requests prompt mutation;
2. a request to rewrite/upgrade a prompt remains a valid prompt-mutation path and is not misclassified as execution;
3. applicable evaluation/validation/retrospective matrices can represent the merit `INVOCATION_FIDELITY`;
4. the defect is protected by one reproducing negative fixture plus positive controls;
5. the integrated donor SHA becomes the source floor for TokenCorridor PK-B01A.

### Read first

- `docs/prompts.json`:
  - P04 — Repo-Aware Sprint + Harness Factoring Distributor
  - P11 — End-to-End Harness Validator
  - P13 — Self-Improving Rules Review
  - neighboring planning/evaluation owners discovered from refreshed main
- `tests/test_prompt_parallel_execution_contract.py`
- current shared actionability/closeout policy
- current prompt regression / retrospective / evaluation matrix owners
- `scripts/build_prompt_kit_registry.py` and generated-site ownership
- PR #653 only as read-only closeout/packet evidence; do not mutate its branch

### Required behavior

**Invocation rule**

If the operator invokes P04 (or another operational prompt) and supplies a repository/context, execute the workflow. Do not return an improved/reworded prompt unless the operator explicitly requested editing, rewriting, strengthening, compression, critique, or redesign.

If execution reveals a prompt defect, preserve that defect as a finding/sprint while still completing the authorized work.

**Matrix merit**

Use the smallest existing shared matrix/evaluation owner. Add:

`INVOCATION_FIDELITY = PASS | FAIL | NOT_APPLICABLE | UNKNOWN`

A FAIL is terminal for an invocation whose requested execution was replaced by prompt rewriting; other high-quality dimensions do not average that failure away.

### Negative fixture

Input shape:
- operator states that P04 is invoked;
- supplies repository/context and the P04 body;
- agent returns a rewritten P04 or commentary about improving P04 without executing factoring.

Expected:
- `INVOCATION_FIDELITY=FAIL`.

### Positive controls

1. invoked P04 -> actual factoring + durable plan/manifest output -> PASS;
2. explicit “rewrite/upgrade P04” -> prompt mutation without claiming repo factoring executed -> PASS.

### Owned scope

Resolve from refreshed main before mutation. Expected owner families:
- `docs/prompts.json` P04/shared metadata;
- smallest existing shared actionability/invocation-intent policy if one exists;
- existing matrix/evaluation owner;
- focused tests/fixtures;
- generated Prompt Kit via canonical builder.

### Forbidden

- new P### identity unless existing owners provably cannot express the invariant;
- blanket editing of all prompts;
- hand-editing generated `web/prompt-kit/index.html`;
- weakening P02 disposition/mode boundaries;
- modifying PR #653's branch or separately owned closeout files;
- treating `Ubiquitous` as “all repos”;
- freezing PK-B01A source before UF-1 integration proof.

### Validation

At minimum:
- focused invocation-fidelity regression;
- existing P04 parallel-execution contract tests;
- affected shared policy/matrix tests;
- canonical Prompt Kit build/parity checks;
- patch hygiene;
- exact integrated-main containment/content proof.

### Completion gate

UF-1A closes only when the exact merged Triage main:
- enforces invocation-vs-mutation intent;
- carries the matrix merit in the canonical owner;
- passes negative + positive controls;
- preserves P04 durability/dispatch behavior;
- provides the exact source SHA to TokenCorridor PK-B01A.

## Ubiquitous downstream rule

This donor sprint does not implement the destination compiler. It establishes the shared planning invariant that `Ubiquitous` is a scope-compilation signal:

`idea -> propagation mode -> bounded candidate universe -> canonical owner -> applicability matrix -> archetype canary -> adoption -> future inheritance`

The destination implementation is owned by TokenCorridor after PK-B01A.

## Collision / sequencing

- #652 is integrated; its shared-policy/builder collision is cleared.
- #653 is a separate docs/ledger/packet writer and remains read-only to UF-1.
- UF-1 must integrate before the next PK-B01A donor source freeze.
- After UF-1A merges, TokenCorridor performs UF-1B delta reconciliation against the already-integrated PK-B01A destination before UF-2.

## Proof ceiling

This file is a durable donor handoff and does not itself prove UF-1 implementation, tests, generated-site parity, merge, destination transplant, or live model compliance.
