# Harness Current State

## Status

The repository has a tracked operational harness for agent entry, workflow selection, Prompt Kit delivery, safe technician acquisition, exhaustive prompt-language auditing, skill-eval routing, validation, artifacts, hooks, and handoff. It now also has a versioned Prompt Kit card-interaction contract with a focused static audit and a strict downstream product gate.

## Working surfaces

- `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md`, `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md` form the human-readable harness spine.
- `harness/manifest.v1.json`, `harness/capabilities.v1.json`, and `harness/triggers.v1.json` provide machine-readable component and routing ownership.
- `harness/contracts/prompt-kit-interactions.v1.json` records the requested prompt-card behavior without moving deterministic UI implementation into harness prose.
- `scripts/validate_prompt_kit_interactions.py` validates that contract, writes a machine-readable interaction audit, and exposes a strict `--require-implementation` gate for the later Prompt Kit product lane.
- `tests/test_prompt_kit_interactions_contract.py` proves contract completeness, detects the legacy single-click-expand behavior, and exercises a synthetic compliant interaction surface.
- `.ai/skills/prompt-language-audit/SKILL.md` governs exhaustive canonical/effective prompt review.
- `.ai/skills/skill-evaluation/SKILL.md` governs correctness, regression, profiling, cost, and token-efficiency eval construction; it may support later interaction evals but does not own product behavior.
- `harness/evals/prompt-language-audit.v1.json` and fixtures define stable prompt-language rules and mutation cases.
- `scripts/evaluate_prompt_language.py` emits one disposition per prompt and fails coverage or error-level defects.
- `scripts/validate_harness.py` and contract tests enforce component, registry, skill, eval, hook, launcher, and report contracts.
- `.githooks/pre-commit` provides a focused gate; `.githooks/pre-push` adds interaction-contract audit, exhaustive prompt audit, and exact Prompt Kit parity.
- `Acquire-Latest-PromptKit.cmd` and its GUI preserve local work, validate the canonical site, and open only after success.

## Technician acquisition behavior

The acquisition GUI clones canonical `main` when absent; otherwise verifies canonical origin, clean `main`, no local-only commits or divergence, fetches and fast-forwards only, validates required files and exact Prompt Kit parity, and opens the selected surface after success. It does not reset, clean, delete branches, force-push, stash, or automate credentials.

## Prompt Kit card interaction contract

The tracked contract requires:

1. single-clicking a prompt card copies that prompt without expanding detail;
2. double-clicking a prompt card expands its detail exactly once;
3. clicking the detail backdrop or main prompt page outside the open detail collapses it, returns the operator to the main prompt results surface, restores usable focus, and preserves active filters/search;
4. Escape continues to close an open detail before broader Escape fallback behavior;
5. explicit Copy controls continue to copy without unintended expansion.

The default audit is intentionally suitable for a harness-only lane: it validates the requirement and reports missing product markers without pretending the UI is implemented. The strict `--require-implementation` gate is reserved for the authorized Prompt Kit product lane and must pass before browser field proof.

## Prompt-language audit behavior

Audit mode covers every raw and effective prompt, requires equal canonical/effective/disposition counts, emits stable findings and dispositions, and fails duplicate IDs, coverage gaps, empty required fields, or missing effective actionability. Warning-level lazy canonical metadata remains visible as repair debt. Strict mode fails warnings and is the completion gate for a bounded prompt-repair sprint.

## Known gaps

- The current canonical `docs/prompt-kit.js` still assigns a prompt card single click to `showPromptDetail(...)`; the requested single-click-copy behavior is therefore not yet implemented.
- No canonical prompt-card double-click expansion handler is currently present.
- No canonical `promptDetailOverlay` outside-click dismissal with focus restoration is currently present.
- Existing Escape-to-close and explicit Copy-button behavior are present and must be preserved by the product repair.
- The harness lane intentionally does not mutate `docs/prompt-kit.js`, `build_prompt_kit.py`, or generated `web/prompt-kit/index.html`; those files belong to the next Prompt Kit product behavior lane.
- Browser event ordering, clipboard permission behavior, focus restoration, and visual acceptance remain field proof even after static implementation markers pass.
- Warning-level canonical prompt metadata may remain until a strict prompt-repair sprint resolves it; effective prompts remain protected by the shared actionability policy.
- Provider/model compliance is not proven by static prompt language.
- Native Windows visual/mouse acquisition and browser behavior remain field proof.
- Technician machines still require Git for Windows, Windows PowerShell, Python 3, network access, and repository authorization.
- Generic P62 capability installs target-repository eval infrastructure; it does not pre-prove every future skill.
- Tracked hooks are optional and must be enabled per worktree with `git config core.hooksPath .githooks`.

## Validation order

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts\validate_prompt_kit_interactions.py --output Outputs\prompt-kit-interaction-audit.json --summary
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Run broader repository tests after focused gates. The strict product interaction gate is deliberately not part of this harness-only completion sequence because current product code is outside the owned scope.

## Build provenance

- Existing operational harness landed on `main` through PR #108; current base is `536a2a86f4c62b4719b4b8c5b596927b3ac0dc40`.
- Prompt-panel interaction harness branch: `feat/prompt-panel-interaction-harness`.
- Open PR #109 (governance) and PR #110 (stacked NTH harness) are separate lanes and are not dependencies of this prompt-panel interaction harness.
- Product implementation dependency after this harness lands: Prompt Kit product behavior lane using Workflow B and the strict interaction gate.

## Proof ceiling

Current harness proof covers tracked interaction-contract presence, schema integrity, required behavior IDs, canonical source/path registration, safe audit-output routing, regression detection for legacy single-click expansion, synthetic compliant-source detection, existing harness component presence, capability/trigger ownership, required skill sections, exhaustive canonical/effective prompt pairing, acquisition command boundaries, protected paths, deterministic Prompt Kit parity, and CI integration when those checks pass on the exact branch head. It does not prove the requested interaction is implemented in the browser, browser click/double-click event ordering, clipboard permissions, focus restoration, visual acceptance, provider obedience, credentials/network availability, protected target runtime behavior, technician acceptance, or production success.
