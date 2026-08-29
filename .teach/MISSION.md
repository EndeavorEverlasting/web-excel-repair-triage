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

Lesson 01 VERIFIED: learner distinguishes stable capability/contract from replaceable implementation, identifies implementation-specific stale skill instructions, and separates deterministic runtime truth from agent reporting. Current Lesson 02 frontier: distinguish **reusable skill procedure/judgment** from **task-specific prompt invocation/orchestration**. Test against the repository's `skill-evaluation` capability, its linked `.ai/skills/skill-evaluation/SKILL.md`, and registered prompt implementation `P62`.
