# Harness Triggers

This file describes deterministic routing into repository skills, capabilities, and registered domain overlays. The machine-readable root authority is `harness/triggers.v1.json`; domain-specific trigger registries are named explicitly below.

## Routing table

| Trigger ID | Route when | Capability | Do not route when |
|---|---|---|---|
| `prompt-language-change` | Prompt registry, actionability policy, builder, or generated Prompt Kit language changes; or a request asks for a full language pass. | `prompt-language-audit` | The request is only to read an already generated report. |
| `lazy-next-action-report` | Empty, placeholder, observation-only, PR/status/log-only, optional-only, or generic next actions are suspected. | `prompt-language-audit` | No canonical registry or effective builder is available; route first to repository intake. |
| `skill-quality-unproven` | A skill exists but correctness, boundary behavior, regression safety, efficiency, or token use lacks executable evidence. | `skill-evaluation` | The task is only skill ownership factoring with no eval implementation requested. |
| `skill-boundary-defect` | A skill is oversized, overlapping, ambiguous, prompt-only, or owns multiple unrelated triggers. | `skill-factoring` | The skill boundary is healthy and only cosmetic text changes are requested. |
| `technician-needs-latest-prompt-kit` | A technician needs a mouse-accessible clone/update/validate/open path for the current main Prompt Kit. | `technician-prompt-kit-acquisition` | The checkout is dirty, divergent, on a non-main branch, or has an unexpected origin. |

## NTH domain overlay triggers

Machine-readable authority: `harness/nth/triggers.v1.json`.

| Trigger ID | Route when | Mode | Do not route when |
|---|---|---|---|
| `nth-internal-workbook-request` | Construct, repair, analyze, audit, or task-distribute a Neuron Track Hours workbook; establish the evidence-rich working artifact. | Internal / working | Active month cannot be resolved, roster/attendance is unavailable, or the action would silently mutate an unchanged historical source. |
| `nth-client-send-copy-request` | Prepare a management/client NTH send copy from a validated internal workbook under the active month's tab/exposure contract. | Client-facing / management | No validated internal workbook exists, the active client tab contract is unknown, or the projection would change totals/dates/task attribution. |

Both NTH triggers route to `WORKFLOW.md#h-neuron-track-hours-monthly-artifact` and `.ai/skills/neuron-track-hours-monthly-artifact/SKILL.md`.

## Routing procedure

1. Match concrete repository state and request language against the root trigger registry and any registered domain overlay in `harness/manifest.v1.json`.
2. Reject any route with a matching forbidden condition.
3. Select one primary capability or domain-overlay workflow/skill owner.
4. Load its required inputs before mutation.
5. Run the linked workflow and validators.
6. Record the trigger ID and capability ID or domain overlay in the handoff.

For NTH work, resolve the active month rule pack before assigning task workstreams or packaging a client copy. Internal construction precedes client projection.

## Collision rule

Prompt-language audit may run read-only beside another lane, but repair mode owns canonical prompt registries, policies, tests, and generated Prompt Kit output. Skill-evaluation implementation owns the target skill's eval files and directly related repairs. NTH internal/client work may share read-only source evidence, but a concrete workbook has one writer and the client send copy must derive from that validated internal writer's artifact. Shared registries, workflows, generated artifacts, or mutable runtime surfaces require one explicit writer.
