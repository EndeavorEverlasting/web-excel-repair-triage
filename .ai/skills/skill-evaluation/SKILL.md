# Skill Evaluation

## Trigger

Use this skill when a target skill exists but its correctness, routing boundary, failure behavior, regression safety, latency, cost, tool-call behavior, context size, or token efficiency lacks executable evidence, or when a known weakness needs a test-driven repair.

Do not use it for cosmetic skill wording or when the target skill and owning repository are unknown.

## Required inputs

- Target skill and version or commit.
- Trigger, capability, workflow, schema, and artifact contracts.
- Representative positive, negative, near-miss, boundary, malformed-input, forbidden-condition, and historical-failure examples.
- Existing unit, integration, and regression tests.
- Baseline traces for latency, tool calls, context size, retries, cost, and tokens when available.
- Proof vocabulary and provider/runtime constraints.

## Outputs

- A weakness inventory covering bugs, inefficiencies, routing mistakes, brittle assumptions, and missing functionality.
- Versioned eval cases and fixtures.
- A reproducible runner with deterministic assertions and explicit scored rubrics where judgment is unavoidable.
- Unit and integration validation.
- Machine-readable results and a finding-to-repair ledger.
- Before-and-after correctness and efficiency evidence.
- Directly related skill, trigger, capability, workflow, or helper repairs.

## Procedure

1. Establish the Git floor and isolate the writing lane.
2. Define the eval contract before changing behavior: case ID, purpose, input, expected route, expected artifacts/properties, forbidden outcomes, scoring rule, thresholds, metrics, and proof ceiling.
3. Record a reproducible baseline for correctness, routing, latency, tool calls, context size, retries, cost, and prompt/completion/cached/total tokens when available.
4. Add positive activation, negative and near-miss routing, boundary, malformed-input, missing-precondition, forbidden-condition, safe-refusal, integration, and historical-regression cases.
5. Validate deterministic helpers, schemas, manifests, triggers, and capabilities with unit tests.
6. Validate the skill, trigger, capability, workflow, tool interaction, and output artifact together with integration tests.
7. Reproduce each valid weakness with a failing case before repair when practical.
8. Apply the smallest sound repair and rerun focused plus regression suites. Do not weaken the rubric.
9. Profile actual traces before optimizing. Reduce excess context, repeated instructions, duplicate tool calls, unnecessary turns, repeated repository scans, and deterministic behavior hidden in prose through sound factoring.
10. Accept a performance, cost, or token improvement only when correctness, safety, routing, and artifact gates remain green and before/after evidence is recorded.
11. Keep offline deterministic CI separate from optional provider-backed or live-runtime lanes with honest credential, cost, and proof blockers.
12. Commit the eval harness and directly related repairs, then provide an exact command that runs the eval and opens or prints the canonical result artifact.

## Guardrails

- Do not tune only for a single happy-path example.
- Do not hide benchmark cases from repository owners or fabricate provider metadata.
- Do not confuse shorter prompts with lower total token use.
- Do not optimize tokens by deleting safety, validation, artifact, or proof requirements.
- Do not claim model or live-runtime quality from static checks.
- Do not modify unrelated product code, provider credentials, or production targets.

## Validation

At minimum require:

- versioned positive, negative, boundary, malformed-input, forbidden-condition, integration, and regression cases;
- unit tests for deterministic helpers and contracts;
- integration tests across routing and artifact production;
- machine-readable case results and aggregate verdict;
- baseline and after metrics for every claimed efficiency improvement;
- no correctness, safety, or routing regression;
- focused CI plus `git diff --check`;
- commit and PR evidence.

## Proof ceiling

The achieved proof equals the strongest executed eval lane. Offline deterministic tests do not prove provider judgment; provider-backed evals do not prove protected target runtime behavior; synthetic runtime tests do not prove production acceptance.
