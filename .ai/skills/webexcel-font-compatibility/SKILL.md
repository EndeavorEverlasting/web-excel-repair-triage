# WebExcel Font Compatibility

## Trigger

Use this skill when a workbook is generated, repaired, reformatted, or prepared for Excel for Web; when a producer/configuration source changes; or when an operator has had to manually replace Carlito or another font with Aptos.

Do not use it as authority to change workbook math, evidence, attendance, privacy posture, or product behavior outside the font surface.

## Required inputs

- repository and exact branch/commit;
- `configs/webexcel_fonts_v1.json`;
- the workbook producer, repair script, or configuration files in scope;
- the exact XLSX/XLSM bytes when artifact validation is requested;
- the owning artifact registry or approved output path;
- known visual regressions and required proof ceiling.

## Outputs

- `webexcel-font-validation-result/v1` JSON report;
- artifact filename, size, SHA-256, default font, and explicit-font inventory;
- stable rule IDs and OOXML/source locations for failures;
- `webexcel-font-harness-result/v1` completeness report when harness files change;
- commit, push/PR, and final handoff evidence.

## Procedure

1. Read `AGENTS.md`, the root harness spine, and `harness/webexcel-fonts/`.
2. Preserve dirty work and use an isolated branch/worktree.
3. Classify the task as source, artifact, or harness validation.
4. Run the completeness validator before changing the harness.
5. Search existing producer helpers and configuration before adding font constants.
6. Set the workbook default explicit font to `Aptos`; use `Aptos Display` only for an intentional display/title role.
7. Run the source scan and focused tests.
8. Generate or resolve the exact workbook through its owning artifact workflow.
9. Run the workbook-byte validator and retain the report with artifact identity.
10. Open the same saved artifact in Excel for Web for visual proof when available.
11. Commit coherent tracked changes, push, open/update the PR, and report the exact next executable command.

## Guardrails

- Carlito is forbidden; do not add an exception for a producer or share-ready workbook.
- Do not widen the approved font list to make a failing artifact pass without an explicit compatibility decision.
- Do not treat a manual Excel ribbon edit as canonical generator repair.
- Do not rewrite workbook values, formulas, attendance, workstream allocations, or evidence while repairing font declarations.
- Do not inspect or report private cell contents; font names and package locations are sufficient.
- Do not write generated outputs into `Candidates/` or `Active/`.
- Do not claim browser rendering, print fidelity, or admin acceptance from static validation.

## Validation

```powershell
python -m py_compile scripts\validate_webexcel_fonts.py scripts\validate_webexcel_font_harness.py tests\test_webexcel_font_compatibility.py tests\test_webexcel_font_harness.py
python scripts\validate_webexcel_font_harness.py --output Outputs\webexcel-font-harness.json --summary
python -m unittest tests.test_webexcel_font_compatibility tests.test_webexcel_font_harness -v
python scripts\validate_webexcel_fonts.py --scan-source --output Outputs\webexcel-font-validation.json --summary
python scripts\validate_webexcel_fonts.py --workbook "<artifact>" --require-workbook --output Outputs\webexcel-font-validation.json --summary
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
git diff --check
```

The artifact command is mandatory for a workbook-producing change and may be skipped only when no workbook is produced in the owned harness-only scope; the skip and proof ceiling must be reported.

## Proof ceiling

This skill can prove tracked harness completeness, source-token safety, synthesized regression behavior, and the explicit font declarations in supplied OOXML bytes. It cannot prove Excel for Web rendering, local font installation, print layout, workbook semantics, or recipient acceptance without separate field evidence.
