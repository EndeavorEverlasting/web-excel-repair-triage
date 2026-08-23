# Harness Infrastructure Maintenance

## Trigger

Use when harness maps, workflows, capabilities, triggers, registries, reports, skills, validators, or context architecture are missing, duplicated, stale, or inconsistent. For token/spec bloat, route through `harness/CONTEXT.md` and `harness/contracts/context-architecture.v1.json`.

Do not use this skill for workbook/product behavior unless the sprint explicitly owns that product surface.

## Required inputs

- Current repository/branch/PR state and `AGENTS.md`.
- `harness/CONTEXT.md` plus only the selected harness contract/registry involved.
- Owned/forbidden scope and expected artifact/proof.
- Existing validators/tests for the changed harness component.

Do not load every root harness document by default.

## Outputs

A coherent tracked harness change with:
- one canonical owner for each rule;
- updated map/manifest/registry/validator/test only where ownership requires;
- no duplicated doctrine added to skills or reports;
- passing focused harness/context gates;
- commit/push/PR evidence and bounded proof ceiling.

## Procedure

1. **Route before reading.** Use `harness/CONTEXT.md` to select the affected control-plane surface.
2. **Inspect canonical ownership.** Read the selected registry/contract plus recent overlapping Git/PR evidence. Reuse or repair existing ownership.
3. **Measure the defect.** For context work, record file size/default-load cost and duplication before changing it.
4. **Factor by authority.**
   - `AGENTS.md`: universal governance/precedence only.
   - maps/indexes: routing and ownership only.
   - `SKILL.md`: repeatable procedure/judgment only.
   - code/schema/registry/validator: deterministic behavior/truth.
   - reports: evidence/state only, never current law.
5. **Mutate the minimum connected set.** Update machine/human twins only when the existing contract requires them; do not create parallel authorities.
6. **Validate focused first.** Run the owning validator/tests, then the harness completeness gate and patch hygiene.
7. **Integrate.** Commit coherently, push, open/update PR, resolve exact-head findings, and merge when the repository merge gate authorizes it.

For Prompt Kit release identity, browser proof, acquisition, or layout, follow the dedicated registered contract/skill instead of copying its procedure here.

## Guardrails

- Preserve dirty/unrelated work; never use destructive cleanup to simplify a harness sprint.
- Do not modify product engines merely to satisfy a harness validator.
- Do not weaken required components/proof to get green.
- Do not duplicate a rule across AGENTS/maps/skills/specs. Keep one authority and references.
- Do not force soft token targets to omit correctness/safety context; record justified escalation instead.
- Historical reports are evidence, not configuration.
- A passing harness proves repository structure/contracts, not live operator or production behavior.

## Validation

Context-architecture changes:

```bash
python scripts/validate_context_architecture.py --summary
python -m unittest tests.test_context_architecture tests.test_governance_contract -v
```

Connected harness gates:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
python -m triage.gitignore_hygiene
git diff --check
```

Run additional registered domain gates for every other harness component changed.

## Proof ceiling

These checks prove tracked ownership, progressive-disclosure budgets/routes, registered harness completeness, and tested static behavior on the validated commit. They do not prove external provider, browser, device, protected-network, or production runtime behavior unless that runtime was separately exercised.
