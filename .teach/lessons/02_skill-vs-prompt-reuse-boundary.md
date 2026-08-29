# Lesson 02 — Reusable skill vs task-specific prompt

Status: ACTIVE — awaiting learner checkpoints.

## Atomic invariant

A **skill** owns reusable procedure and judgment that should survive across multiple concrete missions. A **prompt** binds a concrete mission, context, scope, constraints, and requested closure to an agent; it may invoke or orchestrate one or more reusable skills. A prompt can also be the registered implementation surface for a capability without becoming identical to the linked skill.

## Repository trace

The canonical `skill-evaluation` capability records a stable operation: install executable correctness, routing, regression, performance, cost, and token-efficiency evals for a target skill and repair valid weaknesses. The same capability separately links `.ai/skills/skill-evaluation/SKILL.md` and declares an implementation of `kind: prompt` with `prompt_id: P62`.

The linked skill defines reusable evaluation procedure: establish the Git floor, define the eval contract before behavior changes, record baselines, add positive/negative/boundary/malformed/forbidden/integration/regression cases, reproduce weaknesses, apply the smallest repair, profile before optimizing, and preserve proof boundaries. Those rules are useful whether the target is FUN NTH export, a Prompt Kit skill, a deployment skill, or another agent procedure.

A concrete prompt has a different job: bind that reusable method to the mission being requested now — for example, which target skill/repository to evaluate, which known failure or efficiency concern matters, what scope is forbidden, what runtime/provider constraints exist, and what completion evidence is required.

Therefore, repeated task-specific facts do not automatically belong in the reusable skill, and reusable evaluation doctrine should not need to be recopied into every task prompt when the agent can route to the canonical skill.

## Learner checkpoints

A. **CONCEPTUAL MECHANISM / TRADE-OFF** — You want to evaluate two different skills: `fun-nth-artifact-export` for cross-agent interpretation variance, and a deployment skill for excess tool calls. Both evaluations should use the same rule that weaknesses must be reproduced before repair and that token optimization cannot weaken correctness. Which information belongs in the reusable `skill-evaluation` skill, and which information belongs in each concrete prompt? Explain why moving the target names and one-off objectives into the canonical skill would make the architecture worse.

B. **CODE / DATA DIAGNOSTIC EDGE CASE** — The capability registry still points `skill-evaluation` to the same reusable `SKILL.md`, but P62 is edited so its copied task text hard-codes `Target skill: fun-nth-artifact-export` and `Metric: cross-agent interpretation variance`. Nothing in `SKILL.md` is changed. Has the reusable skill become FUN-specific, has the capability necessarily changed, or has the prompt implementation become over-specialized? Identify the stale/defective layer and the smallest sound repair.
