# Prompt Strength / Execution Reliability Closeout

This directory is the durable execution surface for closing the current Prompt Kit strength, boundary, local-proof, line-ending, publication, and observed-behavior gaps.

## Canonical owners

- Whole program: `harness/evals/PROMPT_STRENGTH_RECOVERY_SPRINT_PLAN.md`
- Launch order: `harness/evals/prompt-strength/LAUNCH_ORDER.md`
- Primary dispatch manifest: `Outputs/prompt-parallel-dispatch/manifest.json`
- Regression-tested seed: `harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json`
- Factoring ledger: `harness/evals/prompt-strength/FACTORIZATION_LEDGER.md`
- Local coordinator bootstrap: `harness/evals/prompt-strength/NEXT_ACTION.md`
- Portability fallback index: `harness/evals/prompt-strength/PORTABILITY_FALLBACK.md`

## Validation

```bash
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract_prompt -v
python scripts/prompt_parallel_dispatch.py validate --manifest Outputs/prompt-parallel-dispatch/manifest.json
```

The focused test requires the primary manifest to be byte-identical to the tracked seed and validates both through the repository-owned dispatcher.

## Current proof boundary

The manifest is a machine-readable dependency/collision/launch contract. In this planning runtime it is DEGRADED because no local autonomous-agent adapter is bound. Validation is not launch proof. A local runtime must perform the runtime-tool dispatches and preserve compatible evidence before claiming observed parallelism.

Repository/static/integration proof also does not prove downstream model effectiveness; that final observed gate is delegated to the existing P67 compute-authority evaluation.
