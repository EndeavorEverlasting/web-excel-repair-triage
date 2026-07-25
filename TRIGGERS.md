# Harness Triggers

This file describes deterministic routing into repository skills and capabilities. The machine-readable root authority is `harness/triggers.v1.json`; prompt-registry passage routing is owned by `harness/prompt-registry/triggers.v1.json`.

## Routing table

| Trigger ID | Route when | Capability | Do not route when |
|---|---|---|---|
| `prompt-language-change` | Prompt registry, actionability policy, builder, or generated Prompt Kit language changes; or a request asks for a full language pass. | `prompt-language-audit` | The request is only to read an already generated report. |
| `lazy-next-action-report` | Empty, placeholder, observation-only, PR/status/log-only, optional-only, or generic next actions are suspected. | `prompt-language-audit` | No canonical registry or effective builder is available; route first to repository intake. |
| `skill-quality-unproven` | A skill exists but correctness, boundary behavior, regression safety, efficiency, or token use lacks executable evidence. | `skill-evaluation` | The task is only skill ownership factoring with no eval implementation requested. |
| `skill-boundary-defect` | A skill is oversized, overlapping, ambiguous, prompt-only, or owns multiple unrelated triggers. | `skill-factoring` | The skill boundary is healthy and only cosmetic text changes are requested. |
| `technician-needs-latest-prompt-kit` | A technician needs a mouse-accessible clone/update/validate/open path for the current main Prompt Kit. | `technician-prompt-kit-acquisition` | The checkout is dirty, divergent, on a non-main branch, or has an unexpected origin. |

## Prompt-registry passage routing

| Trigger group | Deterministic route |
|---|---|
| `conversation-start-or-response` | `conversation-entry` |
| `prompt-impact-inspect`, `prompt-impact-plan` | `repository-inspection` |
| `prompt-impact-mutate`, `prompt-impact-mixed` | `bounded-repository-mutation` |
| `prompt-impact-validate` | `validation-proof-routing` |
| `prompt-impact-integrate` | `integration-handoff` |
| `full-prompt-registry-passage`, `conversation-canary-change` | `prompt-registry-passage` |

The machine-readable domain registry contains the exact positive and forbidden conditions. A generated execution profile is the routing receipt; do not replace it with fresh free-form judgment unless the profile or underlying prompt changed.

## Routing procedure

1. Match concrete repository state and request language against the applicable trigger registry.
2. Reject any route with a matching forbidden condition.
3. Select one primary capability and skill owner.
4. For a Prompt Kit prompt, prefer the generated `prompt-execution-profile/v1` route.
5. Load its required inputs before mutation.
6. Run the linked workflow and validators.
7. Record the trigger ID and capability ID in the handoff.

## Collision rule

Prompt-language audit and prompt-registry passage may run read-only beside another lane, but repair mode owns canonical prompt registries, policies, tests, and generated Prompt Kit output. Skill-evaluation implementation owns the target skill's eval files and directly related repairs. Shared registries, workflows, or generated artifacts require one explicit writer.
