# Codebase Map

This is the operational entry point for `EndeavorEverlasting/web-excel-repair-triage`. It tells a fresh agent where repository law, workflow selection, artifact ownership, validators, product engines, launchers, cross-device Prompt Kit access contracts, command-delivery contracts, and proof reports live.

## Reading order for a fresh agent

1. `AGENTS.md` — governance and safety authority.
2. `CODEBASE_MAP.md` — repository navigation, entry points, commands, and traps.
3. `WORKFLOW.md` and `harness/workflows.v1.json` — select the correct workflow and failure route.
4. `ARTIFACT_REGISTRY.md` and `harness/artifacts.v1.json` — resolve canonical tracked/runtime artifacts and registered delivery surfaces.
5. `harness/validators.v1.json` plus registered `harness/manifest.v1.json` domain contracts — select the correct root profile and focused contract gate.
6. `SKILLS.md`, `CAPABILITIES.md`, `TRIGGERS.md`, and their machine registries — route reusable procedures.
7. `harness/manifest.v1.json` — complete component inventory, domain contracts, and validation order.
8. `harness/reports/CURRENT_STATE.md` — human-readable working, broken, missing, and proof-ceiling state.

## Repository structure

```text
web-excel-repair-triage/
├── AGENTS.md                              governance contract; P00-owned
├── CODEBASE_MAP.md                        repository map and commands
├── WORKFLOW.md                            human workflow specifications
├── ARTIFACT_REGISTRY.md                   human artifact and delivery registry
├── SKILLS.md                              scoped skill index
├── CAPABILITIES.md                        reusable operation index
├── TRIGGERS.md                            deterministic routing index
├── PROMPT_KIT_ACCESS.md                   canonical Prompt Kit access guide
├── OPEN_PROMPT_KIT_ON_PHONE.md            Android/mobile access guide
├── harness/
│   ├── manifest.v1.json                   complete harness component/domain-contract inventory
│   ├── workflows.v1.json                  machine-readable workflow registry
│   ├── artifacts.v1.json                  machine-readable artifact/delivery registry
│   ├── validators.v1.json                 validator profiles and hook ownership
│   ├── capabilities.v1.json               machine-readable capabilities
│   ├── triggers.v1.json                   machine-readable triggers
│   ├── contracts/
│   │   ├── prompt-kit-cross-device-access.v1.json  use/install/edit acquisition routing
│   │   └── operator-command-envelope.v1.json       copy-safe operator handoff contract
│   ├── evals/                             eval policies and fixtures
│   ├── templates/
│   │   └── Invoke-RemoteHarnessProof.ps1  isolated remote-proof command template
│   └── reports/CURRENT_STATE.md            operator-readable current state
├── scripts/
│   ├── validate_harness.py                fail-closed completeness validator/report writer
│   ├── validate_prompt_kit_cross_device_access.py device-aware acquisition contract
│   ├── validate_operator_command_envelope.py command-delivery validator
│   ├── evaluate_prompt_language.py        exhaustive prompt-language evaluator
│   ├── validate_prompt_kit_interactions.py interaction contract audit
│   ├── validate_prompt_kit_discovery.py   prompt discovery contract audit
│   ├── build_prompt_kit_registry.py       canonical Prompt Kit registry builder
│   └── Acquire-LatestPromptKit.ps1        safe Windows acquisition/update GUI
├── .ai/skills/
│   ├── harness-infrastructure-maintenance/SKILL.md
│   ├── prompt-language-audit/SKILL.md
│   ├── skill-evaluation/SKILL.md
│   ├── skill-factoring/SKILL.md
│   └── technician-prompt-kit-acquisition/SKILL.md
├── .githooks/
│   ├── pre-commit                         staged-index harness + focused access gates
│   └── pre-push                           exhaustive non-destructive harness profile
├── .github/workflows/
│   ├── harness-contract.yml               harness completeness + focused contracts
│   ├── artifact-engines.yml               broader artifact-engine checks
│   ├── governance-contract.yml            AGENTS.md governance tests
│   └── other focused workflows            product and report lanes
├── tests/
│   ├── test_harness_contract.py
│   ├── test_prompt_kit_cross_device_access.py
│   ├── test_operator_command_envelope.py
│   ├── test_prompt_kit_interactions_contract.py
│   ├── test_prompt_kit_discovery.py
│   ├── test_prompt_language_audit.py
│   ├── test_skill_prompt_registry.py
│   └── focused product/engine tests
├── triage/                                 workbook, billing, comparison, and artifact engines
├── docs/                                   base Prompt Kit data and browser behavior sources
├── registry/prompts/                       versioned prompt extensions and policies
├── configs/                                generator and artifact configuration
├── web/prompt-kit/index.html               checked-in canonical Prompt Kit
├── Acquire-Latest-PromptKit.cmd            advanced Windows acquisition entry point
├── Open-Latest-PromptKit.cmd               Windows stable-origin Prompt Kit entry point
├── Run-PromptKitGenerator.cmd              generator-selection GUI entry point
├── Build-PromptKitWebsite.cmd              build/validate/open entry point
├── app.py                                  Streamlit application entry point
├── mcp_server.py                           MCP server entry point
├── Candidates/                             protected read-only operator inputs
├── Active/                                 protected read-only golden inputs
└── Outputs/                                gitignored reports, backups, and work products
```

## Key directories and purposes

| Path | Purpose | Mutation rule |
|---|---|---|
| `harness/` | Operational ownership, workflow, artifact, validator, capability, trigger, contract, eval, template, and report data. | Harness lane only; update connected files atomically. |
| `harness/contracts/` | Focused versioned rules such as Prompt Kit cross-device access and operator command delivery. | Contract + validator + tests + registries must stay connected. |
| `harness/templates/` | Repository-owned transport templates for safe operator proof and handoff commands. | Must remain environment-derived, copy-safe, non-destructive, and validator-backed. |
| `.ai/skills/` | Repeatable procedures and judgment boundaries. | Do not hide deterministic application behavior only in prose. |
| `scripts/` | Validators, builders, audit runners, launch support, and utilities. | Add regression tests for behavior changes. |
| `tests/` | Contract, regression, integration, and artifact tests. | Do not weaken expectations to obtain green CI. |
| `triage/` | Workbook and artifact engines. | Product/engine lane; outside a harness-only sprint. |
| `docs/` and `registry/prompts/` | Canonical Prompt Kit sources and shared prompt policies. | Change source, then regenerate; never patch HTML alone. |
| `web/prompt-kit/` | Checked-in generated Prompt Kit. | Builder-owned deterministic output. |
| `Candidates/` and `Active/` | Operator inputs and golden references. | Read-only. |
| `Outputs/` | Runtime reports, backups, previews, and generated work. | Gitignored; resolve paths through the artifact registry. |

## Primary entry points

| Entry point | Audience | Purpose |
|---|---|---|
| `scripts/validate_harness.py` | Agent/developer/CI | Validate every registered harness component and optionally write `harness-completeness-report/v1`. |
| `scripts/validate_prompt_kit_cross_device_access.py` | Agent/developer/CI | Enforce intent-first Prompt Kit access: direct public use/install versus Windows local app versus editable Git checkout versus ZIP snapshot. |
| `scripts/validate_operator_command_envelope.py` | Agent/developer/CI | Reject hard-coded user paths, Markdown-mangled URLs, terminal-closing `exit`, pre-gate Git, unpinned remote work, destructive dirty-work handling, guessed artifacts, and ignored native failures. |
| `harness/templates/Invoke-RemoteHarnessProof.ps1` | Agent/operator | Perform an isolated environment-derived checkout of an exact remote branch/commit, validate it, resolve `harness-completeness-report` from the artifact registry, and print it without assuming a user profile path. |
| `harness/validators.v1.json` | Agent/tooling | Resolve ordered root validator profiles for harness, pre-commit, and pre-push use. |
| `harness/manifest.v1.json` | Agent/tooling | Resolve focused domain gates such as cross-device access and operator command envelope. |
| Public Prompt Kit URL | Browser user | Open the canonical Prompt Kit directly without cloning. |
| Public phone launcher | Phone/tablet user | Install/share/open the same canonical Prompt Kit through browser-native surfaces. |
| `Open-Latest-PromptKit.cmd` | Windows user | Open the validated stable-origin local app with portable Favorites behavior. |
| `Acquire-Latest-PromptKit.cmd` | Technician | Advanced clone or clean-fast-forward acquisition and selected launch surface. |
| `Run-PromptKitGenerator.cmd` | Technician/operator | Open the registered generator GUI. |
| `Build-PromptKitWebsite.cmd` | Technician/operator | Build, validate, and open the Prompt Kit website. |
| `web/prompt-kit/index.html` | Technician/operator | Canonical checked-in Prompt Kit website artifact. |
| `app.py` | Operator/developer | Launch the Streamlit repair-triage application. |
| `mcp_server.py` | MCP client/developer | Expose triage operations through MCP. |

## Configuration and registry files

| Path | Contract |
|---|---|
| `harness/manifest.v1.json` | Complete harness component inventory, registered domain contracts, and ordered full validation commands. |
| `harness/workflows.v1.json` | Workflow IDs, triggers, scope, entry points, validation profiles, failure handling, and handoff fields. |
| `harness/artifacts.v1.json` | Canonical artifact paths, producers, validators, delivery surfaces, naming, tracking, and proof ceilings. |
| `harness/validators.v1.json` | Root validator commands, outputs, profiles, and hook bindings. |
| `harness/contracts/prompt-kit-cross-device-access.v1.json` | Machine policy for choosing public use/install, Windows local-app, editable-checkout, or ZIP routes. |
| `harness/contracts/operator-command-envelope.v1.json` | Machine policy for copy-safe, path-safe, terminal-preserving next commands. |
| `harness/capabilities.v1.json` | Reusable operation IDs, skills, triggers, inputs, outputs, implementations, and proof ceilings. |
| `harness/triggers.v1.json` | Deterministic route and forbidden-condition ownership. |
| `configs/prompt_kit/generators.v1.json` | Allowed Prompt Kit generators and launchers. |
| `docs/prompts.json` | Canonical base prompt registry. |
| `registry/prompts/*.json` | Versioned prompt extensions and shared policies. |
| `.github/workflows/*.yml` | CI gates for governance, harness, artifacts, reports, and product lanes. |

## Build, test, and launch commands

Focused cross-device Prompt Kit acquisition validation:

```bash
python -m py_compile scripts/validate_prompt_kit_cross_device_access.py tests/test_prompt_kit_cross_device_access.py
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
```

Focused operator-command validation:

```bash
python -m py_compile scripts/validate_operator_command_envelope.py tests/test_operator_command_envelope.py
python scripts/validate_operator_command_envelope.py --summary
python -m unittest tests.test_operator_command_envelope -v
```

Focused harness validation:

```bash
python -m py_compile scripts/validate_harness.py tests/test_harness_contract.py
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
```

Connected Prompt Kit contract and parity validation:

```bash
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts/validate_prompt_kit_interactions.py --output Outputs/prompt-kit-interaction-audit.json --summary
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery -v
python -m unittest tests.test_prompt_language_audit -v
python scripts/evaluate_prompt_language.py --output Outputs/prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests/test_prompt_kit_header_contract.py
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

Broader checks:

```bash
python -m triage.gitignore_hygiene
python -m pytest
git diff --check
```

Launch surfaces:

```bash
python -m streamlit run app.py
python mcp_server.py
```

Windows technician launchers:

```text
Open-Latest-PromptKit.cmd
Acquire-Latest-PromptKit.cmd
Run-PromptKitGenerator.cmd
Build-PromptKitWebsite.cmd
```

## Safety boundaries and known traps

- `AGENTS.md` is governance authority and is outside a harness-infrastructure sprint unless P00 explicitly owns it.
- `Candidates/` and `Active/` are protected read-only inputs. Generated output belongs under `Outputs/` or another registered path.
- **Do not make normal Prompt Kit use harder than the product requires.** Browser use goes to the public Prompt Kit and phone/tablet install goes to the public launcher. A Git checkout is appropriate only for edit/commit/push/source/tooling intent.
- **Do not tell a phone user to hunt for `web/prompt-kit/index.html` in the GitHub app.** For Android source work, use Termux from F-Droid and Git; for normal use, stay in the browser path.
- **Never place a remembered or guessed `C:\Users\<name>\...` path in an operator NEXT COMMAND.** A path from another machine, account, or prior chat is not repository evidence. If the current shell has not proven the repository root, use the isolated environment-derived proof template instead.
- **Never rely on a raw URL surviving chat rendering inside pasteable PowerShell.** Markdown syntax such as `[http://host/](http://host/)` is invalid command data. Prefer repository slugs, tracked values, or split non-linkable URL fragments in transport commands.
- **Never use top-level `exit` in an interactive pasteable PowerShell envelope.** It can close the terminal and destroy visible evidence. Convert failures to `throw` inside a script/scriptblock and preserve the operator shell.
- Git fetch/status operations must occur only after repository/directory gating. Unmerged remote work must be pinned to the exact expected commit and exercised in an isolated checkout/worktree.
- A next command must resolve the canonical artifact from `harness/artifacts.v1.json`; do not guess a report, website, workbook, or `index.html` path.
- Pre-commit must validate the staged index through an isolated staged tree; validating the ordinary working tree can miss the actual commit or fail on unrelated unstaged work.
- Update human indexes and machine registries together. A new file is not integrated until the manifest, validator, tests, hooks/CI, and operator report recognize it.
- Do not edit `web/prompt-kit/index.html` as the source. Repair canonical registries, policies, or builders and regenerate deterministically.
- Do not turn a known product gap into a passing harness check by weakening a contract, fixture, strict mode, or proof ceiling.
- Hooks are tracked but must be enabled per checkout with `git config core.hooksPath .githooks`.
- Static and CI proof do not prove Excel for Web, native Windows GUI, browser installation, mobile menus, Termux/F-Droid availability, clipboard permissions, local storage, provider/model behavior, credentials, network, technician acceptance, protected targets, deployment, or production success.
