# Learning record — Prompt Kit ontology

Status: PRACTICED

## Evidence demonstrated

- Learner identified that skill quality should be evaluated with reproducible measurements rather than prose review alone.
- Learner proposed at least two distinct eval families for a target skill: token/efficiency cost across agents/iterations, and cross-agent interpretation/relevance variance.
- Learner correctly reasoned that evidence should be accumulated across repeated eval cases before repairing weaknesses or issuing a durable evidence claim.
- Learner recognized that changing task instructions alone may be insufficient when stronger repository contracts constrain behavior.

## Weak relation / needs review

The learner currently groups executable behavior under “the harness.” The FUN NTH example shows a more precise ownership split: skill prose invokes a CLI; the CLI delegates to deterministic implementation; tests/contracts own invariants. A change to executable mechanism does not automatically imply the reusable skill procedure or task prompt must change if their observable contract remains stable.

## Next frontier

Distinguish contract/capability, implementation, reusable skill procedure, and task-specific prompt by asking which surfaces must change under a mechanism-preserving refactor versus a behavior-contract change.
