# /teach Mission

This file stores the current teaching objective and frontier. `/teach` sessions update it; bootstrap/setup does not invent learning progress.

## Topic

Prompt Kit ontology: capabilities vs skills vs prompts, implementations, invocations, and evidence/proof relationships.

## Target outcome

The learner can inspect an existing or proposed Prompt Kit artifact and independently determine whether it is a capability, skill, prompt, implementation, invocation/run, evidence surface, or a composition/relationship among them; explain the ownership boundary; predict what should change when implementation/procedure/invocation changes; and use that model to critique or design Prompt Kit navigation without collapsing distinct primitives into synonyms.

## Status

MASTERED — teaching lane closed on 2026-08-29.

## Demonstrated mastery

- Stable capability/contract vs replaceable implementation.
- Reusable skill procedure/judgment vs concrete prompt/run binding.
- Deterministic runtime truth vs agent narrative/reporting.
- Reusable metric method vs per-run target/metric selection.
- Heterogeneous implementation as a relationship/lens rather than one uniform peer artifact.
- Evidence/proof as observed support for claims, distinct from the capability itself.
- Product-level transfer: learner independently proposed repository-grounded navigation across capability, skill, implementation/prompt, and evidence surfaces.

## Precision notes retained

- A prompt invocation creates a run/instance; it is not automatically identical to the implementation artifact.
- New reusable metric methods that make executable quality claims require focused eval/test proof in addition to skill prose.

## Implementation handoff

Use these hypotheses for the immediately following production sprint:

- Prompt Kit should expose repository-grounded ownership relationships rather than flattening capabilities, skills, prompts, implementations, invocations, and evidence into one artifact list.
- Separate capability and skill views are justified by distinct user questions.
- Prompt-specific navigation should remain available because prompts can be task artifacts without being capability implementations.
- Implementation should be modeled as a heterogeneous relationship/lens: script, launcher, binary, prompt, or other executable/orchestration surface.
- The UI should make it possible to trace capability → reusable skill → concrete implementation/prompt → invocation/run → relevant tests/evals/evidence → proof ceiling.
- Evidence/history may later include failed runs, critiques, favorites, and invocation metadata, but this should remain separate from minimum viable ontology navigation.

Production Prompt Kit mutation is now permitted under a fresh implementation lane with refreshed repository/provider truth.