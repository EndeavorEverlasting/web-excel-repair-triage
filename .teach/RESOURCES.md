# /teach Resources

Record only sources actually used to ground teaching. Prefer current repository code, tests, contracts, specifications, and primary/trusted external references. Do not add remembered or hypothetical sources as if they were verified.

## Repository truth

| Path or artifact | Why authoritative for the lesson | Notes |
| --- | --- | --- |
| `AGENTS.md` | Defines the repository-local `/teach` protocol and repository governance. | Current floor: `main@b64221a59db2151f3cdd0d52d0bba0d2661db837`. |
| `harness/capabilities.v1.json` | Machine-readable authority for capability identity, operation, inputs/outputs, implementation kind, linked skill, triggers, and proof ceiling. | Primary evidence for what a capability means in this repository. |
| `CAPABILITIES.md` | Human-readable capability index and explicit statement that a capability exposes an operation while skill explains procedure/judgment. | Secondary explanatory authority; machine registry wins on exact data. |
| `SKILLS.md` | Canonical skill selection policy and ownership rule: skills own repeatable procedure and judgment; deterministic truth remains in code/contracts/registries. | Primary evidence for the skill boundary. |
| `.ai/skills/skill-evaluation/SKILL.md` | Concrete skill showing trigger, inputs, outputs, procedure, guardrails, validation, and proof ceiling. | Representative skill instance for the first diagnostic. |
| `registry/prompts/ai-engineering-level-up-prompts.v1.json` | Canonical Prompt Kit prompt records with task-facing metadata and copyable `copyContent` execution contracts. | Representative prompt-registry evidence for how prompts differ from skills/capabilities. |
| `.ai/skills/fun-nth-artifact-export/SKILL.md` | Concrete domain skill selected by the learner; exposes reusable routing/procedure around an existing deterministic exporter and FUN acceptance boundary. | Primary example for ownership-boundary lesson. |
| `scripts/export_fun_nth_artifact_manifest.py` | CLI adapter that parses runtime inputs and calls the deterministic exporter. | Concrete executable mechanism invoked by the skill. |
| `triage/fun_nth_artifact_export.py` | Deterministic implementation of schema/contract validation, manifest construction, receipt construction, and fail-closed behavior. | Demonstrates that runtime truth is not owned by skill prose. |
| `tests/test_fun_nth_artifact_export.py` | Executable assertions for contract pinning, byte identity, share-tab restrictions, unsupported evidence fields, drift, and publication posture. | Evidence for which invariants survive changes to prose or orchestration. |

## Trusted external references

| Reference | Why trusted / relevant | Notes |
| --- | --- | --- |

## Recording rules

- Add a source when a teaching session actually relies on it.
- Prefer the smallest source set that establishes the mechanism or invariant being taught.
- Distinguish current repository evidence from external background material.
- Do not record secrets, private data, protected URLs, or sensitive learning evidence.
- If a source becomes stale or superseded, note that explicitly rather than silently treating it as current.
