# Learning record — Prompt Kit ontology

Status: PRACTICED

## Evidence demonstrated

- Learner identified that skill quality should be evaluated with reproducible measurements rather than prose review alone.
- Learner proposed at least two distinct eval families for a target skill: token/efficiency cost across agents/iterations, and cross-agent interpretation/relevance variance.
- Learner correctly reasoned that evidence should be accumulated across repeated eval cases before repairing weaknesses or issuing a durable evidence claim.
- Learner recognized that changing task instructions alone may be insufficient when stronger repository contracts constrain behavior.
- **Lesson 01 VERIFIED:** learner distinguishes a stable capability/contract from a replaceable implementation mechanism.
- Learner correctly identified that a Python-specific skill instruction becomes stale after a behavior-preserving Rust rewrite even though the capability itself can remain unchanged.
- Learner correctly separated deterministic CLI/runtime rejection from a later agentic false-success report.

## Verified relation

Contract/capability vs implementation vs procedure/reporting is verified at the current lesson level. The learner demonstrated that implementation may change while observable capability behavior remains stable; implementation-specific skill references may then require repair without redefining the capability. The learner also demonstrated that executable runtime truth and agent narrative truth are separate.

## Precision note

The learner briefly said that the Rust rewrite "preserves implementation." Corrected formulation: the rewrite **replaces the implementation while preserving the observable contract**. This was a wording issue rather than a remaining ownership error.

## Next frontier

Distinguish **reusable skill procedure** from **task-specific prompt invocation/orchestration**. Use the repository's `skill-evaluation` case, where the capability links a reusable `.ai/skills/skill-evaluation/SKILL.md` while its registered implementation kind is Prompt Kit prompt `P62`. Determine what should remain reusable across missions versus what belongs in the concrete request handed to an agent.
