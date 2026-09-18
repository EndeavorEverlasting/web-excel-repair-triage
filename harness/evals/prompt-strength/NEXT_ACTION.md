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

python scripts/prompt_parallel_dispatch.py validate --manifest Outputs/prompt-parallel-dispatch/manifest.json
```

The tracked primary manifest and seed are canonical **unbound** orchestration state. Do not edit the tracked seed merely to claim dispatch.

If the local runtime exposes a real autonomous agent/repo-runner adapter:

1. materialize a runtime copy of the manifest;
2. replace each active `UNBOUND_LOCAL_AGENT_RUNTIME` runtime-tool binding with the actual evidenced adapter/tool operation;
3. change runtime disposition to `REQUIRED` and `autonomy_gap` to null only after the adapter is genuinely available;
4. validate the runtime copy;
5. dispatch Wave A lanes 01, 04, and 05 concurrently;
6. preserve a receipt proving overlap and each lane result;
7. rejoin through the declared convergence owners.

If no autonomous adapter exists, report:

`PARALLEL EXECUTION: DEGRADED — graph width 3; no safe bound autonomous local-agent adapter.`

Continue deterministic/read-only local gates where useful, but do not fabricate parallelism.

## Active Wave-A first commands

Lane 01:
```bash
git fetch --all --prune --tags && git switch feat/prompt-strength-contract-matrix-20260917 && python scripts/validate_prompt_strength.py --summary
```

Lane 04:
```bash
git fetch --all --prune --tags && git switch fix/local-proof-continuity-20260917 && git merge --no-edit origin/main
```

Lane 05:
```bash
git fetch --all --prune --tags && git worktree add ../wetr-line-endings -b fix/line-ending-policy-20260918 origin/main
```

## Integration rule

Every lane refreshes main immediately before final validation/merge. If main moved in a proof-relevant owner, reconcile and rerun affected proof. A green PR is not terminal while safe authorized merge remains.
