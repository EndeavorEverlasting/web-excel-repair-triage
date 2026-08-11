# 3. Production agents — harden the non-happy path

**Prompt:** P69 Production Agent Reliability Hardener

## Goal
Treat the agent loop as a distributed system whose components include non-deterministic models and unreliable external tools.

## Walkthrough
1. Draw states, side effects, external calls, and recovery points.
2. Classify failures as retryable, terminal, compensating, or operator-required.
3. Add bounded timeouts/backoff and never blindly retry destructive mutations.
4. Make side effects idempotent or provide explicit compensation.
5. Persist enough state to resume or disposition interrupted work.
6. Instrument transitions, tool outcomes, retries, latency, and terminal reason.
7. Fault-inject malformed responses, timeouts, duplicates, stale state, and provider/tool failures.

## What to avoid
- retry loops with no budget;
- treating process exit as successful task completion;
- duplicate external mutations after restart;
- fallback paths that keep a high proof claim after capability is reduced.

## Completion gate
A high-risk synthetic failure path proves bounded retries, safe side effects, recoverable state, and an actionable terminal failure record.
