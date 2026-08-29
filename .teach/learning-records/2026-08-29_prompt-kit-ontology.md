# Learning record — Prompt Kit ontology

Status: PRACTICED

## Evidence demonstrated

- Learner identified that skill quality should be evaluated with reproducible measurements rather than prose review alone.
- Learner proposed at least two distinct eval families for a target skill: token/efficiency cost across agents/iterations, and cross-agent interpretation/relevance variance.
- Learner correctly reasoned that evidence should be accumulated across repeated eval cases before repairing weaknesses or issuing a durable evidence claim.
- Learner recognized that changing task instructions alone may be insufficient when stronger repository contracts constrain behavior.
- On Lesson 01 checkpoint A, learner correctly identified that replacing a Python implementation with Rust changes the implementation layer and may require implementation-specific validation references to be updated.
- Learner is beginning to distinguish a stable observable contract from its replaceable implementation mechanism.

## Weak relation / needs review

Two ownership distinctions remain unverified:

1. The learner still tends to say “the harness must change” when only implementation-specific references may need repair. A mechanism-preserving language rewrite does not by itself invalidate the capability/contract.
2. On the contradictory-skill edge case, the learner predicted later agent or harness detection rather than immediate runtime rejection. The exporter itself rejects `fixture + protected_runtime` before a valid result is emitted. Runtime enforcement and later harness validation must be kept distinct.

## Next frontier

Complete Lesson 01 by separating (a) a stale skill instruction from an unchanged capability contract and (b) deterministic runtime success/failure from an agent's later narrative claim about that result. Do not use “harness” as an umbrella owner when a concrete implementation, test, skill, prompt, or contract can be named.
