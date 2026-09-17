# Prompt-strength dispatch binding note

The durable seed is `harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json`. Immediately before execution, materialize that seed to the canonical runtime path `Outputs/prompt-parallel-dispatch/manifest.json`; `Outputs/` remains runtime-generated and ignored by Git.

The seed intentionally records `parallel_disposition=DEGRADED` for the current ChatGPT runtime. The dependency graph has width three, but this runtime does not expose a proven native/local agent runner and direct local Git/network access is unavailable.

Do not reinterpret this as `NOT_APPLICABLE`, and do not claim dispatch proof from copy panels or serial tool calls.

A local runtime may promote the materialized manifest to `REQUIRED` only after it binds the lanes to an actually available adapter evidenced in that environment, performs the real launches, writes a compatible receipt, and passes:

```bash
python scripts/prompt_parallel_dispatch.py validate --manifest Outputs/prompt-parallel-dispatch/manifest.json
python scripts/prompt_parallel_dispatch.py verify-receipt --manifest Outputs/prompt-parallel-dispatch/manifest.json --receipt Outputs/prompt-parallel-dispatch/receipt.json
```

OpenCode is repository-evidenced as a bounded executor and its CLI invocation shape is repository-evidenced as `opencode run [--model MODEL] PROMPT`; availability on a particular workstation must still be probed rather than assumed. Strategic harness mutation remains restricted to the strategic-harness-owner tier.
