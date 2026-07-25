# Prompt Registry Harness Codebase Map

## Reading order

1. `AGENTS.md` for repository law.
2. `harness/prompt-registry/manifest.v1.json` for the complete domain inventory.
3. `harness/contracts/conversation-canary.v1.json` for the universal response canary.
4. `harness/prompt-registry/execution-profile.v1.json` for compact per-prompt metadata.
5. `harness/prompt-registry/capabilities.v1.json` and `triggers.v1.json` for deterministic routing.
6. The selected `.ai/skills/*/SKILL.md`.
7. `harness/prompt-registry/WORKFLOW.md` for passage, validation, failure, and handoff.
8. `harness/reports/PROMPT_REGISTRY_PASSAGE.md` for operator state.

## Structure

```text
harness/
├── contracts/conversation-canary.v1.json
├── prompt-registry/
│   ├── manifest.v1.json
│   ├── capabilities.v1.json
│   ├── triggers.v1.json
│   ├── execution-profile.v1.json
│   ├── CODEBASE_MAP.md
│   ├── WORKFLOW.md
│   └── ARTIFACT_REGISTRY.md
└── reports/PROMPT_REGISTRY_PASSAGE.md

.ai/skills/
├── conversation-entry-canary/SKILL.md
├── repository-inspection/SKILL.md
├── bounded-repository-mutation/SKILL.md
├── validation-proof-routing/SKILL.md
├── integration-handoff/SKILL.md
└── prompt-registry-passage/SKILL.md

Full paths:
- `.ai/skills/conversation-entry-canary/SKILL.md`
- `.ai/skills/repository-inspection/SKILL.md`
- `.ai/skills/bounded-repository-mutation/SKILL.md`
- `.ai/skills/validation-proof-routing/SKILL.md`
- `.ai/skills/integration-handoff/SKILL.md`
- `.ai/skills/prompt-registry-passage/SKILL.md`

scripts/prompt_registry_harness_contracts.py
scripts/prompt_registry_profiles.py
scripts/audit_prompt_registry_harness.py
tests/test_prompt_registry_harness.py
```

## Canonical prompt inputs

- `docs/prompts.json`
- `registry/prompts/skill-development-prompts.v1.json`
- `registry/prompts/actionable-next-step-policy.v1.json`
- `scripts/build_prompt_kit_registry.py`

The auditor consumes the **effective** registry through `load_prompt_registry()`. It does not scrape generated HTML and does not duplicate full prompt text into profiles.

## Entry points

| Entry point | Purpose |
|---|---|
| `python scripts/audit_prompt_registry_harness.py --summary` | Inventory and profile every effective prompt. |
| `python scripts/audit_prompt_registry_harness.py --prompt P07 --summary` | Inspect one compact profile. |
| `python scripts/audit_prompt_registry_harness.py --strict-canary --summary` | Downstream gate after prompt product mutation. |
| `python -m unittest tests.test_prompt_registry_harness -v` | Domain contract/completeness tests. |

## Known traps

- A missing canary in the current prompts is a **product gap**, not a harness failure in non-strict mode.
- Static prompt inclusion does not prove that a provider or model will obey the canary.
- Do not add repeated skill procedures or canary prose to every execution profile; use references.
- Do not edit `docs/prompts.json`, prompt extensions, the builder, JavaScript, or generated HTML in this harness lane.
