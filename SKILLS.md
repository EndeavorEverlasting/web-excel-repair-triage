# Skills Index

This is a **selection index**, not a procedure manual. Start with `AGENTS.md` + `harness/CONTEXT.md`; open this file only when the router indicates that a reusable skill is needed.

## Global skill policy

Choose **one primary skill** for the task. Load its `SKILL.md` only after ownership is known. Add a secondary skill only when the task crosses an explicit domain boundary. Do not preload every skill or copy deterministic contracts into skill prose.

Skills own repeatable procedure and judgment. Code, schemas, registries, manifests, validators, and domain contracts own deterministic truth.

## Canonical locations

- Active reusable skills: `.ai/skills/<skill>/SKILL.md`
- Capability ownership: `harness/capabilities.v1.json`
- Trigger routing: `harness/triggers.v1.json`
- Workflow routing: `harness/workflows.v1.json`
- Context routing/budgets: `harness/CONTEXT.md`, `harness/contracts/context-architecture.v1.json`

## Active repository skills

| Skill | Use when | Canonical file |
|---|---|---|
| Harness infrastructure maintenance | harness maps/contracts/workflows/skills drift or context architecture | `.ai/skills/harness-infrastructure-maintenance/SKILL.md` |
| Share artifact alias handoff | create/download a human-facing alias copy without filename encoding or byte drift | `.ai/skills/share-artifact-alias-handoff/SKILL.md` |
| Prompt language audit | prompt language quality/repair | `.ai/skills/prompt-language-audit/SKILL.md` |
| Skill evaluation | skill correctness/quality is unproven | `.ai/skills/skill-evaluation/SKILL.md` |
| Skill factoring | reusable procedure is duplicated or poorly bounded | `.ai/skills/skill-factoring/SKILL.md` |
| Technician Prompt Kit acquisition | open/install/update/edit Prompt Kit across devices | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` |
| Prompt Kit browser-proof cleanup | browser-proof scratch cleanup | `.ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md` |
| Prompt Kit responsive layout | Prompt Kit overlap/responsive layout work | `.ai/skills/prompt-kit-responsive-layout/SKILL.md` |
| Prompt Kit feedback AFK routing | turn accepted explicit feedback into one bounded P115 work request without merge authority | `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md` |

Other domain skills may exist under `.ai/skills/`; route to them only from a selected domain contract or capability.

**Context Engineering System Refactorer** is the Prompt Kit P68 tool for broad model-context systems. Repository-local spec/harness progressive disclosure is P76 and this harness architecture; do not substitute one for the other.

## When to use which skill

Use `harness/triggers.v1.json` when a deterministic trigger owns the choice. Otherwise:
- structure/ownership/context bloat → Harness infrastructure maintenance;
- human-facing artifact download/alias naming → Share artifact alias handoff;
- duplicated reusable procedure → Skill factoring;
- skill quality/evals → Skill evaluation;
- Prompt Kit cross-device acquisition → Technician Prompt Kit acquisition;
- Prompt Kit actionable explicit feedback → Prompt Kit feedback AFK routing;
- prompt wording/audit → Prompt language audit.

If none fits, work directly from the selected workflow/contract rather than loading unrelated skills.

## Full read-before-edit checklist

“Full” means **full for the selected scope**, not “read the repository.”

1. `AGENTS.md` and `harness/CONTEXT.md`.
2. One selected 30,000-foot owner.
3. One primary `SKILL.md` if a reusable skill applies.
4. Exact code/schema/registry/validator/tests being changed.
5. Recent/open Git/PR evidence for overlapping ownership.

Stop loading context once ownership, write surface, validator, artifact, and proof ceiling are resolved.

## Required skill-file sections

Every registered active skill keeps:
- `## Trigger`
- `## Required inputs`
- `## Outputs`
- `## Procedure`
- `## Guardrails`
- `## Validation`
- `## Proof ceiling`

Those headings preserve predictable retrieval without requiring every skill to repeat global governance.
