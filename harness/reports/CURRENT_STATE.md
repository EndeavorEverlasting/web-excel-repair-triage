# Harness Current State

**As of:** 2026-08-06
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Canonical branch:** `main`
**Harness workflow:** `harness-infrastructure`
**Harness capability:** `harness-infrastructure-maintenance`

## Status

The repository has a connected operational harness for fresh-agent entry, workflow selection, artifact resolution, validator selection, scoped skills, deterministic triggers, staged-index and pre-push hooks, CI reporting, technician acquisition, Prompt Kit contracts, prompt-language auditing, handoff, and crash-safe native PowerShell execution.

The harness now has separate machine-readable workflow, artifact, validator, capability, and trigger registries. `harness/manifest.v1.json` is the component inventory; `scripts/validate_harness.py` is the fail-closed completeness validator and writes `harness-completeness-report/v1`.

Operator-facing PowerShell validation is owned by `scripts/Invoke-HarnessProfile.ps1` and `harness/contracts/powershell-command-envelope.v1.json`. The runner executes registry commands in child processes, never calls standalone `exit`, writes durable evidence before failure propagation, and returns control to the caller by throwing after summary finalization.

## Working surfaces

- `CODEBASE_MAP.md` provides structure, directories, entry points, configuration, commands, and known traps.
- `WORKFLOW.md` and `harness/workflows.v1.json` define pickup, workflow selection, validation, failure handling, commit/PR behavior, and handoff.
- `ARTIFACT_REGISTRY.md` and `harness/artifacts.v1.json` define tracked/runtime artifacts, producers, validators, canonical paths, protected paths, naming, tracking, and proof ceilings.
- `harness/validators.v1.json` defines the full harness, pre-commit, and pre-push validator profiles.
- `harness/capabilities.v1.json` and `harness/triggers.v1.json` provide reusable operations and deterministic routing.
- `.ai/skills/harness-infrastructure-maintenance/SKILL.md` provides the repeatable harness repair procedure and PowerShell command-safety boundaries.
- `scripts/validate_harness.py` validates component existence/tracking, human contracts, machine registries, skill/capability/trigger ownership, acquisition safety, hooks, connected domain contracts, and validator-profile parity.
- `scripts/Invoke-HarnessProfile.ps1` runs registered profiles without terminating the caller and writes `summary.json`, `run.log`, and per-step stdout/stderr.
- `tests/test_powershell_command_envelope.py` rejects standalone `exit`, host/process termination, missing durable evidence, surprise dependency installation, destructive cleanup, and missing hook/manifest integration.
- `.githooks/pre-commit` validates an isolated staged tree so unrelated unstaged work cannot mask or block the commit.
- `.githooks/pre-push` runs the exhaustive non-destructive harness profile.
- `.github/workflows/harness-contract.yml` publishes the harness completeness, interaction-audit, and prompt-language-audit reports.
- `Acquire-Latest-PromptKit.cmd` and `scripts/Acquire-LatestPromptKit.ps1` preserve technician work and allow clone or clean fast-forward only.

## Validator behavior

Canonical completeness command:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

Canonical crash-safe native Windows command:

```powershell
& .\scripts\Invoke-HarnessProfile.ps1 -Profile harness -ExpectedHead '<exact-commit-sha>'
```

The completeness report records:

- schema and repository identity;
- overall pass/fail;
- one result per harness check;
- failure count and messages;
- registered component, workflow, artifact, validator, capability, trigger, and skill counts;
- proof ceiling.

The PowerShell command-envelope summary records:

- exact repository root and selected profile;
- expected and actual HEAD;
- start/end timestamps and PASS/FAIL status;
- failed step;
- one child exit code and stdout/stderr path per command;
- combined run-log and summary paths.

The full ordered profile is stored in `harness/validators.v1.json` and mirrored exactly in `harness/manifest.v1.json`.

## Technician acquisition behavior

The acquisition GUI clones canonical `main` when absent. When the repository exists, it verifies canonical origin, clean `main`, no local-only commits or divergence, fetches, fast-forwards only, validates required files and Prompt Kit parity, and opens the selected surface only after success. It does not reset, clean, delete branches, force-push, stash, or automate credentials.

## Prompt-language audit behavior

Audit mode covers every canonical and effective prompt, requires equal canonical/effective/disposition counts, emits stable findings, and fails identity, coverage, or error-level defects. Strict mode additionally fails warning-level lazy canonical language and is the completion gate for bounded prompt-language repair.

## Known gaps

- Tracked hooks are optional until a checkout runs `python scripts/install_local_hooks.py`.
- The new PowerShell command envelope has static contract coverage; exact native Windows terminal-survival behavior still requires one workstation run on the committed head.
- Native Windows acquisition behavior still requires field proof on a technician workstation.
- Prompt Kit browser events, clipboard permissions, focus restoration, and visual acceptance require browser observation.
- Excel for Web compatibility and operator acceptance require protected runtime proof.
- Provider/model behavior is not proven by static prompt language.
- Credentials, network, protected targets, deployment, and production remain outside static harness proof.
- Product-specific behavior gaps must be repaired in their owning product lanes; the harness must not weaken contracts to hide them.

## Validation order

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract tests.test_powershell_command_envelope -v
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts/validate_prompt_kit_interactions.py --output Outputs/prompt-kit-interaction-audit.json --summary
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery -v
python -m unittest tests.test_prompt_language_audit -v
python scripts/evaluate_prompt_language.py --output Outputs/prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests/test_prompt_kit_header_contract.py
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/validate_artifact_hygiene.py
git diff --check
```

## Proof ceiling

A passing completeness report, contract tests, hooks, and CI prove only the tracked repository surfaces and commands exercised on the tested commit. A native command-envelope run additionally proves that the exercised PowerShell process retained durable logs and returned control on that workstation. These checks do not prove product runtime behavior, Excel for Web acceptance, native Windows GUI behavior outside the runner, browser events, clipboard/focus behavior, provider obedience, credentials, network availability, protected target access, technician acceptance, deployment, or production success.

## Operator next action

Fetch the exact unmerged commit into an isolated worktree and invoke `scripts/Invoke-HarnessProfile.ps1` with `-ExpectedHead`. The command must leave the caller terminal open and print the durable `summary.json` and `run.log` paths whether the profile passes or fails.
