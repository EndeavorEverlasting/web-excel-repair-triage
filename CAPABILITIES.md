# Harness Capabilities

This file is the human-readable index for reusable repository operations. The machine-readable authority is `harness/capabilities.v1.json`. A capability exposes an operation; its linked skill explains judgment and procedure; its trigger records when routing is allowed.

## Selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, and `TRIGGERS.md` first.
2. Select a capability only when one registered trigger matches and no forbidden condition is present.
3. Prefer deterministic scripts or launchers for repeatable operations. Prompts and skills may orchestrate them but are not substitutes for implementation.
4. Report the capability ID, inputs, produced artifacts, validation, and proof ceiling.

## Active capabilities

| Capability ID | Skill | Implementation | Primary output |
|---|---|---|---|
| `prompt-language-audit` | `.ai/skills/prompt-language-audit/SKILL.md` | `scripts/evaluate_prompt_language.py` | Exhaustive machine-readable prompt disposition and finding report. |
| `skill-evaluation` | `.ai/skills/skill-evaluation/SKILL.md` | Prompt Kit P62 | A repository-native skill eval harness with cases, runner, results, and repair ledger. |
| `skill-factoring` | `.ai/skills/skill-factoring/SKILL.md` | Prompt Kit P61 | Skill ownership dispositions and repaired routing boundaries. |
| `technician-prompt-kit-acquisition` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` | `Acquire-Latest-PromptKit.cmd` | Safely acquired or fast-forwarded checkout and validated Prompt Kit surface. |

## Prompt-language audit modes

- **Audit mode:** evaluates every raw and effective prompt, emits one disposition per prompt, fails on coverage gaps or error-severity contract defects, and may report warning-severity canonical-source repairs.
- **Strict mode:** additionally fails on warning-severity lazy source language. Use this after a bounded prompt-repair sprint, not to hide current debt.

Canonical report command:

```powershell
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
```

Strict repair gate:

```powershell
python scripts\evaluate_prompt_language.py --strict --output Outputs\prompt-language-audit-strict.json --summary
```

## Skill-evaluation capability

P62 must identify functional weaknesses and inefficiencies, reproduce them with versioned cases, guide the smallest repair through test-driven development or profiling, validate unit and integration correctness, and measure performance, tool-call, context, cost, retry, and token behavior without weakening quality or safety gates.

## Proof boundaries

Capability registration and static tests prove repository integration and deterministic routing contracts. They do not prove provider behavior, model judgment quality, Windows GUI acceptance, protected runtime access, or production success unless those surfaces are exercised separately and honestly reported.
