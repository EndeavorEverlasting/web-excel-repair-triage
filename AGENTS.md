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
Order: (1) Platform, security, legal, and repository-owner instructions. (2) This governance contract. (3) Task-specific prompts and sprint instructions. (4) Generic agent defaults. Domain specs remain subordinate.

## 3. Mandatory sprint declaration
Every writing sprint must state repository and branch or worktree; lane and mission; owned scope and forbidden scope; expected artifacts; validation commands and their order; proof ceiling; integration authority.
Before modifying or integrating overlapping prior work, refresh the default branch. Prove each required integrated slice is an ancestor with `git merge-base --is-ancestor <required-sha> <refreshed-default>` and still materially present using current content plus its owning validator. Ancestry alone cannot prove current content after a revert. Any failed check requires reconciliation and fresh proof before mutation or integration.

## 4. Completion standard
A task is complete only when exact files changed, validations run, commit SHA, push or PR/integration state, blockers/skips, proof ceiling, final Git state, one exact next command are reported.
NEXT COMMAND advances next unproven state. Remote/unmerged: fetch without force; pin branch/commit; preserve dirty work in isolated worktree; run owner validator/builder/launcher; resolve artifacts from tracked authority; propagate nonzero exit codes; must not execute production by default.
Use `none; no safe actionable work remains` only after implementation, validation, integration.

## 5. Safety and mutation boundaries
Forbidden: acknowledgment without mutation; plans without execution; summaries without proof; completion claims without running checks; secret or credential exposure; private workbook/protected/machine-local evidence exposure; force-push/default rewrites/destructive cleanup of unique work; prose-only deterministic behavior; weakened tests/validators/fixtures.
Material behavior changes require proof.
Client-facing delivery uses **minimum sufficient explanation**: purpose, period, totals, attachment, consequence. Omit internal evidence mechanics, private allocation logic, singled-out edge cases, defensive caveats, invitation-to-question closings unless needed for recipient action.

### Provider degradation and merge continuity
Actions minute/billing exhaustion, never-started checks, review-bot/CI limits are expected degradation, NOT merge blockers. Continue via refresh base, exact-head validation, local proof (`.githooks/pre-push`, `scripts/validate_pr_merge_gate.py`), merge when authorized. Real blockers: conflicts, draft, head-moved, failed validators, review, authority. See `harness/contracts/pr-merge-gate.v1.json`.

## 6. Repository identity and product boundary
The core product domain is **spreadsheet intelligence**. Web Excel compatibility, billing, roster/time evidence, triage are first-class.
**AFK Agent Flow** is the operator-approved product identity. Destination: `EndeavorEverlasting/TokenCorridor`; cutover remains unproven.
Until cutover, legacy `operant` / `prompt-kit` paths remain compatibility authority and must not be silently moved. This repo is current donor authority; TokenCorridor is convergence/destination authority. After cutover, migrated surfaces are compatibility/consumer seams; dependencies remain versioned.

## 7. Progressive disclosure and binding domain law
Orient: `AGENTS.md` → `harness/CONTEXT.md` → selected domain. Do **not** preload full harness/skills/history. Escalate context only for evidence.
Bindings: `harness/specs/operator-delivery.md`; `harness/specs/prompt-operations.md`; `harness/specs/billing-artifact-safety.md`.
Panels are agent transport; ingest/dispatch, not emit-and-wait.

### Repository-local `/teach` protocol
`/teach <topic>` uses `.teach/`, repo truth, first principles, one mechanism + code exercise. VERIFIED/MASTERED requires demonstrated understanding. `/teach recap` resumes first weak frontier.

### Agent execution tiering and parallel delegation
Parallelism is capability-earned, not equal-authority. Strategic/harness owners are `ChatGPT` and `Auggie`; they may own governance, harness spine, skills, capabilities, triggers, routing, proof gates. `desktop-app` and `OpenCode` are executors; they consume settled product/test/doc contracts but may not mutate strategic surfaces without promotion.
Machine policy: `harness/contracts/agent-execution-tiering.v1.json`. Availability is not authority. Promotion requires explicit operator approval and evaluation evidence. Shared contracts precede parallel consumers.
