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
Order: (1) Platform, security, legal, and repository-owner instructions. (2) This governance contract. (3) Task-specific prompts and sprint instructions. (4) Generic agent defaults. Domain specs remain subordinate. Lower authority may strengthen safety, never weaken higher authority.

## 3. Mandatory sprint declaration
Every writing sprint must state repository and branch or worktree; lane and mission; owned scope and forbidden scope; expected artifacts; validation commands and their order; proof ceiling; integration authority.
Before modifying or integrating overlapping prior work, refresh the default branch. Prove each required integrated slice is an ancestor with `git merge-base --is-ancestor <required-sha> <refreshed-default>` and still materially present using current content plus its owning validator. Ancestry alone cannot prove current content after a revert. Any failed check requires reconciliation and fresh proof before mutation or integration.

## 4. Completion standard
A task is complete only when exact files changed, validations run, commit SHA, push or PR/integration state, blockers/skips, proof ceiling, final Git state, and one exact next command are reported.
NEXT COMMAND advances the next unproven state. Remote/unmerged: fetch without force; pin branch/commit; preserve dirty work in an isolated worktree; run the owner validator/builder/launcher; resolve canonical artifacts from tracked authority; propagate nonzero exit codes; it must not execute production by default.
Use `none; no safe actionable work remains` only after authorized implementation, validation, integration, preservation/cleanup, and artifact consumption.

## 5. Safety and mutation boundaries
Forbidden: acknowledgment without mutation; plans without execution; summaries without proof; completion claims without running checks; secret or credential exposure; private workbook/protected/machine-local evidence exposure; force-push/default rewrites/destructive cleanup of unique work; prose-only deterministic behavior; weakened tests/validators/fixtures; protected-input generated outputs; guessed latest artifacts.
Material behavior changes require proof and `git diff --check`.

## 6. Repository identity and product boundary
This repository's core product domain is **spreadsheet intelligence**: inspection, validation, repair, transformation. Web Excel compatibility, billing, roster/time evidence, and triage are first-class.
Prompt Kit began here as a spreadsheet and is separable. Intended home: a dedicated repository under `UnderDeskDev`, not yet named or created; agents must not invent its name or claim migration complete.
Until proven, Prompt Kit sources here remain operationally authoritative and must not be silently moved. It may source, pin, mirror, package, link to, or consume Prompt Kit releases, but must not become a competing Prompt Kit authority; keep cross-repo dependencies explicit and versioned.

## 7. Progressive disclosure and binding domain law
Orient: `AGENTS.md` → `harness/CONTEXT.md` → one selected domain and only needed detail. Do **not** preload full harness/skills/history. Escalate context only for evidence, ownership, validation, or safety.
Bindings: `harness/specs/operator-delivery.md`; `harness/specs/prompt-operations.md`; `harness/specs/billing-artifact-safety.md`. `harness/contracts/context-architecture.v1.json` owns budgets/routes.

### Repository-local `/teach` protocol
`/teach <topic>` uses `.teach/`, repo truth, first-principles lessons, exactly one mechanism/trade-off question + one code diagnostic/edge-case exercise, then stops. VERIFIED/MASTERED requires demonstrated understanding. `/teach recap` resumes the first weak frontier. No external package/clone, fabricated mastery, secrets/private/sensitive evidence.

### Agent execution tiering and parallel delegation
Parallelism is capability-earned, not equal-authority. Strategic/harness owners are `ChatGPT` and `Auggie`; only they may own governance, harness spine, skills, capabilities, triggers, routing, proof gates, or cross-repo migration authority. `desktop-app` and `OpenCode` are executors: they may consume settled contracts for application logic, UI, adapters, fixtures, tests, docs, or conforming migration, but may not mutate strategic surfaces without promotion.
Machine policy: `harness/contracts/agent-execution-tiering.v1.json`. Availability is not authority; unknown routes down. Promotion requires explicit operator approval and evaluation evidence. Shared contracts precede parallel consumers; collision owners stay singular.
