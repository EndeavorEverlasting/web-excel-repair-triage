# Bounded Repository Mutation

## Trigger

A prompt execution profile is classified `mutate` or `mixed` and mutation is authorized.

## Required inputs

- Owned scope and forbidden scope.
- Canonical implementation surfaces.
- Validation order and expected artifacts.
- Safe branch/worktree state.

## Outputs

- Tracked bounded changes.
- Focused validation receipts.
- Commit SHA and push/PR evidence when capability exists.

## Procedure

1. Preserve dirty or separately owned work.
2. Modify canonical sources, not generated substitutes.
3. Add focused tests or validators before broad checks.
4. Run `git diff --check`, commit coherently, and push normally.

## Guardrails

- No destructive cleanup, force push, secrets, or scope expansion.
- Do not turn behavior into stubs to pass tests.
- Do not claim skipped validation passed.

## Validation

- Run targeted tests, domain validators, harness validator, generated parity, hygiene, and broader checks when practical.

## Proof ceiling

Committed source plus the validation actually executed.
