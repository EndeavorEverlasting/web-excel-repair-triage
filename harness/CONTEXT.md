# Repository Context Router

This is the **50,000-foot** entry point after `AGENTS.md`. Its job is routing, not teaching the whole repository.

## Default load

Load only:

1. `AGENTS.md`
2. this file

Then choose one domain. Do not eagerly read root contracts, skills, manifests, reports, schemas, fixtures, or implementation files.

## Route by task

| Task | 30,000-foot owner | 15,000-foot detail only when needed |
|---|---|---|
| Harness/spec structure, context bloat | `CODEBASE_MAP.md` | `.ai/skills/harness-infrastructure-maintenance/SKILL.md`, selected harness contract/validator |
| Checkout/use/worktree/entrypoint path | `harness/canonical-paths.v1.json` | `harness/workflows/canonical-paths.md`; P92 for deep repair |
| **Artifact creation / derivation** | `harness/artifact-derivation/CODEBASE_MAP.md` | `.ai/skills/artifact-derivation/SKILL.md`, `harness/artifact-derivation/contracts/create-new-from-source.v1.json` |
| Human-facing artifact alias/download handoff | `harness/artifact-handoff/CODEBASE_MAP.md` | `.ai/skills/share-artifact-alias-handoff/SKILL.md`, `harness/artifact-handoff/contracts/share-alias-download.v1.json` |
| Prompt Kit use/acquisition | `PROMPT_KIT_ACCESS.md` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` |
| Prompt authoring/repair/language | `harness/specs/prompt-operations.md` | selected registry, prompt skill, builder, validator |
| Workbook/Web Excel artifact behavior | `CODEBASE_MAP.md` → artifact-engine route | selected workflow/contract/engine/test |
| Billing/NTH/operator evidence | `harness/specs/billing-artifact-safety.md` | selected NTH contract/skill/validator |
| Technician delivery/live certification | `harness/specs/operator-delivery.md` | selected launcher/workflow/validator |
| PR integration | `harness/contracts/pr-merge-gate.v1.json` | `WORKFLOW.md#e-pr-floor-cleanup-and-integration` |

## Artifact creation reflex
For create/generate/build/produce/make/draft/export work, an existing matching artifact is a **read-only source/reference by default**. Select a distinct output identity before a writer is opened. Same subject, month, audience, or filename family does not authorize in-place mutation. Only an explicit update/repair-in-place request can cross that boundary.

## Zoom rules

- **50,000 ft:** identify ownership, canonical entry point, and proof gate. Soft target: <= 1,000 approximate repo-specific tokens.
- **30,000 ft:** load one selected domain/capability. Soft target: <= 2,000 additional approximate tokens for the selected domain.
- **15,000 ft:** load one selected workflow/spec/skill plus the exact implementation evidence needed. Soft target: <= 4,000 additional approximate tokens.
- Code, full schemas, fixtures, old reports, historical plans, generated files, and unrelated skills are demand-loaded.

If a safety or correctness dependency exceeds a soft target, load it and record why. Token economy never outranks correctness.

## Stop conditions

Stop expanding context when the task owner, write surface, validator, artifact, and proof ceiling are known. Search deeper only to resolve a concrete ambiguity or failure. Prefer canonical references over copied summaries.
