# AI Harness Prompt Kit V33 Self-Service Generation

## Mission

Generate the final V33 workbook and delivery bundle from the latest working V33 workbook or bundle without rebuilding the package through an Office serializer.

The generator preserves the source prompts and visual lineage, then deterministically enforces the navigation, copy-range, tab-color, and protection contract that was established through operator correction.

## Command

PowerShell:

```powershell
.\scripts\Generate-AIPromptKitV33.ps1 `
  -Source "C:\Artifacts\AI_Harness_Prompt_Kit_v33_bundle.zip"
```

Double-click-compatible CMD:

```text
scripts\Generate-AIPromptKitV33.cmd "C:\Artifacts\AI_Harness_Prompt_Kit_v33_bundle.zip"
```

Optional arguments:

```powershell
.\scripts\Generate-AIPromptKitV33.ps1 `
  -Source "C:\Artifacts\AI_Harness_Prompt_Kit_v33_bundle.zip" `
  -OutDir "Outputs\prompt_kit_v33\operator-run" `
  -GnhfBuildPrompt P39
```

## Source contract

The source may be:

- one `.xlsx` workbook; or
- one `.zip` delivery bundle containing exactly one `.xlsx` workbook.

The source workbook must already contain:

- `Prompt_Library`;
- `Opportunity_Discovery`;
- prompt tabs `P00_COPY_SAFE` through `P44_COPY_SAFE`;
- the intended prompt text and established formatting lineage.

Generated files are written under `Outputs/`. The source workbook or bundle is never overwritten.

## Generated artifacts

```text
AI_Harness_Prompt_Kit_v33.xlsx
AI_Harness_Prompt_Kit_v33_manifest.json
AI_Harness_Prompt_Kit_v33_bundle.zip
```

Non-workbook support files from a source bundle, such as the Night Shift Quickstart and generation record, are preserved in the generated delivery bundle.

## Navigation and exact range contract

The generator discovers the final populated row of column A on each prompt tab.

Each Prompt ID in `Prompt_Library!C2:C46` links to the exact copy range:

```text
'<Prompt ID>_COPY_SAFE'!A1:A<last populated prompt row>
```

Every prompt tab receives four visible return links:

- top-left;
- top-right;
- bottom-left;
- bottom-right.

Each return link selects the complete associated Prompt Library row:

```text
Prompt_Library!A<associated row>:P<associated row>
```

The Prompt Library mouse-navigation rails are also enforced:

- top-left to bottom-left;
- top-right to bottom-right;
- bottom-left to top-left;
- bottom-right to top-right.

## Prompt contract

The generator preserves all P00-P44 prompt content.

P02 is rejected unless it includes executable harness-build ownership, including instructions that agents must:

- build or repair the harness rather than only describe it;
- commit coherent changes;
- push normally when allowed.

This prevents a launch pack from identifying a harness gap without assigning an AI agent to implement it.

## Formatting and color coordination

The source workbook remains the formatting authority for the Prompt Library palette, semantic fonts, prompt layout, widths, heights, fills, and other established visual surfaces.

The finalizer preserves those package parts and enforces a shared cream tab color (`FFF7E6C4`) for:

- `Prompt_Library`;
- `Opportunity_Discovery`;
- `P07_COPY_SAFE`;
- the configured GNHF build prompt tab, default `P39_COPY_SAFE`.

## Protection contract

- Workbook structure is locked.
- Every worksheet is protected.
- `Opportunity_Discovery!A1:R100` remains editable.
- Other workbook surfaces remain locked by default.
- No password or secret is embedded in the repository or generated manifest.

## Manifest

The generated JSON manifest records:

- source and output SHA-256 values;
- every discovered prompt ID, sheet, exact range, and final row;
- cream-colored tabs;
- protection posture;
- the editable range;
- the configured GNHF build prompt.

## Validation

Focused repository validation:

```powershell
python -m py_compile `
  triage/prompt_kit_v33_ooxml.py `
  triage/prompt_kit_v33_generator.py `
  tests/test_prompt_kit_v33_generator.py

python -m pytest tests/test_prompt_kit_v33_generator.py -q
python -m triage.prompt_kit_v33_generator --help
```

The synthetic package tests prove:

- exact full-range Prompt ID links;
- exact full-row backlinks;
- all four Prompt Library mouse-navigation rails;
- cream tab colors;
- workbook and sheet protection;
- editable Opportunity Discovery range;
- P02 harness-build ownership rejection;
- support-file preservation and manifest generation.

## Proof ceiling

This establishes deterministic OOXML generation, exact navigation/range contracts, package-level protection, tab-color enforcement, and synthetic regression coverage.

It does not by itself prove:

- Desktop Excel behavior;
- Excel for Web behavior;
- clipboard output;
- native sheet-protection interaction;
- operator acceptance.

Those remain separate runtime and field-acceptance gates.
