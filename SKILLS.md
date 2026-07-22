# Scoped Skills

This file is the repository skill index. Detailed reusable procedures live under `.ai/skills/<skill-name>/SKILL.md`. Deterministic behavior remains in scripts, modules, schemas, manifests, tests, and workflows rather than only in skill prose.

## Skill selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, and `harness/manifest.v1.json` first.
2. Select a skill only when its trigger and preconditions are satisfied.
3. Prefer one primary skill owner for a task. Use another skill only for a distinct downstream phase.
4. Do not use skills to bypass protected inputs, validation, credentials, or proof boundaries.
5. If no skill fits, follow `WORKFLOW.md` and add a skill only when the procedure is reusable and has a deterministic trigger.

## Active repository skills

### Skill factoring

- **Path:** `.ai/skills/skill-factoring/SKILL.md`
- **Trigger:** A repository skill is oversized, overlaps another skill, hides deterministic behavior in prose, owns multiple unrelated activation conditions, or lacks testable boundaries.
- **Inputs:** Repository law, skill/capability/trigger registries, current consumers, tests, fixtures, and failure evidence.
- **Outputs:** `KEEP`, `SPLIT`, `MERGE`, `RETIRE`, or `REWIRE` dispositions; repaired skills and routing; focused validation.
- **Do not use for:** Cosmetic renames or reorganization without a behavioral boundary defect.
- **Primary validation:** `python -m unittest tests.test_skill_prompt_registry -v` plus any repository-specific skill routing checks.

### Technician Prompt Kit acquisition

- **Path:** `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`
- **Trigger:** A technician needs to clone, safely update, validate, and open the latest Prompt Kit website or generator GUI through a mouse-accessible Windows surface.
- **Inputs:** Canonical repository URL, `main`, destination folder, Git for Windows, Windows PowerShell, Python 3, and repository access.
- **Outputs:** A clean checkout on `main`, exact checked-in website validation, and the selected site or generator GUI opened after success.
- **Forbidden conditions:** Dirty worktree, wrong origin, non-`main` branch, local-only commits, divergence, missing required files, or missing tools.
- **Primary validation:** `python scripts/validate_harness.py` and `python -m unittest tests.test_harness_contract -v`.
- **Field proof:** Native Windows double-click clone/update/open check.

## Prompt-driven skill development

The Prompt Kit contains two separate implementation prompts:

- **P61 — Skill Factoring and Boundary Refactorer:** factors skill ownership and routing.
- **P62 — Skill Evaluation Harness Implementer:** implements positive, negative, boundary, malformed-input, and regression evals for a target skill.

These are prompt-registry artifacts, not substitutes for tracked skill files or executable validators.

## Product workflow guidance

Workbook and billing procedures are conventional product workflows and are documented by their focused modules, configs, tests, and contract docs referenced from `README.md`. Do not create broad prose-only skills that claim to implement product behavior. A product skill is appropriate only when it adds reusable judgment or sequencing around already implemented operations.

## Required skill-file sections

Every active `SKILL.md` must include:

- `## Trigger`
- `## Required inputs`
- `## Outputs`
- `## Procedure`
- `## Guardrails`
- `## Validation`
- `## Proof ceiling`

The harness validator rejects missing sections and missing indexed skill paths.

## Adding or retiring a skill

When adding, splitting, merging, rewiring, or retiring a skill:

1. Use P61 and inspect all existing owners and consumers.
2. Update this index and any trigger/capability/manifest references atomically.
3. Preserve unique useful procedures before retiring a source skill.
4. Add positive, negative, and boundary validation.
5. Use P62 when model judgment, routing quality, or regression safety needs an executable eval harness.
6. Report the preservation destination and proof ceiling.
