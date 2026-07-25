# Harness Capabilities

This file is the human-readable index for reusable repository operations. The machine-readable root authority is `harness/capabilities.v1.json`; prompt-registry passage and efficiency ownership lives in `harness/prompt-registry/capabilities.v1.json`.

## Selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, and `TRIGGERS.md` first.
2. Select a capability only when one registered trigger matches and no forbidden condition is present.
3. Prefer deterministic scripts or launchers for repeatable operations. Prompts and skills may orchestrate them but are not substitutes for implementation.
4. Report the capability ID, inputs, produced artifacts, validation, and proof ceiling.
5. For prompt passage, load `harness/prompt-registry/execution-profile.v1.json` and only the profile-selected domain capability/skill.
6. For prompt efficiency, run code checks before emitting or consuming LLM judge evidence.

## Active capabilities

| Capability ID | Skill | Implementation | Primary output |
|---|---|---|---|
| `prompt-language-audit` | `.ai/skills/prompt-language-audit/SKILL.md` | `scripts/evaluate_prompt_language.py` | Exhaustive machine-readable prompt disposition and finding report. |
| `skill-evaluation` | `.ai/skills/skill-evaluation/SKILL.md` | Prompt Kit P62 | A repository-native skill eval harness with cases, runner, results, and repair ledger. |
| `skill-factoring` | `.ai/skills/skill-factoring/SKILL.md` | Prompt Kit P61 | Skill ownership dispositions and repaired routing boundaries. |
| `technician-prompt-kit-acquisition` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` | `Acquire-Latest-PromptKit.cmd` | Safely acquired or fast-forwarded checkout and validated Prompt Kit surface. |

## Prompt-registry domain capabilities

| Capability ID | Selected for | Primary output |
|---|---|---|
| `conversation-entry` | Every response and canary-breach recovery. | Two-line `OBJECTIVE` / `REPOS` canary state. |
| `repository-inspection` | `inspect` or `plan` prompt impact. | Evidence inventory, bounded plan, explicit unknowns. |
| `bounded-repository-mutation` | `mutate` or `mixed` prompt impact. | Tracked changes, focused commit, push/PR receipt. |
| `validation-proof-routing` | `validate` prompt impact. | Ordered validation receipts and honest proof ceiling. |
| `integration-handoff` | `integrate` prompt impact. | Preservation/integration mutation and executable next action. |
| `prompt-registry-passage` | Full registry passage or canary-contract change. | One compact execution profile per effective prompt and canary-gap ledger. |
| `prompt-efficiency-evaluation` | Token efficiency, weak-model readiness, prompt judging, or model-response judging is unproven. | Deterministic findings, ordered judge packets, validated judge aggregation, and strict readiness. |

The passage engine performs deterministic impact routing. The efficiency engine performs deterministic checks first, then accepts independent LLM judge results only through the registered JSON contract.

## Evaluation modes

- **Code-based:** required first; measures size, approximate tokens, duplicate lines, oversized lines, structural signals, empty responses, canaries, and response size.
- **LLM as judge:** required for the strict efficiency gate; one prompt or prompt/response pair per case, fixed rubric, JSON-only result.
- **Human:** resolves disputed findings or intentional exceptions.
- **User:** measures real operator completion speed, corrections, abandonment, and usefulness.

## Prompt-language audit modes

- **Audit mode:** evaluates every raw and effective prompt, emits one disposition per prompt, fails on coverage gaps or error-severity contract defects, and may report warning-severity canonical-source repairs.
- **Strict mode:** additionally fails on warning-severity lazy source language.

## Proof boundaries

Capability registration and static tests prove repository integration and deterministic routing. Code efficiency checks prove measurable structure and size. LLM judge results prove rubric-scored model opinion for evaluated cases. None of these alone prove universal model behavior, human acceptance, user productivity, protected runtime access, or production success.
