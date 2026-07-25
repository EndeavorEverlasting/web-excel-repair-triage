# Prompt Registry Harness Codebase Map

## Reading order

1. `AGENTS.md` for repository law.
2. `harness/prompt-registry/manifest.v1.json` for the complete domain inventory.
3. `harness/contracts/conversation-canary.v1.json` for the universal response canary.
4. `harness/prompt-registry/execution-profile.v1.json` for compact per-prompt metadata.
5. `harness/prompt-registry/prompt-efficiency-eval.v1.json` for code, LLM-judge, human, and user eval contracts.
6. `harness/prompt-registry/capabilities.v1.json` and `triggers.v1.json` for deterministic routing.
7. The selected `.ai/skills/*/SKILL.md`.
8. `harness/prompt-registry/WORKFLOW.md` for passage, evaluation, validation, failure, and handoff.
9. `harness/reports/PROMPT_REGISTRY_PASSAGE.md` and `PROMPT_EFFICIENCY_EVAL.md` for operator state.

## Structure

```text
harness/
├── contracts/conversation-canary.v1.json
├── prompt-registry/
│   ├── manifest.v1.json
│   ├── capabilities.v1.json
│   ├── triggers.v1.json
│   ├── execution-profile.v1.json
│   ├── prompt-efficiency-eval.v1.json
│   ├── fixtures/prompt-efficiency-cases.v1.json
│   ├── CODEBASE_MAP.md
│   ├── WORKFLOW.md
│   └── ARTIFACT_REGISTRY.md
└── reports/
    ├── PROMPT_REGISTRY_PASSAGE.md
    └── PROMPT_EFFICIENCY_EVAL.md

.ai/skills/
├── conversation-entry-canary/SKILL.md
├── repository-inspection/SKILL.md
├── bounded-repository-mutation/SKILL.md
├── validation-proof-routing/SKILL.md
├── integration-handoff/SKILL.md
├── prompt-registry-passage/SKILL.md
└── prompt-efficiency-evaluation/SKILL.md

scripts/prompt_registry_harness_contracts.py
scripts/prompt_registry_profiles.py
scripts/audit_prompt_registry_harness.py
scripts/prompt_efficiency_contracts.py
scripts/prompt_efficiency_cases.py
scripts/prompt_efficiency_judge.py
scripts/prompt_efficiency_eval.py
scripts/evaluate_prompt_efficiency.py
tests/test_prompt_registry_harness.py
tests/test_prompt_efficiency_eval.py
```

Full skill paths:
- `.ai/skills/conversation-entry-canary/SKILL.md`
- `.ai/skills/repository-inspection/SKILL.md`
- `.ai/skills/bounded-repository-mutation/SKILL.md`
- `.ai/skills/validation-proof-routing/SKILL.md`
- `.ai/skills/integration-handoff/SKILL.md`
- `.ai/skills/prompt-registry-passage/SKILL.md`
- `.ai/skills/prompt-efficiency-evaluation/SKILL.md`

## Canonical prompt inputs

- `docs/prompts.json`
- `registry/prompts/skill-development-prompts.v1.json`
- `registry/prompts/actionable-next-step-policy.v1.json`
- `scripts/build_prompt_kit_registry.py`

The passage auditor consumes the **effective** registry through `load_prompt_registry()`. Compact profiles never embed full prompt text. The efficiency evaluator reads one selected prompt per judge case and can also pair that prompt with one candidate model response.

## Entry points

| Entry point | Purpose |
|---|---|
| `python scripts/audit_prompt_registry_harness.py --summary` | Inventory and profile every effective prompt. |
| `python scripts/audit_prompt_registry_harness.py --prompt P07 --summary` | Inspect one compact profile. |
| `python scripts/audit_prompt_registry_harness.py --strict-canary --summary` | Downstream gate after prompt product mutation. |
| `python scripts/evaluate_prompt_efficiency.py --output Outputs/prompt-efficiency-eval.json --emit-judge-packets Outputs/prompt-efficiency-judge-packets.json --summary` | Run code checks first and emit ordered prompt-registry judge packets. |
| `python scripts/evaluate_prompt_efficiency.py --candidate-responses Outputs/candidate-responses.jsonl --emit-judge-packets Outputs/model-response-judge-packets.json --summary` | Build LLM-on-LLM evaluation packets. |
| `python scripts/evaluate_prompt_efficiency.py --judge-results Outputs/prompt-efficiency-judge-results.jsonl --strict --summary` | Enforce complete passing judge evidence plus zero deterministic warnings. |
| `python -m unittest tests.test_prompt_registry_harness -v` | Domain contract/completeness tests. |
| `python -m unittest tests.test_prompt_efficiency_eval -v` | Efficiency and judge-result contract tests. |

## Known traps

- A missing canary in current prompts is a **product gap**, not a harness failure in non-strict mode.
- A missing judge result is not a passing LLM evaluation; strict mode fails incomplete coverage.
- Do not optimize only for fewer tokens. Removing objective, scope, failure handling, validation, output, or handoff structure can make weak models less reliable.
- LLM judge scores are model opinions under a fixed rubric, not ground truth or user acceptance.
- Candidate responses and judge results may contain private data; keep them under approved gitignored output paths.
- Do not add repeated skill procedures or rubrics to every execution profile; use shared references and one-case packets.
- Do not edit canonical prompts, the builder, JavaScript, or generated HTML in this harness lane.
