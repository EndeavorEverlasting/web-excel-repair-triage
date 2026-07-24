# Harness Capabilities

This file is the human-readable index for reusable repository operations. The machine-readable root authority is `harness/capabilities.v1.json`. Domain overlays may register focused operations and routing under their own harness directory without changing the root capability set. A capability exposes an operation; its linked skill explains judgment and procedure; its trigger records when routing is allowed.

## Selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, and `TRIGGERS.md` first.
2. Select a root capability only when one registered root trigger matches and no forbidden condition is present. For domain work, load the domain manifest and trigger registry before selecting its workflow.
3. Prefer deterministic scripts or launchers for repeatable operations. Prompts and skills may orchestrate them but are not substitutes for implementation.
4. Report the root capability ID or domain overlay, inputs, produced artifacts, validation, and proof ceiling.

## Active capabilities

| Capability ID | Skill | Implementation | Primary output |
|---|---|---|---|
| `prompt-language-audit` | `.ai/skills/prompt-language-audit/SKILL.md` | `scripts/evaluate_prompt_language.py` | Exhaustive machine-readable prompt disposition and finding report. |
| `skill-evaluation` | `.ai/skills/skill-evaluation/SKILL.md` | Prompt Kit P62 | A repository-native skill eval harness with cases, runner, results, and repair ledger. |
| `skill-factoring` | `.ai/skills/skill-factoring/SKILL.md` | Prompt Kit P61 | Skill ownership dispositions and repaired routing boundaries. |
| `technician-prompt-kit-acquisition` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` | `Acquire-Latest-PromptKit.cmd` | Safely acquired or fast-forwarded checkout and validated Prompt Kit surface. |

## Domain overlay operations

### Neuron Track Hours monthly artifact overlay

- **Manifest:** `harness/nth/manifest.v1.json`
- **Rule-pack registry:** `harness/nth/monthly-rule-packs.v1.json`
- **Trigger registry:** `harness/nth/triggers.v1.json`
- **Skill:** `.ai/skills/neuron-track-hours-monthly-artifact/SKILL.md`
- **Workflow:** `WORKFLOW.md#h-neuron-track-hours-monthly-artifact`
- **Operation:** Resolve the active NTH month, use roster/attendance as labor-hour truth, apply evidence-first task attribution, build or validate the internal working workbook, and derive the governed client-facing send copy without changing the underlying math or operational story.
- **Outputs:** Internal NTH working artifact, client-facing NTH send copy, and focused NTH validation evidence.
- **Proof ceiling:** Static domain routing/rule-pack proof until an actual workbook is generated and its focused workbook/Excel/client gates are exercised.

The NTH overlay deliberately does not become a competing root capability registry. `harness/capabilities.v1.json` remains the root machine-readable capability authority; `harness/manifest.v1.json` explicitly registers the NTH domain overlay.

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

Capability registration and static tests prove repository integration and deterministic routing contracts. NTH overlay validation proves the tracked month-specific rule, delivery-mode, and routing contract, not a concrete workbook's correctness. These surfaces do not prove provider behavior, model judgment quality, Excel for Web acceptance, Windows GUI acceptance, protected runtime access, client acceptance, or production success unless those surfaces are exercised separately and honestly reported.
