# Harness Capabilities

This file is the human-readable index for reusable repository operations. The machine-readable authority is `harness/capabilities.v1.json`. A capability exposes an operation; its linked skill explains procedure and judgment; its trigger records deterministic routing.

## Selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, and `TRIGGERS.md`.
2. Select a capability only when one registered trigger matches and no forbidden condition is present.
3. Prefer deterministic scripts or launchers. Prompts and skills may orchestrate them but are not substitutes for implementation.
4. Report the capability ID, inputs, produced artifacts, validators, and proof ceiling.
5. Keep one explicit owner for shared registries, workflows, generated outputs, branches, and PRs.

## Active capabilities

| Capability ID | Skill | Implementation | Primary output |
|---|---|---|---|
| `harness-infrastructure-maintenance` | `.ai/skills/harness-infrastructure-maintenance/SKILL.md` | `scripts/validate_harness.py` | Canonical harness repairs plus `harness-completeness-report/v1`. |
| `prompt-language-audit` | `.ai/skills/prompt-language-audit/SKILL.md` | `scripts/evaluate_prompt_language.py` | Exhaustive prompt disposition and finding report. |
| `skill-evaluation` | `.ai/skills/skill-evaluation/SKILL.md` | Prompt Kit P62 | Repository-native eval harness, cases, runner, results, and repair ledger. |
| `skill-factoring` | `.ai/skills/skill-factoring/SKILL.md` | Prompt Kit P61 | Skill ownership dispositions and repaired routing boundaries. |
| `technician-prompt-kit-acquisition` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` | Existing public/Windows/Git acquisition surfaces | Device-aware access mode: public use, phone install, Windows local app, editable checkout, or ZIP snapshot. |
| `prompt-kit-browser-proof-scratch-cleanup` | `.ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md` | `scripts/Clear-PromptKitBrowserProofScratch.ps1` | Preview/apply cleanup receipt for exact eligible detached browser-proof scratch. |
| `prompt-kit-feedback-afk-routing` | `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md` | `scripts/prompt_kit_afk_signal_router.py` | One deduplicated P115 work request or information-only disposition; promotion remains P105/pr-floor. |

## Harness infrastructure capability

The `harness-infrastructure-maintenance` capability owns maps, workflow/artifact/validator/capability/trigger registries, completeness validation, harness tests, staged-index and pre-push hooks, harness CI, skills, and operator reports. It explicitly excludes `AGENTS.md` governance, product implementation, secrets, destructive cleanup, and production deployment.

Canonical report command:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

## Prompt Kit acquisition capability

`technician-prompt-kit-acquisition` is intentionally one capability across devices rather than separate phone, browser, Windows, and Git implementations. `harness/contracts/prompt-kit-cross-device-access.v1.json` owns the routing boundary.

- **Use/open/share:** open `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`; no Git checkout is required.
- **Phone/tablet install:** open `https://endeavoreverlasting.github.io/web-excel-repair-triage/` in the system browser and use the install/Add to Home Screen surface.
- **Windows stable local app:** use `Open-Latest-PromptKit.cmd` so repository-owned clone/update/validation and portable Favorites behavior remain centralized.
- **Edit/commit/push/local tooling:** use a real `main` checkout. Android source work uses Termux from F-Droid and Git. Before updating any existing editable checkout, prove canonical origin, a clean worktree, current branch `main`, and zero local-only commits; fetch `origin/main` and finish with `git merge --ff-only origin/main`.
- **No-Git source snapshot:** use the repository `main.zip`, explicitly as a point-in-time snapshot.

Focused contract proof:

```bash
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
```

## Prompt-language audit modes

- **Audit mode:** evaluates every raw and effective prompt, emits one disposition per prompt, fails coverage gaps and error-severity defects, and may report warning-severity canonical-source debt.
- **Strict mode:** also fails warning-severity lazy source language. Use after bounded canonical repair.

## Skill-evaluation capability

P62 must reproduce functional weaknesses and inefficiencies with versioned cases, guide the smallest valid repair through tests or profiling, validate unit/integration correctness, and measure performance, tool calls, context, cost, retries, and tokens without weakening safety or routing.

## Browser-proof scratch cleanup capability

`prompt-kit-browser-proof-scratch-cleanup` owns only detached `prompt-kit-browser-proof-*` directories directly under the OS temp root. Preview is default; apply is explicit; rejected paths are preserved; prior stable receipts are backed up. Browser profile data, localStorage, Favorites, canonical repositories, public Pages, and unrelated Temp contents are outside this capability.

## Prompt Kit feedback AFK routing capability

`prompt-kit-feedback-afk-routing` consumes one accepted explicit feedback signal at a time. P99 owns explicit feedback semantics, P115 owns AFK coordination, P07/P32 own bounded repair lanes, and P105 / `pr-floor-integration` owns promotion. The router may classify, deduplicate, write a private work request, and invoke one configured worker through argv; it must not poll indefinitely, scan provider PR queues, or merge. Raw written feedback remains local and provider wakeups are receipt-only.

## Proof boundaries

Capability registration, static validators, tests, and CI prove only the repository surfaces and commands exercised on the tested commit. Cross-device Prompt Kit validation proves routing intent and canonical access surfaces plus the existing-checkout preconditions encoded in the contract, not a phone/browser install menu, Termux/F-Droid availability, Git credentials, browser storage, clipboard behavior, or push success. Other capability proof likewise does not establish provider behavior, model judgment, Excel for Web, Windows GUI, protected runtime access, technician acceptance, deployment, or production success.
