# AI Prompt Kit V33 PR #64 / PR #66 Convergence Disposition

PR #66 remains the convergence owner. PR #64 remains open until the pushed PR #66 head and CI evidence are recorded; this document does not authorize premature closure.

Verified input heads:

- PR #64 `afb94973030de47d4366cfe66ef5113f8c36163f`;
- PR #66 `f0181dad2e37d7f20152fca2ace815a4eb075d07`;
- AgentSwitchboard PR #17 `720e2b1f1b171949a8e8e9233f4162bdd2581937`.

## File disposition

| PR | File | Disposition | Result in PR #66 |
| --- | --- | --- | --- |
| #64 | `.github/workflows/prompt-kit-v21.yml` | Merge | Generator import, tests, and CLI checks are combined with PR #66 finalizer/layout/artifact coverage. |
| #64 | `docs/AI_PROMPT_KIT_V33_SELF_SERVICE_GENERATION.md` | Keep and revise | Documents the canonical workbook/bundle generator, support files, backups, reports, and compatibility aliases. |
| #64 | `scripts/Generate-AIPromptKitV33.cmd` | Keep and refine | Canonical double-click launcher with bounded arguments and exit-code preservation. |
| #64 | `scripts/Generate-AIPromptKitV33.ps1` | Keep and refine | Canonical PowerShell launcher for workbook or bundle input. |
| #64 | `tests/test_prompt_kit_v33_generator.py` | Merge and replace | Preserves bundle/support/manifest behavior while testing the PR #66 declarative finalizer and layout path. |
| #64 | `triage/prompt_kit_v33_generator.py` | Merge and replace | Becomes the only orchestration path; delegates prompt and layout mutation to PR #66 code and adds package normalization and focused reports. |
| #64 | `triage/prompt_kit_v33_ooxml.py` | Retire | Not copied. Its unique protection, bundle, and support-file behaviors are covered by the canonical finalizer/generator contracts without a competing engine. |
| #66 | `.github/workflows/prompt-kit-v21.yml` | Keep and merge | Retains finalizer/layout/artifact suite and adds canonical generator, copy-surface, and prompt-source gates. |
| #66 | `configs/prompt_kit/v33_gnhf_harness_prompts.json` | Keep and extend | Repairs P02, preserves P45-P47, adds P48-P49, pins AgentSwitchboard v1, and declares exact protection/order. |
| #66 | `docs/AI_PROMPT_KIT_GNHF_HARNESS_PROMPTS.md` | Keep and extend | Documents P02/P45-P49 activation and cross-repository authority. |
| #66 | `scripts/Finalize-AIPromptKitV33.cmd` | Replace with alias | Delegates to the canonical Generate CMD path. |
| #66 | `scripts/Finalize-AIPromptKitV33.ps1` | Replace with shim | Delegates to the canonical Generate PowerShell path. |
| #66 | `tests/test_prompt_kit_v33_artifact_contract.py` | Keep and extend | Covers P00-P49, workbook lock, all-sheet protection, exact editable range, links, order, and colors. |
| #66 | `tests/test_prompt_kit_v33_finalizer.py` | Keep and extend | Covers P02/P45-P49 payload projection and compatibility launchers. |
| #66 | `tests/test_prompt_kit_v33_layout_finalizer.py` | Keep and extend | Covers P00-P49 order, range recovery, colors, workbook lock, and exact editable range. |
| #66 | `triage/prompt_kit_v33_artifact_contract.py` | Keep and extend | Remains independent acceptance authority for the generated workbook. |
| #66 | `triage/prompt_kit_v33_finalizer.py` | Keep and extend | Remains the declarative prompt and workbook mutation authority. |
| #66 | `triage/prompt_kit_v33_layout_finalizer.py` | Keep and extend | Remains the accepted-layout canonicalization authority. |

## Behavior disposition

| Behavior | Disposition | Evidence surface |
| --- | --- | --- |
| Workbook input | Merge | Canonical generator accepts `.xlsx`. |
| Bundle input | Keep from #64 | Exactly one workbook is extracted read-only. |
| Support-file preservation | Keep from #64 | Support files and hashes are retained in the generated bundle. |
| Deterministic OOXML | Merge | PR #66 finalizers plus relationship, shared-string, and package-metadata normalization. |
| P02 executable assignment | Merge and strengthen | Declarative validator rejects descriptive-only P02. |
| P45-P49 insertion | Keep/extend #66 | One source writes distinct compile, build, run, desktop-execute, and configure semantics. |
| Prompt ID and sheet links | Merge | C/O exact range links, B/E row backlinks, C range-recovery links, and library rails. |
| Protection | Merge and repair | Workbook structure and all sheets locked; only `Opportunity_Discovery!A1:R100` editable. |
| Reports and manifest | Merge | Finalizer, layout, artifact, copy, hygiene, operability, integrity, and compatibility reports plus hashes. |
| PowerShell and CMD launch | Keep from #64 | Generate launchers are canonical; Finalize names are aliases. |
| Raw OOXML engine | Retire | Unique behavior moved into the canonical path; no second V33 engine remains. |

## Closure gate for PR #64

Do not close PR #64 until PR #66 is pushed with this disposition, focused CI passes on the new head, and the PR discussion links the preserving commits. A later operator may then close #64 as superseded without merging its raw-OOXML engine.
