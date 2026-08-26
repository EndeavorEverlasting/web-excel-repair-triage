# Agent Governance Contract

This file is the single repository governance authority for `EndeavorEverlasting/web-excel-repair-triage`.

## 1. Agent operating principles

1. **Evidence before action.** Inspect Git/PR truth and the smallest authoritative repo surface before mutation.
2. **Floor before furniture.** Repair unsafe shared state or broken contracts before dependent work.
3. **Bounded sprints.** Declare mission, ownership, exclusions, artifacts, validation, and proof ceiling.
4. **One writer per branch.** Preserve unrelated work; isolate unclear ownership.
5. **Reuse before replacing.** Extend canonical code/contracts/registries/validators/workflows instead of competing authorities.
6. **No completion without proof.** Plans, prose, process start, and acknowledgment are not completion.

## 2. Instruction precedence

Apply conflicts in this order:

1. Platform, security, legal, and repository-owner instructions.
2. This governance contract plus any selected binding domain spec.
3. Task-specific prompts and sprint instructions.
4. Generic agent defaults.

Lower authority may narrow scope or strengthen safety, never weaken higher authority.

## 3. Mandatory sprint declaration

Before tracked writes state: repository and branch or worktree; lane and mission; owned scope and forbidden scope; expected artifacts; validation commands and their order; proof ceiling; push/PR/merge/deploy authority.

Preserve dirty, conflicted, stale, or separately owned work and isolate the sprint. Never discard unrelated work merely to become current.

Before modifying or integrating overlapping prior work, refresh the default branch. Prove each required integrated slice is an ancestor with `git merge-base --is-ancestor <required-sha> <refreshed-default>` and still materially present using current content plus its owning validator. Ancestry alone cannot prove current content after a revert. Any failed check requires reconciliation and fresh proof before mutation or integration.

## 4. Completion standard

Report exact files changed, validations run, commit SHA, push state, PR/integration state, blockers/skips, proof ceiling, final Git state, and one exact next command.

NEXT COMMAND must advance the next useful unproven state. For remote/unmerged work, fetch without force, pin exact branch/commit, preserve dirty work through an isolated worktree, run the owner validator/builder/launcher, resolve the canonical artifact from tracked authority, and propagate nonzero exit codes; it must not execute production by default.

Use `none; no safe actionable work remains` only after authorized implementation, validation, integration, preservation/cleanup reporting, and artifact consumption are complete.

## 5. Safety and mutation boundaries

Agents must not:

- substitute acknowledgment, plans, or summaries for authorized safe mutation and proof;
- claim completion without checks;
- expose secrets, credentials, private workbook data, protected inputs, or machine-local evidence;
- force-push, rewrite default history, destructively clean unknown work, or delete unique work without authority;
- hide deterministic product behavior only in prompts/skills/prose;
- weaken tests/validators/fixtures to obtain green checks;
- write generated outputs into protected inputs;
- guess the latest artifact from generic filenames.

Material behavior changes require implementation and proof. Run focused checks and `git diff --check` before commit.

## 6. Repository identity and product boundary

This repository's core product domain is **spreadsheet intelligence**: spreadsheet inspection, validation, repair, transformation, and safe delivery. Web Excel compatibility, billing, roster/time evidence, and triage are first-class.

The Prompt Kit began here as a spreadsheet and is now separable. Its intended core home is a dedicated repository under `UnderDeskDev`, not yet named or created; agents must not invent its name or claim migration is complete.

Until migration/integration is proven, Prompt Kit sources here remain operationally authoritative and must not be silently moved. After external authority exists, this repo may source, pin, mirror, package, link to, or consume Prompt Kit releases, but must not become a competing Prompt Kit authority. Keep cross-repo dependencies explicit and versioned.

## 7. Progressive disclosure and binding domain law

Default orientation is exactly:

1. `AGENTS.md` — universal governance.
2. `harness/CONTEXT.md` — 50,000-foot router.
3. Select one task domain, then load only its routed map/contract and one workflow/skill/spec as needed.

Do **not** preload the full harness, every skill, or historical reports. Escalate context only when evidence, ownership, validation, or safety requires it.

Binding only in the selected domain:

- operator delivery/live certification: `harness/specs/operator-delivery.md`;
- Prompt Kit operations: `harness/specs/prompt-operations.md`;
- billing/artifact safety: `harness/specs/billing-artifact-safety.md`.

`harness/contracts/context-architecture.v1.json` defines context budgets/routes. `scripts/validate_context_architecture.py --summary` fails closed on bloat or routing drift.

## 8. Repository-local `/teach` workspace protocol

`/teach` is repository-local learning state, not a package, clone, or production-feature lane. The canonical core is `.teach/MISSION.md`, `.teach/RESOURCES.md`, `.teach/lessons/`, and `.teach/learning-records/`. Preserve existing valid teaching state; never fabricate lessons, resources, verification, or mastery, and never commit secrets, private data, or sensitive learning evidence.

- `/teach <topic>` routes to the Stateful Socratic Technical Tutor Workspace behavior. Read and update `.teach/MISSION.md`; ground the session from `.teach/RESOURCES.md` plus current repository truth; create or reuse `.teach/lessons/<number>_<topic>.md` (or `.html` only when a visual simulator materially helps); teach from first principles without jumping to final production code; and end the atomic lesson with exactly one conceptual trade-off/mechanism question plus one code diagnostic or edge-case exercise.
- After those two checkpoints, stop for the learner response. Evaluate demonstrated understanding before writing `.teach/learning-records/<date>_<topic>.md`; mark VERIFIED or MASTERED only when the learner has actually demonstrated the corresponding understanding.
- `/teach recap` reads `.teach/learning-records/` first, runs a quick roughly three-minute refresher quiz, and resumes at the first weak, decayed, or unmastered frontier.

Bootstrap/setup work must stop after establishing or repairing this protocol and its state. Actual `/teach <topic>` and `/teach recap` sessions belong to the Stateful Socratic Technical Tutor Workspace.
