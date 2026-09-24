# Lesson 02 — Reusable skill vs task-specific prompt

Status: VERIFIED — completed through final synthesis transfer.

## Atomic invariant

A **skill** owns reusable procedure and judgment that should survive across multiple concrete missions. A **prompt** binds a concrete mission, context, scope, constraints, and requested closure to an agent; it may invoke or orchestrate one or more reusable skills. A prompt can also be the registered implementation surface for a capability without becoming identical to the linked skill.

## Repository trace

The canonical `skill-evaluation` capability records a stable operation: install executable correctness, routing, regression, performance, cost, and token-efficiency evals for a target skill and repair valid weaknesses. The same capability separately links `.ai/skills/skill-evaluation/SKILL.md` and declares an implementation of `kind: prompt` with `prompt_id: P62`.

The linked skill defines reusable evaluation procedure: establish the Git floor, define the eval contract before behavior changes, record baselines, add positive/negative/boundary/malformed/forbidden/integration/regression cases, reproduce weaknesses, apply the smallest repair, profile before optimizing, and preserve proof boundaries. Those rules are useful whether the target is FUN NTH export, a Prompt Kit skill, a deployment skill, or another agent procedure.

A concrete prompt has a different job: bind that reusable method to the mission being requested now — for example, which target skill/repository to evaluate, which known failure or efficiency concern matters, what scope is forbidden, what runtime/provider constraints exist, and what completion evidence is required.

Therefore, repeated task-specific facts do not automatically belong in the reusable skill, and reusable evaluation doctrine should not need to be recopied into every task prompt when the agent can route to the canonical skill.

## Learner evidence

The learner correctly explained why target names and target-specific assumptions should not be embedded in a canonical reusable skill: doing so forces later agents to undo stale assumptions and damages reuse. The learner correctly diagnosed a P62 that hard-codes `fun-nth-artifact-export` and a single primary metric as a prompt-implementation defect rather than automatically a skill or capability defect.

In the final synthesis, the learner correctly placed reusable measurement knowledge in the skill layer and concrete target/run binding in the invocation/implementation context. The learner also independently applied the model to Prompt Kit information architecture, which demonstrates transfer beyond memorized labels.

## Precision corrections retained

Two refinements remain important but do not invalidate the demonstrated ownership model:

1. Reusable metric **methods/families** may belong in `skill-evaluation`; the concrete prompt selects which supported metric/objective matters for a particular run. Metric names do not determine ownership by themselves.
2. Sending a prompt to an agent creates a concrete invocation/run. That run is not automatically identical to the capability's implementation artifact, even when the prompt itself is the registered implementation surface.

The learner also proposed preserving failed or over-specialized invocation evidence in a tutorial/log view. That is a potentially useful later product/evidence feature, not part of the smallest repair for an over-specialized prompt.

## Closure

VERIFIED through final transfer: the learner can distinguish reusable skill knowledge from concrete prompt/run binding and can use that distinction to reason about design and change impact.