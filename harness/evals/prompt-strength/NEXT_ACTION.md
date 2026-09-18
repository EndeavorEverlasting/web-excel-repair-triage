# Next Action

**Owner:** local strategic-harness coordinator.

**Dependency:** authenticated local checkout with network access; refresh before using any remembered SHA.

## First executable action

```bash
set -euo pipefail
repo="$(git rev-parse --show-toplevel)"
cd "$repo"
git fetch --all --prune --tags
default_branch="$(git remote show origin | sed -n '/HEAD branch/s/.*: //p')"
test "$default_branch" = "main"

python -c "from pathlib import Path; src=Path('harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json'); dst=Path('Outputs/prompt-parallel-dispatch/manifest.json'); dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(src.read_bytes())"
python scripts/prompt_parallel_dispatch.py validate --manifest Outputs/prompt-parallel-dispatch/manifest.json
```

If the local runtime exposes an autonomous agent runner, bind the five Wave-A `runtime_tool` lanes and dispatch them immediately. Preserve one branch/worktree per writer and return each lane's commit/receipt to its declared convergence owner.

If no autonomous runner is available, report:

`PARALLEL EXECUTION: DEGRADED — graph width 5, no safe bound local agent adapter`

and keep progressing only through deterministic/read-only local gates; do not fabricate dispatch proof.

## First semantic repair

Lane 01 repairs PSA-029 on #537-owned files only. Completion gate: `python scripts/validate_prompt_strength.py --summary` plus `python -m unittest tests.test_prompt_strength_contract_prompt -v` PASS on the exact branch head. Do not touch `harness/test-floor.v1.json` until Lane 07.

## Integration rule

Every lane refreshes main immediately before final validation/merge. If main moved in a proof-relevant owner, reconcile and rerun affected proof. A clean PR is not terminal while safe merge remains available.
