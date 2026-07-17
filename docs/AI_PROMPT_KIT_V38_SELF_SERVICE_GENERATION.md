# AI Harness Prompt Kit V38 Self-Service Generation

## Mission

Generate `AI_Harness_Prompt_Kit_v38.xlsx` from the field-open V37 workbook without rebuilding or reserializing the package.

V38 owns one bounded repair: every `P##_COPY_SAFE` tab receives clickable copy-range cells at `C1` and `C<last prompt row>`, and the existing calculation chain is synchronized. The Prompt Library already supplies the exact canonical `A1:A<n>` targets.

## Canonical commands

PowerShell:

```powershell
.\scripts\Generate-AIPromptKitV38.ps1 `
  -Source "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx"
```

Double-click-compatible CMD:

```text
scripts\Generate-AIPromptKitV38.cmd "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx"
```

Direct Python:

```powershell
python -m triage.prompt_kit_v38_generator `
  --source "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx" `
  --out-dir "Outputs\prompt_kit_v38" `
  --expected-prompt-count 45 `
  --json
```

## Source contract

The source may be:

- the field-open V37 `.xlsx`; or
- a delivery `.zip` containing exactly one V37 workbook.

The source is never overwritten. The default output root is `Outputs/prompt_kit_v38/`.

## Generated artifacts

```text
AI_Harness_Prompt_Kit_v38.xlsx
AI_Harness_Prompt_Kit_v38_manifest.json
AI_Harness_Prompt_Kit_v38_bundle.zip
```

Support files from an input bundle are preserved in the output bundle. Workbook binaries and operator-local reports remain generated outputs and must not be committed.

## Package boundary

The canonical V38 generator delegates workbook mutation to `triage.prompt_kit_copy_range_links`.

Allowed changes:

- the 45 prompt worksheet parts;
- `xl/calcChain.xml`, when it already exists and needs the new formula entries.

Forbidden changes include workbook metadata, relationships, content types, styles, shared strings, theme, properties, sheet order, protection, ZIP member set, and ZIP member order.

Excel automation, LibreOffice, `openpyxl`, and any other whole-workbook serializer are forbidden for this conversion.

## Fail-closed gates

Generation fails when:

- the source is missing or is not an `.xlsx`/single-workbook bundle;
- the Prompt Library exact range links are missing or malformed;
- the prompt-tab copy-label cells are absent;
- the discovered prompt count differs from 45 by default;
- fewer or more than 90 links are produced;
- a non-prompt worksheet part changes;
- calculation-chain identities are stale or incomplete;
- a second generation pass is not byte-identical.

## Validation

```powershell
python -m py_compile triage/prompt_kit_v38_generator.py tests/test_prompt_kit_v38_generator.py
python -m pytest tests/test_prompt_kit_copy_range_links.py tests/test_prompt_kit_v38_generator.py -q
python -m triage.prompt_kit_v38_generator --help
```

Then run the existing package, worksheet, copy-surface, operability, and Web Excel compatibility validators against the generated workbook.

## Compatibility posture

The older `prompt_kit_v33_*` modules remain compatibility internals on the stacked branch. They are not the canonical operator entrypoint for the accepted V37-to-V38 conversion.

## Proof ceiling

Repository tests and the V38 manifest may prove exact formula generation, package boundaries, calculation-chain integrity, output naming, bundle construction, and byte idempotence. Excel for Web opening and click-selection behavior remain the final operator field gate.
