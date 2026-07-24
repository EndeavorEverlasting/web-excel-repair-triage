# Artifact Registry

This registry defines repository artifacts that agents, CI, and operators may produce or consume. Machine-readable harness ownership lives in `harness/manifest.v1.json` and `harness/capabilities.v1.json`.

## Tracked control-plane artifacts

| Artifact | Path | Source of truth | Validation or generation | Delivery rule |
|---|---|---|---|---|
| Governance contract | `AGENTS.md` | edited canonical file | governance tests | Tracked; one authority. |
| Codebase map | `CODEBASE_MAP.md` | edited Markdown | harness validator | Tracked; verified current paths. |
| Workflow specification | `WORKFLOW.md` | edited Markdown | harness validator | Tracked; repository operating flow. |
| Artifact registry | `ARTIFACT_REGISTRY.md` | edited Markdown | harness validator | Tracked. |
| Skill index | `SKILLS.md` | edited Markdown | harness validator | Tracked; indexes every active skill. |
| Capability index | `CAPABILITIES.md` | edited Markdown | harness validator | Tracked; mirrors capability registry. |
| Trigger index | `TRIGGERS.md` | edited Markdown | harness validator | Tracked; mirrors trigger registry. |
| Harness manifest | `harness/manifest.v1.json` | edited JSON | `python scripts/validate_harness.py` | Tracked; update atomically. |
| Capability registry | `harness/capabilities.v1.json` | edited JSON | harness validator/tests | Tracked; unique IDs and implementations. |
| Trigger registry | `harness/triggers.v1.json` | edited JSON | harness validator/tests | Tracked; one capability/skill owner per trigger. |
| Prompt-language policy | `harness/evals/prompt-language-audit.v1.json` | edited JSON | prompt-language tests | Tracked; rules, severities, dispositions, result schema. |
| Prompt-language fixtures | `harness/evals/fixtures/prompt-language-cases.v1.json` | edited JSON | `tests.test_prompt_language_audit` | Tracked positive/negative/mutation examples. |
| Scoped skills | `.ai/skills/*/SKILL.md` | edited Markdown | harness validator and focused tests | Tracked; one reusable boundary each. |
| Operator report | `harness/reports/CURRENT_STATE.md` | edited Markdown | harness validator | Tracked current status, gaps, and proof ceiling. |
| Prompt registries/policies | `docs/prompts.json`, `registry/prompts/*.json` | edited JSON | registry builder/tests/audit | Tracked canonical prompt sources. |
| Prompt Kit website | `web/prompt-kit/index.html` | deterministic generated HTML | combined builder `--check` | Tracked and exact-parity required. |
| Technician acquisition surfaces | `Acquire-Latest-PromptKit.cmd`, `scripts/Acquire-LatestPromptKit.ps1` | edited code | harness tests plus Windows field proof | Tracked; preservation-first. |
| Hooks | `.githooks/pre-commit`, `.githooks/pre-push` | edited shell | harness validator | Optional per-worktree local gates. |

## Generated runtime artifacts

| Artifact family | Default location | Naming contract | Tracking policy |
|---|---|---|---|
| Prompt-language audit report | `Outputs/prompt-language-audit.json` or CI artifact storage | stable result schema `prompt-language-audit-result/v1` | Gitignored runtime evidence; upload from CI when useful. |
| Strict prompt-language repair report | `Outputs/prompt-language-audit-strict.json` | include strict flag and per-prompt dispositions | Gitignored. |
| Skill eval results | Target repository approved output path | stable skill ID/version/run ID | Gitignored unless a sanitized fixture or approved baseline. |
| Workbook engine outputs | `Outputs/` or focused contract directory | focused contract; otherwise family + run ID/timestamp | Gitignored unless sanitized and approved. |
| Backups before permitted overwrite | `Outputs/backups/` | `<source-stem>_backup_<YYYYMMDD_HHMMSS>.<ext>` | Gitignored. |
| Test and CI reports | CI logs/artifacts or temp directories | workflow/run identifier | Do not commit generated logs. |
| Prompt Kit preview | `Outputs/prompt-kit-preview.html` or temp | `prompt-kit-preview.html` | Never replace canonical site without exact parity. |

## Protected inputs

| Path | Rule |
|---|---|
| `Candidates/` | Read-only operator input. Never write, overwrite, rename, or generate here. |
| `Active/` | Read-only golden/reference input. Never use as output. |
| Private workbook locations | Never commit, quote, or copy into tracked evidence; use sanitized fixtures. |

## Artifact lifecycle

1. Declare artifact family, owner capability, source, destination, schema/profile, and proof ceiling.
2. Generate through a registered script, module, launcher, prompt workflow, or CI job.
3. Validate structural, semantic, parity, and safety requirements appropriate to the artifact.
4. Deliver only from the contract-defined path.
5. Record commit/PR evidence for tracked artifacts or path/checksum/run ID for runtime artifacts.
6. Clean only known generated outputs; never apply broad deletion to unknown work.

## Naming rules

- Tracked schemas/manifests: `<domain>.<version>.json`.
- Scoped skills: `.ai/skills/<kebab-case-skill>/SKILL.md`.
- Operator reports: stable uppercase names under `harness/reports/`.
- Runtime reports: stable family name plus skill/source and run ID when needed.
- Backups: `<source-stem>_backup_<YYYYMMDD_HHMMSS>.<ext>`.

## Validation commands

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python -m triage.gitignore_hygiene
git diff --check
```

## Proof boundaries

File/schema presence proves repository integration only. Exhaustive prompt-language audit proves static canonical/effective coverage and findings, not provider obedience. Deterministic builder parity proves tracked-site identity, not browser acceptance. CI proves only exercised commands and fixtures. Excel for Web, Windows GUI, credentials, network, model/provider behavior, protected targets, and production acceptance require separate observed proof.
