# Agent Governance Contract

This file is the single repository governance authority for `EndeavorEverlasting/web-excel-repair-triage`. Domain law is incorporated by reference in section 7.

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
2. This contract plus any selected binding domain spec.
3. Task-specific prompts and sprint instructions.
4. Generic defaults.

Lower authority may narrow scope or strengthen safety, never weaken higher authority.

## 3. Mandatory sprint declaration

Before tracked writes state: repository and branch/worktree; lane and mission; owned and forbidden scope; expected artifacts; validation commands/order; proof ceiling; push/PR/merge/deploy authority.

Preserve dirty, conflicted, stale, or separately owned work and isolate the sprint. Never discard unrelated work merely to become current.

## 4. Completion standard

Report files changed, validations run, commit SHA, push/PR/integration state, blockers/skips, proof ceiling, final Git state, and one exact next command.

NEXT COMMAND must advance the next useful unproven state. For remote/unmerged work, fetch without force, pin exact branch/commit, isolate dirty work, run the owner validator/builder/launcher, resolve the canonical artifact from tracked authority, and propagate failures; never execute production by default.

Use `none; no safe actionable work remains` only after authorized implementation, validation, integration, preservation/cleanup reporting, and artifact consumption are complete.

## 5. Safety and mutation boundaries

Agents must not:

- substitute acknowledgment/planning for an authorized safe mutation;
- claim completion without checks;
- expose secrets, credentials, private workbook data, protected inputs, or machine-local evidence;
- force-push, rewrite default history, destructively clean unknown work, or delete unique work without authority;
- hide deterministic product behavior only in prompts/skills/prose;
- weaken tests/validators/fixtures to obtain green checks;
- write generated outputs into protected inputs;
- guess the latest artifact from generic filenames.

Material behavior changes require implementation and proof. Run focused checks and `git diff --check` before commit.

## 6. Repository identity and product boundary

This repository's core product domain is **spreadsheet intelligence**: inspect, validate, repair, transform, and safely deliver spreadsheet artifacts. Web Excel compatibility, billing, roster/time evidence, and triage are first-class concerns.

The Prompt Kit began here as a spreadsheet and evolved into a website/app, but it is now separable. Its intended long-term core home is a dedicated repository under `UnderDeskDev`. That repository is not yet named or created; agents must not invent its name or claim migration is complete.

Until that repository exists and migration/integration is proven, Prompt Kit sources here remain operationally authoritative and must not be silently moved. After external authority is established, this repo may source, pin, mirror, package, link to, or consume Prompt Kit releases, but must not become a competing Prompt Kit authority.

Deepen spreadsheet intelligence here. Move Prompt Kit product identity/evolution to its dedicated repo once established; keep cross-repo dependencies explicit and versioned.

## 7. Progressive disclosure and binding domain law

Default orientation is exactly:

1. `AGENTS.md` — universal governance.
2. `harness/CONTEXT.md` — 50,000-foot router.
3. Select one task domain, then load only its routed 30,000-foot map/contract and one 15,000-foot workflow/skill/spec as needed.

Do **not** preload `CODEBASE_MAP.md`, `WORKFLOW.md`, `CAPABILITIES.md`, `SKILLS.md`, `TRIGGERS.md`, the harness manifest, every skill, or historical reports as a bundle. Escalate only when evidence, ownership, validation, or safety requires it.

Binding only in the selected domain:

- operator delivery/live certification: `harness/specs/operator-delivery.md`;
- Prompt Kit operations: `harness/specs/prompt-operations.md`;
- billing/artifact safety: `harness/specs/billing-artifact-safety.md`.

`harness/contracts/context-architecture.v1.json` defines context budgets/routes. `scripts/validate_context_architecture.py --summary` fails closed on bloat or routing drift.
