# AI Harness Prompt Kit V33 Self-Service Generation

## One canonical path

`triage.prompt_kit_v33_generator` is the V33 orchestration authority. It calls the declarative finalizer and accepted-layout finalizer, normalizes the saved OOXML package, runs focused validators, and writes one delivery bundle. The retired PR #64 raw-OOXML implementation is not a second engine.

Use PowerShell:

```powershell
.\scripts\Generate-AIPromptKitV33.ps1 `
  -Source ".\Artifacts\AI_Harness_Prompt_Kit_v33.xlsx" `
  -OutDir ".\Outputs\prompt-kit-v33"
```

Or double-click/run:

```text
scripts\Generate-AIPromptKitV33.cmd ".\Artifacts\AI_Harness_Prompt_Kit_v33_bundle.zip"
```

The source may be one `.xlsx` workbook or one `.zip` bundle containing exactly one workbook. Unsafe bundle paths and generated-output name collisions are rejected.

## Preservation and outputs

The generator hashes the source before and after generation and refuses delivery if it changed. Non-workbook support files in a source bundle are copied into the output bundle. Existing outputs are moved to a timestamped `Outputs/.../backups/` directory before replacement.

Generated files include:

```text
AI_Harness_Prompt_Kit_v33.xlsx
AI_Harness_Prompt_Kit_v33_manifest.json
AI_Harness_Prompt_Kit_v33_bundle.zip
finalize-report.json
layout-report.json
artifact-contract-report.json
copy-surface-bounds-report.json
package-hygiene-report.json
operability-report.json
worksheet-integrity-report.json
web-excel-compatibility-report.json
```

The manifest records source and workbook hashes, P00-P49 ranges, the AgentSwitchboard contract pin, support-file hashes, protection posture, validator results, bundle hash, backup path when used, and the static proof ceiling.

## Protection and navigation

- Workbook structure is locked.
- Every worksheet is protected.
- Only `Opportunity_Discovery!A1:R100` is unlocked.
- Prompt Library C/O links select the exact column-A payload.
- Prompt-tab C links reselect the exact copy range.
- Prompt-tab B/E links return to the complete Prompt Library row.
- Navigation rails remain outside the linked column-A copy range.

## Validation

```powershell
python -m py_compile `
  triage/prompt_kit_v33_generator.py `
  triage/prompt_kit_v33_finalizer.py `
  triage/prompt_kit_v33_layout_finalizer.py

python -m pytest `
  tests/test_prompt_kit_v33_generator.py `
  tests/test_prompt_kit_v33_finalizer.py `
  tests/test_prompt_kit_v33_layout_finalizer.py -q
```

The package stage converts inline strings to shared strings, rewrites package-absolute internal relationship targets as valid OPC-relative targets, and canonicalizes package metadata for stable hashes from identical inputs.

## Compatibility aliases

The previous `Finalize-AIPromptKitV33.ps1` and `.cmd` names remain available and delegate to `Generate-AIPromptKitV33`. They do not contain a second generator implementation.

## Proof ceiling

This workflow proves deterministic static workbook and package behavior. It does not prove Excel Desktop or Web interaction, clipboard behavior, live GNHF runtime, provider readiness, or operator acceptance.
