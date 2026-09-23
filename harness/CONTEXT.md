# Repository Context Router

This is the **50,000-foot** entry point after `AGENTS.md`. Its job is routing, not teaching the repository.

## Default load

Load only:

1. `AGENTS.md`
2. this file

Then choose one domain. Do not eagerly read root contracts, skills, manifests, reports, schemas, fixtures, or implementation files.

## Route by task

| Task | 30,000-foot owner | 15,000-foot detail only when needed |
|---|---|---|
| Harness/spec structure, context bloat | `CODEBASE_MAP.md` | harness-infrastructure skill + contract/validator |
| Boundary-to-sprint routing | `CODEBASE_MAP.md` → `TRIGGERS.md` (`harness-infrastructure-change`) | capability `execution-boundary-continuation` + harness-infrastructure workflow/skill |
| Artifact creation / derivation | `harness/artifact-derivation/CODEBASE_MAP.md` | artifact-derivation skill + create-new-from-source contract |
| Repo-native codegen | `harness/repo-native-update/CODEBASE_MAP.md` | contract + `scripts/run_repo_native_update.py` |
| Artifact alias/download handoff | `harness/artifact-handoff/CODEBASE_MAP.md` | share-alias skill + share-alias-download contract |
| Prompt Kit use/acquisition | `PROMPT_KIT_ACCESS.md` | technician-prompt-kit-acquisition skill |
| Ad campaign prompts/workflow | `harness/ad-campaign/CODEBASE_MAP.md` | campaign contract, CLI, or prompt |
| Prompt authoring/repair/language | `harness/specs/prompt-operations.md` | registry, prompt skill, builder, validator |
| Donor / registered external source / prompt prior-art | `operant-external-resource-intake` skill | contract `sources[]`; `python scripts/prompt_registry_ops.py prior-art --query "<terms>"` → P79 |
| Workbook/Web Excel behavior | `CODEBASE_MAP.md` → artifact-engine | selected workflow/contract/engine/test |
| Billing/NTH/operator evidence | `harness/specs/billing-artifact-safety.md` | selected NTH contract/skill/validator |
| Technician delivery/live cert | `harness/specs/operator-delivery.md` | selected launcher/workflow/validator |
| PR integration | `harness/contracts/pr-merge-gate.v1.json` | `WORKFLOW.md#e-pr-floor-cleanup-and-integration` |

## Artifact creation reflex
Create/generate/build/produce/make/draft/export: an existing matching artifact is **read-only by default**. Choose a distinct output identity before writing. Same subject/month/filename does not authorize overwrite; only explicit update/repair-in-place may.

## Zoom rules

- **50,000 ft:** ownership, entry, proof gate. Soft target: <= 1,000 repo-specific tokens.
- **30,000 ft:** one selected domain/capability. Soft target: <= 2,000 additional tokens.
- **15,000 ft:** one workflow/spec/skill plus exact implementation evidence. Soft target: <= 4,000 additional tokens.
- Code, schemas, fixtures, old reports, historical plans, generated files, and unrelated skills are demand-loaded.

If a safety/correctness dependency exceeds a soft target, load it and record why. Token economy never outranks correctness.

## Stop conditions

Stop expanding context when the task owner, write surface, validator, artifact, and proof ceiling are known. Search deeper only for concrete ambiguity or failure. Prefer canonical references over copied summaries.
