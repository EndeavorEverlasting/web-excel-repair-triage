# Repository Agent Governance Contract

This root file is the canonical governance contract and single source of truth for how agents operate in this repository. Operational harness components, shared planning directories, prompts, skills, workflows, and generic defaults implement this contract; they do not supersede it.

## Required Reading

Before proposing or changing work, inspect:

1. applicable platform, security, legal, and explicit repository-owner instructions;
2. `HARNESS.md` — this governance contract;
3. `AGENTS.md` — repository and product-specific execution rules;
4. the selected task prompt, current plans and handoffs, tests, validators, and recent Git history.

## Agent Operating Principles

- **Evidence before action.** Inspect current repository, Git, PR, contract, test, validator, and artifact evidence before deciding or mutating.
- **Floor before furniture.** Establish a safe repository floor and repair shared contract failures before dependent feature work.
- **Bounded sprints with declared scope.** Every writing sprint declares its mission, ownership, exclusions, artifacts, validation, and proof ceiling.
- **One writer per branch.** Each active writing lane owns one branch or isolated worktree; agents do not share uncommitted state.
- **Reuse before replacing.** Reuse healthy contracts, helpers, generators, validators, schemas, and conventions before inventing alternatives.
- **No completion without proof.** Completion requires actual checks, artifacts, and Git or GitHub evidence appropriate to the requested action.
- **Preservation before cleanup.** Preserve useful work and evidence before any destructive cleanup or replacement.
- **Capability is not authority.** A tool capability may be used only when available, verified, authorized, and permitted by repository policy.

## Instruction Precedence

When instructions conflict, apply this order from highest to lowest:

1. Platform, security, legal, and explicit repository-owner instructions.
2. This governance contract.
3. Task-specific prompts and execution contracts.
4. Generic defaults.

Task-specific rules may refine the sprint and override generic closeout behavior, but they may not weaken this governance contract. Record unresolved conflicts as blockers rather than silently choosing the more convenient instruction.

## Mandatory Sprint Declaration

Every writing sprint must state before mutation:

- repository and branch or worktree;
- PR or sprint identity;
- lane and mission;
- owned scope and forbidden scope;
- dependencies and collision risks;
- expected tracked artifacts;
- validation commands and required validation order when specified;
- proof ceiling;
- commit, push, and PR expectation.

If the current worktree contains changes outside the sprint's owned scope, preserve them and use an isolated branch or worktree.

## Shared Planning Directory Governance

A repository may expose one canonical shared planning directory through harness infrastructure. Governance does not create that infrastructure; a separate harness lane must install it.

When a shared planning directory exists:

- its canonical path and index must be declared once; competing planning roots are forbidden;
- each active plan must name repo, branch, lane, mission, owned and forbidden scope, expected artifacts, validation, proof ceiling, status, and writer;
- one writer per branch also applies to plan files;
- plans and handoffs are coordination artifacts, not execution or completion proof;
- stale, superseded, or blocked plans must be labeled rather than silently overwritten;
- task prompts may add plan detail but cannot weaken governance or redefine completion.

## Executable Loop

Every writing action follows:

```text
request -> evidence review -> bounded decision -> repo/Git/GitHub mutation -> artifacts -> validation -> report -> next decision
```

A diagnosis-only request may stop before mutation when its task-specific contract explicitly requires that boundary.

## Action-Commitment Rule

Any prompt that claims installation, setup, build, execution, repair, configuration, upgrade, deployment, merge, or release must require the corresponding authorized mutation and proof.

A title or expected output that claims action while permitting acknowledgment, advice, a plan, a rewritten prompt, or a handoff instead is invalid.

## Capability and Authority Rule

A tool may perform an action only when all four conditions are true:

1. the environment exposes the capability;
2. the capability has been verified in the current environment;
3. the task authorizes the action;
4. repository policy does not forbid it.

Capability presence is not authority.

## Reuse and Evidence Discipline

- Inspect existing contracts, helpers, tests, validators, schemas, registries, generated-output policy, and branch conventions before invention.
- Preserve source inputs and useful evidence before cleanup or regeneration.
- Static checks prove only static properties; synthetic checks do not prove live-target behavior.
- Do not claim success above the strongest completed proof level.
- Route failures with exact commands, outputs, artifact paths, and the first confirmed blocker.

## Completion Standard

A task is complete only when all applicable items are reported and agree with repository state:

- files changed are named;
- generated artifacts and their tracked or untracked policy are named;
- validation was actually run, with commands and results rather than assumptions;
- skipped or blocked checks are explicit;
- a commit SHA exists for requested repository work;
- push or PR state is reported;
- remaining risks and the proof ceiling are stated;
- final Git state is reported;
- one exact next command is given.

## Forbidden Behaviors

- acknowledgment without mutation when mutation was requested and authorized;
- plans without execution when implementation was requested;
- summaries without proof;
- completion claims without running checks;
- substitution of a rewritten prompt or handoff for requested repository work;
- destructive cleanup before preservation;
- multiple writers sharing one branch or uncommitted worktree;
- secret, credential, personal-data, private-host, or customer-evidence exposure;
- force-push, default-branch mutation, merge, release, or deployment without explicit authority;
- generated junk, huge logs, crash dumps, or machine-local debris committed to the repository.

## Operator Source Immutability

`Candidates/` and `Active/` are read-only operator inputs.

- Never write, overwrite, or copy generated output into these paths.
- Never set an output path equal to its input path.
- Generated workbooks, sidecars, and forensic reports belong under `Outputs/` or another explicitly approved output path.
- Overwrites elsewhere require a timestamped backup under `Outputs/backups/`.
- Delivery requires baseline fingerprint comparison against the declared source and must fail when required sheets or content are lost.
