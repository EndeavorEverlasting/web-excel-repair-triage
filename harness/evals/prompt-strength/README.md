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
```

The primary manifest and seed are intentionally byte-identical. Generated Prompt Kit HTML is never semantic authority and is updated only through the canonical builder/repository action.

## Current proof boundary

The active execution wave uses isolated GitHub-provider branches for #543 and #537. Provider commits/CI/review plus the #543 canonical repository-action artifact establish provider proof. Local workstation execution and downstream model behavior remain separate proof surfaces.
