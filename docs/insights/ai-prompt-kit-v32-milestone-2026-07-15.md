# AI Prompt Kit V32 Milestone Insights — 2026-07-15

## Mission

Turn the AI Harness Prompt Kit into a Web Excel-compatible, mouse-friendly, protected operator workbook whose prompts are explicit about their execution surface and whose GNHF commands launch small, bounded, complementary repository workflows.

## Why this record exists

The workbook reached a useful milestone only after several revisions exposed distinct failure classes. This record preserves the decisions that prevent the next version from repeating them.

## Decisions

### One workbook is the product

A partial addendum containing only new prompts was rejected. A numbered workbook release must preserve the complete prompt library and navigation system.

### Copy controls must select exact ranges

Clicking a Prompt ID or Copy-Safe entry must open the target prompt tab and select the exact column-A payload range. The operator should not assemble a prompt from several workbook regions.

### Every prompt tab has return navigation

A Prompt Library link appears at both the top and bottom of every prompt tab. Navigation remains outside the copied payload.

### Prompt Library supports mouse travel in both directions

The library is framed by left and right navigation rails. Top controls jump to the bottom; footer controls return to the top.

### Workbook surfaces are protected

All worksheets and workbook structure are protected against accidental edits. `Opportunity_Discovery!A1:R100` is the sole operator-entry range.

### Semantic styles follow columns and data

Sequence is a compact index. Prompt ID is the large identifier. Prompt Type, Prompt Class, progress flag, Prompt Name, Color, and Copy-Safe link each have intentional font roles.

A row's declared `Color` controls the row fill and font color. Shifting columns without reapplying semantic styles is a contract failure.

### Working package lineage outranks broken semantic branches

The next workbook version starts from the last package that preserves navigation, links, protection, style, and Web Excel behavior. New semantic content is applied to that working package rather than rebuilding from a structurally broken branch.

### GNHF prompt architecture is atomic

The first GNHF addendum was too planning-oriented. The corrected suite separates complementary jobs:

- proof-floor reproduction;
- interrupted-run recovery;
- single mutation;
- repo-first mutation;
- finite queue;
- commit finalization;
- validation and CI repair;
- offline harness hardening;
- technician experience;
- dependency maintenance;
- exact PR-branch repair.

Each command includes finite iteration and token caps and one positive stop condition.

### Chat prompts are not terminal commands

A natural-language closeout prompt can be valid in ChatGPT and invalid in PowerShell. Terminal tabs must contain a complete `gnhf` command or use a documented stdin/here-string wrapper.

### GNHF cannot see this chat implicitly

Conversation-derived requirements must be harvested into a named context document before an external coding agent can act on them reliably.

## Rejected patterns

- calling a two-prompt addendum a full version;
- splitting the operator product across two workbooks;
- drawing-only navigation that disappears or breaks after export;
- links that open a tab without selecting the payload range;
- one return link only at the top;
- leaving all sheets editable;
- shifting columns and preserving the wrong inherited font style;
- decorative colors that do not match the Color field;
- copying large sprint-plan prose into every GNHF iteration;
- unlimited unattended runs;
- using `--worktree` and `--current-branch` together;
- assuming `--prevent-sleep` blocks Windows Update restart;
- searching only the primary checkout for worktree-local GNHF evidence;
- claiming provider failure from low token movement without logs;
- using serializer import/render as Web Excel acceptance proof.

## Current proof ceiling

V32 has static workbook, OOXML, navigation, protection, semantic style, color coordination, and GNHF command-shape proof.

The following remain separate gates:

- PowerShell paste execution;
- OpenCode/provider response;
- a completed GNHF iteration and commit;
- Desktop Excel exact-range and clipboard behavior;
- Excel for Web open-without-repair behavior;
- protected-sheet hyperlink behavior in both Excel clients;
- operator acceptance.

## Highest-value next work

1. Integrate the operability contract into the package-preserving prompt-kit generator lane.
2. Run the validator against every generated prompt-kit artifact.
3. Capture a Windows PowerShell smoke run for one atomic GNHF command.
4. Capture Desktop Excel and Excel for Web navigation/copy acceptance.
5. Converge the working workbook lineage and the repository generator without reintroducing drawing-link or package-shape regressions.
6. Route agent/provider failover through AgentSwitchboard rather than pretending it is native GNHF behavior.
