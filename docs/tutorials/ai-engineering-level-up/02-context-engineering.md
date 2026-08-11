# 2. Context engineering — design the information system around the model

**Prompt:** P68 Context Engineering System Refactorer

## Goal
Make every piece of model context intentional: prompts, tool definitions, retrieved chunks, memory, history, repo maps, skills, and runtime state.

## Walkthrough
1. Inventory every context source and record owner, trigger, size, freshness, and precedence.
2. Measure the baseline context bytes/tokens and representative task success.
3. Identify always-loaded material that is lane-specific, duplicated, stale, or deterministic.
4. Demand-load skills and tools, bound history/retrieval, and move deterministic facts into registries/maps/validators.
5. Add tests proving required context remains present and stale/irrelevant context is excluded.
6. Compare before/after context load and task quality.

## What to avoid
- pruning security or precedence rules because they consume tokens;
- optimizing token count while silently reducing correctness;
- letting multiple files claim the same authority;
- assuming a larger context window removes the need for routing.

## Completion gate
Context selection is measured and regression-tested, and unnecessary always-loaded context is reduced or better routed without representative quality loss.
