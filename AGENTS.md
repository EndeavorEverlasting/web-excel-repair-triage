# Agent Governance Contract
This file is the single repository governance authority for `EndeavorEverlasting/web-excel-repair-triage`.

## 1. Agent operating principles
1. **Evidence before action.** Inspect authoritative evidence first.
2. **Floor before furniture.** Repair unsafe shared state/contracts first.
3. **Bounded sprints.** Declare mission, scope, artifacts, validation, proof ceiling.
4. **One writer per branch.** Preserve unrelated work; isolate unclear ownership.
5. **Reuse before replacing.** Extend canonical owners.
6. **No completion without proof.** Plans/process start are not completion.

## 2. Instruction precedence
Order: (1) Platform, security, legal, and repository-owner instructions. (2) This governance contract plus selected binding domain spec. (3) Task-specific prompts and sprint instructions. (4) Generic agent defaults. Lower authority may narrow scope/strengthen safety, never weaken higher authority.

## 3. Mandatory sprint declaration
Before writes state repository and branch or worktree; lane and mission; owned scope and forbidden scope; expected artifacts; validation commands and their order; proof ceiling; push/PR/merge/deploy authority. Preserve/isolate dirty, conflicted, stale, or separately owned work; never discard unrelated work to become current.
Before modifying or integrating overlapping prior work, refresh the default branch. Prove each required integrated slice is an ancestor via `git merge-base --is-ancestor <required-sha> <refreshed-default>` and still materially present using current content plus its owning validator. Ancestry alone cannot prove current content after a revert. Any failed check requires reconciliation and fresh proof before mutation or integration.

## 4. Completion standard
Report exact files changed, validations run, commit SHA, push state, PR/integration state, blockers/skips, proof ceiling, final Git state, and one exact next command.
NEXT COMMAND advances the next unproven state. Remote/unmerged: fetch without force; pin branch/commit; preserve dirty work in an isolated worktree; run owner validator/builder/launcher; resolve canonical artifact from tracked authority; propagate nonzero exit codes; it must not execute production by default.
Use `none; no safe actionable work remains` only after authorized implementation/validation/integration, preservation/cleanup, and artifact consumption.

## 5. Safety and mutation boundaries
Do not substitute acknowledgment, plans, or summaries for safe mutation/proof; claim completion without checks; expose secrets, credentials, private workbook/protected/machine-local evidence; force-push/rewrite default/destructively clean unknown work/delete unique work; hide deterministic behavior only in prompts/skills/prose; weaken tests/validators/fixtures for green; write generated outputs into protected inputs; or guess latest artifacts from generic names.
Material behavior changes require proof. Run focused checks and `git diff --check` before commit.

## 6. Repository identity and product boundary
This repository's core product domain is **spreadsheet intelligence**: inspection, validation, repair, transformation, safe delivery. Web Excel compatibility, billing, roster/time evidence, and triage are first-class.
The Prompt Kit began here as a spreadsheet and is separable. Intended home: a dedicated repository under `UnderDeskDev`, not yet named or created; agents must not invent its name or claim migration complete.
Until proven, Prompt Kit sources here remain operationally authoritative and must not be silently moved. Then this repo may source, pin, mirror, package, link to, or consume Prompt Kit releases, but must not become a competing Prompt Kit authority. Keep cross-repo dependencies explicit and versioned.

## 7. Progressive disclosure and binding domain law
Orient: `AGENTS.md` → `harness/CONTEXT.md` → one selected domain + only its needed routed map/contract and one workflow/skill/spec. Do **not** preload full harness/skills/history. Escalate context only for evidence, ownership, validation, or safety.
Bindings: delivery/live cert → `harness/specs/operator-delivery.md`; Prompt Kit → `harness/specs/prompt-operations.md`; billing/artifact safety → `harness/specs/billing-artifact-safety.md`. `harness/contracts/context-architecture.v1.json` defines context budgets/routes; `scripts/validate_context_architecture.py --summary` fails closed on bloat/routing drift.

### Repository-local `/teach` protocol
`/teach <topic>` uses `.teach/`: update `MISSION.md`; ground from `RESOURCES.md` + repo truth; create/reuse `lessons/<number>_<topic>.md` (`.html` for useful visual); teach first principles, not final production code; end with exactly one mechanism/trade-off question + one code diagnostic/edge-case exercise; stop for learner response. Write dated `learning-records/<date>_<topic>.md` VERIFIED/MASTERED only after demonstrated understanding. `/teach recap` reads records first, runs a roughly three-minute refresher, resumes first weak/unmastered frontier. No external package/clone, fabricated mastery, secrets/private/sensitive evidence. Setup stops here; sessions use Stateful Socratic Technical Tutor Workspace.
