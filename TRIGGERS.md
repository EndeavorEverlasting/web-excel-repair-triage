# Harness Triggers

This file describes deterministic routing into repository skills and capabilities. The machine-readable authority is `harness/triggers.v1.json`.

## Routing table

| Trigger ID | Route when | Capability | Do not route when |
|---|---|---|---|
| `harness-infrastructure-change` | Maps, workflow/artifact/validator registries, completeness checks, hooks, skills, reports, or ownership are missing, stale, disconnected, or failing. | `harness-infrastructure-maintenance` | The task changes `AGENTS.md`, implements product behavior only, requires secrets, or requests destructive cleanup. |
| `prompt-language-change` | Prompt registry, actionability policy, builder, or generated Prompt Kit language changes; or a full language pass is requested. | `prompt-language-audit` | The request is only to read an existing validated report. |
| `lazy-next-action-report` | Empty, placeholder, observation-only, PR/status/log-only, optional-only, or generic next actions are suspected. | `prompt-language-audit` | No canonical registry/effective builder exists; route to repository intake first. |
| `skill-quality-unproven` | Skill correctness, routing, regression safety, efficiency, or token use lacks executable proof. | `skill-evaluation` | The task is ownership factoring only. |
| `skill-boundary-defect` | A skill is oversized, overlapping, ambiguous, prompt-only, or owns unrelated triggers. | `skill-factoring` | The boundary is healthy and the change is cosmetic only. |
| `technician-needs-latest-prompt-kit` | A technician needs a mouse-accessible clone/update/validate/open path for current `main`. | `technician-prompt-kit-acquisition` | The checkout is dirty, divergent, non-main, or has an unexpected origin. |

## Routing procedure

1. Match concrete repository state and request language against `harness/triggers.v1.json`.
2. Reject a route when any forbidden condition matches.
3. Select one primary capability, skill, and workflow ID.
4. Load required inputs and canonical registries before mutation.
5. Run the linked validator profile.
6. Record trigger, capability, workflow, artifacts, validation, and proof ceiling in the handoff.

## Collision rule

One writer owns each shared registry, workflow, generated artifact, branch, PR, or mutable runtime. Read-only audits may run in parallel only when they cannot invalidate the writer's floor. Harness infrastructure may modify contracts, registries, validators, tests, hooks, CI, skills, and reports; it may not silently take ownership of product implementation or governance.
