# Harness Current State

## Status

The repository has a tracked operational harness for agent entry, workflow selection, Prompt Kit delivery, safe technician acquisition, exhaustive prompt-language auditing, skill-eval routing, validation, artifacts, hooks, and handoff.

## Working surfaces

- `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md`, `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md` form the human-readable harness spine.
- `harness/manifest.v1.json`, `harness/capabilities.v1.json`, and `harness/triggers.v1.json` provide machine-readable component and routing ownership.
- `.ai/skills/prompt-language-audit/SKILL.md` governs exhaustive canonical/effective prompt review.
- `.ai/skills/skill-evaluation/SKILL.md` governs correctness, regression, profiling, cost, and token-efficiency eval construction.
- `harness/evals/prompt-language-audit.v1.json` and fixtures define stable prompt-language rules and mutation cases.
- `scripts/evaluate_prompt_language.py` emits one disposition per prompt and fails coverage or error-level defects.
- `scripts/validate_harness.py` and contract tests enforce component, registry, skill, eval, hook, launcher, and report contracts.
- `.githooks/pre-commit` provides a focused gate; `.githooks/pre-push` adds exhaustive audit and exact Prompt Kit parity.
- `Acquire-Latest-PromptKit.cmd` and its GUI preserve local work, validate the canonical site, and open only after success.

## Technician acquisition behavior

The acquisition GUI clones canonical `main` when absent; otherwise verifies canonical origin, clean `main`, no local-only commits or divergence, fetches and fast-forwards only, validates required files and exact Prompt Kit parity, and opens the selected surface after success. It does not reset, clean, delete branches, force-push, stash, or automate credentials.

## Prompt-language audit behavior

Audit mode covers every raw and effective prompt, requires equal canonical/effective/disposition counts, emits stable findings and dispositions, and fails duplicate IDs, coverage gaps, empty required fields, or missing effective actionability. Warning-level lazy canonical metadata remains visible as repair debt. Strict mode fails warnings and is the completion gate for a bounded prompt-repair sprint.

## Known gaps

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
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python -m triage.gitignore_hygiene
git diff --check
```

Run broader repository tests after focused gates.

## Proof ceiling

Current proof covers tracked component presence, schema integrity, unique capability/trigger ownership, required skill sections, exhaustive canonical/effective prompt pairing, error-level language rules, fixture mutation detection, acquisition command boundaries, protected paths, deterministic Prompt Kit parity, and CI integration. It does not prove provider obedience, model judgment quality, Windows GUI rendering, credentials/network availability, protected target runtime behavior, technician acceptance, or production success.
