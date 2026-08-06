# Workbook Visual Integrity Codebase Map

## Entry order

1. Read root `AGENTS.md`; do not modify it in this lane.
2. Read root `CODEBASE_MAP.md`, `WORKFLOW.md`, and `ARTIFACT_REGISTRY.md`.
3. Read `configs/workbook_visual_integrity_v1.json` for canonical colors, fonts, proof boundaries, and stable rule IDs.
4. Select the artifact profile under `harness/workbook-visual-integrity/profiles/`.
5. Inspect `generator-bindings.v1.json` and `fun-triage-contract.v1.json` before generating or accepting an artifact.
6. Run the completeness validator, focused tests, profile audit, exact-workbook validator, and existing repository gates.

## Structure

```text
configs/workbook_visual_integrity_v1.json       canonical policy and semantic palette
schemas/workbook-visual-profile.schema.json     profile contract
schemas/workbook-visual-validation-result.schema.json result contract
harness/workbook-visual-integrity/
  CODEBASE_MAP.md                               this map
  WORKFLOWS.md                                  pickup, validation, failure, handoff
  ARTIFACT_REGISTRY.md                          generated reports and naming
  registry.json                                 machine-readable harness inventory
  generator-bindings.v1.json                    artifact-family producer bindings
  fun-triage-contract.v1.json                   cross-repo receipt ownership
  profiles/*.json                               exact artifact-family visual profiles
scripts/validate_workbook_visual_integrity.py   OOXML profile/artifact validator
scripts/validate_workbook_visual_harness.py     completeness validator
tests/test_workbook_visual_integrity.py         synthesized workbook regressions
tests/test_workbook_visual_harness.py           component and integration regressions
.ai/skills/workbook-visual-integrity/SKILL.md   repeatable operator/agent procedure
.github/workflows/workbook-visual-integrity.yml exact-head CI gate
reports/harness/workbook-visual-integrity-state.md human-readable state
```

## Existing authorities reused

- `configs/spreadsheet_style_v1.json` — broad slate presentation system.
- `configs/workbook_visual_design_v1.json` — visual hierarchy and function-first doctrine.
- `configs/webexcel_fonts_v1.json` — Aptos/Aptos Display and Carlito prohibition.
- Existing artifact-specific generators and validators remain product owners; this harness does not rewrite them.

## Entry points

```powershell
python scripts\validate_workbook_visual_harness.py --output Outputs\workbook-visual-harness.json --summary
python scripts\validate_workbook_visual_integrity.py --validate-profiles --output Outputs\workbook-visual-profile-audit.json --summary
python scripts\validate_workbook_visual_integrity.py --workbook <artifact.xlsx> --profile <profile.json> --output Outputs\workbook-visual-validation.json --summary
python scripts\validate_workbook_visual_integrity.py --workbook <styled.xlsx> --baseline <pre-style.xlsx> --profile <profile.json> --output Outputs\workbook-visual-validation.json --summary
```

## Known traps

- A valid XLSX can still have one row styled with the preceding range because the generator wrote the wrong inclusive boundary.
- Same-date formatting is a bounded May exception, not a general NTH rule; July rows are colored by primary workstream.
- A chart palette is not a cell palette.
- Similar-looking fills with different RGB values are contract drift.
- A style-only pass may not change formulas, values, sheet order, merges, table ranges, or calculation behavior.
- Current private workbooks are runtime inputs and must not be committed as fixtures.
- Static OOXML proof does not establish Excel for Web rendering or operator acceptance.
