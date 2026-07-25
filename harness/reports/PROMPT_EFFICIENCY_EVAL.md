# Prompt Efficiency Evaluation State

## Objective

Minimize avoidable prompt and response tokens while retaining the explicit objective, context, action, scope, failure, validation, output, and handoff structure required by weak models.

## Evaluation stack

1. **Code-based:** runs first and measures prompt size, approximate tokens, duplicate lines, oversized lines, weak-model structure signals, empty content, response canaries, and response size.
2. **LLM as judge:** evaluates one prompt or model response at a time against a versioned rubric and returns strict JSON evidence.
3. **Human:** resolves disputed findings and approves intentional exceptions.
4. **User:** measures actual completion speed, corrections, abandonment, and usefulness.

## Working surfaces

- Policy: `harness/prompt-registry/prompt-efficiency-eval.v1.json`
- Fixtures: `harness/prompt-registry/fixtures/prompt-efficiency-cases.v1.json`
- Engine: `scripts/prompt_efficiency_eval.py`
- CLI: `scripts/evaluate_prompt_efficiency.py`
- Tests: `tests/test_prompt_efficiency_eval.py`
- Skill: `.ai/skills/prompt-efficiency-evaluation/SKILL.md`

## Pass-through behavior

The CLI performs deterministic checks before creating judge work. Judge packets are ordered and declare `one case at a time in listed order`, allowing an agent to evaluate prompts without loading or reinterpreting the full registry at once. Prompt packets contain only the selected prompt and the shared rubric. Model-response packets pair one candidate response with its owning prompt, enabling one LLM to evaluate another LLM.

## Gates

Non-strict harness audit:

```powershell
python scripts\evaluate_prompt_efficiency.py --output Outputs\prompt-efficiency-eval.json --emit-judge-packets Outputs\prompt-efficiency-judge-packets.json --summary
```

Strict product/eval gate:

```powershell
python scripts\evaluate_prompt_efficiency.py --judge-results Outputs\prompt-efficiency-judge-results.jsonl --strict --output Outputs\prompt-efficiency-eval-strict.json --summary
```

The strict gate requires no deterministic warnings, complete judge coverage, passing verdicts, passing average score, every dimension above its floor, and higher floors for token economy and weak-model resilience.

## Known gap

The harness can identify and enforce repair debt, but it does not mutate canonical prompts in this harness lane. Current prompt findings must be repaired in an authorized prompt-product sprint, then evaluated with an independent model. Real operator speed remains user-eval proof.

## Proof ceiling

Static code metrics and validated judge opinions only. No claim of universal provider adherence, actual weak-model completion, or user productivity is made without corresponding model runs and user evidence.
