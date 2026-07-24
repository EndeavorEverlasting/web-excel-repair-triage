# Codebase Map

This map is the harness entry point for `EndeavorEverlasting/web-excel-repair-triage`. It focuses on verified governance, Prompt Kit, harness, validation, Neuron Track Hours domain routing, and artifact surfaces rather than enumerating every historical workbook workflow.

## Reading order for a fresh agent

1. `AGENTS.md` — canonical repository governance and safety law.
2. `CODEBASE_MAP.md` — repository navigation and known traps.
3. `WORKFLOW.md` — task pickup, workflow selection, validation, recovery, and handoff.
4. `ARTIFACT_REGISTRY.md` — tracked and runtime artifact contracts.
5. `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md` — reusable procedures, operations, and deterministic routing.
6. `harness/manifest.v1.json` — machine-readable root harness component inventory and validation order.
7. When the task is Neuron Track Hours work, load `harness/nth/manifest.v1.json` and the active month from `harness/nth/monthly-rule-packs.v1.json` before task attribution or workbook packaging.
8. `harness/reports/CURRENT_STATE.md` — operator-readable status, gaps, and proof ceiling.

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
│   ├── manifest.v1.json                   root harness inventory and validation order
│   ├── capabilities.v1.json               machine-readable root capabilities
│   ├── triggers.v1.json                   machine-readable root triggers
│   ├── nth/
│   │   ├── manifest.v1.json               NTH domain harness overlay
│   │   ├── monthly-rule-packs.v1.json     month-specific NTH attribution/delivery rules
│   │   └── triggers.v1.json               NTH internal/client routing
│   ├── evals/
│   │   ├── prompt-language-audit.v1.json  audit policy and result contract
│   │   └── fixtures/prompt-language-cases.v1.json
│   └── reports/CURRENT_STATE.md            operator report
├── scripts/
│   ├── Acquire-LatestPromptKit.ps1        safe technician acquisition GUI
│   ├── build_prompt_kit_registry.py       combined registry builder
│   ├── evaluate_prompt_language.py        exhaustive prompt-language evaluator
│   ├── validate_harness.py                fail-closed root harness validator
│   └── validate_nth_harness.py            fail-closed NTH overlay/rule-pack validator
├── .ai/skills/
│   ├── neuron-track-hours-monthly-artifact/SKILL.md
│   ├── prompt-language-audit/SKILL.md
│   ├── skill-evaluation/SKILL.md
│   ├── skill-factoring/SKILL.md
│   └── technician-prompt-kit-acquisition/SKILL.md
├── .githooks/
│   ├── pre-commit                          focused local harness gates
│   └── pre-push                            exhaustive harness/domain/prompt gates
├── tests/
│   ├── test_governance_contract.py
│   ├── test_harness_contract.py
│   ├── test_nth_harness_contract.py
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
| `scripts/validate_harness.py` | Agent/developer/CI | Validate root maps, workflows, registries, skills, triggers, capabilities, evals, launchers, hooks, and reports. |
| `scripts/validate_nth_harness.py` | Agent/developer/CI | Validate the NTH domain overlay, July rule pack, internal/client mode contract, routing, skill, and human harness surfaces. |
| `triage.*` modules | Developer/operator | Workbook, billing, comparison, and artifact engines documented by focused contracts and tests. |

## Neuron Track Hours domain overlay

Use this overlay whenever the task concerns Neuron Track Hours construction, repair, task distribution, audit, or management delivery.

| Path | Responsibility |
|---|---|
| `harness/nth/manifest.v1.json` | Domain entry point, validation order, and linked harness surfaces. |
| `harness/nth/monthly-rule-packs.v1.json` | Machine-readable month-specific NTH rules. July 2026 includes the 60/40 reasonableness guardrail, weekly correspondence cadence, date/person exceptions, and two-mode delivery contract. |
| `harness/nth/triggers.v1.json` | Routes internal working requests and client send-copy requests. |
| `.ai/skills/neuron-track-hours-monthly-artifact/SKILL.md` | Repeatable NTH construction, attribution, mode-selection, validation, and handoff procedure. |
| `tests/test_nth_harness_contract.py` | Regression contract for month rules and internal/client parity requirements. |

The NTH overlay consumes `AGENTS.md`; it does not replace or modify governance. Internal mode is the construction/audit source. Client mode is a narrowed projection of a validated internal workbook.

## Configuration and registries

| Path | Contract |
|---|---|
| `harness/manifest.v1.json` | Single root machine-readable inventory of required harness components and validation order, including registered domain overlays. |
| `harness/capabilities.v1.json` | Reusable root operation IDs, inputs, outputs, implementations, and proof ceilings. |
| `harness/triggers.v1.json` | Root deterministic conditions and forbidden conditions routing into one capability/skill owner. |
| `harness/nth/manifest.v1.json` | NTH domain overlay inventory and focused validation order. |
| `harness/nth/monthly-rule-packs.v1.json` | NTH month-specific task-distribution and delivery-mode registry. |
| `harness/nth/triggers.v1.json` | NTH domain routing for internal and client modes. |
| `harness/evals/prompt-language-audit.v1.json` | Prompt-language rules, severities, dispositions, and result schema. |
| `configs/prompt_kit/generators.v1.json` | Allowed generators, launchers, defaults, and GUI options. |
| `docs/prompts.json` | Canonical base prompt registry. |
| `registry/prompts/*.json` | Versioned prompt extensions and shared policies. |
| `.github/workflows/*.yml` | Governance, Prompt Kit, harness, documentation, and artifact-engine CI gates. |

## Build and validation commands

Run focused harness and domain checks first:

```powershell
python -m py_compile scripts\validate_harness.py scripts\validate_nth_harness.py scripts\evaluate_prompt_language.py tests\test_harness_contract.py tests\test_nth_harness_contract.py tests\test_prompt_language_audit.py
python scripts\validate_harness.py
python scripts\validate_nth_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_nth_harness_contract -v
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
- For NTH work, do not create hours from device counts, task percentages, or allocation targets; resolve roster/attendance first.
- For NTH work, do not silently carry a prior month's allocation rules into the next month. Load the active rule pack.
- For NTH client delivery, do not hide internal sheets and call the workbook client-safe. Derive a separate client copy and omit internal-only sheets.
- July 2026 client mode is exactly two tabs: `Executive Summary` and `July 2026`.
- Static or CI checks do not prove Excel for Web, Windows GUI, network, credential, provider, model, client, or production acceptance.
- Do not update technician checkouts with reset, clean, force, or overwrite behavior. Acquisition supports clone or clean fast-forward only.
- `README.md` contains historical and current product surfaces; verify focused files, tests, and contracts before relying on older text.
