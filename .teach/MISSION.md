# /teach Mission

This file stores the current teaching objective and frontier. `/teach` sessions update it; bootstrap/setup does not invent learning progress.

## Topic

Prompt Kit ontology: capabilities vs skills vs prompts, and how those primitives should compose in the Prompt Kit viewer/interface.

## Target outcome

The learner can inspect an existing or proposed Prompt Kit artifact and independently determine whether it is a capability, skill, prompt, or a composition of them; explain the ownership boundary; predict what should change when implementation/procedure/invocation changes; and use that model to critique or design Prompt Kit navigation without collapsing distinct primitives into synonyms.

## Constraints

- Ground distinctions in current repository authority before generalizing.
- Teach Socratically from first principles; do not front-load a finished taxonomy.
- Keep production Prompt Kit registries/UI unchanged during teaching.
- One atomic invariant at a time; require retrieval and diagnosis before advancing.
- Do not record VERIFIED/MASTERED until learner responses demonstrate it.

## Current frontier

PRACTICED diagnostic: learner can propose measurable skill-evaluation cases and understands that evidence should precede repair. Current weak relation: separating the harness/capability contract from the executable implementation and from the skill's reusable procedure. Next atomic invariant: **contract describes what operation must remain true; implementation performs it; skill tells the agent how to conduct the work around those deterministic owners.** Test against `fun-nth-artifact-export`.
