# Prompt Registry Harness Artifact Registry

## Tracked artifacts

| Artifact | Path | Owner | Validation |
|---|---|---|---|
| Domain manifest | `harness/prompt-registry/manifest.v1.json` | harness lane | domain tests/auditor |
| Canary contract | `harness/contracts/conversation-canary.v1.json` | harness lane | domain tests |
| Execution-profile schema | `harness/prompt-registry/execution-profile.v1.json` | harness lane | domain tests/auditor |
| Capability registry | `harness/prompt-registry/capabilities.v1.json` | harness lane | domain tests/auditor |
| Trigger registry | `harness/prompt-registry/triggers.v1.json` | harness lane | domain tests/auditor |
| Scoped skills | `.ai/skills/*/SKILL.md` paths in domain manifest | harness lane | domain tests |
| Contract validator | `scripts/prompt_registry_harness_contracts.py` | harness lane | unit tests/CI |
| Profile engine | `scripts/prompt_registry_profiles.py` | harness lane | unit tests/CI |
| Auditor CLI | `scripts/audit_prompt_registry_harness.py` | harness lane | unit tests/CI |
| Operator report | `harness/reports/PROMPT_REGISTRY_PASSAGE.md` | harness lane | domain tests |

## Runtime artifacts

| Artifact | Default path | Schema | Tracking |
|---|---|---|---|
| Full passage audit | `Outputs/prompt-registry-harness-audit.json` | `prompt-registry-harness-audit-result/v1` | Gitignored; CI artifact allowed |
| Strict canary audit | `Outputs/prompt-registry-canary-strict.json` | same schema with `strict_canary=true` | Gitignored; downstream product gate |

## Compact profile rules

Profiles contain IDs, routing, impacts, context/proof classes, source identity, shared references, and token metrics. They must not contain `copyContent`, full prompt text, or duplicated skill/canary prose.

## Naming

- Tracked contracts and registries: explicit `v1` schema/version.
- Runtime reports: stable family names under `Outputs/`.
- Skill directories: lower-case kebab-case.
- Findings: stable IDs such as `canary-missing` and `profile-coverage-gap`.

## Proof boundary

These artifacts prove repository integration, deterministic effective-prompt coverage, routing consistency, compactness, and static canary inclusion. They do not prove provider obedience, model quality, context-window survival, runtime tool behavior, or successful repository mutation.
