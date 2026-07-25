# Prompt Efficiency Evaluation

## Trigger

Prompt token efficiency, weak-model readiness, LLM-as-judge evaluation, or model-response efficiency lacks executable proof.

## Required inputs

- Effective prompt registry or candidate-response JSONL.
- `harness/prompt-registry/prompt-efficiency-eval.v1.json`.
- Optional independent judge results using `prompt-efficiency-judge-result/v1`.
- Target prompt ID when the pass is intentionally bounded.

## Outputs

- Deterministic prompt or response findings.
- One compact judge packet per evaluated case.
- Validated and aggregated LLM judge scores when supplied.
- Strict readiness result and smallest repair ledger.

## Procedure

1. Run deterministic checks before spending judge-model tokens.
2. Emit judge packets and process them one case at a time in passage order.
3. Use an independent model and require JSON-only results against the registered rubric.
4. Ingest judge results; reject missing cases, duplicate judges, unknown dimensions, or out-of-range scores.
5. Repair canonical prompt sources only in an authorized product lane.
6. Rerun deterministic and judge gates; keep code, judge, human, and user evidence distinct.

## Guardrails

- Do not reward prompt length, confidence, or stylistic polish.
- Do not remove scope, validation, failure handling, or output contracts merely to reduce tokens.
- Do not claim LLM-judge proof when no validated judge results were supplied.
- Do not call a prompt weak-model ready when any strict rubric floor fails.
- Do not commit candidate responses, private transcripts, credentials, or generated runtime reports.

## Validation

- `python -m unittest tests.test_prompt_efficiency_eval -v`
- `python scripts/evaluate_prompt_efficiency.py --output Outputs/prompt-efficiency-eval.json --emit-judge-packets Outputs/prompt-efficiency-judge-packets.json --summary`
- Strict downstream gate: `python scripts/evaluate_prompt_efficiency.py --judge-results Outputs/prompt-efficiency-judge-results.jsonl --strict --output Outputs/prompt-efficiency-eval-strict.json --summary`

## Proof ceiling

Deterministic checks prove measurable structure and size. Validated judge results prove rubric-scored model opinion for the evaluated inputs, not real-user success or universal model behavior.
