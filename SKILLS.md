# Scoped Skills

This is the repository skill index. Reusable procedures live under `.ai/skills/<skill-name>/SKILL.md`. Deterministic behavior remains in scripts, modules, schemas, manifests, tests, registries, and workflows rather than only in prose.

## Skill selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, `CAPABILITIES.md`, `TRIGGERS.md`, and `harness/manifest.v1.json` first.
2. Select a skill only when a registered trigger matches and no forbidden condition applies.
3. Prefer one primary skill/capability owner; add a second only for a distinct downstream phase.
4. Do not use skills to bypass protected inputs, credentials, validation, or proof boundaries.
5. Update skill, capability, trigger, manifest, tests, and docs atomically when ownership changes.

## Active repository skills

### Prompt language audit

- **Path:** `.ai/skills/prompt-language-audit/SKILL.md`
- **Trigger:** Prompt registry/policy/builder/generated language changes, or empty/lazy next-action language is suspected.
- **Capability:** `prompt-language-audit`
- **Inputs:** Every canonical registry, effective builder output, actionability policy, eval policy, fixtures, and known failures.
- **Outputs:** Complete inventory, one disposition per prompt, stable findings, machine-readable report, and canonical-source repairs when authorized.
- **Primary validation:** `python -m unittest tests.test_prompt_language_audit -v` and `python scripts/evaluate_prompt_language.py --summary`.

### Skill evaluation

- **Path:** `.ai/skills/skill-evaluation/SKILL.md`
- **Trigger:** A target skill's correctness, routing, failure behavior, regression safety, performance, cost, or token efficiency lacks executable proof.
- **Capability:** `skill-evaluation`; Prompt Kit owner P62 — Skill Correctness and Efficiency Eval Implementer.
- **Inputs:** Target skill/contracts, known failures, representative cases, unit/integration surfaces, and baseline traces.
- **Outputs:** Versioned eval cases, runner, machine-readable results, finding-to-repair ledger, and before/after measurements.
- **Primary validation:** Target-repository eval suite plus unit, integration, regression, profiling, and token/cost evidence appropriate to the claim.

### Skill factoring

- **Path:** `.ai/skills/skill-factoring/SKILL.md`
- **Trigger:** A skill is oversized, overlapping, ambiguous, prompt-only, or lacks testable boundaries.
- **Capability:** `skill-factoring`; Prompt Kit owner P61.
- **Outputs:** `KEEP`, `SPLIT`, `MERGE`, `RETIRE`, or `REWIRE` dispositions; repaired skills/routing; boundary fixtures.

### Technician Prompt Kit acquisition

- **Path:** `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`
- **Trigger:** A technician needs to clone, safely update, validate, and open the latest `main` Prompt Kit through Windows GUI/CMD.
- **Capability:** `technician-prompt-kit-acquisition`
- **Forbidden conditions:** Dirty worktree, wrong origin, non-main branch, local-only commits, divergence, missing tools/files.
- **Primary validation:** harness validator/contracts plus native Windows field proof.

## Required skill-file sections

Every active `SKILL.md` must include `## Trigger`, `## Required inputs`, `## Outputs`, `## Procedure`, `## Guardrails`, `## Validation`, and `## Proof ceiling`.

## Adding, repairing, or retiring a skill

1. Use P61 for ownership factoring and inspect all consumers.
2. Update `SKILLS.md`, `CAPABILITIES.md`, `TRIGGERS.md`, machine-readable registries, and manifest references atomically.
3. Preserve unique useful procedures before retirement.
4. Add positive, negative, boundary, malformed-input, and regression validation appropriate to the skill.
5. Use P62 to implement correctness and efficiency evals.
6. Report the preservation destination, executed proof, and proof ceiling.
