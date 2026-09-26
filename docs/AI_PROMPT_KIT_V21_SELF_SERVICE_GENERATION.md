# AI Harness Prompt Kit V21 Self-Service Generation

This document outlines the deterministic, self-service generation workflow for the AI Harness Prompt Kit V21 workbook.

## Setup and Requirements

1. **Source Bundle**: The process requires the authoritative AI Harness Prompt Kit V20 bundle ZIP file.
   - Required V20 Source Workbook SHA-256: `9b0934ef7bca9b308bf605c9be0c98f75f420c92d5a3f6e1995df1465747c076`
2. **Environment**: A standard Python 3.11+ environment.

## Running Generation

The generation can be triggered using either the PowerShell launcher or the double-click compatible CMD wrapper.

### PowerShell Launcher

Run the following command:

```powershell
.\scripts\Generate-AIPromptKitV21.ps1 -SourceBundle "C:\Users\Cheex\Downloads\AI_Harness_Prompt_Kit_v20_bundle.zip"
```

### CMD Wrapper

Alternatively, run the batch script:

```cmd
scripts\Generate-AIPromptKitV21.cmd "C:\Users\Cheex\Downloads\AI_Harness_Prompt_Kit_v20_bundle.zip"
```

## Bounded OOXML Generation & Materialization

The generator logic and templates are packaged as checksum-verified base64 source text inside `triage/prompt_kit_v21_impl.parts/payload.b64`.

At runtime, `triage/prompt_kit_v21_generator.py`:
1. Verifies the V20 source hash to prevent silent drift;
2. Dynamically materializes the zip payload containing the generator module and assets;
3. Imports the module dynamically using `zipimport`;
4. Edits the OOXML structure and outputs `AI_Harness_Prompt_Kit_v21.xlsx` and the delivery bundle;
5. Fails closed if the output workbook does not match the exact accepted V21 SHA-256:
   - Output SHA-256: `47cfe3ca37f5ebba4ac056ee001d2dad69bd4dee81d7b7be0f7cf83affe4ba9b`

## Regression Checks

Two key repair causes are programmatically validated on the output workbook:
1. **TargetMode check**: Ensure same-workbook drawing hyperlinks do not use `TargetMode="External"`.
2. **calcChain check**: Ensure `calcChain.xml` uses the worksheet `sheetId` (e.g. `sheetId="28"`), not worksheet ordinal position.
