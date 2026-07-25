# Prompt Registry Passage — Operator Report

## Status

The prompt registry now has a dedicated harness design for exhaustive passage, compact execution profiles, deterministic capability/skill routing, token-efficient shared instruction references, and the `OBJECTIVE`/`REPOS` conversation canary.

## Working

- Effective prompts are loaded through the canonical combined registry builder.
- Every prompt receives exactly one compact execution profile and one primary capability/skill.
- Full prompt bodies are excluded from profiles and runtime reports.
- Shared canary, skill, actionability, and workflow instructions are referenced rather than copied.
- Non-strict audit mode reports canary coverage without blocking a harness-only change.
- Strict canary mode is available as the downstream prompt-product completion gate.
- Domain tests, root pre-push, and harness CI own the deterministic checks.

## Current gap

Canonical prompts do not yet contain the new conversation canary. That is intentionally visible as `canary-missing` product debt. This harness sprint does not edit prompt registries, builders, JavaScript, or generated Prompt Kit HTML.

## How to pass through prompts

1. Run the full audit.
2. Use `passage_order` to visit prompts in canonical sequence.
3. Load the compact profile for the selected prompt.
4. Follow its `primary_capability`, `primary_skill`, and `shared_instruction_refs`.
5. Record model adherence separately; leave a chat when the canary stops appearing or becomes materially wrong.

## Validation

```powershell
python -m unittest tests.test_prompt_registry_harness -v
python scripts\audit_prompt_registry_harness.py --output Outputs\prompt-registry-harness-audit.json --summary
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

## Proof ceiling

The harness can prove complete deterministic prompt inventory, compact profile coverage, connected capability/skill routing, report generation, and static canary inclusion when strict mode passes. It cannot prove that a model will retain or obey the canary over a long conversation; that requires repeated model-run evidence.
