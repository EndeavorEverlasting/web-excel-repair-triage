# Codebase Map

This map is the harness entry point for `EndeavorEverlasting/web-excel-repair-triage`. It focuses on verified governance, Prompt Kit, harness, validation, and artifact surfaces rather than enumerating every historical workbook workflow.

## Reading order for a fresh agent

1. `AGENTS.md` — canonical repository governance and safety law.
2. `CODEBASE_MAP.md` — repository navigation and known traps.
3. `WORKFLOW.md` — task pickup, workflow selection, validation, recovery, and handoff.
4. `ARTIFACT_REGISTRY.md` — tracked and runtime artifact contracts.
5. `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md` — reusable procedures, operations, and deterministic routing.
6. `harness/manifest.v1.json` — machine-readable harness component inventory and validation order.
7. `harness/reports/CURRENT_STATE.md` — operator-readable status, gaps, and proof ceiling.

## Repository structure

```text
web-excel-repair-triage/
├── AGENTS.md                              governance contract
├── CODEBASE_MAP.md                        this navigation map
├── WORKFLOW.md                            repository workflow specification
├── ARTIFACT_REGISTRY.md                   artifact ownership and generation rules
├── SKILLS.md                              scoped skill index
├── CAPABILITIES.md                        reusable operation index
├── TRIGGERS.md                            deterministic routing index
├── Acquire-Latest-PromptKit.cmd           technician clone/update/open entry point
├── Run-PromptKitGenerator.cmd             generator GUI entry point
├── Build-PromptKitWebsite.cmd             one-click Prompt Kit build
├── build_prompt_kit.py                    canonical HTML renderer
├── configs/prompt_kit/generators.v1.json  bounded generator manifest
├── docs/
│   ├── prompts.json                       base Prompt Kit registry
│   ├── reference.json                     reference-panel data
│   └── prompt-kit.js                      client behavior
├── registry/prompts/
│   ├── skill-development-prompts.v1.json  P61/P62 extension
│   └── actionable-next-step-policy.v1.json
├── harness/
│   ├── manifest.v1.json                   harness inventory and validation order
│   ├── capabilities.v1.json               machine-readable capabilities
│   ├── triggers.v1.json                   machine-readable triggers
│   ├── evals/
│   │   ├── prompt-language-audit.v1.json  audit policy and result contract
│   │   └── fixtures/prompt-language-cases.v1.json
│   └── reports/CURRENT_STATE.md            operator report
├── scripts/
│   ├── Acquire-LatestPromptKit.ps1        safe technician acquisition GUI
│   ├── build_prompt_kit_registry.py       combined registry builder
│   ├── evaluate_prompt_language.py        exhaustive prompt-language evaluator
│   └── validate_harness.py                fail-closed harness validator
├── .ai/skills/
│   ├── prompt-language-audit/SKILL.md
│   ├── skill-evaluation/SKILL.md
│   ├── skill-factoring/SKILL.md
│   └── technician-prompt-kit-acquisition/SKILL.md
├── .githooks/
│   ├── pre-commit                          focused local harness gate
│   └── pre-push                            exhaustive harness and prompt audit gate
├── tests/
│   ├── test_governance_contract.py
│   ├── test_harness_contract.py
│   ├── test_prompt_language_audit.py
│   ├── test_skill_prompt_registry.py
│   └── test_prompt_kit_header_contract.py
├── triage/                                 workbook and artifact engines
├── web/prompt-kit/index.html               checked-in canonical Prompt Kit
├── Candidates/                             protected read-only operator inputs
├── Active/                                 protected read-only golden inputs
└── Outputs/                                gitignored runtime reports and work products
```

## Primary entry points

| Entry point | Audience | Purpose |
|---|---|---|
| `Acquire-Latest-PromptKit.cmd` | Technician | Clone canonical `main` when absent, clean-fast-forward when present, validate, then open the selected surface. |
| `Run-PromptKitGenerator.cmd` | Technician/operator | Open the registered generator-selection GUI. |
| `Build-PromptKitWebsite.cmd` | Technician/operator | Build, validate, and open the default Prompt Kit website. |
| `web/prompt-kit/index.html` | Technician/operator | Canonical checked-in Prompt Kit website. |
| `scripts/build_prompt_kit_registry.py` | Developer/CI | Merge prompt registries, apply shared policies, and render deterministic HTML. |
| `scripts/evaluate_prompt_language.py` | Agent/developer/CI | Evaluate every canonical and effective prompt and emit a machine-readable disposition report. |
| `scripts/validate_harness.py` | Agent/developer/CI | Validate maps, workflows, registries, skills, triggers, capabilities, evals, launchers, hooks, and reports. |
| `triage.*` modules | Developer/operator | Workbook, billing, comparison, and artifact engines documented by focused contracts and tests. |

## Configuration and registries

| Path | Contract |
|---|---|
| `harness/manifest.v1.json` | Single machine-readable inventory of required harness components and validation order. |
| `harness/capabilities.v1.json` | Reusable operation IDs, inputs, outputs, implementations, and proof ceilings. |
| `harness/triggers.v1.json` | Deterministic conditions and forbidden conditions routing into one capability/skill owner. |
| `harness/evals/prompt-language-audit.v1.json` | Prompt-language rules, severities, dispositions, and result schema. |
| `configs/prompt_kit/generators.v1.json` | Allowed generators, launchers, defaults, and GUI options. |
| `docs/prompts.json` | Canonical base prompt registry. |
| `registry/prompts/*.json` | Versioned prompt extensions and shared policies. |
| `.github/workflows/*.yml` | Governance, Prompt Kit, harness, documentation, and artifact-engine CI gates. |

## Build and validation commands

Run focused harness and eval checks first:

```powershell
python -m py_compile scripts\validate_harness.py scripts\evaluate_prompt_language.py tests\test_harness_contract.py tests\test_prompt_language_audit.py
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
```

Validate Prompt Kit source and exact checked-in site:

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

- `Candidates/` and `Active/` are read-only operator-input surfaces. Generated output belongs under `Outputs/` or another focused contract path.
- Do not edit `web/prompt-kit/index.html` as the source. Repair canonical registries, policies, or builders and regenerate deterministically.
- A policy marker alone is not full language proof. The prompt-language audit must cover every canonical and effective prompt with one disposition each.
- Audit mode may report warning-level canonical-source debt while still proving effective prompt safety. Strict mode is the repair completion gate.
- Static or CI checks do not prove Excel for Web, Windows GUI, network, credential, provider, model, or production acceptance.
- Do not update technician checkouts with reset, clean, force, or overwrite behavior. Acquisition supports clone or clean fast-forward only.
- `README.md` contains historical and current product surfaces; verify focused files, tests, and contracts before relying on older text.
