# Prompt Registry Passage

## Trigger

A full pass across Prompt Kit prompts, canary coverage, prompt impacts, skill factoring, capability routing, or token reduction is requested.

## Required inputs

- Effective prompt registry from `scripts/build_prompt_kit_registry.py`.
- Domain manifest, capability/trigger registries, execution-profile schema, and canary contract.
- Optional prompt ID filter.

## Outputs

- One compact execution profile per effective prompt.
- Capability/skill counts and ordered passage list.
- Canary coverage and gap ledger.
- Estimated repeated-character avoidance from references instead of embedded shared prose.

## Procedure

1. Run the auditor in non-strict mode to establish complete coverage.
2. Inspect compact profiles instead of loading every full prompt simultaneously.
3. Use the assigned capability/skill and shared contract references for each passage.
4. Use strict canary mode only after an authorized prompt-registry product sprint inserts the canary.
5. Route valid defects to prompt-language audit, skill factoring, skill evaluation, or product repair as appropriate.

## Guardrails

- Do not mutate prompt registries in a harness-only lane.
- Do not embed full `copyContent` in execution profiles or reports.
- Do not interpret missing canaries as provider failure before the prompts contain the contract.
- Do not make provider/model quality claims from static registry analysis.

## Validation

- `python -m unittest tests.test_prompt_registry_harness -v`
- `python scripts/audit_prompt_registry_harness.py --output Outputs/prompt-registry-harness-audit.json --summary`
- Downstream strict gate: `python scripts/audit_prompt_registry_harness.py --strict-canary --output Outputs/prompt-registry-canary-strict.json --summary`.

## Proof ceiling

Exhaustive static registry/profile coverage and canary inclusion only; no provider obedience.
