# Prompt Kit Isolated Writer + Convergence Contract

## Decision
Prompt Kit uses a shared conditional contract rather than a new prompt identity. The invariant is compiled into every effective prompt but activates only for version-controlled repository mutation or concurrent mutating writers.

## External precedent
This design was informed by Michael Shimeles' public `michaelshimeles/skills` repository, especially `new-feature/SKILL.md` and `AGENTS.md`: scope-check open pull requests before writing, start from a fresh default-branch floor, give each task its own worktree/branch, install dependencies in that isolated directory, and retain the lane until its pull request is resolved.

Sources:
- https://github.com/michaelshimeles/skills/blob/main/new-feature/SKILL.md
- https://github.com/michaelshimeles/skills/blob/main/AGENTS.md

No external source code is copied. Prompt Kit adapts the mechanics to its existing governance and mainline-convergence contracts.

## Prompt Kit adaptation
Isolation covers filesystem/dependency state as well as Git refs. Shared ports, databases, services, caches, lockfiles, environment files, credentials, and generated outputs remain collision surfaces unless explicitly separated.

Finishing a lane is not permission to destroy siblings. Each writer commits only owned scope; unfinished lanes remain intact. Completed lanes converge in dependency order into a dedicated local convergence worktree/branch based on refreshed default, and combined validators/build/tests run against that integrated candidate before the normal local-default and remote-default gates advance.

## Required dependency floor
A fresh default branch is necessary but not sufficient when a writer depends on a specific previously integrated slice. Before creating or advancing that lane, prove the required SHA is still an ancestor of the refreshed default with `git merge-base --is-ancestor <required-sha> <refreshed-default>`, then prove the expected contract/content is still materially present with its owning validator. A revert can preserve ancestry while removing the behavior that later work depends on, so either failed check blocks mutation or integration until the dependency is reconciled and freshly proven. Repeat this proof before convergence whenever the default floor or another proof-relevant dependency moves.

## Environment modes
### Local Git available
Prefer one worktree plus one branch per independent writer and a separate convergence worktree/branch. Do not use the shared default checkout as a scratch integration surface while sibling writers are active.

### Isolated workspace/clone fallback
If worktrees are unavailable, use an environment-provided isolated workspace pinned to the same refreshed base and preserve the same ownership, collision, convergence, and cleanup semantics.

### Provider-only / remote execution
Use one isolated remote branch/PR per writer. Exact-head provider CI can prove the remote candidate; local convergence remains unavailable/unproven and must not be relabeled as local-main/workstation proof. If an automation-authored convergence commit cannot trigger the repository's normal validation suite, use a separately authorized exact-head update or validation gate; changing event provenance must never weaken the proof requirements.

## Cleanup gate
Cleanup happens after integration, never because another lane finished first. Before removing a lane, prove no unique unmerged commit, untracked artifact, evidence file, or operator-owned work would disappear. Prune stale metadata and delete task branches only after that preservation gate.

## Why shared policy, not a new prompt
P07, P13, P50, repository bootstrap/continuity prompts, harness workflows, and future mutation owners all need the same writer-safety invariant. A standalone prompt would require callers to remember another routing hop. The global actionability policy is already compiled into every effective Prompt Kit prompt, making it the lowest-duplication enforcement point.
