# Prompt Outcome Divergence Sprint

Canonical execution lane: PR #452 (`feat/prompt-outcome-receipts-20260913`).

## Accepted model

- P99 owns privacy-bounded outcome/friction semantics.
- P115 owns the grounding recovery protocol.
- P07/P32 own bounded repair.
- P105 owns authorized promotion.
- Observed outcome symptoms remain separate from candidate cause families.
- Divergence math is scoped to a grounding episode, never to global prompt usage.
- Ordinary prompt reuse across separate sprint/task anchors is neutral.
- Legitimate repeated work with durable evidence advance is neutral.
- Repeated corrective actions are separate uniquely identified correction events; they are not an occurrence-count multiplier and are never inferred from prompt invocation count.

## Formula

For grounding episode `e`, `C_e` contains only correction events whose `grounding_episode_id` equals `e` and whose `corrective` flag is true.

`B_e = sum(weight[a.kind] for a in C_e)`

`Y_e = response_relevance_e / (1 + B_e)`

`D_e = 1 - Y_e`

Prompt-usage count and legitimate sprint/task iteration count do not appear in `B_e`.

## Fixed-point gates

1. Contract, receipt schema, deterministic classifier, fixtures and tests encode episode-scoped semantics.
2. Review findings on schema bounds, fractional counts, nested validation, decision tuple consistency and durability classification are regression-tested.
3. Validator/test are registered in harness manifest, validator profiles, deterministic test floor and operational harness CI.
4. Exact PR head is reconciled with current default-branch truth and CI/review are green.
5. Authorized exact head is integrated into `main` and containment/content proof is refreshed from provider truth.
