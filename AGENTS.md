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
Apply conflicts in this order: (1) platform/security/legal/repository-owner instructions; (2) this contract plus selected binding domain spec; (3) task/sprint instructions; (4) generic defaults. Lower authority may narrow scope or strengthen safety, never weaken higher authority.

## 3. Mandatory sprint declaration
Before tracked writes state repo + branch/worktree, lane/mission, owned/forbidden scope, expected artifacts, validation order, proof ceiling, and push/PR/merge/deploy authority. Preserve dirty/conflicted/stale/separately owned work; never discard it merely to become current.

Before overlapping mutation/integration, refresh default. Prove each required slice is an ancestor with `git merge-base --is-ancestor <required-sha> <refreshed-default>` and still materially present via content plus its owning validator. Ancestry cannot prove content after revert; failed checks require reconciliation and fresh proof.

## 4. Completion standard
Report exact files, validations, commit SHA, push/PR/integration state, blockers/skips, proof ceiling, final Git state, and one exact NEXT COMMAND. That command must advance the next unproven state; for remote/unmerged work fetch without force, pin the exact branch/commit, preserve dirty work via isolated worktree, run the owner validator/builder/launcher, resolve canonical artifacts from tracked authority, and propagate nonzero exits; do not execute production by default.

Use `none; no safe actionable work remains` only after authorized implementation, validation, integration, preservation/cleanup, and artifact consumption are complete.

## 5. Safety and mutation boundaries
Do not substitute plans/summaries for safe mutation/proof; claim completion without checks; expose secrets, credentials, private workbook data, protected inputs, or machine-local evidence; force-push/rewrite default history/destructively clean unknown work/delete unique work; hide deterministic behavior only in prompts/skills/prose; weaken tests/validators/fixtures for green; write generated outputs into protected inputs; or guess latest artifacts from generic filenames.

Material behavior changes require implementation/proof. Run focused checks and `git diff --check` before commit.

## 6. Repository identity and product boundary
Core product: **spreadsheet intelligence**—inspection, validation, repair, transformation, and safe delivery; Web Excel, billing, roster/time evidence, and triage are first-class.

Prompt Kit sources here remain authoritative until migration/integration is proven. Their intended core home is a not-yet-named `UnderDeskDev` repo; do not invent its name or claim migration complete. After external authority exists, this repo may source/pin/mirror/package/link/consume versioned Prompt Kit releases, but must not compete.

## 7. Progressive disclosure and binding domain law
Default orientation: `AGENTS.md` → `harness/CONTEXT.md` → one selected task domain and only its needed routed map/contract plus one workflow/spec. Do not preload the full harness, every skill, or historical reports; escalate only for evidence, ownership, validation, or safety.

Selected-domain bindings: operator delivery/live certification → `harness/specs/operator-delivery.md`; Prompt Kit operations → `harness/specs/prompt-operations.md`; billing/artifact safety → `harness/specs/billing-artifact-safety.md`.

`harness/contracts/context-architecture.v1.json` defines context budgets/routes; `scripts/validate_context_architecture.py --summary` fails closed on bloat/routing drift.

## 8. Repository-local `/teach` protocol
`/teach <topic>`: use repo-local `.teach/`; update `MISSION.md`, ground from `RESOURCES.md` + repo truth, create/reuse `lessons/<number>_<topic>.md` (`.html` only when a visual materially helps), teach first principles without final production code, then end with exactly one mechanism/trade-off question + one code diagnostic/edge-case exercise; stop for the learner response. Write dated `learning-records/<date>_<topic>.md` VERIFIED/MASTERED only after demonstrated understanding. `/teach recap`: read records first, run a roughly three-minute refresher, resume first weak/unmastered frontier. No external package/clone, fabricated mastery, secrets/private data, or sensitive learning evidence. Setup stops here; actual sessions use Stateful Socratic Technical Tutor Workspace.
