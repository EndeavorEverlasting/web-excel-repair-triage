# Spreadsheet Style System

## Purpose

Use the restyled 1 Marcus recon workbook as the visual baseline for generated spreadsheet artifacts.

The goal is not decoration. The goal is fast operator comprehension, executive-safe presentation, and Excel for Web compatibility.

## Core rule

Styling must never change workbook logic.

When an artifact is already functionally correct, restyling is limited to safe presentation primitives:

- fills
- fonts
- borders
- alignment
- widths
- row heights
- tab colors
- freeze panes
- conditional-format colors

Do not change formulas, defined names, sheet references, table ranges, pivot caches, workbook relationships, or calculation behavior during a style-only pass.

## Canonical config

Machine-readable palette:

```text
configs/spreadsheet_style_v1.json
```

This config is the default style contract for new workbook generators unless a workflow-specific contract overrides it.

## Visual thesis

Use a restrained slate system:

- dark slate title and section bars
- muted blue-gray table headers
- soft row/background fills
- red only for true blockers or duplicate-key review
- amber only for review/warning states
- green only for resolved/valid states or trusted source-entry tabs
- gray for snapshots, archived, deprecated, or quiet reference material

No bright traffic-light carnival unless the status truly demands it.

## Required palette roles

| Role | Config key | Use |
| --- | --- | --- |
| Title bar | `header_primary` | Workbook or sheet title rows |
| Section bar | `header_secondary` | Major dashboard sections |
| Table header | `table_header` | Structured data headers |
| Operator/source tab | `source_green` | Source sheets users may edit |
| Executive/review hub | `header_secondary` | Leadership-facing modules |
| Duplicate/blocker | `action_red` / `duplicate_red_fill` | Review queues and duplicate key flags |
| Warning/review | `review_amber_fill` | Ambiguous or needs-review rows |
| Resolved | `resolved_green_fill` | Done, confirmed, resolved rows |
| Quiet/archive | `quiet_gray_fill` | Quiet queues or archive rows |
| Snapshot/deprecated | `snapshot_gray`, `deprecated_gray` | Evidence-only sheets |

## 1 Marcus inventory recon application

The 1 Marcus recon lane should use this sheet posture:

| Sheet | Tab style |
| --- | --- |
| `README Integration` | dark slate |
| `Part Numbers` | source green |
| `1M Recon Pivot Module` | executive slate |
| `Duplicate Key Review` | blocker red |
| `CF Dictionary` | reference slate |
| `Repo Automation Notes` | reference slate |
| snapshot sheets | muted gray |
| deprecated snapshots | light gray |

## Web Excel safety

The style system must stay boring at the package level.

Allowed:

- simple solid fills
- standard fonts
- simple borders
- number formats
- regular conditional formatting formulas already accepted by the repo validators
- stable tab colors

Avoid in generated Web Excel-safe workbooks:

- VBA
- slicers
- custom theme dependency as the only styling source
- shape/drawing-dependent layout
- native pivot-cache dependency for dynamic executive rollups
- R1C1 conditional-format leakage
- unsupported formula namespace tokens

## Generator adoption requirements

New spreadsheet generators should:

1. Load `configs/spreadsheet_style_v1.json`.
2. Apply tab colors by exact sheet name when present.
3. Apply role-based defaults when exact sheet name is absent.
4. Write a reference/notes sheet identifying the style config version.
5. Preserve formulas during style-only passes and report formula counts before and after.
6. Keep Web Excel preflight gates authoritative.

## Existing palette relationship

`configs/cf_palette_v1.json` remains the NW PRJ dashboard conditional-format contract.

`configs/spreadsheet_style_v1.json` is the broader workbook presentation contract for new artifacts. Future work can migrate NW PRJ generated workbooks toward this calmer palette, but do not silently break existing validator expectations.

## Acceptance criteria

A styled output is acceptable only when:

- the workbook still passes package preflight
- formula count does not change during a style-only pass
- no formulas are rewritten during restyling
- conditional-format rules keep the same logical triggers
- tab colors communicate worksheet purpose
- the workbook looks presentation-safe in Excel for Web
