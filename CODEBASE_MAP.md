# Codebase Map

This map is the harness entry point for `EndeavorEverlasting/web-excel-repair-triage`.

## Reading order for a fresh agent

1. `AGENTS.md` — repository governance.
2. `CODEBASE_MAP.md` — repository navigation.
3. `WORKFLOW.md` — task selection, validation, recovery, and handoff.
4. `ARTIFACT_REGISTRY.md` — tracked and runtime artifact contracts.
5. `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md` — reusable procedures and deterministic routing.
6. `harness/manifest.v1.json` — root harness inventory and validation order.
7. `harness/prompt-registry/manifest.v1.json` — prompt passage, canary, efficiency, and judge-eval domain.
8. `harness/reports/CURRENT_STATE.md` — current working state and proof ceiling.

## Repository structure

```text
web-excel-repair-triage/
├── AGENTS.md
├── CODEBASE_MAP.md
├── WORKFLOW.md
├── ARTIFACT_REGISTRY.md
├── SKILLS.md
├── CAPABILITIES.md
├── TRIGGERS.md
├── docs/prompts.json
├── registry/prompts/
├── build_prompt_kit.py
├── web/prompt-kit/index.html
├── harness/
│   ├── manifest.v1.json
│   ├── capabilities.v1.json
│   ├── triggers.v1.json
│   ├── contracts/
│   │   ├── prompt-kit-interactions.v1.json
│   │   └── conversation-canary.v1.json
│   ├── evals/
│   ├── prompt-registry/
│   │   ├── manifest.v1.json
│   │   ├── capabilities.v1.json
│   │   ├── triggers.v1.json
│   │   ├── execution-profile.v1.json
│   │   ├── prompt-efficiency-eval.v1.json
│   │   ├── fixtures/prompt-efficiency-cases.v1.json
│   │   ├── CODEBASE_MAP.md
│   │   ├── WORKFLOW.md
│   │   └── ARTIFACT_REGISTRY.md
│   └── reports/
│       ├── CURRENT_STATE.md
│       ├── PROMPT_REGISTRY_PASSAGE.md
│       └── PROMPT_EFFICIENCY_EVAL.md
├── scripts/
│   ├── build_prompt_kit_registry.py
│   ├── evaluate_prompt_language.py
│   ├── audit_prompt_registry_harness.py
│   ├── prompt_registry_harness_contracts.py
│   ├── prompt_registry_profiles.py
│   ├── prompt_efficiency_contracts.py
│   ├── prompt_efficiency_cases.py
│   ├── prompt_efficiency_judge.py
│   ├── prompt_efficiency_eval.py
│   ├── evaluate_prompt_efficiency.py
│   ├── validate_prompt_kit_interactions.py
│   └── validate_harness.py
├── tests/
│   ├── test_harness_contract.py
│   ├── test_prompt_registry_harness.py
│   ├── test_prompt_efficiency_eval.py
│   ├── test_prompt_kit_interactions_contract.py
│   └── test_prompt_language_audit.py
├── .ai/skills/
├── .githooks/
├── Candidates/
├── Active/
└── Outputs/
```

## Primary entry points

| Entry point | Purpose |
|---|---|
| `Acquire-Latest-PromptKit.cmd` | Safe technician clone/update/validate/open flow. |
| `web/prompt-kit/index.html` | Canonical checked-in Prompt Kit website. |
| `scripts/build_prompt_kit_registry.py` | Build the effective registry and deterministic website. |
| `scripts/evaluate_prompt_language.py` | Exhaustive prompt-language audit. |
| `scripts/audit_prompt_registry_harness.py` | Compact profile and canary passage audit. |
| `scripts/evaluate_prompt_efficiency.py` | Code-based prompt/response checks, judge packets, LLM-result validation, and strict weak-model gate. |
| `scripts/validate_prompt_kit_interactions.py` | Prompt-card interaction contract audit. |
| `scripts/validate_harness.py` | Root harness completeness validator. |

## Configuration and registries

| Path | Contract |
|---|---|
| `harness/manifest.v1.json` | Root component and domain-contract inventory. |
| `harness/prompt-registry/manifest.v1.json` | Prompt passage/evaluation component inventory. |
| `harness/prompt-registry/execution-profile.v1.json` | Compact routing profile; full prompt text forbidden. |
| `harness/prompt-registry/prompt-efficiency-eval.v1.json` | Four-lane eval policy, deterministic thresholds, two judge rubrics, and strict gate. |
| `harness/contracts/conversation-canary.v1.json` | `OBJECTIVE` / `REPOS` response canary. |
| `docs/prompts.json`, `registry/prompts/*.json` | Canonical prompt sources and shared policies. |

## Build and validation commands

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_registry_harness -v
python -m unittest tests.test_prompt_efficiency_eval -v
python scripts\audit_prompt_registry_harness.py --output Outputs\prompt-registry-harness-audit.json --summary
python scripts\evaluate_prompt_efficiency.py --output Outputs\prompt-efficiency-eval.json --emit-judge-packets Outputs\prompt-efficiency-judge-packets.json --summary
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts\validate_prompt_kit_interactions.py --output Outputs\prompt-kit-interaction-audit.json --summary
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Strict efficiency additionally requires validated independent judge results:

```powershell
python scripts\evaluate_prompt_efficiency.py --judge-results Outputs\prompt-efficiency-judge-results.jsonl --strict --output Outputs\prompt-efficiency-eval-strict.json --summary
```

## Safety boundaries and known traps

- `Candidates/` and `Active/` are read-only inputs; runtime outputs belong under `Outputs/`.
- Do not edit generated HTML as the canonical source.
- Run code-based efficiency checks before judge-model calls.
- Token reduction must not remove objective, scope, input, action, failure, validation, output, or handoff structure required by weak models.
- Missing judge evidence is not a passing LLM evaluation; strict mode fails incomplete coverage.
- LLM judge scores are model opinions under a fixed rubric, not human truth or user acceptance.
- Candidate responses and judge results may contain private data; do not commit them.
- Static or CI proof does not establish browser, provider, live-runtime, production, or user-productivity success.
