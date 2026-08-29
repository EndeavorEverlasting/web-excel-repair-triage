# /teach Mission

This file stores the current teaching objective and frontier. `/teach` sessions update it; bootstrap/setup does not invent learning progress.

## Topic

Prompt Kit ontology: capabilities vs skills vs prompts, and how those primitives should compose in the Prompt Kit viewer/interface.

## Target outcome

The learner can inspect an existing or proposed Prompt Kit artifact and independently determine whether it is a capability, skill, prompt, implementation, or a composition/relationship among them; explain the ownership boundary; predict what should change when implementation/procedure/invocation changes; and use that model to critique or design Prompt Kit navigation without collapsing distinct primitives into synonyms.

## Constraints

- Ground distinctions in current repository authority before generalizing.
- Teach Socratically from first principles; do not front-load a finished taxonomy.
- Keep production Prompt Kit registries/UI unchanged during teaching.
- One atomic invariant at a time; require retrieval and diagnosis before advancing.
- Do not record VERIFIED/MASTERED until learner responses demonstrate it.

## Current frontier

Teaching closeout. Lesson 01 is VERIFIED. Lesson 02 is CLOSED at PRACTICED with its remaining reusable-metric-method vs per-run-selection nuance folded into one final mastery synthesis. The next learner response should answer exactly two synthesis checkpoints. If the response demonstrates ownership and change-impact reasoning across the full model, promote the ontology record to MASTERED and close the teaching lane.

## Implementation handoff after mastery

Preserve these hypotheses for the immediately following implementation sprint:

- Prompt Kit should expose repository-grounded ownership relationships rather than flattening capabilities, skills, prompts, implementations, and evidence into one artifact list.
- Separate capability and skill views appear useful.
- An implementation view/lens may also be useful, but implementation is a heterogeneous relationship: script, launcher, binary, prompt, or other executable/orchestration surface.
- Prompt-specific views should remain available because prompts can be concrete task artifacts even when they are not capability implementations.
- The UI should make it possible to trace from a capability to its reusable skill, concrete implementation/prompt, relevant tests/evals/evidence, and proof ceiling.
- Failed/over-specialized invocation evidence may later support tutorial/log surfaces, but that is separate from minimum viable ontology navigation.

Do not mutate production Prompt Kit UI until the mastery synthesis is complete and the teaching lane is closed.
