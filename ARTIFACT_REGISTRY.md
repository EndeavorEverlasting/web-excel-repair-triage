# Artifact Registry

This registry defines repository artifacts that agents, CI, and operators may produce or consume. The machine-readable root authority is `harness/artifacts.v1.json`; domain-specific artifact ownership may also be declared by a registered contract in `harness/manifest.v1.json`. Validator ownership lives in `harness/validators.v1.json`.

## Tracked control-plane artifacts

| Artifact | Canonical path | Source of truth | Validation or generation | Delivery rule |
|---|---|---|---|---|
| Governance contract | `AGENTS.md` | P00-owned canonical file | governance tests | One authority; outside harness-infrastructure scope. |
| Codebase map | `CODEBASE_MAP.md` | edited Markdown | `harness-completeness` | Tracked; paths and commands must be current. |
| Workflow specification | `WORKFLOW.md` | edited Markdown | `harness-completeness` | Tracked human workflow source. |
| Workflow registry | `harness/workflows.v1.json` | edited versioned JSON | `harness-completeness` and contract tests | Machine-readable triggers, scope, failure, validation, and handoff ownership. |
| Artifact registry | `ARTIFACT_REGISTRY.md` | edited Markdown | `harness-completeness` | Human-readable artifact contract. |
| Machine artifact registry | `harness/artifacts.v1.json` | edited versioned JSON | `harness-completeness` and contract tests | Root artifact families, canonical paths, producers, validators, naming, tracking, and proof ceilings. |
| Validator registry | `harness/validators.v1.json` | edited versioned JSON | `harness-completeness` and contract tests | Root validator commands, outputs, profiles, and hook bindings. |
| Skill index | `SKILLS.md` | edited Markdown | harness validator | Indexes every active skill. |
| Capability index | `CAPABILITIES.md` | edited Markdown | harness validator | Mirrors the capability registry. |
| Trigger index | `TRIGGERS.md` | edited Markdown | harness validator | Mirrors the trigger registry. |
| Harness manifest | `harness/manifest.v1.json` | edited JSON | `python scripts/validate_harness.py` | Complete component inventory, registered domain contracts, and root validation order; update atomically. |
| Capability registry | `harness/capabilities.v1.json` | edited JSON | harness validator/tests | Unique IDs, inputs, outputs, implementation, skill, triggers, and proof ceiling. |
| Trigger registry | `harness/triggers.v1.json` | edited JSON | harness validator/tests | Deterministic conditions and forbidden conditions with one capability/skill owner. |
| Scoped skills | `.ai/skills/*/SKILL.md` | edited Markdown | harness validator/tests | Repeatable procedures; deterministic behavior remains in code/contracts. |
| Operator report | `harness/reports/CURRENT_STATE.md` | edited Markdown | harness validator | Current working, broken, missing, validation, and proof state. |
| Prompt Kit interaction contract | `harness/contracts/prompt-kit-interactions.v1.json` | edited versioned JSON | focused tests and audit | Harness owns the requirement; product lane owns implementation. |
| Prompt Kit discovery contract | `harness/contracts/prompt-kit-discovery.v1.json` | edited versioned JSON | focused tests and audit | Tracked discovery requirement and proof boundary. |
| Prompt Kit portability contract | `harness/contracts/prompt-kit-portability.v1.json` | edited versioned JSON | portability validator/tests | Stable-origin Favorites persistence, transfer schema, artifact rules, connected-GitHub fallback, and sequential prompt routing. |
| Prompt-language policy and fixtures | `harness/evals/**` | edited versioned JSON | prompt-language tests/evaluator | Rules, severities, fixtures, and result contract. |
| Prompt Kit website | `web/prompt-kit/index.html` | deterministic builder output | `prompt-kit-parity` | Tracked canonical source artifact; change canonical sources and rebuild. Runtime portability injection must not modify it. |
| Prompt Kit portable runtime source | `docs/prompt-kit-favorites-portability.js` | edited JavaScript | Node syntax plus portability tests | Tracked Export/Import behavior; injected only into the generated runtime artifact. |
| Prompt Kit portable generator/server | `scripts/serve_prompt_kit_portable.py` | edited Python | portability tests and validator | Generates a hash-receipted artifact and serves it from loopback only. |
| Technician acquisition surfaces | `Acquire-Latest-PromptKit.cmd`, `scripts/Acquire-LatestPromptKit.ps1` | edited code | harness tests plus native Windows proof | Preservation-first clone/fast-forward/validate behavior. |
| Portable quick-open surfaces | `Open-Latest-PromptKit.cmd`, `scripts/Open-LatestPromptKitPortable.ps1` | edited code | portability tests plus native Windows proof | Reuse acquisition helpers, generate/validate the runtime artifact, open the stable origin. |
| Hooks | `.githooks/pre-commit`, `.githooks/pre-push` | edited shell | harness validator/tests | Optional per-worktree local gates. |

## Generated runtime artifacts

| Artifact family | Canonical location | Generation | Naming contract | Tracking policy |
|---|---|---|---|---|
| Harness completeness report | `Outputs/harness-completeness-report.json` | `python scripts/validate_harness.py --report Outputs/harness-completeness-report.json` | schema `harness-completeness-report/v1`; stable family name | Gitignored or CI artifact. |
| Prompt Kit interaction audit | `Outputs/prompt-kit-interaction-audit.json` | focused interaction validator | stable result schema and family name | Gitignored or CI artifact. |
| Prompt Kit portable site | `Outputs/prompt-kit-portable/index.html` | `python scripts/serve_prompt_kit_portable.py --build-only` | exact tracked site plus tracked portability runtime | Gitignored; CI artifact name `prompt-kit-portable-runtime`. |
| Prompt Kit portable receipt | `Outputs/prompt-kit-portable/manifest.json` | portable builder/server | schema `prompt-kit-portable-artifact/v1`; source/runtime/artifact SHA-256 | Gitignored or CI artifact. |
| Prompt Kit portability validation | `Outputs/prompt-kit-portability-validation.json` | portability validator with `--require-artifact` | schema `prompt-kit-portability-validation-result/v1` | Gitignored or CI artifact. |
| Prompt-language audit | `Outputs/prompt-language-audit.json` | exhaustive evaluator | stable result schema and family name | Gitignored or CI artifact. |
| Strict prompt-language repair audit | `Outputs/prompt-language-audit-strict.json` | evaluator `--strict` | strict flag plus one disposition per prompt | Gitignored. |
| Skill eval results | target repository approved output path | target eval runner | stable skill ID/version/run ID | Gitignored unless sanitized baseline. |
| Workbook/artifact engine outputs | `Outputs/` or focused contract path | focused `triage` engine/launcher/workflow | family plus run ID/timestamp unless contract defines more | Gitignored unless sanitized and approved. |
| Backups before permitted overwrite | `Outputs/backups/` | owning generator/workflow | `<source-stem>_backup_<YYYYMMDD_HHMMSS>.<ext>` | Gitignored. |
| CI reports and logs | CI artifact storage or runner temp | workflow job | workflow/run identifier | Never commit generated logs. |
| Prompt Kit preview | `Outputs/prompt-kit-preview.html` or temp | builder preview mode | stable preview name | Never replace canonical site without parity. |

## Protected inputs

| Path | Rule |
|---|---|
| `Candidates/` | Read-only operator input. Never write, overwrite, rename, or generate here. |
| `Active/` | Read-only golden/reference input. Never use as output. |
| Private workbook locations | Never commit, quote, or copy into tracked evidence; use sanitized fixtures. |
| Credentials and tokens | Never embed, log, upload, or place in artifact manifests. |

## Artifact lifecycle

1. Resolve the artifact ID from `harness/artifacts.v1.json` or the registered domain contract in `harness/manifest.v1.json`; do not guess from a generic filename.
2. Declare artifact owner, source, destination, schema/profile, validator, and proof ceiling.
3. Generate through the registered script, module, launcher, workflow, or CI job.
4. Validate structural, semantic, parity, safety, and path requirements appropriate to the artifact.
5. Deliver only from the registry-defined canonical path or CI artifact.
6. Record commit/PR evidence for tracked artifacts and path/checksum/run ID for runtime artifacts.
7. Clean only known generated outputs; never apply broad deletion to unknown work.

## Naming conventions

- Versioned registries/contracts: `<domain>.v<major>.json` or an existing stable versioned family.
- Scoped skills: `.ai/skills/<kebab-case-skill>/SKILL.md`.
- Operator reports: stable uppercase names under `harness/reports/`.
- Runtime reports: stable artifact family plus run ID when simultaneous runs must coexist.
- Backups: `<source-stem>_backup_<YYYYMMDD_HHMMSS>.<ext>`.
- Generated product artifacts: use the focused contract or manifest; do not infer “latest” from modification time alone.

## Generation and validation commands

Harness report:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

Portable Prompt Kit artifact and receipt:

```bash
python scripts/serve_prompt_kit_portable.py --build-only
python scripts/validate_prompt_kit_portability.py --require-artifact --output Outputs/prompt-kit-portability-validation.json --summary
python -m unittest tests.test_prompt_kit_portability -v
```

Full root harness profile:

```bash
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts/validate_prompt_kit_interactions.py --output Outputs/prompt-kit-interaction-audit.json --summary
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery -v
python -m unittest tests.test_prompt_language_audit -v
python scripts/evaluate_prompt_language.py --output Outputs/prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests/test_prompt_kit_header_contract.py
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

## Proof boundaries

File and registry presence prove repository integration only. A harness completeness report proves the registered static checks executed on one checkout and commit. Deterministic canonical builder parity proves source-to-generated identity, not browser acceptance. A portable artifact receipt proves exact source/runtime composition and hashes on one execution; loopback launch, browser storage persistence, Export/Import dialogs, browser-profile transfer, and cross-device acceptance remain separate observed gates. Interaction/discovery audits prove only their documented static surfaces. Prompt-language audit proves canonical/effective coverage and findings, not provider obedience. CI proves only the commands and fixtures exercised by that workflow. Excel for Web, native Windows GUI, browser events, clipboard/focus behavior, credentials, network, protected targets, technician acceptance, deployment, and production success require separate observed proof.
