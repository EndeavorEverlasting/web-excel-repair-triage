# AI Harness Prompt Kit V39 — Local-First and Zero-Token Contracts

## Mission

V39 extends the operator-accepted V38 workbook with five standard-AI prompts that remain useful when the operator has no model, API, provider, or coding-agent tokens.

V39 is generated directly from the V38 OOXML package. It must not be reconstructed through Excel, LibreOffice, `openpyxl`, or another whole-workbook serializer.

## Prompt surfaces

The workbook has two different execution surfaces. They are not interchangeable.

### Standard AI prompts

A standard AI prompt is natural-language instruction given to a repo-aware AI. It may ask the AI to inspect the repository, implement changes, interpret evidence, or return commands for the operator to run locally.

A standard AI prompt:

- does not begin with `gnhf`;
- does not contain GNHF token or iteration flags;
- must not be placed in the GNHF launch section;
- may return local commands only after resolving and verifying the repository directory.

### Goodnight, Have Fun (GNHF) prompts

A GNHF prompt is a bounded PowerShell terminal launch command. It begins with `gnhf` and carries explicit agent, Git-mode, iteration, token, sleep, and stop contracts.

The exact product name is **Goodnight, Have Fun (GNHF)**.

A GNHF prompt:

- is a terminal command rather than ordinary chat prose;
- belongs only in the contiguous P26–P36 GNHF section;
- must contain the required bounded launch flags;
- must not be mislabeled as a standard AI prompt.

## Section contract

- P00–P25: standard AI core section.
- P26–P36: contiguous GNHF launch section.
- P37–P49: contiguous standard AI advanced/local section.
- P45–P49 are the new V39 local-first prompts.

The V39 validator fails when P26–P36 are no longer contiguous, when P37–P49 are no longer contiguous, when a P45–P49 prompt contains GNHF command markers, or when the Prompt Library class mixes the two surfaces.

## New prompts

| ID | Name | Purpose |
|---|---|---|
| P45 | Directory-First Repository Command Guard | Resolve the correct local checkout before any repository command is emitted. |
| P46 | Zero-Token Local Test Planner | Analyze the repo and return exact local tests requiring no model/provider tokens. |
| P47 | Repository Factoring Analyzer | Determine whether harness, agent-harness, application, seam, validation, docs, runtime, and research surfaces are correctly factored. |
| P48 | Repository Factoring Builder | Implement one selected factoring gap and carry it through tests, commit, push, and PR evidence. |
| P49 | Local-Only Validation and Closeout | Interpret local test and Git evidence without starting another token-consuming agent. |

## Directory gate

Every P45–P49 prompt requires the AI to resolve the intended checkout before returning repository commands.

The first executable task command must be one of:

```powershell
Set-Location -LiteralPath "<verified-root>"
git rev-parse --show-toplevel
```

```bash
cd -- "<verified-root>"
git rev-parse --show-toplevel
```

When the root is unknown, the AI may return bounded discovery commands only. Tests, builds, mutations, commits, deployment, and cleanup commands must wait until the root is proven.

## Generate V39 locally

PowerShell:

```powershell
.\scripts\Generate-AIPromptKitV39.ps1 `
  -Source "C:\Artifacts\AI_Harness_Prompt_Kit_v38.xlsx"
```

Double-click-compatible wrapper:

```text
scripts\Generate-AIPromptKitV39.cmd "C:\Artifacts\AI_Harness_Prompt_Kit_v38.xlsx"
```

Python:

```powershell
Set-Location -LiteralPath "C:\path\to\web-excel-repair-triage"
git rev-parse --show-toplevel
python -m triage.prompt_kit_v39_generator `
  --source "C:\Artifacts\AI_Harness_Prompt_Kit_v38.xlsx" `
  --out-dir "Outputs\prompt_kit_v39" `
  --spec "configs\prompt_kit\v39_local_first_prompts.json" `
  --json
```

These commands use local Python and repository code. They do not launch a model-backed agent.

## Generated outputs

- `AI_Harness_Prompt_Kit_v39.xlsx`
- `AI_Harness_Prompt_Kit_v39_manifest.json`
- `AI_Harness_Prompt_Kit_v39_bundle.zip`

## Validation order

1. Parse the V39 prompt specification.
2. Verify the source has the exact P00–P44 V38 prompt floor.
3. Add P45–P49 by direct OOXML package edits.
4. Verify standard AI and GNHF section boundaries.
5. Verify directory gates, zero-token language, factoring prompts, library metadata, exact-range links, backlinks, protection inheritance, and formula-chain equality.
6. Repeat generation from the same source and require byte-identical output.
7. Run focused repository tests and compatibility validators.
8. Open the generated workbook in Excel for Web and perform the operator field gate.

## Safety and proof ceiling

The generator does not overwrite the source and does not commit workbook binaries.

Repository tests can prove prompt payloads, taxonomy, package structure, formulas, calculation-chain integrity, and deterministic generation. V39 changes workbook topology by adding sheets, so Excel for Web opening, navigation, range selection, and operator acceptance remain a new field gate.
