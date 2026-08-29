# Lesson 02 — Reusable skill vs task-specific prompt

Status: CLOSED — PRACTICED; remaining metric-method vs per-run binding nuance is folded into the final ontology mastery check.

## Atomic invariant

A **skill** owns reusable procedure and judgment that should survive across multiple concrete missions. A **prompt** binds a concrete mission, context, scope, constraints, and requested closure to an agent; it may invoke or orchestrate one or more reusable skills. A prompt can also be the registered implementation surface for a capability without becoming identical to the linked skill.

## Repository trace

The canonical `skill-evaluation` capability records a stable operation: install executable correctness, routing, regression, performance, cost, and token-efficiency evals for a target skill and repair valid weaknesses. The same capability separately links `.ai/skills/skill-evaluation/SKILL.md` and declares an implementation of `kind: prompt` with `prompt_id: P62`.

The linked skill defines reusable evaluation procedure: establish the Git floor, define the eval contract before behavior changes, record baselines, add positive/negative/boundary/malformed/forbidden/integration/regression cases, reproduce weaknesses, apply the smallest repair, profile before optimizing, and preserve proof boundaries. Those rules are useful whether the target is FUN NTH export, a Prompt Kit skill, a deployment skill, or another agent procedure.

A concrete prompt has a different job: bind that reusable method to the mission being requested now — for example, which target skill/repository to evaluate, which known failure or efficiency concern matters, what scope is forbidden, what runtime/provider constraints exist, and what completion evidence is required.

Therefore, repeated task-specific facts do not automatically belong in the reusable skill, and reusable evaluation doctrine should not need to be recopied into every task prompt when the agent can route to the canonical skill.

## Learner evidence

The learner correctly explained why target names and target-specific assumptions should not be embedded in a canonical reusable skill: doing so forces later agents to undo stale assumptions and damages reuse. The learner also correctly diagnosed a P62 that hard-codes `fun-nth-artifact-export` and a single primary metric as a prompt-implementation defect rather than automatically a skill or capability defect.

The remaining precision point is narrow: metric names do not determine ownership by themselves. Reusable **metric methods/families** may belong in `skill-evaluation` when they generalize across targets. A concrete prompt selects the target and which supported metric/objective matters for the current run. Thus the skill may know *how* to measure tool-call excess, token use, retries, latency, or cross-agent interpretation variance, while a prompt says *measure this target with this metric now*.

The learner also proposed preserving failed or over-specialized invocation evidence in a tutorial/log view. That is a potentially useful later product/evidence feature, but it is not part of the smallest repair for an over-specialized prompt.

## Emerging product hypothesis

Prompt Kit may benefit from repository-grounded views that expose capability, reusable skill, implementation/prompt, and evidence relationships instead of flattening all agent artifacts into one library. In particular, the learner proposed separate capability, skill, and implementation views tied to actual repository-owned skills. Preserve this for post-teaching implementation critique; do not mutate production UI during the teaching lane.

## Closure

Lesson 02 is closed at PRACTICED rather than VERIFIED so the remaining metric-method vs per-run selection distinction can be tested once, in context, as part of the final mastery synthesis instead of extending the lesson with another micro-remediation cycle.
