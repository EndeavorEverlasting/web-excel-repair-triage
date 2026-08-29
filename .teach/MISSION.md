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

Lesson 01 VERIFIED. Lesson 02 PRACTICED: learner understands that target-specific names/assumptions make canonical skills less reusable and correctly diagnosed an over-specialized P62 as a prompt defect. Remaining boundary: distinguish a reusable **metric method/family** from the concrete prompt's **selection/binding** of target + metric for one run. `excess tool calls` and `cross-agent interpretation variance` can both be reusable evaluation methods; the prompt chooses which one applies now.

## Emerging product hypothesis

Prompt Kit may benefit from separate **capability**, **skill**, and **implementation** views grounded in actual repository owners. Preserve this as a hypothesis during teaching; do not mutate production UI until later examples test whether these views remain distinct and useful.