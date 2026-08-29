# Learning record — Prompt Kit ontology

Status: PRACTICED — final mastery synthesis pending.

## Evidence demonstrated

- Learner identified that skill quality should be evaluated with reproducible measurements rather than prose review alone.
- Learner proposed distinct eval families including token/efficiency cost and cross-agent interpretation/relevance variance.
- Learner correctly reasoned that evidence should accumulate across repeated eval cases before repairing weaknesses or issuing durable evidence claims.
- **Lesson 01 VERIFIED:** learner distinguishes a stable capability/contract from a replaceable implementation mechanism.
- Learner correctly identified that a Python-specific skill instruction becomes stale after a behavior-preserving Rust rewrite even though the capability contract can remain unchanged.
- Learner correctly separated deterministic CLI/runtime rejection from a later agentic false-success report.
- In Lesson 02, learner correctly explained that canonical skills should avoid target-specific assumptions because those assumptions damage reuse and force future agents to undo stale context.
- Learner correctly diagnosed an over-specialized P62 as a prompt-implementation defect rather than automatically a skill or capability defect.
- Learner independently articulated the product utility of the distinctions and proposed repository-grounded Prompt Kit views for capability, skill, and implementation relationships.

## Verified relation

Contract/capability vs implementation vs procedure/reporting is VERIFIED at the current lesson level. The learner demonstrated that implementation may change while observable capability behavior remains stable; implementation-specific skill references may then require repair without redefining the capability. The learner also demonstrated that executable runtime truth and agent narrative truth are separate.

## Practiced relation

Reusable skill vs concrete prompt is PRACTICED. The learner understands that target-specific literals and assumptions belong in concrete invocation context rather than a reusable skill and that an over-specialized prompt can be repaired without redefining a stable capability or reusable skill.

The final precision point remains: reusable metric **methods/families** may belong in the skill when they generalize; the prompt selects/binds the target and metric/objective for one run. Metric names themselves do not determine ownership.

## Emerging implementation hypothesis

Prompt Kit may benefit from repository-grounded views/lenses that expose the graph among capability, reusable skill, concrete implementation or prompt, and evidence instead of flattening those artifacts into one library. A dedicated implementation view may be useful, but implementation should be tested as a relationship/lens because an implementation can be a script, launcher, binary, or prompt rather than one uniform peer primitive.

A later product/evidence idea is to preserve failed or over-specialized invocation evidence and expose useful logs/tutorial context. This remains separate from smallest-sound repairs.

## Final mastery frontier

One final synthesis must show that the learner can classify ownership and change impact without relying on memorized labels, including the remaining reusable-metric-method vs per-run-selection distinction. If demonstrated, promote the overall ontology record to MASTERED and use the resulting ownership model as the design basis for the Prompt Kit implementation sprint.
