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
- In Lesson 02, learner correctly explained that canonical skills should avoid target-specific assumptions because those assumptions damage reuse and force future agents to undo stale context.
- Learner correctly diagnosed an over-specialized P62 as a prompt-implementation defect rather than automatically a skill or capability defect.

## Verified relation

Contract/capability vs implementation vs procedure/reporting is verified at the current lesson level. The learner demonstrated that implementation may change while observable capability behavior remains stable; implementation-specific skill references may then require repair without redefining the capability. The learner also demonstrated that executable runtime truth and agent narrative truth are separate.

## Current remediation

Lesson 02 is not yet VERIFIED. The learner separated target names from reusable skill doctrine, but initially assigned `excess tool calls` to the skill and `cross-agent interpretation variance` to the prompt as though the metric names themselves determine ownership. The stronger rule is: reusable metric **methods/families** may belong in the skill when they generalize across targets; the concrete prompt selects which target and metric/objective matter for the current run.

The learner also proposed preserving failed/over-specialized invocation evidence in a tutorial/log view. Record this as a later product/evidence hypothesis, not part of the smallest prompt repair.

## Emerging product hypothesis

Prompt Kit may benefit from separate capability, skill, and implementation views tied to actual repository-owned skills. This is not yet an implementation decision; revisit after the ontology lessons establish whether those views remain distinct and useful under multiple examples.

## Next frontier

Complete Lesson 02 by separating reusable measurement method from concrete mission selection. Verify that adding a reusable metric family to the skill does not inherently require a new prompt, and that parameterizing an over-specialized prompt can repair the invocation layer without changing the skill or capability when their contracts already support the metric.