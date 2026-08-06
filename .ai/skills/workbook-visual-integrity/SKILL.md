# Workbook Visual Integrity

## Trigger

Use this skill when a generated or restyled workbook must preserve canonical cell colors, fonts, borders, alignment, tab/layout conventions, paired visual ranges, or exact inclusive range boundaries. Trigger it especially after a row, date block, workstream, summary table, or artifact family has drifted from its accepted formatting.

## Required inputs

- repository and exact commit/branch;
- generated workbook path and artifact-family profile;
- preserved pre-style baseline when the task is style-only;
- generator manifest or registry path;
- current visual policy, font policy, and artifact-specific semantic/package validators;
- operator-reported formatting defect or accepted reference evidence when available.

## Outputs

- exact generated workbook identity;
- `triage-workbook-visual-validation-result/v1` JSON;
- profile/policy hashes and stable rule findings;
- repaired profile/harness tests when the contract was missing;
- generator repair handoff when product code is outside the current lane;
- explicit Excel for Web field-proof status.

## Procedure

1. Read root governance and the visual-integrity codebase map/workflow.
2. Resolve the profile through `registry.json` and `generator-bindings.v1.json`.
3. Run completeness and profile audit before validating a workbook.
4. Generate or obtain the exact candidate bytes without overwriting protected inputs.
5. Run the Aptos font gate.
6. Run visual validation; include `--baseline` for every style-only pass.
7. On a failure, repair the owning range/profile/generator and add a focused mutation test; do not hand-fix only the current cell.
8. Run semantic/package gates and ensure every receipt names the same artifact SHA-256.
9. Open those exact bytes in Excel for Web for operator review.
10. Hand off with artifact/profile/policy identity, validation proof, field gaps, Git state, and one exact next command.

## Guardrails

- Do not modify `AGENTS.md` in a harness lane.
- Do not change values, formulas, sheet order, merges, table ranges, or calculation behavior during style-only work.
- Do not use dates or people as general color categories; only a bounded profile exception may do so.
- Do not reuse one fill for two legend meanings in the same profile.
- Do not invent a global color for an artifact-specific role.
- Do not treat a chart palette, process exit code, package-open success, or screenshot as complete visual proof.
- Do not commit private workbook bytes or cell text in fixtures or reports.
- Do not claim Excel for Web acceptance without opening the exact validated bytes.

## Validation

```powershell
python scripts\validate_workbook_visual_harness.py --output Outputs\workbook-visual-harness.json --summary
python -m unittest tests.test_workbook_visual_integrity tests.test_workbook_visual_harness -v
python scripts\validate_workbook_visual_integrity.py --validate-profiles --output Outputs\workbook-visual-profile-audit.json --summary
python scripts\validate_workbook_visual_integrity.py --workbook <artifact.xlsx> --profile <profile.json> --output Outputs\workbook-visual-validation.json --summary
```

For a style-only pass, add `--baseline <pre-style.xlsx>` and require `WVI007` count zero. Then run font, artifact-specific semantic/package, root harness, broad tests, and `git diff --check`.

## Proof ceiling

Passing static checks proves tracked profile/harness completeness and the exercised OOXML colors, styles, boundaries, paired ranges, layout, and baseline preservation. It does not prove Excel for Web rendering, subjective visual quality, print fidelity, evidence truth, workbook math, or recipient acceptance.
