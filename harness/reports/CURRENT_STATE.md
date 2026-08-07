# Harness Current State

**As of:** 2026-08-07
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Canonical branch:** `main`
**Harness workflow:** `harness-infrastructure`
**Harness capability:** `harness-infrastructure-maintenance`

## Status

The repository has a connected operational harness for fresh-agent entry, workflow selection, artifact resolution, validator selection, scoped skills, deterministic triggers, staged-index and pre-push hooks, CI reporting, technician acquisition, Prompt Kit contracts, prompt-language auditing, operator-command delivery, and handoff.

The harness has separate machine-readable workflow, artifact, validator, capability, trigger, and focused domain-contract registries. `harness/manifest.v1.json` is the component/domain-contract inventory; `scripts/validate_harness.py` is the fail-closed completeness validator and writes `harness-completeness-report/v1`.

The operator-command envelope closes a reproduced failure class where an unverified remembered Windows path caused `Set-Location` to fail, a subsequent Git command ran outside a repository, a raw localhost URL arrived as Markdown hyperlink syntax, and top-level `exit` could terminate the interactive shell. Those shapes are now fixture-backed failures rather than documentation-only warnings.

## Working surfaces

- `CODEBASE_MAP.md` provides structure, directories, entry points, configuration, commands, and known traps.
- `WORKFLOW.md` and `harness/workflows.v1.json` define pickup, workflow selection, validation, failure handling, commit/PR behavior, and handoff.
- `ARTIFACT_REGISTRY.md` and `harness/artifacts.v1.json` define tracked/runtime artifacts, producers, validators, canonical paths, protected paths, naming, tracking, and proof ceilings.
- `harness/validators.v1.json` defines the root harness, pre-commit, and pre-push validator profiles.
- `harness/manifest.v1.json` additionally registers focused domain gates, including `operator_command_envelope`.
- `harness/contracts/operator-command-envelope.v1.json` defines eight fail-closed operator-command rules: person-specific path, Markdown link data, interactive `exit`, Git before directory gate, unpinned remote work, destructive dirty-work handling, guessed artifact, and ignored native failure.
- `harness/evals/fixtures/operator-command-cases.v1.json` contains positive and mutation fixtures for those rules.
- `harness/templates/Invoke-RemoteHarnessProof.ps1` provides a repository-owned unmerged-harness proof path that uses `LOCALAPPDATA`/`TEMP`, an isolated checkout, exact branch/commit verification, the owning validators, artifact-registry resolution, and `throw` rather than terminal-closing `exit`.
- `scripts/validate_operator_command_envelope.py` validates the contract, fixtures, and canonical PowerShell template.
- `harness/capabilities.v1.json` and `harness/triggers.v1.json` provide reusable operations and deterministic routing.
- `.ai/skills/harness-infrastructure-maintenance/SKILL.md` provides the repeatable harness repair procedure, including command-delivery recovery.
- `scripts/validate_harness.py` validates component existence/tracking, human contracts, machine registries, skill/capability/trigger ownership, acquisition safety, hooks, connected domain contracts, and validator-profile parity.
- `.githooks/pre-commit` validates an isolated staged tree so unrelated unstaged work cannot mask or block the commit; because it runs `tests.test_harness_contract`, registered operator-command integration is included.
- `.githooks/pre-push` runs the exhaustive non-destructive root harness profile.
- `.github/workflows/harness-contract.yml` runs the focused operator-command gate before harness completeness and the connected contract suites.
- `Acquire-Latest-PromptKit.cmd` and `scripts/Acquire-LatestPromptKit.ps1` preserve technician work and allow clone or clean fast-forward only.

## Validator behavior

Focused operator-command command:

```bash
python scripts/validate_operator_command_envelope.py --summary
python -m unittest tests.test_operator_command_envelope -v
```

It fails when a command:

- embeds a literal `C:\Users\<name>\...` path;
- contains Markdown hyperlink syntax as command data;
- can execute top-level interactive `exit`;
- runs fetch/status Git work before a location/clone gate;
- fetches unmerged remote work without verifying the exact commit;
- uses destructive reset/clean/stash/force-style dirty-work handling;
- validates remote work without resolving the canonical artifact from `harness/artifacts.v1.json`;
- invokes native Git without terminating-error propagation.

Canonical completeness command:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

The report records:

- schema and repository identity;
- overall pass/fail;
- one result per root harness check;
- failure count and messages;
- registered component, workflow, artifact, validator, capability, trigger, and skill counts;
- proof ceiling.

The root ordered profile is stored in `harness/validators.v1.json` and mirrored exactly in `harness/manifest.v1.json`. Focused domain gates are registered separately in `harness/manifest.v1.json` and may run before the root profile when their surface changes.

## Technician acquisition behavior

The acquisition GUI clones canonical `main` when absent. When the repository exists, it verifies canonical origin, clean `main`, no local-only commits or divergence, fetches, fast-forwards only, validates required files and Prompt Kit parity, and opens the selected surface only after success. It does not reset, clean, delete branches, force-push, stash, or automate credentials.

## Operator command delivery behavior

For unmerged harness work, the preferred proof transport is `harness/templates/Invoke-RemoteHarnessProof.ps1` rather than a path-heavy command reconstructed from remembered machine state.

The template:

1. uses an environment-derived isolated checkout under `LOCALAPPDATA` or `TEMP`;
2. creates no `C:\Users\<name>` assumption;
3. constructs the repository URL from non-auto-linkable fragments;
4. refuses a dirty existing proof checkout;
5. verifies canonical origin;
6. fetches without force and verifies `FETCH_HEAD` equals the exact expected commit;
7. checks out detached at that commit;
8. runs the command-envelope validator, harness completeness, focused/harness contract tests, and patch hygiene;
9. resolves `harness-completeness-report` from `harness/artifacts.v1.json`;
10. prints the report while leaving the interactive terminal alive on failure.

## Prompt-language audit behavior

Audit mode covers every canonical and effective prompt, requires equal canonical/effective/disposition counts, emits stable findings, and fails identity, coverage, or error-level defects. Strict mode additionally fails warning-level lazy canonical language and is the completion gate for bounded prompt-language repair.

## Known gaps

- Tracked hooks are optional until a checkout runs `git config core.hooksPath .githooks`.
- Native Windows parsing/execution of `harness/templates/Invoke-RemoteHarnessProof.ps1` still requires a Windows operator proof; the current execution container has no PowerShell runtime.
- A static command-envelope pass cannot prove the operator machine has GitHub DNS/network reachability, Git credentials, or Python.
- Native Windows acquisition behavior still requires field proof on a technician workstation.
- Prompt Kit browser events, clipboard permissions, focus restoration, and visual acceptance require browser observation.
- Excel for Web compatibility and operator acceptance require protected runtime proof.
- Provider/model behavior is not proven by static prompt language.
- Credentials, network, protected targets, deployment, and production remain outside static harness proof.
- Product-specific behavior gaps must be repaired in their owning product lanes; the harness must not weaken contracts to hide them.

## Validation order

For command-delivery changes, run the focused domain gate first:

```bash
python -m py_compile scripts/validate_operator_command_envelope.py tests/test_operator_command_envelope.py
python scripts/validate_operator_command_envelope.py --summary
python -m unittest tests.test_operator_command_envelope -v
```

Then run the registered root profile:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
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

## Proof ceiling

A passing command-envelope validator, harness completeness report, contract tests, hooks, and CI prove only the tracked repository surfaces, command shapes, fixtures, and commands exercised on the tested commit. They do not prove the operator's local path, native Windows execution, product runtime behavior, Excel for Web acceptance, browser events, clipboard/focus behavior, provider obedience, credentials, network availability, protected target access, technician acceptance, deployment, or production success.

## Operator next action

For an unmerged harness head, retrieve `harness/templates/Invoke-RemoteHarnessProof.ps1` from the exact branch/commit and execute it with that same branch/commit. The template itself creates or reuses a clean environment-derived proof checkout, runs the owning validators, resolves `harness-completeness-report` through `harness/artifacts.v1.json`, prints the report, and throws on failure without closing the operator terminal. Do not substitute a remembered local repository path.
