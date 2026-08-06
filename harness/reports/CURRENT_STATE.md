# Harness Current State

**As of:** 2026-08-06
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Canonical branch:** `main`
**Harness workflow:** `harness-infrastructure`
**Harness capability:** `harness-infrastructure-maintenance`

## Status

The repository has a connected operational harness for fresh-agent entry, workflow selection, artifact resolution, validator selection, scoped skills, deterministic triggers, staged-index and pre-push hooks, CI reporting, technician acquisition, Prompt Kit contracts, prompt-language auditing, and handoff.

The harness has separate machine-readable workflow, artifact, validator, capability, and trigger registries. `harness/manifest.v1.json` is the component inventory and domain-contract registry; `scripts/validate_harness.py` is the fail-closed root completeness validator and writes `harness-completeness-report/v1`.

The Prompt Kit portability domain contract now defines a stable-origin runtime path for Favorites. The canonical checked-in site remains unchanged and parity-controlled. The supported quick launcher generates a gitignored artifact from the exact canonical site plus the tracked portability runtime, records source/runtime/artifact hashes, serves it at `http://127.0.0.1:8765/`, and exposes Export/Import controls for profile or device transfer.

## Working surfaces

- `CODEBASE_MAP.md` provides structure, directories, entry points, configuration, commands, and known traps.
- `WORKFLOW.md` and `harness/workflows.v1.json` define pickup, workflow selection, validation, failure handling, commit/PR behavior, and handoff.
- `ARTIFACT_REGISTRY.md` and `harness/artifacts.v1.json` define tracked/runtime artifacts, producers, validators, canonical paths, protected paths, naming, tracking, and proof ceilings; registered domain contracts may define focused runtime artifacts without expanding the closed root artifact-ID set.
- `harness/validators.v1.json` defines the full root harness, pre-commit, and pre-push validator profiles.
- `harness/capabilities.v1.json` and `harness/triggers.v1.json` provide reusable operations and deterministic routing.
- `.ai/skills/harness-infrastructure-maintenance/SKILL.md` provides the repeatable harness repair procedure and boundaries.
- `scripts/validate_harness.py` validates component existence/tracking, human contracts, machine registries, skill/capability/trigger ownership, acquisition safety, hooks, connected Prompt Kit contracts, and validator-profile parity.
- `.githooks/pre-commit` validates an isolated staged tree so unrelated unstaged work cannot mask or block the commit.
- `.githooks/pre-push` runs the exhaustive non-destructive root harness profile.
- `.github/workflows/harness-contract.yml` publishes the harness completeness, interaction-audit, and prompt-language-audit reports.
- `Acquire-Latest-PromptKit.cmd` and `scripts/Acquire-LatestPromptKit.ps1` preserve technician work and allow clone or clean fast-forward only.
- `Open-Latest-PromptKit.cmd` and `scripts/Open-LatestPromptKitPortable.ps1` reuse the acquisition helpers, generate and validate the portable runtime artifact, reuse the stable origin, and open the current site.
- `docs/prompt-kit-favorites-portability.js` owns Export/Import behavior.
- `scripts/serve_prompt_kit_portable.py` owns exact runtime generation, receipt hashes, loopback-only serving, and no-cache delivery.
- `harness/contracts/prompt-kit-portability.v1.json` owns required context, connected-GitHub fallback, execution loop, Prompt Library links/cadence, sequential prompt routing, runtime artifact, and proof boundaries.

## Validator behavior

Canonical root completeness command:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

Portable Prompt Kit commands:

```bash
python scripts/serve_prompt_kit_portable.py --build-only
python scripts/validate_prompt_kit_portability.py --require-artifact --output Outputs/prompt-kit-portability-validation.json --summary
python -m unittest tests.test_prompt_kit_portability -v
```

The portability receipt records:

- canonical site path, SHA-256, and bytes;
- tracked runtime path, schema, SHA-256, and bytes;
- generated artifact path, SHA-256, and bytes;
- stable origin;
- loopback, cache, protected-input, and canonical-site guardrails;
- proof ceiling.

The root harness report records:

- schema and repository identity;
- overall pass/fail;
- one result per harness check;
- failure count and messages;
- registered component, workflow, artifact, validator, capability, trigger, and skill counts;
- proof ceiling.

The full ordered root profile remains stored in `harness/validators.v1.json` and mirrored exactly in `harness/manifest.v1.json`. Portability's focused strict gate is registered under `domain_contracts.prompt_kit_portability` and in the Prompt Kit web workflow rather than silently altering the closed root validator profile.

## Technician acquisition behavior

The acquisition GUI clones canonical `main` when absent. When the repository exists, it verifies canonical origin, clean `main`, no local-only commits or divergence, fetches, fast-forwards only, validates required files and Prompt Kit parity, and opens the selected surface only after success. It does not reset, clean, delete branches, force-push, stash, or automate credentials.

The quick-open path parses and reuses those acquisition helper functions without executing the GUI/direct-file entry point. It then builds the portable site under `Outputs/`, validates the receipt, starts or reuses the loopback server, and opens `http://127.0.0.1:8765/`. Browser caching is disabled, and a non-loopback bind is rejected.

## Prompt-language audit behavior

Audit mode covers every canonical and effective prompt, requires equal canonical/effective/disposition counts, emits stable findings, and fails identity, coverage, or error-level defects. Strict mode additionally fails warning-level lazy canonical language and is the completion gate for bounded prompt-language repair.

## Known gaps

- Tracked hooks are optional until a checkout runs `git config core.hooksPath .githooks`.
- Native Windows acquisition and portable-launch behavior still require field proof on a technician workstation.
- The stable-origin design and receipt can prove generation and local HTTP configuration statically; browser persistence across an actual upgrade requires an observed before/after run.
- Export download, Import file-picker, browser-profile transfer, mobile file selection, and cross-device restoration require browser observation.
- Prompt Kit browser events, clipboard permissions, focus restoration, and visual acceptance require browser observation.
- Excel for Web compatibility and operator acceptance require protected runtime proof.
- Provider/model behavior is not proven by static prompt language.
- Credentials, network, protected targets, deployment, and production remain outside static harness proof.
- Product-specific behavior gaps must be repaired in their owning product lanes; the harness must not weaken contracts to hide them.

## Validation order

Root harness profile:

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

Focused portability gate runs before the broader Prompt Kit and root harness profiles when portability surfaces change.

## Proof ceiling

A passing portability validator proves the tracked policy, source, launcher/server wiring, exact runtime composition, hashes, and focused regression behavior on the tested checkout. A passing root completeness report, contract tests, hooks, and CI prove only the tracked repository surfaces and commands exercised on the tested commit. Neither proves physical browser persistence, download/upload dialogs, cross-profile or cross-device restoration, native Windows operator acceptance, provider obedience, credentials, network availability, protected target access, deployment, or production success.

## Operator next action

Use the final sprint report's pinned worktree command to fetch the exact unmerged portability commit, run the portable builder and validator, resolve `Outputs/prompt-kit-portable/manifest.json`, open the stable origin through the tracked PowerShell launcher, and propagate any failure.
