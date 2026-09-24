# 5. Adaptability — isolate churn behind stable contracts

**Prompt:** P71 AI Toolchain Adaptability Review + Upgrade

## Goal
Keep fast-changing models, providers, SDKs, agent frameworks, and tool protocols replaceable without recurring repository-wide rewrites.

## Walkthrough
1. Inventory volatile assumptions and rank them by critical-path impact and observed churn.
2. Identify stable contracts: task inputs/outputs, artifact schemas, tool semantics, errors, proof levels, and safety boundaries.
3. Add a small adapter or registry only where direct coupling is already costly.
4. Run the same representative evals against current and candidate implementations.
5. Upgrade when evidence shows a real gap, deprecation/security need, or measurable benefit.
6. Preserve pinning, rollback/coexistence, and migration notes.

## What to avoid
- framework abstraction with no proven churn problem;
- unbounded "keep dependencies current" work;
- adopting a new model/tool because it is fashionable rather than useful;
- deleting the known-good path before compatibility proof exists.

## Completion gate
The highest-risk volatile dependency is behind a tested stable contract, or the repo records an evidence-backed deferral with an explicit rollback/migration path.
