# Agent Governance Contract

This file is the single repository governance authority for agents working in `EndeavorEverlasting/web-excel-repair-triage`. It contains only universal law. Domain law is incorporated by reference from the binding specs named in section 6 and must be loaded only when that domain is selected.

## 1. Agent operating principles

1. **Evidence before action.** Inspect current Git/PR state and the smallest authoritative repository surface needed before mutation.
2. **Floor before furniture.** Repair unsafe shared state or broken contracts before dependent feature work.
3. **Bounded sprints.** Declare mission, ownership, exclusions, expected artifacts, validation, and proof ceiling.
4. **One writer per branch.** Preserve unrelated work; use an isolated branch/worktree when ownership is unclear.
5. **Reuse before replacing.** Extend canonical code, contracts, registries, validators, workflows, and skills instead of creating competing authorities.
6. **No completion without proof.** Plans, prose, process start, and acknowledgments are not completion.

## 2. Instruction precedence

Apply conflicting instructions in this order:

1. Platform, security, legal, and repository-owner instructions.
2. This governance contract and any binding domain spec it incorporates for the selected task.
3. Task-specific prompts and sprint instructions.
4. Generic agent defaults.

A lower-precedence instruction may narrow scope or strengthen safety, but may not weaken a higher authority.

## 3. Mandatory sprint declaration

Before tracked writes, resolve and record:

- repository and branch or worktree;
- lane and mission;
- owned scope and forbidden scope;
- expected artifacts;
- validation commands and their order;
- proof ceiling;
- push/PR/merge/deploy authority.

If the primary checkout is dirty, conflicted, stale, or separately owned, preserve it and isolate the sprint. Never discard unrelated work to obtain a clean floor.

## 4. Completion standard

Report exact files changed, validations actually run, commit SHA, push state, PR state, blockers/skips, proof ceiling, final Git state, and one exact next command.

The next command must advance the work into the next useful unproven state: consume, validate, build, launch, open, or otherwise exercise the canonical artifact. Status-only, branch-listing, log-viewing, or PR-opening commands are insufficient while safe executable work remains.

For remote/unmerged work, fetch without force, verify exact branch/commit, preserve dirty or separately owned work through an isolated worktree, run the owning validator/builder/launcher, resolve the artifact from tracked repository authority, and propagate nonzero exit codes. It must not execute production by default.

Use `none; no safe actionable work remains` only after authorized implementation, validation, integration, cleanup/preservation reporting, and artifact consumption are complete.

## 5. Safety and mutation boundaries

Agents must not:

- acknowledge or return a plan instead of making an authorized safe mutation;
- claim completion without the stated checks;
- expose secrets, credentials, private workbook contents, protected inputs, or machine-local evidence;
- force-push, rewrite default-branch history, or destructively clean unknown work without explicit authority;
- delete unique branches/worktrees/PRs/commits before preservation proof;
- hide deterministic product behavior only in prompts, skills, or prose;
- weaken tests/validators/fixtures merely to obtain green checks;
- write generated outputs into protected operator-input directories;
- guess the latest artifact from generic filenames.

Material behavior changes require corresponding deterministic implementation and proof. Run focused checks before broad checks and `git diff --check` before commit.

## 6. Progressive disclosure and binding domain law

Default orientation is exactly:

1. `AGENTS.md` — universal governance.
2. `harness/CONTEXT.md` — 50,000-foot router.
3. Select one task domain, then load only its routed 30,000-foot map/contract and one 15,000-foot workflow/skill/spec as needed.

Do **not** preload `CODEBASE_MAP.md`, `WORKFLOW.md`, `CAPABILITIES.md`, `SKILLS.md`, `TRIGGERS.md`, the harness manifest, every skill, or historical reports as a bundle. Escalate context only when evidence, ownership, validation, or safety requires it.

These specs are incorporated by reference and binding only in their selected domain:

- technician acquisition, delivery, and live certification: `harness/specs/operator-delivery.md`;
- Prompt Kit contribution, language quality, panels/chats, and prompt operations: `harness/specs/prompt-operations.md`;
- billing direction, source precedence, and operator-input immutability: `harness/specs/billing-artifact-safety.md`.

`harness/contracts/context-architecture.v1.json` defines context budgets and canonical routes. `scripts/validate_context_architecture.py --summary` fails closed when the default path or routed documents bloat beyond those boundaries.
