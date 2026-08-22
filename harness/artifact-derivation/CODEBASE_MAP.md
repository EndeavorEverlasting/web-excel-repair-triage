# Artifact Derivation Harness — Codebase Map

## Purpose
This overlay owns the create-versus-update safety seam for Triage artifact production. Triage remains the workbook/artifact producer; this harness prevents a creation request from being routed into an in-place source mutation merely because a good reference artifact already exists.

## Key surfaces
- `harness/CONTEXT.md` — fresh-agent router.
- `ARTIFACT_REGISTRY.md` and `harness/artifacts.v1.json` — artifact families and protected inputs.
- `harness/artifact-derivation/contracts/create-new-from-source.v1.json` — derivation policy.
- `scripts/validate_artifact_derivation_harness.py` — static completeness and runtime preflight.
- `.ai/skills/artifact-derivation/SKILL.md` — repeatable procedure.
- focused artifact engine/validator — content generation and correctness remain with the owning engine.

## Entry points and configuration
1. Read `AGENTS.md`, then `harness/CONTEXT.md`.
2. Resolve the owning artifact engine through `CODEBASE_MAP.md` and the artifact registry.
3. Resolve available source/reference artifacts under protected/local/provider surfaces.
4. Run derivation preflight before any artifact write.
5. Generate only into the distinct output identity and run the focused engine validator.

## Build / test / deploy commands
- Inspect: `python scripts/validate_artifact_derivation_harness.py --summary`
- Runtime preflight: `python scripts/validate_artifact_derivation_harness.py --request-text "create June NTH" --source path:Candidates/reference.xlsx --output path:Outputs/June_NTH_candidate.xlsx --summary`
- Tests: `python -m unittest tests.test_artifact_derivation_harness -v`
- Existing harness: `python scripts/validate_harness.py --report Outputs/harness-completeness-report.json`
- Publish/deliver: only after the new artifact passes its engine preflight/manifest/package gates.

## Known trap closed
A source workbook can be the best template and evidence source without being the output target. `Candidates/` and `Active/` remain protected inputs, and a create request must not overwrite a current workbook anywhere else either.
