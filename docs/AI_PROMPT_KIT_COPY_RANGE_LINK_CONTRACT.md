# AI Prompt Kit Copy-Range Link Contract

## Non-negotiable workbook behavior

Every `P##_COPY_SAFE` prompt tab has two cells that state the exact copy range:

- top: `C1`
- bottom: `C<last prompt row>`

Both cells must be clickable internal `HYPERLINK()` formulas targeting the complete prompt payload on the same sheet.

Example:

```excel
=HYPERLINK("#'P01_COPY_SAFE'!A1:A17","Copy A1:A17 only")
```

The target must exactly match the corresponding Prompt Library ID link. A text-only `Copy A1:A<n> only` cell is a failed artifact.

## Why this is a harness contract

This behavior is generated and validated by the repository. It is not a manual post-processing instruction and must not depend on an operator remembering to repair every prompt tab.

Authority:

- generator integration: `triage/prompt_kit_v33_generator.py`
- package-preserving patcher and validator: `triage/prompt_kit_copy_range_links.py`
- regression test: `tests/test_prompt_kit_copy_range_links.py`
- CI: `.github/workflows/prompt-kit-v21.yml`

## Compatibility lane

The field-accepted V37 workbook established the package baseline. The range-link operation may change only:

- each affected `xl/worksheets/sheetN.xml` prompt part;
- `xl/calcChain.xml`, when that part already exists and requires the new formula cells.

The operation must preserve byte-for-byte:

- `xl/workbook.xml` and workbook calculation metadata;
- workbook and worksheet relationship parts;
- `[Content_Types].xml`;
- `xl/styles.xml`;
- `xl/sharedStrings.xml`;
- theme and document properties;
- sheet order, tab colors, protection, ZIP member set, and ZIP member order.

Do not load and save the workbook through Excel automation, LibreOffice, `openpyxl`, or another whole-workbook serializer for this repair. The patcher edits only the existing copy-label cell records, retains their style IDs, writes cached display text, and synchronizes the existing calculation chain.

## Required validation

A candidate passes the repository gate only when:

1. every Prompt Library P-ID link targets a valid `A1:A<n>` prompt range;
2. both copy-label cells on every prompt tab contain the matching same-sheet formula;
3. the cached value remains `Copy A1:A<n> only`;
4. formula count grows by exactly two per prompt, or by zero on an idempotent rerun;
5. every formula cell is represented in an existing `calcChain.xml`;
6. no package members are added, removed, or reordered;
7. every non-target package part remains byte-identical;
8. the patch is byte-for-byte idempotent;
9. Excel for Web opens the exact output without repair, crash, refusal, or unresponsiveness.

## Operator command

```powershell
python -m triage.prompt_kit_copy_range_links `
  --source "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx" `
  --output "Outputs\AI_Harness_Prompt_Kit_v38.xlsx" `
  --report "Outputs\AI_Harness_Prompt_Kit_v38_copy_range_links.json"
```

Excel for Web remains the final field judge. Static validation must never be reported as field acceptance.
