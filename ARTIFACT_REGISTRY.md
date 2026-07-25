# Artifact Registry

This registry defines tracked control-plane and runtime artifacts. Machine-readable ownership lives in root and prompt-registry manifests.

## Tracked control-plane artifacts

| Artifact | Path | Validation |
|---|---|---|
| Governance contract | `AGENTS.md` | governance tests |
| Codebase/workflow/artifact indexes | `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md` | harness validator |
| Skill/capability/trigger indexes | `SKILLS.md`, `CAPABILITIES.md`, `TRIGGERS.md` | harness/domain tests |
| Harness manifest | `harness/manifest.v1.json` | `scripts/validate_harness.py` |
| Capability registry | `harness/capabilities.v1.json` and `harness/prompt-registry/capabilities.v1.json` | root/domain tests |
| Trigger registries | `harness/triggers.v1.json` and `harness/prompt-registry/triggers.v1.json` | root/domain tests |
| Prompt passage manifest/schema | `harness/prompt-registry/manifest.v1.json`, `execution-profile.v1.json` | passage tests |
| Conversation canary | `harness/contracts/conversation-canary.v1.json` | passage tests |
| Prompt efficiency policy/fixtures | `harness/prompt-registry/prompt-efficiency-eval.v1.json`, `fixtures/prompt-efficiency-cases.v1.json` | efficiency tests |
| Scoped skills | `.ai/skills/*/SKILL.md` | root/domain tests |
| Prompt Kit interaction contract | `harness/contracts/prompt-kit-interactions.v1.json` | interaction tests/audit |
| Prompt-language policy/fixtures | `harness/evals/**` | Prompt-language audit/tests |
| Operator reports | `harness/reports/*.md` | harness/domain tests |

## Generated runtime artifacts

| Artifact | Default path | Tracking |
|---|---|---|
| Prompt-language audit report | `Outputs/prompt-language-audit.json` | Gitignored; CI artifact allowed |
| Prompt passage audit | `Outputs/prompt-registry-harness-audit.json` | Gitignored; CI artifact allowed |
| Prompt efficiency audit | `Outputs/prompt-efficiency-eval.json` | Gitignored; CI artifact allowed |
| Judge packets | `Outputs/prompt-efficiency-judge-packets.json` | Gitignored; one-case passage evidence |
| Judge results | `Outputs/prompt-efficiency-judge-results.jsonl` | Gitignored; external model evidence |
| Strict efficiency report | `Outputs/prompt-efficiency-eval-strict.json` | Gitignored; downstream gate |
| Candidate model responses | operator-selected `Outputs/*.jsonl` | Gitignored; never commit private transcripts |
| Prompt Kit interaction audit | `Outputs/prompt-kit-interaction-audit.json` | Gitignored; CI artifact allowed |
| Workbook/artifact outputs | `Outputs/` or focused contract path | Gitignored unless sanitized and approved |

## Protected inputs

- `Candidates/` and `Active/` are read-only.
- Private workbooks, transcripts, candidate responses, judge outputs, credentials, and model-provider payloads must not be committed.
- Generated output must not replace canonical sources without deterministic regeneration and validation.

## Artifact lifecycle

Declare owner, source, destination, schema, and proof ceiling; generate through a registered script; validate; deliver from the contract path; record commit/PR or artifact digest; clean only known outputs.

## Proof boundaries

File/schema presence proves integration. Code metrics prove measurable size and structure. LLM judge results prove rubric-scored model opinion for evaluated cases. Human resolution, user productivity, browser behavior, live runtime, and production acceptance remain separate proof lanes.
