# Prompt Registry Harness Workflow

## 1. Pick up a passage or evaluation task

1. Read `AGENTS.md`, the domain manifest, canary contract, execution-profile schema, efficiency policy, capability registry, trigger registry, and operator reports.
2. Record repository and Git state without discarding existing work.
3. Declare the lane:
   - **audit-only** — inventory, profiling, routing, canary, and efficiency findings;
   - **harness repair** — contracts, skills, validators, tests, hooks, CI, and reports;
   - **prompt product repair** — canonical prompt sources and generated output, outside this harness sprint;
   - **model-response eval** — approved candidate-response evidence and independent judge results.
4. Select `prompt-registry-passage` for full inventory or `prompt-efficiency-evaluation` for token/weak-model proof.
5. Use the profile-assigned execution capability only when moving into an authorized prompt run.

## 2. Run a full passage

```powershell
python scripts\audit_prompt_registry_harness.py `
  --output Outputs\prompt-registry-harness-audit.json `
  --summary
```

The report must contain one compact profile per effective prompt, no embedded full prompt text, deterministic capability/skill ownership, ordered passage, and visible canary coverage.

## 3. Run efficiency checks before judge tokens

```powershell
python scripts\evaluate_prompt_efficiency.py `
  --output Outputs\prompt-efficiency-eval.json `
  --emit-judge-packets Outputs\prompt-efficiency-judge-packets.json `
  --summary
```

Code checks measure prompt characters, approximate tokens, duplicate lines, oversized lines, explicit weak-model structure signals, and missing required metadata. They run before any LLM judge.

For a bounded prompt:

```powershell
python scripts\evaluate_prompt_efficiency.py --prompt P07 --emit-judge-packets Outputs\P07-judge-packet.json --summary
```

## 4. LLM-as-judge pass-through

1. Process the packet list in order, one case at a time.
2. Use an independent model where practical.
3. Judge only against the registered rubric; do not reward length, confidence, or polish.
4. Return one `prompt-efficiency-judge-result/v1` JSON object per case.
5. Store results as JSONL under `Outputs/`.
6. Ingest and validate:

```powershell
python scripts\evaluate_prompt_efficiency.py `
  --judge-results Outputs\prompt-efficiency-judge-results.jsonl `
  --strict `
  --output Outputs\prompt-efficiency-eval-strict.json `
  --summary
```

Strict mode requires zero code warnings, complete judge coverage, passing verdicts, passing average scores, all dimensions above the general floor, and higher required floors for token economy and weak-model resilience.

## 5. Evaluate one LLM with another LLM

Create candidate-response JSONL with `case_id`, `prompt_id`, `model_id`, and `response`, then run:

```powershell
python scripts\evaluate_prompt_efficiency.py `
  --candidate-responses Outputs\candidate-responses.jsonl `
  --emit-judge-packets Outputs\model-response-judge-packets.json `
  --summary
```

This path adds deterministic empty-response, canary, and response-size checks, then emits one prompt/response pair per judge case.

## 6. Canary gate

Non-strict passage mode records missing canaries without failing the harness. After an authorized prompt-product sprint inserts the contract, run the existing strict canary gate. Canary inclusion, efficiency scoring, and model adherence remain separate proof lanes.

## 7. Validate before committing

1. Compile passage and efficiency modules/tests.
2. Run domain contract tests and efficiency tests.
3. Generate non-strict passage and efficiency reports plus judge packets.
4. Run root harness validator/contracts.
5. Run exact Prompt Kit parity to prove the harness did not mutate product output.
6. Run artifact hygiene and `git diff --check`.
7. Run broader suites last.

## 8. Handle failures

- **Coverage mismatch:** repair registry loading/profile or case generation before interpreting findings.
- **Unknown capability/skill:** repair registries atomically; do not ask the model to guess.
- **Judge result malformed:** reject unknown cases, duplicate judge IDs, wrong rubrics, missing dimensions, or scores outside 0..4.
- **Judge coverage incomplete:** strict mode fails; do not report an LLM evaluation as passed.
- **Code warning:** preserve it as prompt-product repair debt; do not lower thresholds merely to turn green.
- **Token reduction weakens structure:** reject the repair; weak-model readiness outranks raw brevity.
- **Provider/model stops emitting the canary:** leave the chat and preserve the last trustworthy state.
- **Dirty or conflicting worktree:** isolate the lane; no reset, clean, or force.

## 9. Handoff

Report repository, branch, domain capability, target kind, prompt/case counts, code findings, judge coverage/pass counts, canary coverage, artifact paths, validation, commit SHA, PR state, proof ceiling, product gaps, and one exact executable next command.
