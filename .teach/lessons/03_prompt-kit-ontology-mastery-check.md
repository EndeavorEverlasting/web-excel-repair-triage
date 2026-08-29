# Lesson 03 — Prompt Kit ontology mastery synthesis

Status: ACTIVE — final mastery check.

## Purpose

This is not a new content lesson. It is a transfer test across the distinctions already practiced: capability/contract, reusable skill, concrete prompt, heterogeneous implementation, deterministic runtime truth, agent reporting, and evidence/eval surfaces.

If the learner can answer both checkpoints by reasoning from ownership and change impact rather than memorized labels, the ontology can be recorded as MASTERED and used as the basis for the Prompt Kit implementation sprint.

## Implementation hypotheses preserved for handoff

- Prompt Kit should expose relationships among repository-grounded capabilities, skills, prompts/implementations, and evidence rather than flattening them into one list.
- Capability and skill deserve distinct navigation views.
- Implementation may deserve a distinct view or lens, but it is heterogeneous: a capability implementation may be a script, launcher, binary, prompt, or another surface.
- Prompts also deserve direct navigation because a prompt may be a task artifact without being a capability implementation.
- A useful graph should allow traversal from capability → skill → implementation/prompt → tests/evals/evidence → proof ceiling.

## Final learner checkpoints

A. **CONCEPTUAL SYNTHESIS / DESIGN MECHANISM** — A new Prompt Kit screen is showing `skill-evaluation`. The repository says the capability operation is to install executable evals for a target skill and repair valid weaknesses; the reusable `SKILL.md` knows how to build baselines, reproduce weaknesses, measure tool calls/tokens/interpretation consistency, repair safely, and preserve proof ceilings; P62 is the prompt implementation that accepts a concrete target and selected metric for one run. Explain what the **capability view**, **skill view**, **prompt/implementation view**, and **evidence/proof view** should each answer for a user. Then explain why “implementation” may be better modeled as a relationship/lens than as a single uniform artifact type.

B. **CHANGE-IMPACT / EDGE-CASE DIAGNOSTIC** — Tomorrow three things happen independently: (1) a reusable `agent retry-loop rate` measurement method is added to `skill-evaluation/SKILL.md`; (2) no capability operation changes; (3) a user invokes P62 with `Target skill: deployment-safety` and `Primary metric: agent retry-loop rate`. Which layer gained reusable knowledge, which layer performs the per-run binding, which layer can remain unchanged, and does this scenario require a brand-new prompt identity? Explain the smallest sound set of repository changes and why.
