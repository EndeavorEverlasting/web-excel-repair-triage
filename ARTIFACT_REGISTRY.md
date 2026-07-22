# Artifact Registry

This registry defines the repository artifacts that agents, CI, and operators may produce or consume. Machine-readable harness ownership lives in `harness/manifest.v1.json`.

## Tracked control-plane artifacts

| Artifact | Path | Source of truth | Generation or update command | Delivery rule |
|---|---|---|---|---|
| Governance contract | `AGENTS.md` | edited canonical file | `python -m unittest tests.test_governance_contract -v` | Tracked; one canonical authority only. |
| Harness manifest | `harness/manifest.v1.json` | edited JSON | `python scripts/validate_harness.py` | Tracked; update atomically with moved components. |
| Codebase map | `CODEBASE_MAP.md` | edited Markdown | `python scripts/validate_harness.py` | Tracked; describe verified current paths. |
| Workflow specification | `WORKFLOW.md` | edited Markdown | `python scripts/validate_harness.py` | Tracked; repository workflow, not product implementation. |
| Artifact registry | `ARTIFACT_REGISTRY.md` | edited Markdown | `python scripts/validate_harness.py` | Tracked. |
| Skill index | `SKILLS.md` | edited Markdown | `python scripts/validate_harness.py` | Tracked; points to scoped skill files. |
| Scoped skills | `.ai/skills/*/SKILL.md` | edited Markdown | harness and focused skill tests | Tracked; one reusable trigger/procedure boundary per skill. |
| Operator state report | `harness/reports/CURRENT_STATE.md` | edited Markdown | harness validator | Tracked; concise English status and proof ceiling. |
| Prompt registry base | `docs/prompts.json` | edited JSON | `python scripts/build_prompt_kit_registry.py ...` | Tracked canonical base registry. |
| Prompt registry extensions | `registry/prompts/*.json` | edited JSON | combined registry builder and tests | Tracked, versioned, duplicate IDs forbidden. |
| Generator manifest | `configs/prompt_kit/generators.v1.json` | edited JSON | `python -m unittest tests.test_skill_prompt_registry -v` | Tracked; only allow bounded registered generators. |
| Prompt Kit website | `web/prompt-kit/index.html` | deterministic generated HTML | `Build-PromptKitWebsite.cmd` or combined registry builder | Tracked and must exactly match the builder output. |
| Technician acquisition launcher | `Acquire-Latest-PromptKit.cmd` | edited CMD | harness tests and Windows field check | Tracked; may clone or clean-fast-forward only. |
| Technician acquisition GUI | `scripts/Acquire-LatestPromptKit.ps1` | edited PowerShell | harness tests and Windows field check | Tracked; no reset, clean, force, or credential automation. |

## Generated runtime artifacts

| Artifact family | Default location | Naming contract | Tracking policy |
|---|---|---|---|
| Workbook engine outputs | `Outputs/` or focused contract subdirectory | Determined by focused engine contract; prefer stable family name plus timestamp or run ID | Gitignored unless a sanitized fixture or explicitly approved tracked example. |
| Backups before permitted overwrite | `Outputs/backups/` | `<source-stem>_backup_<YYYYMMDD_HHMMSS>.<ext>` | Gitignored runtime evidence. |
| Forensic and comparison reports | `Outputs/` or `artifacts/` as defined by focused contract | Include source family and run ID/date | Gitignored unless sanitized and intentionally documented. |
| Review queues and sidecars | Focused engine output directory | Stable schema name plus run ID/date | Gitignored; may contain internal review context. |
| Test and CI reports | CI logs/artifacts or temporary directories | Workflow/run identifier | Do not commit generated logs. |
| Prompt Kit preview | `Outputs/prompt-kit-preview.html` or a temporary path | `prompt-kit-preview.html` | Do not replace the checked-in site unless exact-output validation passes. |

## Protected inputs

| Path | Rule |
|---|---|
| `Candidates/` | Read-only operator input. Never write, overwrite, rename, or place generated artifacts here. |
| `Active/` | Read-only golden/reference input. Never use as an output destination. |
| Private workbook locations | Do not commit, quote, or copy into tracked evidence. Use sanitized fixtures. |

## Artifact lifecycle

1. **Declare** the artifact family, source, destination, schema/profile, and proof ceiling.
2. **Generate** with a registered script, module, launcher, or workflow.
3. **Validate** package/static/semantic requirements appropriate to the artifact.
4. **Compare** against source or approved baseline when the focused contract requires it.
5. **Deliver** only from the contract-defined output surface.
6. **Record** commit/PR evidence for tracked artifacts or a local path plus checksum for runtime artifacts.
7. **Clean up** only known generated outputs. Never apply broad deletion commands to unknown work.

## Naming rules

- Tracked schemas and manifests: `<domain>.<version>.json`, such as `manifest.v1.json`.
- Scoped skills: `.ai/skills/<kebab-case-skill>/SKILL.md`.
- Operator reports: stable uppercase names under `harness/reports/`; replace current-state content rather than accumulating generated snapshots.
- Runtime outputs: `<family>_<source-or-scope>_<YYYYMMDD_HHMMSS>.<ext>` when a focused contract does not define a stronger convention.
- Backups: `<source-stem>_backup_<YYYYMMDD_HHMMSS>.<ext>`.

## Validation commands

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python -m triage.gitignore_hygiene
git diff --check
```

## Proof boundaries

- File presence and schema checks prove repository integration only.
- Deterministic builder parity proves the tracked site matches current source.
- CI proves only the commands and fixtures run in CI.
- Excel for Web acceptance, Windows GUI usability, network access, credentials, and technician acceptance require separate field proof.
