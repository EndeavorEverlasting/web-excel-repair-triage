# Harness Triggers

This file describes deterministic routing into repository skills and capabilities. The machine-readable root authority is `harness/triggers.v1.json`; prompt-registry passage and efficiency routing is owned by `harness/prompt-registry/triggers.v1.json`.

## Routing table

| Trigger ID | Route when | Capability | Do not route when |
|---|---|---|---|
| `prompt-language-change` | Prompt registry, actionability policy, builder, or generated Prompt Kit language changes; or a request asks for a full language pass. | `prompt-language-audit` | The request is only to read an already generated report. |
| `lazy-next-action-report` | Empty, placeholder, observation-only, PR/status/log-only, optional-only, or generic next actions are suspected. | `prompt-language-audit` | No canonical registry or effective builder is available. |
| `skill-quality-unproven` | A skill exists but correctness, boundary behavior, regression safety, efficiency, or token use lacks executable evidence. | `skill-evaluation` | The task is only skill ownership factoring. |
| `skill-boundary-defect` | A skill is oversized, overlapping, ambiguous, prompt-only, or owns multiple unrelated triggers. | `skill-factoring` | The boundary is healthy and only cosmetic text changes are requested. |
| `technician-needs-latest-prompt-kit` | A technician needs a mouse-accessible clone/update/validate/open path for current main. | `technician-prompt-kit-acquisition` | The checkout is dirty, divergent, non-main, or has an unexpected origin. |

## Prompt-registry passage and efficiency routing

| Trigger group | Deterministic route |
|---|---|
| `conversation-start-or-response` | `conversation-entry` |
| `prompt-impact-inspect`, `prompt-impact-plan` | `repository-inspection` |
| `prompt-impact-mutate`, `prompt-impact-mixed` | `bounded-repository-mutation` |
| `prompt-impact-validate` | `validation-proof-routing` |
| `prompt-impact-integrate` | `integration-handoff` |
| `full-prompt-registry-passage`, `conversation-canary-change` | `prompt-registry-passage` |
| `prompt-efficiency-unproven` | `prompt-efficiency-evaluation` for prompt-registry code and judge evaluation |
| `weak-model-readiness-unproven` | `prompt-efficiency-evaluation` with weak-model rubric floors |
| `model-response-efficiency-unproven` | `prompt-efficiency-evaluation` with candidate-response JSONL and LLM-on-LLM packets |

A generated execution profile is the routing receipt for prompt execution. An efficiency case and registered rubric are the routing receipt for evaluation. Do not replace either with fresh free-form judgment unless the source changed.

## Routing procedure

1. Match concrete state and request language against the applicable trigger registry.
2. Reject any route with a matching forbidden condition.
3. Select one primary capability and skill owner.
4. For a Prompt Kit prompt, prefer the generated execution profile.
5. For efficiency work, run deterministic checks before judge-model calls.
6. Load required inputs before mutation or judging.
7. Run linked workflow and validators.
8. Record trigger ID, capability ID, target kind, and proof ceiling.

## Collision rule

Prompt-language audit, prompt-registry passage, and non-strict efficiency audit may run read-only beside another lane. Prompt repair owns canonical prompt sources and generated output. Judge results and candidate responses remain runtime evidence. Shared registries or generated artifacts require one explicit writer.
