---
id: prompt-surface-routing
version: 1.0.0
status: canonical
---

# Prompt Execution-Surface Routing

## Trigger

Use before generating or validating anything described as a regular AI prompt, GNHF prompt, Good Night Have Fun prompt, runtime objective, launch script, terminal command, or local-agent launcher.

## Required distinction

Route the request to exactly one surface:

1. `regular_ai_prompt` — pasted into an interactive AI chat.
2. `gnhf_runtime_objective` — compact repository objective consumed by GNHF.
3. `gnhf_launch_artifact` — executable shell content that enters the repository, selects the route, applies bounds, and supplies or references the runtime objective.

A literal request for a GNHF prompt means `gnhf_launch_artifact` unless the operator explicitly requests only the inner objective.

## Procedure

1. Classify the requested surface before drafting.
2. Read the target repository rules and the smallest relevant prompt-kit contract.
3. For a launch artifact, resolve and enter the repository before Git, installation, validation, provider, or GNHF logic.
4. Use variable-based user and repository paths.
5. When a provider/model route is requested, use the reviewed AgentSwitchboard provider launcher. Do not present a provider as a native GNHF agent.
6. Include worktree posture, iteration cap, token cap, bounded preflight, positive stop condition, tracked deliverable, validation, and proof ceiling.
7. Run `python -m triage.prompt_execution_surface_contract <artifact>` before accepting the artifact.
8. Reject the artifact rather than silently converting it to another surface.

## Acceptance rules

A GNHF launch artifact is invalid when it is only an ordinary AI prompt, only the inner runtime objective, assumes the terminal is already in the right directory, uses a machine-specific username, runs Git or installation before repository entry, bypasses the reviewed provider route, misstates the adapter, omits bounds, enables push by default, or treats process completion as repository delivery.

## Outputs

- the requested surface only;
- deterministic classification and validation result;
- exact findings when invalid;
- no substitution of a different prompt category.

## Proof ceiling

Static classification and command-shape validation do not prove local shell execution, provider readiness, GNHF mutation, generated commits, Excel opening, or Excel for Web behavior.
