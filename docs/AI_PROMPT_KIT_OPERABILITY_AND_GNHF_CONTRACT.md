# AI Prompt Kit Operability and GNHF Launch Contract

## Purpose

This contract separates three surfaces that look similar to a human but are not interchangeable:

1. **chat prompts** copied into ChatGPT or another conversational agent;
2. **GNHF objectives** supplied to the `gnhf` process;
3. **PowerShell launch commands** pasted into Windows PowerShell 7 to start GNHF.

A prompt is not terminal-safe merely because it is copyable from Excel.

## Execution-surface rule

| Surface | Valid first token | Required wrapper | Expected effect |
|---|---|---|---|
| Chat prompt | Natural-language instruction | None | The current chat analyzes or executes the request. |
| GNHF objective | Repository objective text | `gnhf "..."` or stdin | GNHF repeatedly invokes the selected coding agent. |
| PowerShell launch command | `gnhf` | Complete flags and quoted objective | PowerShell starts one bounded GNHF run. |

A block beginning with `We covered a lot...` is a **chat closeout prompt**. Pasting it directly into PowerShell attempts to execute the first word as a command and fails. It is valid in a chat interface, not as a naked terminal command.

## PowerShell-safe long-prompt form

GNHF officially accepts a prompt argument or stdin. Use a single-quoted PowerShell here-string for a long prompt when it must be launched from a terminal:

```powershell
Set-Location "C:\path\to\repo"

$Prompt = @'
Repo: xyz_repo_or_path

Context path:
- docs/insights/xyz_chat_harvest.md

Objective:
Read the named context file, implement one bounded owned-scope improvement, validate it, commit it, and stop.
'@

$Prompt | gnhf `
  --agent opencode `
  --worktree `
  --max-iterations 3 `
  --max-tokens 300000 `
  --prevent-sleep on `
  --stop-when "One bounded mutation is committed and validated, or an exact external blocker is recorded."
```

PowerShell requirements:

- the opening `@'` and closing `'@` markers are on their own lines;
- the closing marker starts in column one;
- a continuation backtick is the final character on its line;
- no spaces follow a continuation backtick;
- the repository working tree is clean before a new GNHF run;
- exactly one of `--worktree` and `--current-branch` is used;
- unattended runs always set both `--max-iterations` and `--max-tokens`;
- `--push` is absent unless remote mutation is explicitly authorized.

## Context-availability rule

GNHF and OpenCode do not inherit the current ChatGPT conversation.

An objective that says “use the best available chat context” is not self-sufficient in a terminal run unless the conversation evidence is provided through one of these bounded mechanisms:

- a tracked repository context document;
- a local untracked context file named in the objective;
- stdin containing the needed context;
- a supported connected-source retrieval step with explicit authority.

Do not tell GNHF to recover unspecified chat context that it cannot access. First harvest the decisions and constraints into a context file, then reference that file from the launch command.

## Atomic GNHF command contract

Each GNHF launch tab must own one complementary job. It must not repeat an entire sprint planning system.

Required command shape:

```text
gnhf
--agent opencode
exactly one Git execution mode
--max-iterations with a finite value
--max-tokens with a finite value
--prevent-sleep on when appropriate
one observable --stop-when condition
one compact quoted objective
```

The objective must include:

- `Repo: xyz_repo_or_path`;
- one atomic lane;
- owned scope;
- forbidden scope;
- direct mutation or proof outcome;
- targeted validation;
- a compact final report.

The objective must not include:

- provider credentials;
- automatic authentication;
- an unlimited backlog;
- a request to improve everything possible;
- a second launch command;
- unrelated remote Git authority;
- a requirement to prove that no useful work exists anywhere in the repository.

## Prompt-kit workbook contract

### Prompt Library layout

The canonical mouse-first layout is:

- navigation rail: column `A`;
- prompt table: columns `B:O`;
- navigation rail: column `P`;
- top-to-bottom links: `A1` and `P1`;
- bottom-to-top links: `A39` and `P39` for a P00-P36 library.

### Semantic font hierarchy

| Column | Meaning | Contract |
|---|---|---|
| B | Sequence | 10-point bold compact index |
| C | Prompt ID | 28-point bold primary identifier |
| D | Prompt Type | 10-point bold category |
| E | Prompt Class | 10-point bold category |
| F | Sprint Path Role | 10-point body |
| G | Use For Progress? | 10-point bold centered flag |
| H | Prompt Name | 12-point bold title |
| I:M | Workflow guidance | 10-point body |
| N | Color | 10-point bold palette label |
| O | Copy-Safe Sheet | 10-point bold mouse target |

A column shift must never be allowed to carry the old Prompt ID style into Sequence.

### Color coordination

The `Color` value is data, not decoration metadata that may drift.

Every cell in the Prompt Library row must use the fill and font color assigned to that row's declared color label. The validator fails unknown labels or mismatched fills/text colors.

### Copy surface

A forward Prompt ID or Copy-Safe link selects the exact payload range in column A.

Blank separator rows inside that selected range are allowed. Styled blank cells outside the selected range are tolerated when they are not selected and contain no hidden payload. The hyperlink range, not a serializer-inflated worksheet dimension, is the copy boundary.

Each prompt tab provides native internal `Back to Prompt Library` links at:

- `C1`;
- `C<last payload row>`.

Navigation and usage labels stay outside the copied column-A range.

### Protection

- workbook structure is locked;
- every worksheet is protected;
- only `Opportunity_Discovery!A1:R100` is unlocked for operator input;
- formula cells remain locked;
- no protection password is required for accidental-edit protection.

### Package lineage

Generate the next workbook from the last working workbook package. Do not restart from a known-broken package branch merely because its semantic content is newer.

Prefer package-preserving OOXML edits for workbook lineage changes. Serializer import/render success is not proof that drawings, hyperlinks, relationships, protection, styles, or Web Excel behavior survived.

## Proof taxonomy

| Proof | What it establishes |
|---|---|
| Command-shape proof | The copied text has a valid bounded GNHF/PowerShell structure. |
| OOXML contract proof | Links, protection, styles, palette, and copy ranges are structurally present. |
| PowerShell runtime proof | Windows PowerShell successfully starts the intended GNHF run. |
| GNHF runtime proof | The selected agent responds and the bounded loop behaves as expected. |
| Desktop Excel proof | Protected links, selection, and clipboard behavior work in Desktop Excel. |
| Excel for Web proof | The workbook opens without repair and mouse/copy behavior works in the browser. |
| Operator acceptance | A human confirms the real workflow is usable. |

Do not promote static command or OOXML proof into any runtime or field-acceptance claim.

## Canonical validator

```powershell
python -m triage.prompt_kit_operability_contract `
  "C:\path\to\AI_Harness_Prompt_Kit_v32.xlsx"
```

The validator is read-only and checks:

- P00-P36 copy tabs;
- P26-P36 atomic PowerShell GNHF command shape;
- exact Prompt Library links and top/bottom navigation;
- top and bottom backlinks on each prompt tab;
- semantic font hierarchy;
- row palette coordination;
- workbook and worksheet protection;
- the sole editable Opportunity Discovery range.

It does not execute PowerShell, GNHF, OpenCode, Desktop Excel, or Excel for Web.
