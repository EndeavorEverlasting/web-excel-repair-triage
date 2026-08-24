# Codebase Map — Web Excel Triage

**Web Excel Triage** owns workbook/web-Excel compatibility tooling plus the Prompt Kit and its operational harness. This file is the **30,000-foot** repository map: use it only after `AGENTS.md` + `harness/CONTEXT.md` route the task here.

## Reading order for a fresh agent

1. Read `AGENTS.md`.
2. Read `harness/CONTEXT.md`.
3. Select one task domain.
4. Read this map only when the router points here.
5. Load one selected workflow/skill/spec and exact implementation evidence as required.

Do **not** preload `WORKFLOW.md`, `CAPABILITIES.md`, `SKILLS.md`, `TRIGGERS.md`, `harness/manifest.v1.json`, all `.ai/skills`, or historical reports. They are routed detail.

## Repository structure

| Area | Purpose | Load when |
|---|---|---|
| `triage/` | workbook repair/compatibility engines and shared Python behavior | workbook/product change |
| `scripts/` | deterministic builders, validators, launchers, operational helpers | selected workflow names one |
| `web/` + `docs/` | Prompt Kit generated/public surfaces and tracked docs/runtime JS | Prompt Kit work |
| `registry/` + `configs/` | canonical prompt/config registries | registry/config change |
| `harness/` | machine-readable contracts, maps, workflows, validators, reports, evals | harness/domain contract work |
| `harness/artifact-handoff/` | alias/download handoff contract that separates canonical artifact identity from human-facing filenames | share/download naming handoff |
| `.ai/skills/` | demand-loaded repeatable procedures/judgment | only after skill selection |
| `tests/` | focused and regression proof | changed surface |
| `Candidates/`, `Active/` | protected operator inputs | read only when domain requires |
| `Outputs/` | generated runtime evidence/artifacts | validator/generator output |

Machine control-plane entry points are `harness/manifest.v1.json`, `harness/workflows.v1.json`, `harness/artifacts.v1.json`, `harness/validators.v1.json`, and the focused path authority `harness/canonical-paths.v1.json`. Focused overlays may additionally own a scoped manifest/registry after `harness/CONTEXT.md` routes the task there.

## Primary entry points

| Need | Canonical entry |
|---|---|
| orient/rout task | `harness/CONTEXT.md` |
| canonical development/use/worktree/entrypoint paths | `harness/canonical-paths.v1.json` + `harness/workflows/canonical-paths.md` |
| workbook repair/analysis | selected `triage/` engine + artifact contract |
| human alias/download handoff | `harness/artifact-handoff/CODEBASE_MAP.md` + `scripts/validate_artifact_handoff_harness.py` |
| Prompt Kit build | `scripts/build_prompt_kit_registry.py` |
| Prompt Kit generator selection | `generator_selection_gui.py` / registered launcher |
| harness integrity | `scripts/validate_harness.py` |
| context architecture | `scripts/validate_context_architecture.py` |
| prompt language | `scripts/evaluate_prompt_language.py` |
| workflow detail | selected anchor in `WORKFLOW.md` or `harness/workflows.v1.json` |
| skill procedure | one selected `.ai/skills/*/SKILL.md` |

## Build, test, and launch commands

Use only the commands owned by the changed surface. Common gates:

```bash
python scripts/validate_context_architecture.py --summary
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_context_architecture tests.test_harness_contract -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Canonical path/profile gate:

```bash
python scripts/validate_canonical_paths.py --summary
python -m unittest tests.test_canonical_paths -v
```

Artifact alias/download handoff uses:

```bash
python scripts/validate_artifact_handoff_harness.py --summary
python -m unittest tests.test_artifact_handoff_harness -v
```

Workbook/product changes require their focused engine tests. Prompt Kit changes require the registered Prompt Kit web/interaction/discovery/portability gates rather than this generic set.

## Public Prompt Kit access

Canonical browser surface:

`https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`

Normal browser users should not clone the repository. Cross-device acquisition is routed through `PROMPT_KIT_ACCESS.md` and the selected technician skill.

## Artifact engine

The artifact engine owns workbook/output generation and validation. Protected inputs stay in `Candidates/`/`Active/`; generated results belong in registered `Outputs/` paths. Resolve outputs through `harness/artifacts.v1.json` or the selected domain contract rather than guessing filenames.

## Copy-safe behavior

Prompt Kit copy behavior is registry-driven. Copy-safe prompt bodies and index/reference-only records have different contracts; do not infer copy permission from display presence. Prompt operations route through `harness/specs/prompt-operations.md`.

## Safety boundaries and known traps

- Never use a broad recursive source hunt as orientation.
- Never edit generated Prompt Kit HTML as canonical source.
- Never overwrite protected operator inputs.
- Never create an actual alias/download file whose basename contains URL escapes such as `%20`; URL encoding is transport metadata, not a filename convention.
- Never make the operator manually rename an alias copy when the agent can materialize the correct literal filename and verify byte identity.
- Never create a second authority because the first is large; factor it and retain one canonical owner.
- Never invent a checkout, install/use, worktree, or entrypoint path from model preference. Resolve `harness/canonical-paths.v1.json`; a second mutable clone is not parallel-writer isolation.
- Never promote `remote main contains SHA` into workstation/deployment proof. Canonical checkout current, production/use path current, and real entrypoint observation are separate gates.
- Historical reports describe evidence, not current law.
- A green CI/build check is not live browser/device/production proof.
- If ownership becomes unclear, return to `harness/CONTEXT.md` instead of loading every document.
