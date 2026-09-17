# Portability fallback

The machine dispatch manifest is authoritative for orchestration state. This file exists only as a recovery surface when a local runtime has no autonomous adapter binding yet.

## Lane 01 — upstream refresh

Research-only until owner mapping is settled. Refresh donor revisions, extract mechanics with provenance, compare each mechanic to current canonical owners, and write only `harness/evals/prompt-strength/upstream-residual-map.v1.json`. Do not edit shared prompt/compiler policy.

## Lane 02 — adversarial fixtures

Implement negative fixtures and positive controls for the priority PSA cases under `harness/evals/prompt-strength/fixtures/**` plus `tests/test_prompt_strength_adversarial.py`. Do not edit shared policy, P07 semantics, or generated Prompt Kit HTML.

## Lane 03 — dependency reconciliation

Refresh `main` and PRs #533/#535/#536. Record current merge state, current surviving semantics, collision surfaces, and owning validator proof in `harness/evals/prompt-strength/dependency-reconciliation.v1.json`. Do not mutate those PR-owned files.

## Lane 04 — shared-policy convergence

Strategic-harness owner only, after lanes 01–03 return. Select the smallest canonical shared owners, integrate proven residuals and adversarial controls, register focused proof, regenerate only through canonical builders, and converge to current main when gates allow.

Copy panels are not dispatch proof. A local runtime that can launch these lanes should bind the manifest directly instead of asking the operator to act as scheduler.
