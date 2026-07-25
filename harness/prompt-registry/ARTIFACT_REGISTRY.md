# Prompt Registry Harness Artifact Registry

## Tracked artifacts

| Artifact | Path | Owner | Validation |
|---|---|---|---|
| Domain manifest | `harness/prompt-registry/manifest.v1.json` | harness lane | domain tests/auditors |
| Canary contract | `harness/contracts/conversation-canary.v1.json` | harness lane | domain tests |
| Execution-profile schema | `harness/prompt-registry/execution-profile.v1.json` | harness lane | domain tests/passage auditor |
| Efficiency policy | `harness/prompt-registry/prompt-efficiency-eval.v1.json` | harness lane | efficiency tests/evaluator |
| Efficiency fixtures | `harness/prompt-registry/fixtures/prompt-efficiency-cases.v1.json` | harness lane | efficiency tests |
| Capability registry | `harness/prompt-registry/capabilities.v1.json` | harness lane | domain tests/auditors |
| Trigger registry | `harness/prompt-registry/triggers.v1.json` | harness lane | domain tests/auditors |
| Scoped skills | `.ai/skills/*/SKILL.md` paths in domain manifest | harness lane | domain tests |
| Contract validator | `scripts/prompt_registry_harness_contracts.py` | harness lane | unit tests/CI |
| Profile engine | `scripts/prompt_registry_profiles.py` | harness lane | unit tests/CI |
| Passage auditor | `scripts/audit_prompt_registry_harness.py` | harness lane | unit tests/CI |
| Efficiency contracts | `scripts/prompt_efficiency_contracts.py` | harness lane | unit tests/CI |
| Deterministic case engine | `scripts/prompt_efficiency_cases.py` | harness lane | unit tests/CI |
| LLM judge aggregator | `scripts/prompt_efficiency_judge.py` | harness lane | unit tests/CI |
| Public eval facade | `scripts/prompt_efficiency_eval.py` | harness lane | unit tests/CI |
| Efficiency CLI | `scripts/evaluate_prompt_efficiency.py` | harness lane | unit tests/CI |
| Operator reports | `harness/reports/PROMPT_REGISTRY_PASSAGE.md`, `harness/reports/PROMPT_EFFICIENCY_EVAL.md` | harness lane | domain tests |

## Runtime artifacts

| Artifact | Default path | Schema | Tracking |
|---|---|---|---|
| Full passage audit | `Outputs/prompt-registry-harness-audit.json` | `prompt-registry-harness-audit-result/v1` | Gitignored; CI artifact allowed |
| Strict canary audit | `Outputs/prompt-registry-canary-strict.json` | passage schema with `strict_canary=true` | Gitignored; product gate |
| Efficiency audit | `Outputs/prompt-efficiency-eval.json` | `prompt-efficiency-eval-result/v1` | Gitignored; CI artifact allowed |
| Efficiency strict audit | `Outputs/prompt-efficiency-eval-strict.json` | same schema with `strict=true` | Gitignored; product/eval gate |
| Judge packet set | `Outputs/prompt-efficiency-judge-packets.json` | `prompt-efficiency-judge-packet-set/v1` | Gitignored; process one case at a time |
| Judge result stream | `Outputs/prompt-efficiency-judge-results.jsonl` | one `prompt-efficiency-judge-result/v1` object per line | Gitignored; external model evidence |
| Candidate responses | operator-selected `Outputs/*.jsonl` | `case_id`, `prompt_id`, `model_id`, `response` | Gitignored; never commit private transcripts |

## Compactness and judge rules

Execution profiles contain IDs, routing, impacts, source identity, references, and token metrics, but no full prompt. Judge packets may contain one selected prompt because the judge must evaluate it; they are ordered for one-case passage and remain runtime artifacts. Judge results must use exact dimensions, scores 0..4, unique `(case_id, judge_id)` pairs, and registered verdicts.

## Naming

- Tracked contracts and registries: explicit `v1` schema/version.
- Runtime reports: stable family names under `Outputs/`.
- Skill directories: lower-case kebab-case.
- Findings: stable IDs such as `duplicate-lines`, `weak-model-structure`, `response-objective-canary`, and `canary-missing`.

## Proof boundary

Code artifacts prove measurable structure, size, routing, and schema coverage. Validated LLM judge results prove rubric-scored model opinion for the evaluated cases. Human resolution, real weak-model completion, and user productivity remain separate evidence.
