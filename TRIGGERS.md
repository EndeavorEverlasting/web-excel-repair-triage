# Harness Triggers

This file describes deterministic routing into repository skills and capabilities. The machine-readable authority is `harness/triggers.v1.json`.

## Routing table

| Trigger ID | Route when | Capability | Do not route when |
|---|---|---|---|
| `harness-infrastructure-change` | Maps, workflow/artifact/validator registries, completeness checks, hooks, skills, reports, or ownership are missing, stale, disconnected, or failing. | `harness-infrastructure-maintenance` | The task changes `AGENTS.md`, implements product behavior only, requires secrets, or requests destructive cleanup. |
| `repository-hook-installation-needed` | Tracked hooks need activation/verification, or an external agent/provider hook must be reconciled with repository hook ownership. | `repository-hook-integration` | Global Git config, ambiguous linked-worktree mutation, silent replacement of another hook owner, or unproved provider-hook behavior would result. |
| `prompt-language-change` | Prompt registry, actionability policy, builder, or generated Prompt Kit language changes; or a full language pass is requested. | `prompt-language-audit` | The request is only to read an existing validated report. |
| `lazy-next-action-report` | Empty, placeholder, observation-only, PR/status/log-only, optional-only, or generic next actions are suspected. | `prompt-language-audit` | No canonical registry/effective builder exists; route to repository intake first. |
| `skill-quality-unproven` | Skill correctness, routing, regression safety, efficiency, or token use lacks executable proof. | `skill-evaluation` | The task is ownership factoring only. |
| `skill-boundary-defect` | A skill is oversized, overlapping, ambiguous, prompt-only, or owns unrelated triggers. | `skill-factoring` | The boundary is healthy and the change is cosmetic only. |
| `technician-needs-latest-prompt-kit` | A user needs to open/use the Prompt Kit in a browser, install it on a phone/tablet, launch the Windows stable local app, obtain a source snapshot, or create/update an editable checkout for edit/commit/push work. | `technician-prompt-kit-acquisition` | Destructive Git cleanup or credential automation is proposed; or an editable checkout update is unsafe because the checkout is dirty, divergent, non-main, or has the wrong origin. |
| `prompt-kit-browser-proof-temp-path` | An operator supplies a `prompt-kit-browser-proof-*` path under OS Temp or asks to classify/remove detached Prompt Kit browser-proof scratch. | `prompt-kit-browser-proof-scratch-cleanup` | The real request is browser-site data/Favorites deletion, broad Temp cleanup, canonical-repo cleanup, or durable evidence deletion. |
| `prompt-kit-actionable-feedback` | Accepted written feedback or a dislike has an unconsumed actionable Prompt Kit signal. | `prompt-kit-feedback-afk-routing` | The signal is like/usage-only, malformed/sensitive/already consumed, requires a second scheduler, or the only remaining gate is P105 promotion. |

## Repository hook integration routing rule

Route hook-install requests to the tracked `.githooks` owner first. Existing `core.hooksPath`, default hooks, and linked worktrees are preconditions, not cleanup targets. Claude/Codex/DeepSeek/Husky/Lefthook examples may inform an adapter, but they do not supersede repository ownership merely because they are installed or popular.

## Prompt Kit acquisition routing rule

The acquisition trigger is intent-first, not device-command-first:

1. **Use/open/share** → public Prompt Kit; do not require clone, ZIP, PowerShell, Python, or Termux.
2. **Install on phone/tablet** → public phone launcher in the system browser; do not require a source checkout.
3. **Windows stable local app** → repository-owned `Open-Latest-PromptKit.cmd`.
4. **Edit/commit/push/local tooling** → editable `main` checkout; on Android, route to Termux from F-Droid plus Git and keep updates fast-forward-only.
5. **Explicit no-Git source snapshot** → `main.zip`, with snapshot semantics stated clearly.

The focused owner is `harness/contracts/prompt-kit-cross-device-access.v1.json`. A normal-use request must fail routing review if the proposed answer unnecessarily sends the user into Git or file extraction.

## Browser-proof cleanup routing rule

A `file:///.../Temp/prompt-kit-browser-proof-<hex>/web/prompt-kit/index.html` path routes to the cleanup capability only after filesystem classification. Preview first. Do not translate this trigger into browser localStorage/Favorites deletion or generic Temp cleanup.

## Prompt Kit feedback AFK routing rule

Explicit written feedback and dislikes may create one bounded P115 work request after validation and deduplication. Likes and usage are informational by default. The private bridge may sanitize and transport; it does not schedule or merge. A validated candidate leaves this capability and enters P105 / `pr-floor-integration`. No local infinite poller is authorized.

## Routing procedure

1. Match concrete repository state and request language against `harness/triggers.v1.json`.
2. Reject a route when any forbidden condition matches.
3. Select one primary capability, skill, and workflow ID.
4. Load required inputs and canonical registries before mutation.
5. Run the linked validator profile plus any focused domain gate named in `harness/manifest.v1.json`.
6. Record trigger, capability, workflow, artifacts, validation, and proof ceiling in the handoff.

## Collision rule

One writer owns each shared registry, workflow, generated artifact, branch, PR, or mutable runtime. Read-only audits may run in parallel only when they cannot invalidate the writer's floor. Harness infrastructure may modify contracts, registries, validators, tests, hooks, CI, skills, and reports; it may not silently take ownership of product implementation or governance.
