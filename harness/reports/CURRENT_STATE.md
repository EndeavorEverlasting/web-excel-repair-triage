# Harness Current State

## Status

The repository has a tracked operational harness for agent entry, workflow selection, Prompt Kit delivery, safe technician acquisition, exhaustive prompt-language auditing, skill-eval routing, validation, artifacts, hooks, handoff, and a focused Neuron Track Hours domain overlay for month-specific task distribution and workbook delivery modes.

## Working surfaces

- `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md`, `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md` form the human-readable harness spine.
- `harness/manifest.v1.json`, `harness/capabilities.v1.json`, and `harness/triggers.v1.json` provide machine-readable root component and routing ownership.
- `harness/nth/manifest.v1.json`, `harness/nth/monthly-rule-packs.v1.json`, and `harness/nth/triggers.v1.json` provide the NTH domain overlay, active month rules, and internal/client routing.
- `.ai/skills/neuron-track-hours-monthly-artifact/SKILL.md` governs NTH month selection, attendance-first attribution, primary-versus-complimentary work, delivery-mode selection, client/internal parity, and historical-review wording.
- `.ai/skills/prompt-language-audit/SKILL.md` governs exhaustive canonical/effective prompt review.
- `.ai/skills/skill-evaluation/SKILL.md` governs correctness, regression, profiling, cost, and token-efficiency eval construction.
- `harness/evals/prompt-language-audit.v1.json` and fixtures define stable prompt-language rules and mutation cases.
- `scripts/evaluate_prompt_language.py` emits one disposition per prompt and fails coverage or error-level defects.
- `scripts/validate_harness.py` and root contract tests enforce component, registry, skill, eval, hook, launcher, and report contracts.
- `scripts/validate_nth_harness.py` and `tests/test_nth_harness_contract.py` fail closed on missing or drifted NTH rule-pack, mode, role-cadence, exception, routing, skill, and human-surface contracts.
- `.githooks/pre-commit` provides focused root + NTH gates; `.githooks/pre-push` adds NTH contracts, exhaustive prompt audit, and exact Prompt Kit parity.
- `Acquire-Latest-PromptKit.cmd` and its GUI preserve local work, validate the canonical site, and open only after success.

## Neuron Track Hours domain overlay

The NTH overlay consumes the canonical `AGENTS.md` doctrine and makes the rules executable without creating a competing governance file.

- Roster/attendance remains the labor-hours source of truth; device counts and allocation targets do not create hours.
- Each paid shift has one dominant primary workstream; complimentary work may carry concurrent context without adding hours.
- Configuration and Deployment remain distinct; PM/client/ticket work remains role-specific.
- Month-specific rules must be resolved before attribution. A prior month cannot silently carry forward.
- July 2026 uses the June-26-forward 60% Configuration / 40% other-work rule as a reasonableness guardrail, not a quota.
- Rich has one full Client Correspondence / Coordination day per week, usually Thursday, with July 2 and July 23 as known anchors.
- July 3 is a holiday; July 10 is mixed operational work; Alejandro has zero scheduled project hours on July 24.
- The overlay enforces **two workbook delivery modes**: internal/working and client-facing/management.
- Internal mode is the construction, repair, analysis, and audit source and preserves the complete supporting workbook.
- Client mode is derived from a validated internal workbook, must preserve the same attendance/task truth, and omits internal-only sheets rather than hiding them.
- **July 2026 client mode contains exactly two tabs: `Executive Summary` and `July 2026`.**
- May 26–29 remains a historical review boundary; an unchanged historical workbook must not be described as reconciled, corrected, revised, or updated.

## Technician acquisition behavior

The acquisition GUI clones canonical `main` when absent; otherwise verifies canonical origin, clean `main`, no local-only commits or divergence, fetches and fast-forwards only, validates required files and exact Prompt Kit parity, and opens the selected surface after success. It does not reset, clean, delete branches, force-push, stash, or automate credentials.

## Prompt-language audit behavior

Audit mode covers every raw and effective prompt, requires equal canonical/effective/disposition counts, emits stable findings and dispositions, and fails duplicate IDs, coverage gaps, empty required fields, or missing effective actionability. Warning-level lazy canonical metadata remains visible as repair debt. Strict mode fails warnings and is the completion gate for a bounded prompt-repair sprint.

## Known gaps

- The NTH overlay proves repository rules and routing, not that a particular workbook has been generated correctly. Concrete internal and client workbooks still require focused workbook validators and cross-mode parity proof.
- Excel for Web/client acceptance is not proven by static NTH harness checks.
- The July rule pack is explicit; a future month must receive its own confirmed rule pack rather than inheriting July by habit.
- Warning-level canonical prompt metadata may remain until a strict prompt-repair sprint resolves it; effective prompts remain protected by the shared actionability policy.
- Provider/model compliance is not proven by static prompt language.
- Native Windows visual/mouse acquisition and browser behavior remain field proof.
- Technician machines still require Git for Windows, Windows PowerShell, Python 3, network access, and repository authorization.
- Generic P62 capability installs target-repository eval infrastructure; it does not pre-prove every future skill.
- Tracked hooks are optional and must be enabled per worktree with `git config core.hooksPath .githooks`.

## Validation order

```powershell
python scripts\validate_harness.py
python scripts\validate_nth_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_nth_harness_contract -v
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python -m triage.gitignore_hygiene
git diff --check
```

Run broader repository tests after focused gates.

## Build provenance

- Root harness build branch: `feat/operational-harness-prompt-audit` (merged through the existing harness floor).
- NTH domain overlay build branch: `feat/nth-monthly-artifact-harness`.
- NTH governance dependency: `governance/july-2026-neuron-task-distribution` / PR #109.
- The NTH harness branch is intentionally stacked on the governance head so harness code consumes the doctrine without modifying `AGENTS.md`.

## Proof ceiling

Current root proof covers tracked component presence, schema integrity, unique root capability/trigger ownership, required root skill sections, exhaustive canonical/effective prompt pairing, error-level language rules, fixture mutation detection, acquisition command boundaries, protected paths, deterministic Prompt Kit parity, and CI integration. NTH overlay proof additionally covers month-rule registration, July 2026 60/40 guardrail semantics, weekly correspondence cadence, known date/person exceptions, internal/client mode separation, exact July client tab contract, historical-review boundary, and focused routing. It does not prove provider obedience, model judgment quality, Excel for Web rendering, concrete workbook correctness, timestamp-level historical reconstruction, client acceptance, Windows GUI rendering, credentials/network availability, protected target runtime behavior, or production success.
