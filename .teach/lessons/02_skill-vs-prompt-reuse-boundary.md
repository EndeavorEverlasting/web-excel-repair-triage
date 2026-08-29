# Lesson 02 — Reusable skill vs task-specific prompt

Status: ACTIVE — learner has the reuse principle; metric-selection boundary needs one remediation pass.

## Atomic invariant

A **skill** owns reusable procedure and judgment that should survive across multiple concrete missions. A **prompt** binds a concrete mission, context, scope, constraints, and requested closure to an agent; it may invoke or orchestrate one or more reusable skills. A prompt can also be the registered implementation surface for a capability without becoming identical to the linked skill.

## Repository trace

The canonical `skill-evaluation` capability records a stable operation: install executable correctness, routing, regression, performance, cost, and token-efficiency evals for a target skill and repair valid weaknesses. The same capability separately links `.ai/skills/skill-evaluation/SKILL.md` and declares an implementation of `kind: prompt` with `prompt_id: P62`.

The linked skill defines reusable evaluation procedure: establish the Git floor, define the eval contract before behavior changes, record baselines, add positive/negative/boundary/malformed/forbidden/integration/regression cases, reproduce weaknesses, apply the smallest repair, profile before optimizing, and preserve proof boundaries. Those rules are useful whether the target is FUN NTH export, a Prompt Kit skill, a deployment skill, or another agent procedure.

A concrete prompt has a different job: bind that reusable method to the mission being requested now — for example, which target skill/repository to evaluate, which known failure or efficiency concern matters, what scope is forbidden, what runtime/provider constraints exist, and what completion evidence is required.

Therefore, repeated task-specific facts do not automatically belong in the reusable skill, and reusable evaluation doctrine should not need to be recopied into every task prompt when the agent can route to the canonical skill.

## Learner checkpoint attempt 1

### A — reuse boundary

The learner correctly explained why target names and target-specific assumptions should not be embedded in the canonical skill: doing so makes future agents undo stale assumptions and damages reuse. The learner also correctly identified cross-agent interpretation variance as something a concrete evaluation mission may select.

Remediation point: `excess tool calls` is not inherently skill-owned while `cross-agent interpretation variance` is prompt-owned. Both can exist as reusable **metric families or measurement procedures** inside `skill-evaluation` when their method generalizes across targets. The concrete prompt should select the target and the metric/objective to emphasize for this run. In other words, the reusable skill may know *how* to measure tool-call excess and interpretation variance; the prompt says *measure this target with this metric now*.

### B — over-specialized P62

The learner correctly identified the prompt implementation as defective when P62 hard-codes one target and one primary metric while the capability and reusable skill remain generic. The smallest sound repair is to remove or parameterize those target-specific literals so P62 again accepts the concrete target/metric from invocation context while preserving the reusable skill and capability contract.

The learner proposed a further idea: preserve evidence from the failed or over-specialized invocation and surface it in a tutorial/log view. This may be useful later, but it is not part of the smallest repair and remains a product/evidence hypothesis rather than a Lesson 02 requirement.

## Emerging product hypothesis

The learner proposed that Prompt Kit may benefit from separate capability, skill, and implementation views tied to actual repository-owned skills. Preserve this as a design hypothesis for later critique after the ontology is better verified; do not mutate production UI during teaching.

## Learner checkpoints — remediation

A. **CONCEPTUAL MECHANISM / TRADE-OFF** — `skill-evaluation` contains reusable procedures for measuring tool calls, latency, token use, and interpretation consistency. A concrete request says: “Evaluate deployment-safety for excess tool calls.” Which part is the reusable *method* and which part is the concrete *selection/binding*? Then explain whether adding a new reusable metric family such as “cross-agent interpretation variance” necessarily requires a new prompt.

B. **CODE / DATA DIAGNOSTIC EDGE CASE** — P62 is repaired from hard-coded values to parameters: `Target skill: <target skill>` and `Primary metric: <metric selected for this run>`. The linked `SKILL.md` already explains how to measure both supported metric families, and the capability operation remains unchanged. Which repository layers changed in this repair, and which explicitly did **not** need to change?