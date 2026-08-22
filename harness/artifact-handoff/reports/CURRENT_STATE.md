# Artifact Handoff Alias Harness — Current State

## Working surfaces

- Scoped map: `harness/artifact-handoff/CODEBASE_MAP.md`
- Workflow: `harness/artifact-handoff/WORKFLOW.md`
- Machine artifact registry: `harness/artifact-handoff/artifacts.v1.json`
- Contract: `harness/artifact-handoff/contracts/share-alias-download.v1.json`
- Validator: `scripts/validate_artifact_handoff_harness.py`
- Tests: `tests/test_artifact_handoff_harness.py`
- Skill: `.ai/skills/share-artifact-alias-handoff/SKILL.md`

## What is working

The harness distinguishes canonical artifact identity from human-facing delivery identity. It fails closed when an actual alias filename contains URL percent escapes, when the extension changes during a rename-only handoff, when a transport target decodes to the wrong basename, or when validated source/alias bytes differ.

## Known trap closed

Literal `%20` belongs in URL transport encoding only. It must not be baked into the saved filename. The operator should receive a ready-to-share alias and should not have to repair the title manually.

## What remains external

Static repository proof cannot guarantee that SharePoint, Drive, a browser, or another external provider will preserve a displayed/downloaded name. A real provider handoff remains a separate runtime observation after the alias pair passes repository validation.

## Proof ceiling

Tracked harness completeness, deterministic fixtures, and byte-level local pair validation only.
