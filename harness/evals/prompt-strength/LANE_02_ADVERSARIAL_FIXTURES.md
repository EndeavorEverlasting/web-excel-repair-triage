# Lane 02 — Adversarial Fixture Implementation

**Authority:** bounded-application executor after Phase-0 contract is pinned

**Owned outputs:** `harness/evals/prompt-strength/fixtures/**`, `tests/test_prompt_strength_adversarial.py`

**Forbidden:** shared actionability policy, P07 semantics/build-context, prompt-quality-history files, local-proof-continuity files, generated Prompt Kit HTML.

## Mission

Turn the highest-risk adversarial matrix rows into executable negative fixtures and positive controls without changing strategic prompt policy.

## Read first

- `AGENTS.md`
- `harness/contracts/prompt-strength.v1.json`
- `harness/evals/prompt-strength/adversarial-regression-matrix.v1.json`
- `harness/contracts/prompt-regression-safety.v1.json`
- `harness/contracts/prompt-parallel-dispatch.v1.json`
- relevant compute-authority and compilation tests

## Priority cases

PSA-001, PSA-002, PSA-003, PSA-005, PSA-006, PSA-007, PSA-011, PSA-012, PSA-017, PSA-018, PSA-023, PSA-024, PSA-027.

## Tasks

1. Reuse existing fixture/eval contracts where they already express the scenario.
2. For each selected case, create a negative fixture that reproduces the defect and a positive control that preserves allowed behavior.
3. Keep fixtures deterministic and free of private/runtime-only payloads.
4. Write a focused test that fails closed on the negative fixture and passes the positive control.
5. Do not weaken existing validators to make the cases pass.

## Validation

Run the new focused tests plus `python scripts/validate_prompt_strength.py --summary`; include `git diff --check` before handoff.

## Proof ceiling

Deterministic repository fixture/test proof only; no downstream model-obedience claim.
