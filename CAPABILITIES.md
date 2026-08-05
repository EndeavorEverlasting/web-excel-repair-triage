# Harness Capabilities

This file is the human-readable index for reusable repository operations. The machine-readable authority is `harness/capabilities.v1.json`. A capability exposes an operation; its linked skill explains procedure and judgment; its trigger records deterministic routing.

## Selection rules

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `WORKFLOW.md`, and `TRIGGERS.md`.
2. Select a capability only when one registered trigger matches and no forbidden condition is present.
3. Prefer deterministic scripts or launchers. Prompts and skills may orchestrate them but are not substitutes for implementation.
4. Report the capability ID, inputs, produced artifacts, validators, and proof ceiling.
5. Keep one explicit owner for shared registries, workflows, generated outputs, branches, and PRs.

## Active capabilities

| Capability ID | Skill | Implementation | Primary output |
|---|---|---|---|
| `harness-infrastructure-maintenance` | `.ai/skills/harness-infrastructure-maintenance/SKILL.md` | `scripts/validate_harness.py` | Canonical harness repairs plus `harness-completeness-report/v1`. |
| `prompt-language-audit` | `.ai/skills/prompt-language-audit/SKILL.md` | `scripts/evaluate_prompt_language.py` | Exhaustive prompt disposition and finding report. |
| `skill-evaluation` | `.ai/skills/skill-evaluation/SKILL.md` | Prompt Kit P62 | Repository-native eval harness, cases, runner, results, and repair ledger. |
| `skill-factoring` | `.ai/skills/skill-factoring/SKILL.md` | Prompt Kit P61 | Skill ownership dispositions and repaired routing boundaries. |
| `technician-prompt-kit-acquisition` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` | `Acquire-Latest-PromptKit.cmd` | Safely acquired or fast-forwarded checkout and validated Prompt Kit surface. |

## Harness infrastructure capability

The `harness-infrastructure-maintenance` capability owns maps, workflow/artifact/validator/capability/trigger registries, completeness validation, harness tests, staged-index and pre-push hooks, harness CI, skills, and operator reports. It explicitly excludes `AGENTS.md` governance, product implementation, secrets, destructive cleanup, and production deployment.

Canonical report command:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

## Prompt-language audit modes

- **Audit mode:** evaluates every raw and effective prompt, emits one disposition per prompt, fails coverage gaps and error-severity defects, and may report warning-severity canonical-source debt.
- **Strict mode:** also fails warning-severity lazy source language. Use after bounded canonical repair.

## Skill-evaluation capability

P62 must reproduce functional weaknesses and inefficiencies with versioned cases, guide the smallest valid repair through tests or profiling, validate unit/integration correctness, and measure performance, tool calls, context, cost, retries, and tokens without weakening safety or routing.

## Proof boundaries

Capability registration, static validators, tests, and CI prove only the repository surfaces and commands exercised on the tested commit. They do not prove provider behavior, model judgment, Excel for Web, Windows GUI, browser behavior, credentials, network, protected runtime access, technician acceptance, deployment, or production success.
