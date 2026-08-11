# 4. LLM Ops — make model behavior operable

**Prompt:** P70 LLM Ops Production Readiness Builder

## Goal
Build the operational layer around model-backed behavior: deployment readiness, monitoring, latency, cost, caching, provider fallback, release identity, and rollback.

## Walkthrough
1. Define measurable latency/error/cost/quality budgets from available evidence.
2. Instrument provider/model identity, latency, retries, tokens, cache behavior, fallback, and terminal errors.
3. Bound context and choose cache rules with explicit privacy/invalidation behavior.
4. Test rate limits, provider failure, fallback routing, and reduced-capability behavior.
5. Tie the release gate to evals plus operational readiness.
6. Record exact model/config identity and rollback/runbook actions.
7. Stop at the production-access gate unless credentials and deployment authority are explicitly present.

## What to avoid
- logging raw sensitive prompts by default;
- provider fallback that changes capability without changing proof claims;
- optimizing latency/cost without a quality regression gate;
- reporting configuration readiness as a successful deployment.

## Completion gate
The exact candidate configuration has measurable readiness checks, tested fallback behavior, and a rollback path; production remains a separate observed gate.
