# AI Prompt Kit GNHF Harness Generation Contract

This lane makes the prompt-kit generator produce workbook behavior that previously required manual repair:

- internal Prompt Library links target each prompt's exact copy range;
- every prompt sheet returns to the complete matching Prompt Library row;
- Prompt Library top corners jump to the bottom and bottom corners return to the top;
- Prompt Library rows, prompt tabs, ranges, fonts, fills, and color declarations are coordinated;
- `Prompt_Library`, `Opportunity_Discovery`, `P07_COPY_SAFE`, and the GNHF harness-build prompt `P46_COPY_SAFE` use the same cream tab color;
- every sheet is protected, with only `Opportunity_Discovery!A1:R100` unlocked for operator input;
- GNHF prompts are generated from a declarative JSON source rather than hidden in a workbook binary.

## New prompts

### P45 — AI-to-GNHF Prompt Compiler

Use P45 in ChatGPT or another repo-aware AI. It produces one bounded, paste-ready GNHF prompt and does not execute the sprint itself. The generated prompt must include spawn readiness, worktree or branch mode, iteration and token caps, owned and forbidden scope, artifacts, validators, commit proof, stop conditions, proof ceiling, and final response contract.

### P46 — GNHF Repo Harness Builder

P46 is a direct GNHF command. It tells GNHF to inspect the repository and implement or repair the harness spine, agent harness, application boundaries, integration seams, registries, schemas, fixtures, skills, capabilities, triggers, validators, and operator documentation. It requires tracked changes and a commit; a plan-only answer is failure.

### P47 — GNHF Harness Workflow Executor

P47 is a direct GNHF command for a repository that already has a committed harness. It executes one registered workflow, requires run-context and artifact registration, uses checkpoint commits, runs canonical validators, and treats a process exit without the required artifact and commit as failure.

## Generation

```powershell
.\scripts\Finalize-AIPromptKitV33.ps1 `
  -SourceWorkbook "C:\Artifacts\AI_Harness_Prompt_Kit_v33.xlsx" `
  -OutDir "Outputs\prompt-kit-v33"
```

Double-click-compatible launcher:

```text
scripts\Finalize-AIPromptKitV33.cmd "C:\Artifacts\AI_Harness_Prompt_Kit_v33.xlsx"
```

The source is never overwritten. Generated workbooks and reports belong under ignored output paths.

## Direct Python command

```powershell
python -m triage.prompt_kit_v33_finalizer `
  --source "C:\Artifacts\AI_Harness_Prompt_Kit_v33.xlsx" `
  --output "Outputs\prompt-kit-v33\AI_Harness_Prompt_Kit_v33_GNHF.xlsx" `
  --report "Outputs\prompt-kit-v33\finalize-report.json"
```

## Validation

```powershell
python -m py_compile triage/prompt_kit_v33_finalizer.py tests/test_prompt_kit_v33_finalizer.py
python -m pytest tests/test_prompt_kit_v33_finalizer.py -q
python -m triage.prompt_kit_operability_contract "<generated workbook>"
python -m triage.workbook_package_hygiene "<generated workbook>"
python -m triage.web_excel_compatibility_rules "<generated workbook>"
```

## Proof ceiling

The generator and tests prove deterministic prompt insertion, internal link targets, exact ranges, formatting contracts, selected tab colors, and protection state in the saved OOXML package. Desktop Excel clean-open behavior, Excel for Web behavior, clipboard output, GNHF agent spawnability, provider readiness, completed GNHF mutation, and operator acceptance remain separate runtime gates.
