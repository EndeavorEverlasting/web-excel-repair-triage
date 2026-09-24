# 1. Evals — turn quality into an executable contract

**Prompt:** P67 Repository Eval Framework Builder

## Goal
Build a small eval suite around the repository's real user tasks before adding more agent complexity.

## Walkthrough
1. Pick one high-value task and write down what a correct result means.
2. Collect one normal case, one edge case, one known regression, and one malformed/failure case.
3. Use deterministic assertions first: schema, exact fields, files, commands, tool choice, or invariants.
4. Add model/judge scoring only for criteria such as usefulness or semantic completeness that deterministic code cannot represent well.
5. Emit a machine-readable result and wire the focused suite into CI.
6. Deliberately run a known-bad fixture and prove the gate fails.

## What to avoid
- counting unit tests as proof of model quality;
- spending LLM tokens on exact checks code can perform;
- changing the rubric and the candidate in the same unreviewed step;
- hiding skipped judge/human evidence as a pass.

## Completion gate
A representative eval suite fails on a known bad case and passes on the intended behavior, with the proof ceiling stated explicitly.
