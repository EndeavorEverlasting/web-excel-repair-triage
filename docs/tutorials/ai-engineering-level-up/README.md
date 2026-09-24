# Production AI Engineering: Five Repository Level-Up Tracks

This tutorial pack turns five useful AI-engineering ideas into repository work that can be inspected, tested, committed, and reviewed. The goal is not a title or compensation claim; it is to make AI-enabled repositories more reliable and easier to operate.

## Choose the largest verified gap

| Track | Prompt | Start here when | Durable result |
|---|---|---|---|
| Evals | P67 | quality is anecdotal or regressions escape | executable cases, oracles, reports, CI gates |
| Context engineering | P68 | prompts/tools/retrieval/history are bloated or stale | measured context map, routing/pruning, context tests |
| Production agents | P69 | the happy path works but failures are fragile | idempotency, bounded retries, recovery, fault tests |
| LLM Ops | P70 | the feature must be deployable and operable | SLOs, telemetry, cost/latency controls, fallback, rollback |
| Adaptability | P71 | models/SDKs/frameworks change faster than the repo can absorb | stable contracts, adapters, compatibility proof |

The tracks are complementary, not a rigid waterfall. A new repo may start with P67. A deployed repo with provider incidents may need P70 first. A sprawling agent harness may get the largest immediate gain from P68.

## Maturity loop

1. **Evaluate** the real task and known failure modes.
2. **Engineer context** so the model receives the right information, not all information.
3. **Harden agent execution** against distributed-system failure modes.
4. **Operate the model layer** with measurable reliability, latency, cost, fallback, and rollback.
5. **Adapt deliberately** as providers, models, frameworks, and tool protocols change.
6. **Re-run evals** after material changes.

## Repository rule

Every track should end in tracked artifacts and an executable gate. Prose alone is not completion when the behavior is machine-checkable. Static and synthetic proof must remain distinct from live or production proof.
