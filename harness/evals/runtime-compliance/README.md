# Prompt Runtime Compliance — Contract & Receipt Floor

Status: **TRACKED / VALIDATED contract floor** (Sprint 1 of the Prompt Runtime Compliance Pilot).

Canonical plan: [`harness/evals/PROMPT_RUNTIME_COMPLIANCE_PILOT_PLAN.md`](../PROMPT_RUNTIME_COMPLIANCE_PILOT_PLAN.md).
Owner: P67 / `skill-evaluation`. No new prompt or skill identity is introduced by this pilot.

This directory holds the deterministic contract floor for measuring whether an actual
model/runtime obeys execution-boundary, continuation, proof-state, and regression
contracts — not merely whether those instructions compile into Prompt Kit output.

## Canonical identities (Sprint 1)

| Identity | Path | Role |
|---|---|---|
| `prompt-runtime-compliance-receipt/v1` | `harness/contracts/prompt-runtime-compliance-receipt.schema.v1.json` | Strict Draft 2020-12 schema for one runtime-compliance trace receipt. |
| `prompt-runtime-compliance/v1` | `harness/contracts/prompt-runtime-compliance.v1.json` | Pinned machine-readable rule identities/severity/trigger/required-relationship table plus composition. |
| `prompt-runtime-compliance-validation/v1` | `harness/contracts/prompt-runtime-compliance.v1.json#/validation_result_schema_definition` | Draft 2020-12 schema for the validator's machine-readable result. |
| `prompt-runtime-compliance-capture-mapping/v1` | `harness/evals/runtime-compliance/runtime/capture-mapping.v1.json` | Lossless capture → receipt → observed-proof field mapping and fail-closed invariants. |

Accepted semantic rule design: [`SEMANTIC_VALIDATOR_RULES_V1.md`](./SEMANTIC_VALIDATOR_RULES_V1.md).

Later root-harness registration must point to these exact paths/identities; aliases or
"equivalent" alternate owners are rejected unless a separately reviewed migration changes
the plan first.

## Composition — this receipt links upward, it does not replace owners

The runtime-compliance receipt is a specialized trace authority. It must not become a
second generic outcome authority or a second failure observatory.

- `prompt-outcome-receipt/v1` (P99) may reference a compliance receipt as bounded evidence.
- `observed-behavior-proof/v1` may certify an exact observed run and PASSes only when the
  compliance receipt validates and the observed evidence class is strong enough.
- `execution-boundary-enforcement/v1` + `execution-boundary-taxonomy/v1` own boundary and
  recovery semantics; this floor pins the taxonomy revision rather than redefining it.
- `prompt-regression-safety/v1` (P13/P94) owns recurring-defect and retained-regression
  routing; this floor only records linkage.
- `privacy-preserving-failure-observatory/v1` (PR #544) is a read-only dependency; no hook
  or sentinel is implemented or mutated here.

## Privacy invariants

Raw prompts, responses, conversation transcripts, hidden reasoning, credentials, and
secret-bearing payloads are forbidden persisted evidence. The receipt schema carries only
distilled operational state; `additionalProperties: false` at every object prevents raw
payload smuggling, and the optional `privacy` block pins the non-persistence booleans.

## Proof taxonomy and ceiling

- TRACKED: plan/contracts/fixtures exist in repository state.
- VALIDATED: deterministic validators/tests pass for the exact candidate.
- OBSERVED: actual model/runtime scenario execution is captured and validated.

No lower state silently proves a higher state. Sprint 1's ceiling is a **VALIDATED contract
floor**: identities, schemas, rule table, and capture mapping exist and parse. It does not
implement the executable validator (Sprint 2A), fixtures/oracles (Sprint 2B), runner
(Sprint 3A), linkage (Sprint 3B), harness registration (Sprint 4), or any observed runtime
obedience (Sprint 5).

## Contract-proof fixtures

`contract-fixtures/receipt.positive.v1.json` is a schema-valid RTC01-style receipt used to
prove the receipt schema accepts a well-formed trace. Negative controls (additional-property
smuggling, missing required fields, malformed identity/pattern) are derived by mutation in
`tests/test_prompt_runtime_compliance_contract.py`. Full five-scenario RTC01..RTC05
fixtures/oracles are owned by Sprint 2B under `fixtures/` and are intentionally absent here.
