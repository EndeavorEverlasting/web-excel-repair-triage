# Repository Inspection

## Trigger

A prompt execution profile is classified `inspect` or `plan`.

## Required inputs

- Prompt execution profile.
- Repository state, contracts, recent commits, PRs, validators, and artifacts.
- Owned and forbidden scope.

## Outputs

- A bounded evidence inventory.
- A factual plan or route with explicit unknowns and proof ceiling.

## Procedure

1. Read only the smallest relevant repository surfaces.
2. Prefer canonical evidence over remembered context.
3. Classify gaps, collisions, dependencies, and safe next action.
4. Stop before mutation unless a mutation capability is selected.

## Guardrails

- Do not convert an authorized implementation request into plan-only output.
- Do not infer current Git or PR state without evidence.
- Do not mutate protected inputs.

## Validation

- Verify cited paths and commands exist.
- Run the domain audit for deterministic profile/routing coverage.

## Proof ceiling

Inspection and planning proof only.
