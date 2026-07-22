# Codebase Map

This map is the harness entry point for `EndeavorEverlasting/web-excel-repair-triage`. It is intentionally focused on verified control-plane, Prompt Kit, validation, and artifact surfaces rather than attempting to enumerate every historical workbook workflow.

## Reading order for a fresh agent

1. `AGENTS.md` — canonical repository governance and safety law.
2. `CODEBASE_MAP.md` — current repository navigation.
3. `WORKFLOW.md` — task pickup, validation, failure routing, and handoff.
4. `ARTIFACT_REGISTRY.md` — generated and tracked artifact contracts.
5. `SKILLS.md` and `.ai/skills/` — repeatable scoped procedures.
6. `harness/manifest.v1.json` — machine-readable harness component registry.
7. `harness/reports/CURRENT_STATE.md` — English-language state, gaps, and proof ceiling.

## Repository structure

```text
web-excel-repair-triage/
├── AGENTS.md                         canonical governance contract
├── CODEBASE_MAP.md                   this navigation map
├── WORKFLOW.md                       repository workflow specification
├── ARTIFACT_REGISTRY.md              artifact ownership and generation rules
├── SKILLS.md                         skill index
├── Acquire-Latest-PromptKit.cmd      technician clone/update/open entry point
├── Run-PromptKitGenerator.cmd        generator GUI entry point
├── Build-PromptKitWebsite.cmd        one-click default website build
├── build_prompt_kit.py               canonical HTML renderer
├── configs/
│   └── prompt_kit/generators.v1.json generator and GUI option contract
├── docs/
│   ├── prompts.json                  base Prompt Kit registry
│   ├── reference.json                Prompt Kit reference-panel data
│   ├── prompt-kit.js                 Prompt Kit client behavior
│   └── PROMPT_KIT_GENERATOR_OPERATOR_GUIDE.md
├── harness/
│   ├── manifest.v1.json              required harness components and commands
│   └── reports/CURRENT_STATE.md       operator-readable harness status
├── registry/prompts/
│   └── skill-development-prompts.v1.json
├── scripts/
│   ├── Acquire-LatestPromptKit.ps1   safe technician acquisition GUI
│   ├── build_prompt_kit_registry.py  combined prompt-registry builder
│   └── validate_harness.py           fail-closed harness validator
├── .ai/skills/
│   ├── skill-factoring/SKILL.md
│   └── technician-prompt-kit-acquisition/SKILL.md
├── .githooks/pre-commit              optional focused harness hook
├── tests/
│   ├── test_governance_contract.py
│   ├── test_harness_contract.py
│   ├── test_prompt_kit_header_contract.py
│   └── test_skill_prompt_registry.py
├── triage/                            workbook and artifact engines
├── web/prompt-kit/index.html          checked-in technician website
├── Candidates/                        protected read-only operator inputs
├── Active/                            protected read-only golden inputs
└── Outputs/                           generated reports and work products
```

## Primary entry points

| Entry point | Audience | Purpose |
|---|---|---|
| `Acquire-Latest-PromptKit.cmd` | Technician | Clone the canonical repo when absent, fast-forward clean `main` when present, validate, then open the selected surface. |
| `Run-PromptKitGenerator.cmd` | Technician/operator | Open the tracked generator selection GUI. |
| `Build-PromptKitWebsite.cmd` | Technician/operator | Build, validate, and open the default Prompt Kit website without choices. |
| `web/prompt-kit/index.html` | Technician/operator | Open the checked-in current Prompt Kit directly. |
| `scripts/build_prompt_kit_registry.py` | Developer/CI | Merge base and extension prompt registries and render deterministic HTML. |
| `scripts/validate_harness.py` | Agent/developer/CI | Validate harness files, manifests, skills, launchers, hooks, and safety contracts. |
| `triage.*` modules | Developer/operator | Workbook, billing, comparison, and artifact engines documented in `README.md` and focused contract docs. |

## Configuration and registries

| Path | Contract |
|---|---|
| `harness/manifest.v1.json` | Single machine-readable inventory of harness components, acquisition requirements, and validation order. |
| `configs/prompt_kit/generators.v1.json` | Allowed generators, direct launchers, defaults, and GUI options. |
| `docs/prompts.json` | Canonical base prompt registry. |
| `registry/prompts/skill-development-prompts.v1.json` | Versioned prompt extension containing skill factoring and skill eval prompts. |
| `docs/reference.json` | Prompt Kit reference data. |
| `.github/workflows/*.yml` | Governance, Prompt Kit, harness, and artifact-engine CI gates. |

## Build and validation commands

Run focused harness checks first:

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
```

Validate Prompt Kit registry and exact checked-in site:

```powershell
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

Run repository hygiene and broader tests last:

```powershell
python -m triage.gitignore_hygiene
python -m pytest

git diff --check
```

## Safety boundaries and known traps

- `Candidates/` and `Active/` are read-only operator-input surfaces. Generated output belongs under `Outputs/` unless a focused contract explicitly defines another safe tracked artifact.
- Do not infer that a passing static or CI check proves Excel for Web, Windows GUI, network, credential, or production acceptance.
- Do not update an existing technician checkout with reset, clean, forced branch changes, or overwrite behavior. The acquisition launcher permits clone or clean fast-forward only.
- `README.md` covers many product engines and may retain historical sections; verify current files, tests, and focused contracts before acting on an older section.
- The checked-in Prompt Kit site must remain byte-identical to the combined-registry builder output.
