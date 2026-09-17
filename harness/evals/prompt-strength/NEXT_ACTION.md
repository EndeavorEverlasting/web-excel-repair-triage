# Next Action

Owner: local strategic-harness agent.

Dependency: refresh provider/default-branch truth and resolve the exact current head of `feat/prompt-strength-contract-matrix-20260917` or its successor PR.

Execute from an isolated clean worktree pinned to that exact head:

```bash
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract -v
python -c "from pathlib import Path; src=Path('harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json'); dst=Path('Outputs/prompt-parallel-dispatch/manifest.json'); dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(src.read_bytes())"
python scripts/prompt_parallel_dispatch.py validate --manifest Outputs/prompt-parallel-dispatch/manifest.json
git diff --check
```

Populate `harness/evals/prompt-strength/phase0-validation-receipt.v1.json` from the exact results. Completion gate: all checks pass on the exact feature head. Afterward, advance Lane 03 dependency reconciliation rather than stopping at status inspection.
