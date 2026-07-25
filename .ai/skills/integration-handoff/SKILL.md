# Integration and Handoff

## Trigger

A prompt execution profile is classified `integrate`, or work must move across branch/PR/chat boundaries.

## Required inputs

- Branch, commit, PR, review, and dependency state.
- Unique-work comparison.
- Validation receipts and artifact registry.

## Outputs

- Preserved/integrated work.
- Resolved review state when authorized.
- Executable handoff or exact next command.

## Procedure

1. Compare branches and preserve unique commits before closure.
2. Integrate in dependency order without force.
3. Verify exact head and required checks.
4. Name owner, dependency, artifact, gate, and next executable action.

## Guardrails

- Do not close/delete unique work before preservation proof.
- Do not use status-only output as the sole next action.
- Do not claim merge or deployment without mutation evidence.

## Validation

- Verify exact commit/PR state and rerun the owning validator after integration.

## Proof ceiling

Observed Git/PR mutations and executed integration validation.
