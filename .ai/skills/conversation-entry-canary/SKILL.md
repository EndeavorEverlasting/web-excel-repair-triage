# Conversation Entry Canary

## Trigger

Every assistant response, or whenever objective/repository context may have changed.

## Required inputs

- Current concrete objective.
- Every relevant canonical repository and active branch when known.
- `harness/contracts/conversation-canary.v1.json`.

## Outputs

- The required `OBJECTIVE:` and `REPOS:` prefix.
- A canary-breach signal when either line is absent, stale, or materially wrong.

## Procedure

1. Resolve the current objective from the latest governing task.
2. Resolve relevant repositories from active work; use `none` only for non-repository work.
3. Emit the two contract lines before other content.
4. When a breach is detected, reload objective, repositories, branch, scope, and last proven state before continuing.

## Guardrails

- Do not include personal names or identifiers.
- Do not invent repositories or branches.
- Do not treat the canary as proof that later work is correct.

## Validation

- Run `python -m unittest tests.test_prompt_registry_harness -v`.
- Use downstream model-response evals for actual adherence.

## Proof ceiling

Static contract and routing proof until model responses are observed.
