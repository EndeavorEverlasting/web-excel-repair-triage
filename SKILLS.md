# Scoped Skills

This is the repository skill index. Reusable procedures live under `.ai/skills/<skill-name>/SKILL.md`. Deterministic behavior remains in scripts, modules, schemas, manifests, tests, registries, and workflows rather than only in prose.

## Skill selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, `CAPABILITIES.md`, `TRIGGERS.md`, and `harness/manifest.v1.json`.
2. Select a skill only when a registered trigger matches and no forbidden condition applies.
3. Prefer one primary skill/capability owner; add another only for a distinct downstream phase.
4. Do not use skills to bypass protected inputs, credentials, validators, or proof boundaries.
5. Update skill, capability, trigger, manifest, tests, docs, hooks/CI, and reports atomically when ownership changes.
6. Skills describe repeatable judgment and procedure. Product behavior remains in deterministic code and contracts.

## Active repository skills

### Harness infrastructure maintenance

- **Path:** `.ai/skills/harness-infrastructure-maintenance/SKILL.md`
- **Trigger:** `harness-infrastructure-change`
- **Capability:** `harness-infrastructure-maintenance`
- **Use when:** Maps, workflow/artifact/validator registries, validators, hooks, skills, reports, or component ownership are missing, stale, disconnected, or failing.
- **Forbidden scope:** `AGENTS.md`, product implementation, secrets, destructive cleanup.
- **Outputs:** Canonical harness repairs, completeness report, regression tests, current-state report, commit/PR evidence, and an actionable next command.
- **Primary validation:** `python scripts/validate_harness.py --report Outputs/harness-completeness-report.json` and `python -m unittest tests.test_harness_contract -v`.

### Prompt language audit

- **Path:** `.ai/skills/prompt-language-audit/SKILL.md`
- **Triggers:** `prompt-language-change`, `lazy-next-action-report`
- **Capability:** `prompt-language-audit`
- **Inputs:** Canonical registries, effective builder output, actionability policy, eval policy, fixtures, and known failures.
- **Outputs:** Complete inventory, one disposition per prompt, stable findings, machine-readable report, and authorized canonical-source repairs.
- **Primary validation:** `python -m unittest tests.test_prompt_language_audit -v` and `python scripts/evaluate_prompt_language.py --summary`.

### Skill evaluation

- **Path:** `.ai/skills/skill-evaluation/SKILL.md`
- **Trigger:** `skill-quality-unproven`
- **Capability:** `skill-evaluation`; Prompt Kit owner P62.
- **Outputs:** Versioned cases, runner, machine-readable results, repair ledger, and before/after correctness and efficiency evidence.
- **Boundary:** May evaluate product behavior but cannot become the product implementation.

### Skill factoring

- **Path:** `.ai/skills/skill-factoring/SKILL.md`
- **Trigger:** `skill-boundary-defect`
- **Capability:** `skill-factoring`; Prompt Kit owner P61.
- **Outputs:** `KEEP`, `SPLIT`, `MERGE`, `RETIRE`, or `REWIRE` dispositions; repaired skills/routing; boundary fixtures.

### Technician Prompt Kit acquisition

- **Path:** `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`
- **Trigger:** `technician-needs-latest-prompt-kit`
- **Capability:** `technician-prompt-kit-acquisition`
- **Use when:** A user needs to open, install, share, download, clone, update, or locally edit the Prompt Kit on a browser, phone/tablet, Windows PC, macOS, or Linux machine. Also enter the skill when the user reports a Prompt Kit/prompt version or an older downloaded/installed/cloned copy whose currentness has not been proven.
- **Freshness gate:** A version label is not proof of currentness. Before troubleshooting, tutorial guidance, or prompt selection against a versioned/potentially stale copy, recommend the lowest-friction latest route. If refresh is declined, keep the copy labeled `stale-or-unverified`.
- **Routing:** Normal browser use goes directly to the public Prompt Kit; phone/tablet install uses the public launcher; Windows stable-origin use prefers `Open-Latest-PromptKit.cmd`; an editable checkout is reserved for edit/commit/push/local-tooling intent; ZIP is a source snapshot fallback.
- **Android editable checkout:** Use Termux from F-Droid, install Git, clone `main`, then update an existing checkout only after verifying canonical origin, a clean worktree, current branch `main`, and zero local-only commits; fetch and finish with `git merge --ff-only origin/main`.
- **Forbidden conditions:** Destructive Git cleanup, credential automation, or updating an editable checkout that is dirty, divergent, non-main, or has an unexpected origin.
- **Primary validation:** `python scripts/validate_prompt_kit_cross_device_access.py --summary`, `python -m unittest tests.test_prompt_kit_cross_device_access -v`, `python scripts/validate_prompt_kit_freshness_guidance.py --summary`, `python -m unittest tests.test_prompt_kit_freshness_guidance -v`, then the root harness validator/contracts and native device field proof.

## Required skill-file sections

Every active `SKILL.md` must include:

- `## Trigger`
- `## Required inputs`
- `## Outputs`
- `## Procedure`
- `## Guardrails`
- `## Validation`
- `## Proof ceiling`

## Adding, repairing, or retiring a skill

1. Inspect all triggers, capabilities, workflows, consumers, validators, and historical failures.
2. Use skill factoring when ownership is ambiguous.
3. Update `SKILLS.md`, `CAPABILITIES.md`, `TRIGGERS.md`, machine registries, manifest, tests, hooks/CI, and reports atomically.
4. Preserve unique useful procedures before retirement.
5. Add positive, negative, boundary, malformed-input, and regression validation.
6. Use skill evaluation for correctness and efficiency proof.
7. Report preservation destination, executed proof, commit/PR state, and proof ceiling.
