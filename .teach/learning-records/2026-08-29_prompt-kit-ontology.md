# Learning record — Prompt Kit ontology

Status: MASTERED

## Evidence demonstrated

- Learner identified that skill quality should be evaluated with reproducible measurements rather than prose review alone.
- Learner proposed distinct eval families including token/efficiency cost and cross-agent interpretation/relevance variance.
- Learner correctly reasoned that evidence should accumulate across repeated eval cases before repairing weaknesses or issuing durable evidence claims.
- **Lesson 01 VERIFIED:** learner distinguishes a stable capability/contract from a replaceable implementation mechanism.
- Learner correctly identified that a Python-specific skill instruction becomes stale after a behavior-preserving Rust rewrite even though the capability contract can remain unchanged.
- Learner correctly separated deterministic CLI/runtime rejection from a later agentic false-success report.
- **Lesson 02 VERIFIED through transfer:** learner distinguishes reusable skill knowledge from concrete prompt/run binding and understands why target-specific assumptions damage reuse.
- Learner correctly diagnosed an over-specialized P62 as a prompt-implementation defect rather than automatically a skill or capability defect.
- Learner independently synthesized the ontology into a repository-grounded Prompt Kit navigation model spanning capability, skill, prompt/invocation, heterogeneous implementation, and evidence/proof.
- Learner correctly reasoned that adding reusable measurement knowledge can leave a stable capability unchanged and does not inherently require a new prompt identity.

## Mastered relations

The learner can now reason about:

- **Capability/contract:** the stable operation, inputs/outputs, routing, and proof boundary consumers may rely upon.
- **Implementation:** the heterogeneous mechanism or relationship that realizes/orchestrates an operation; it may be script, launcher, binary, prompt, or another surface.
- **Skill:** reusable procedure, judgment, and metric methods that should survive across multiple missions.
- **Prompt:** a reusable or task-facing instruction artifact that can bind concrete mission context and may itself serve as a capability implementation surface.
- **Invocation/run:** one concrete execution of a prompt/implementation with selected target, metric, constraints, and context.
- **Evidence/proof:** observed tests, evals, logs/results, and proof ceiling showing what the system actually demonstrated rather than merely claimed.

## Precision notes

Two terminology/implementation refinements remain recorded:

1. A prompt invocation creates a run/instance; the invocation is not automatically identical to the implementation artifact.
2. Adding a reusable metric method to a canonical skill should be accompanied by focused executable eval/test evidence when the method makes an executable quality claim. Editing Markdown alone is not sufficient proof.

These refinements do not undermine the demonstrated ownership model.

## Product handoff

Use the mastered model as the design basis for Prompt Kit implementation:

- expose repository-grounded ownership relationships rather than flattening all artifacts into one library;
- support distinct capability and skill navigation;
- preserve direct prompt navigation;
- treat implementation as a heterogeneous relationship/lens;
- trace capability → skill → implementation/prompt → invocation/run → tests/evals/evidence → proof ceiling;
- consider failed runs, critiques, favorites, and invocation metadata as a later evidence/history layer, separate from minimum viable ontology navigation.

## Closure

Prompt Kit ontology: MASTERED. Teaching mode closed; production implementation may proceed from this record.