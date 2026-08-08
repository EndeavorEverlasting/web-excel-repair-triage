# Harness Current State

**As of:** 2026-08-08
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Canonical branch:** `main`
**Harness workflow:** `harness-infrastructure`
**Harness capability:** `harness-infrastructure-maintenance`

## Status

The repository has a connected operational harness for fresh-agent entry, workflow selection, artifact resolution, validator selection, scoped skills, deterministic triggers, staged-index and pre-push hooks, CI reporting, cross-device Prompt Kit acquisition, Prompt Kit contracts, prompt-language auditing, operator-command delivery, and handoff.

The harness has separate machine-readable workflow, artifact, validator, capability, trigger, and focused domain-contract registries. `harness/manifest.v1.json` is the component/domain-contract inventory; `scripts/validate_harness.py` is the fail-closed completeness validator and writes `harness-completeness-report/v1`.

Prompt Kit access is now intent-first across devices. Normal browser/phone use is explicitly separated from editable Git checkout work so a future operator or agent cannot require Termux, ZIP extraction, or a clone merely to open the app. Windows stable-origin acquisition remains owned by the existing repository launchers rather than by a competing implementation.

The operator-command envelope separately closes a reproduced failure class where an unverified remembered Windows path caused `Set-Location` to fail, a subsequent Git command ran outside a repository, a raw localhost URL arrived as Markdown hyperlink syntax, and top-level `exit` could terminate the interactive shell. Those shapes remain fixture-backed failures rather than documentation-only warnings.

## Working surfaces

- `CODEBASE_MAP.md` provides structure, directories, entry points, configuration, commands, cross-device acquisition routes, and known traps.
- `WORKFLOW.md` and `harness/workflows.v1.json` define pickup, workflow selection, validation, failure handling, commit/PR behavior, and handoff.
- `ARTIFACT_REGISTRY.md` and `harness/artifacts.v1.json` define tracked/runtime artifacts, producers, validators, canonical paths, delivery surfaces, protected paths, naming, tracking, and proof ceilings.
- `harness/validators.v1.json` defines the root harness, pre-commit, and pre-push validator profiles.
- `harness/manifest.v1.json` additionally registers focused domain gates, including `prompt_kit_cross_device_access` and `operator_command_envelope`.
- `harness/contracts/prompt-kit-cross-device-access.v1.json` defines five acquisition modes: browser use, phone install, Windows local app, editable checkout, and ZIP snapshot. It requires direct public routes for normal use and reserves manual Git checkout for source-work intent.
- `scripts/validate_prompt_kit_cross_device_access.py` validates canonical URLs, route priority, no-clone browser/phone rules, safe existing-checkout origin/cleanliness/branch/divergence gates, Android Termux/F-Droid prerequisites, access guides, workflow/capability/trigger ownership, artifact delivery surfaces, and the existing acquisition skill.
- `tests/test_prompt_kit_cross_device_access.py` supplies positive and mutation regressions for accidental browser cloning, malformed JSON roots, contradictory phone guidance, ownership drift, missing checkout-state gates, and unsafe editable updates.
- `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` is the single reusable cross-device procedure. It does not duplicate the public Pages launcher, Windows launcher, or Git implementation.
- `harness/contracts/operator-command-envelope.v1.json` defines fail-closed operator-command rules for person-specific paths, Markdown link data, interactive `exit`, Git before directory gate, unpinned remote work, destructive dirty-work handling, guessed artifacts, and ignored native failure.
- `harness/templates/Invoke-RemoteHarnessProof.ps1` provides a repository-owned unmerged-harness proof path that uses `LOCALAPPDATA`/`TEMP`, an isolated checkout, exact branch/commit verification, the owning validators, artifact-registry resolution, and `throw` rather than terminal-closing `exit`.
- `scripts/validate_operator_command_envelope.py` validates the command-delivery contract, fixtures, and canonical PowerShell template.
- `harness/capabilities.v1.json` and `harness/triggers.v1.json` provide reusable operations and deterministic routing.
- `.ai/skills/harness-infrastructure-maintenance/SKILL.md` provides the repeatable harness repair procedure.
- `scripts/validate_harness.py` validates component existence/tracking, human contracts, machine registries, skill/capability/trigger ownership, acquisition safety, hooks, connected domain contracts, and validator-profile parity.
- `.githooks/pre-commit` validates an isolated staged tree so unrelated unstaged work cannot mask or block the commit.
- `.githooks/pre-push` runs focused acquisition/access gates plus the exhaustive non-destructive root harness profile.
- `.github/workflows/harness-contract.yml` runs focused cross-device and operator-command gates before harness completeness and the connected contract suites.
- `Open-Latest-PromptKit.cmd`, `Acquire-Latest-PromptKit.cmd`, public GitHub Pages URLs, and the documented Git/ZIP fallbacks remain the existing delivery implementations; the harness only routes and validates their ownership.

## Validator behavior

Focused cross-device acquisition commands:

```bash
python -m py_compile scripts/validate_prompt_kit_cross_device_access.py tests/test_prompt_kit_cross_device_access.py
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
```

They fail when normal browser/phone use requires a clone, public URLs drift, phone installation is routed through source-file hunting, an existing editable checkout omits canonical-origin/clean-worktree/main-branch/local-only-commit gates, an unsafe integration command replaces the ff-only merge, Android source-work prerequisites drift, access docs disagree with the contract, or machine registries stop owning the route.

Focused operator-command commands:

```bash
python scripts/validate_operator_command_envelope.py --summary
python -m unittest tests.test_operator_command_envelope -v
```

Canonical completeness command:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

The report records repository identity, overall pass/fail, one result per root harness check, failure count/messages, registered component/workflow/artifact/validator/capability/trigger/skill counts, and proof ceiling.

The root ordered profile is stored in `harness/validators.v1.json` and mirrored exactly in `harness/manifest.v1.json`. Focused domain gates are registered separately in `harness/manifest.v1.json` and may run before the root profile when their surface changes.

## Technician acquisition behavior

### Browser and phone/tablet

- Normal use: `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`.
- Install/share: `https://endeavoreverlasting.github.io/web-excel-repair-triage/` in the system browser.
- No clone, ZIP, PowerShell, Python, or Termux is required merely to use the Prompt Kit.

### Windows stable local app

`Open-Latest-PromptKit.cmd` remains the app-like Windows entry point. The advanced acquisition GUI can clone canonical `main` when absent and, when a repository exists, verifies canonical origin, clean `main`, no local-only commits or divergence, fetches, fast-forwards only, validates required files and Prompt Kit parity, and opens the selected surface only after success. It does not reset, clean, delete branches, force-push, stash, or automate credentials.

### Editable checkout

A real checkout is selected only when the user intends to edit, commit, push, inspect source locally, or run repository tooling. The canonical clone is:

```bash
git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
```

For an existing editable checkout, verify state before integration:

```bash
git remote get-url origin
git status --porcelain
git branch --show-current
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git merge --ff-only origin/main
```

The origin must exactly match the canonical repository URL, status must be empty, the current branch must be `main`, and the first/local-only count must be `0`. Any failed gate preserves the checkout and stops the update. Only after all gates pass may the ff-only merge advance `main`.

Android source work uses Termux from F-Droid, then `pkg update` and `pkg install git`. Fresh Android source acquisition uses the canonical clone; later updates use the same existing-checkout state gates above. This is not the normal-use route.

## Operator command delivery behavior

For unmerged harness work, the preferred proof transport is `harness/templates/Invoke-RemoteHarnessProof.ps1` rather than a path-heavy command reconstructed from remembered machine state. The template creates/reuses a clean environment-derived proof checkout, verifies exact remote identity, runs the owning validators, resolves the registered harness report, prints evidence, and leaves the interactive terminal alive on failure.

## Prompt-language audit behavior

Audit mode covers every canonical and effective prompt, requires equal canonical/effective/disposition counts, emits stable findings, and fails identity, coverage, or error-level defects. Strict mode additionally fails warning-level lazy canonical language and is the completion gate for bounded prompt-language repair.

## Known gaps

- Tracked hooks are optional until a checkout runs `git config core.hooksPath .githooks`.
- Cross-device static validation does not prove a phone browser exposes the expected install menu, a PWA installs, Termux/F-Droid is available on a particular device, Git authentication succeeds, browser storage persists Favorites, clipboard APIs work, or a push is authorized.
- Native Windows parsing/execution of `harness/templates/Invoke-RemoteHarnessProof.ps1` still requires a Windows operator proof when that path changes.
- A static command-envelope pass cannot prove the operator machine has GitHub DNS/network reachability, Git credentials, or Python.
- Native Windows acquisition behavior still requires field proof on a technician workstation.
- Prompt Kit browser events, clipboard permissions, focus restoration, and visual acceptance require browser observation.
- Excel for Web compatibility and operator acceptance require protected runtime proof.
- Provider/model behavior is not proven by static prompt language.
- Credentials, network, protected targets, deployment, and production remain outside static harness proof.
- Product-specific behavior gaps must be repaired in their owning product lanes; the harness must not weaken contracts to hide them.

## Validation order

For Prompt Kit cross-device acquisition changes, run the focused domain gate first:

```bash
python -m py_compile scripts/validate_prompt_kit_cross_device_access.py tests/test_prompt_kit_cross_device_access.py
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
```

For command-delivery changes, run its focused domain gate before the root profile:

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

A passing cross-device validator proves registered routing, canonical URLs/commands, no-clone normal-use rules, explicit existing-checkout safety gates, and source-work boundaries on the tested commit. A passing command-envelope validator, harness completeness report, contract tests, hooks, and CI prove only the tracked repository surfaces, command shapes, fixtures, and commands exercised on that commit. They do not prove a specific phone/tablet/Windows device, browser install behavior, Termux/F-Droid, credentials, network, local storage, clipboard/focus behavior, Excel for Web acceptance, provider obedience, protected target access, technician acceptance, deployment, or production success.

## Operator next action

For an unmerged harness head, retrieve `harness/templates/Invoke-RemoteHarnessProof.ps1` from the exact branch/commit and execute it with that same branch/commit. The template itself creates or reuses a clean environment-derived proof checkout, runs the owning validators, resolves `harness-completeness-report` through `harness/artifacts.v1.json`, prints the report, and throws on failure without closing the operator terminal. For cross-device Prompt Kit acceptance after merge, select the device route from `harness/contracts/prompt-kit-cross-device-access.v1.json` and observe that runtime rather than substituting a higher-friction path.
