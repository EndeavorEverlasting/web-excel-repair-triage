# Validation and Proof Routing

## Trigger

A prompt execution profile is classified `validate`, or a completion claim needs evidence.

## Required inputs

- Target behavior/artifact.
- Available static, unit, integration, CI, browser, live, and production gates.
- Known blockers and proof class.

## Outputs

- Ordered validation receipts.
- Highest achieved proof level.
- Exact skipped gate and follow-up command.

## Procedure

1. Start with focused deterministic gates.
2. Run broader checks after focused gates pass.
3. Use runtime/browser/live proof only when the environment supports it.
4. Keep inspection, static, CI, runtime, and production claims separate.

## Guardrails

- Never upgrade proof by wording.
- Do not weaken a validator merely to turn it green.
- Preserve exact failures and commands.

## Validation

- The validation receipt must name command, result, artifact, and proof ceiling.

## Proof ceiling

The strongest proof lane actually executed.
