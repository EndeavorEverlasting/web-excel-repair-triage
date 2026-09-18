# Prompt Strength / Execution Reliability Closeout

This directory owns the durable semantic and execution-continuity artifacts for the current Prompt Kit reliability program.

## Canonical owners

- Program plan: `harness/evals/PROMPT_STRENGTH_RECOVERY_SPRINT_PLAN.md`
- Semantic contract: `harness/contracts/prompt-strength.v1.json`
- Adversarial matrix: `harness/evals/prompt-strength/adversarial-regression-matrix.v1.json`
- Validator: `scripts/validate_prompt_strength.py`
- Focused regression: `tests/test_prompt_strength_contract_prompt.py`
- Dispatch manifest: `Outputs/prompt-parallel-dispatch/manifest.json`
- Regression seed: `harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json`
- Factoring ledger: `harness/evals/prompt-strength/FACTORIZATION_LEDGER.md`

## Validation

```bash
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract_prompt -v
python scripts/prompt_parallel_dispatch.py validate --manifest Outputs/prompt-parallel-dispatch/manifest.json
python -m unittest tests.test_gitignore_hygiene -v
python -m triage.gitignore_hygiene
```

The historical prompt-strength dispatch seed (`parallel-dispatch-manifest.seed.v1.json`) and the global active manifest (`Outputs/prompt-parallel-dispatch/manifest.json`) each validate independently against the parallel-dispatch contract. The active manifest is no longer required to remain byte-identical to the historical seed forever: it may rotate to a different valid orchestration run, while the historical seed is retained as independent regression evidence. The current graph width is 1, so the durable dispatch disposition is `NOT_APPLICABLE`; this is serial correctness, not degraded autonomy.

Only the dispatch **manifest** is tracked under `Outputs/` as control-plane state. Runtime receipts remain generated evidence and are rejected by artifact hygiene.

Generated Prompt Kit HTML is never semantic authority and is updated only through the canonical builder/repository action.
