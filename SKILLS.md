# Scoped Skills

This is the repository skill index. Reusable procedures live under `.ai/skills/<skill-name>/SKILL.md`. Deterministic behavior remains in scripts, modules, schemas, manifests, tests, registries, workflows, and domain overlays rather than only in prose.

## Skill selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, `CAPABILITIES.md`, `TRIGGERS.md`, and `harness/manifest.v1.json` first.
2. Select a root skill only when a registered root trigger matches and no forbidden condition applies. For a registered domain overlay, load its manifest and trigger registry before selecting the overlay skill.
3. Prefer one primary skill/capability or domain-overlay owner; add a second only for a distinct downstream phase.
4. Do not use skills to bypass protected inputs, credentials, validation, delivery-mode contracts, or proof boundaries.
5. Update skill, capability/overlay, trigger, manifest, tests, and docs atomically when ownership changes.

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

### Neuron Track Hours monthly artifact

- **Path:** `.ai/skills/neuron-track-hours-monthly-artifact/SKILL.md`
- **Domain overlay:** `harness/nth/manifest.v1.json`
- **Triggers:** `nth-internal-workbook-request` or `nth-client-send-copy-request` in `harness/nth/triggers.v1.json`.
- **Inputs:** Canonical governance, active NTH month rule pack, roster/attendance, explicit date/person evidence, requested delivery mode, and a validated internal workbook before client projection.
- **Outputs:** Internal working NTH artifact or client-facing derived send copy, plus rule-pack/mode/parity validation and handoff.
- **Primary validation:** `python scripts/validate_nth_harness.py` and `python -m unittest tests.test_nth_harness_contract -v`, followed by the focused workbook validators for the concrete artifact.
- **Key boundary:** Internal mode is the construction/audit source. Client mode is a narrowed projection of validated internal truth; July 2026 client mode is exactly `Executive Summary` + `July 2026`.

## Required skill-file sections

Every active `SKILL.md` must include `## Trigger`, `## Required inputs`, `## Outputs`, `## Procedure`, `## Guardrails`, `## Validation`, and `## Proof ceiling`.

## Adding, repairing, or retiring a skill

1. Use P61 for root ownership factoring and inspect all consumers; use the relevant domain manifest for overlay ownership.
2. Update `SKILLS.md`, root capability/trigger registries or the owning domain overlay, manifest references, tests, and docs atomically.
3. Preserve unique useful procedures before retirement.
4. Add positive, negative, boundary, malformed-input, and regression validation appropriate to the skill.
5. Use P62 to implement correctness and efficiency evals when a reusable skill's behavior needs deeper executable evidence.
6. Report the preservation destination, executed proof, and proof ceiling.
