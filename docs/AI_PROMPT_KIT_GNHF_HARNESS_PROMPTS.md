# AI Prompt Kit V33 Executable GNHF Contract

V33 keeps prompt prose subordinate to versioned contracts and repository code. Web Excel owns the declarative prompt source, workbook presentation, and deterministic generation. AgentSwitchboard owns regular-request and compiled-prompt schemas, workstation setup, GNHF launch, and local runtime evidence.

## External authority

The prompt source is pinned to `EndeavorEverlasting/AgentSwitchboard` PR #17 head `720e2b1f1b171949a8e8e9233f4162bdd2581937` and version 1 of:

- `tooling/gnhf/schemas/regular-sprint-request.v1.schema.json`;
- `tooling/gnhf/schemas/compiled-gnhf-prompt-result.v1.schema.json`;
- `tooling/gnhf/Invoke-ChatGPTDesktopGnhfSprint.ps1`;
- `tooling/wsl/Start-TmuxGnhfWorkspaceSetup.ps1`.

Web Excel projects these contracts into the workbook. It does not copy or fork AgentSwitchboard runtime code.

## Executable prompt roles

| Prompt | Activation | Required behavior |
| --- | --- | --- |
| P02 | Assign harness construction | A coding agent inspects the repository, creates or repairs schemas, fixtures, validators, skills, capabilities, triggers, workflows, and seams, validates, commits, pushes, and opens or updates the PR. Descriptive-only output fails. |
| P45 | Compile only | A regular AI prompt converts one `regular-sprint-request` v1 object into exactly one `compiled-gnhf-prompt-result` v1 object. It must not execute. |
| P46 | Direct GNHF build | GNHF builds or repairs a repository harness. A plan-only response fails. |
| P47 | Direct GNHF run | GNHF executes one registered harness workflow. Process exit without the required artifact and commit fails. |
| P48 | Desktop local execute | ChatGPT Desktop Codex writes request and compiled-prompt evidence, invokes the AgentSwitchboard desktop entrypoint with explicit `-Run`, requires visible full-prompt emission, and reports proof and preservation gaps. |
| P49 | Environment configure | A local coding agent invokes AgentSwitchboard workstation setup in `-Mode Plan`, and uses `-Mode Apply` only after explicit operator authorization. Authentication remains operator-owned. |

P48 does not claim that PowerShell controls the ChatGPT Desktop UI. The desktop Codex task initiates the chain. Failed runtime work is reported using returned references or the failed branch where available; unconditional failed-worktree preservation is outside the current upstream proof ceiling.

## Workbook behavior

The declarative source at `configs/prompt_kit/v33_gnhf_harness_prompts.json` repairs P02 and writes P45-P49. The canonical generator preserves P00-P44 from the source workbook, then enforces:

- exact Prompt Library links to every `A1:A<last prompt row>` range;
- top and bottom B/E backlinks to the complete Prompt Library row;
- C-column range-recovery links that reselect the exact copy range;
- Prompt Library top-to-bottom and bottom-to-top rails;
- the accepted V33 sheet order and semantic tab colors;
- locked workbook structure and protection on every worksheet;
- only `Opportunity_Discovery!A1:R100` editable.

## Canonical generation

```powershell
.\scripts\Generate-AIPromptKitV33.ps1 `
  -Source ".\Artifacts\AI_Harness_Prompt_Kit_v33_bundle.zip" `
  -OutDir ".\Outputs\prompt-kit-v33"
```

Double-click-compatible launcher:

```text
scripts\Generate-AIPromptKitV33.cmd ".\Artifacts\AI_Harness_Prompt_Kit_v33_bundle.zip"
```

`Finalize-AIPromptKitV33.ps1` and `.cmd` remain compatibility shims that delegate to this generator. Generated workbooks, reports, manifests, bundles, and backups belong under ignored `Outputs/` paths. Source workbooks and bundles are read-only.

## Focused validation

```powershell
python -m triage.prompt_kit_v33_prompt_contract
python -m pytest `
  tests/test_prompt_kit_v33_prompt_contract.py `
  tests/test_prompt_kit_v33_finalizer.py `
  tests/test_prompt_kit_v33_generator.py `
  tests/test_prompt_kit_v33_layout_finalizer.py `
  tests/test_prompt_kit_v33_artifact_contract.py `
  tests/test_prompt_kit_v33_copy_surface_contract.py -q
```

## Proof ceiling

Source and package tests prove prompt projection, deterministic generation, exact links and copy ranges, support-file preservation, manifest/report creation, package hygiene, Web Excel compatibility rules, worksheet protection, and source immutability. Excel Desktop and Excel for Web interaction, clipboard behavior, live GNHF execution, provider readiness, environment Apply, and operator acceptance remain separate runtime gates.
