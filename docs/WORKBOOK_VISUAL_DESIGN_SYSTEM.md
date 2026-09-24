# Workbook Visual Design System

## Purpose

Generated workbooks need a stable visual language. The repo should not keep rediscovering color schemes, tab colors, visual hierarchy, or executive scan patterns by accident.

This document codifies the artistic layer that operators usually do not want to think about while still preserving strict workbook functionality.

Machine-readable config:

```text
configs/workbook_visual_design_v1.json
```

Related palette:

```text
configs/spreadsheet_style_v1.json
```

## Core doctrine

Function comes first. Style must never rewrite workbook logic.

A style-only pass may adjust:

- fills
- fonts
- borders
- tab colors
- row heights
- column widths
- alignment
- freeze panes
- conditional-format colors

A style-only pass must not adjust:

- formulas
- formula references
- table ranges
- source rows
- workbook relationships
- calculation behavior
- pivot/cache mechanics

## Visual principles

| Principle | Meaning |
| --- | --- |
| Function first | Do not sacrifice formulas for presentation. |
| Executive scan first | The first screen should tell leadership what matters. |
| Semantic color only | Color must explain role, state, or hierarchy. |
| Calm by default | Slate, charcoal, muted blue-gray, and soft fills are the baseline. |
| Red is expensive | Red means blocker, duplicate, failed check, or stop-ship. |
| Amber means review | Amber means inspect, not panic. |
| Green means valid or source | Green marks resolved/valid status or trusted source-entry surfaces. |
| Gray means quiet or evidence | Gray belongs to snapshots, archives, deprecated sheets, and quiet references. |

## Sheet role colors

| Sheet role | Visual intent |
| --- | --- |
| Executive view | Slate/charcoal, calm authority |
| Source entry | Green, edit surface |
| Review queue | Deep red, action required |
| Reference | Muted slate |
| Automation notes | Muted slate |
| Snapshot | Medium gray |
| Deprecated | Light gray |

## Executive inventory visual field

For inventory recon workbooks, the embedded executive visual field is required.

It is not a separate chart. It is a `Visual` column inside the executive rollup table.

Expected shape:

```text
Inventory Rollup by Item | Total Qty | Visual | Lines | ...
```

The field should use a compact in-cell progression bar such as the `REPT("█", ...)` pattern. It belongs in the executive tab so the visual scan happens without leaving the leadership view.

## One Marcus checkpoint lessons

The accepted 2026-06-03 One Marcus recon artifact proved these rules:

- A workbook can open in Excel for Web and still be wrong if the executive visual field is missing.
- Nice tab colors do not compensate for a missing functional visual column.
- Separate charts are optional and secondary.
- Claims such as Web Excel-safe should not appear in client-facing workbook text.
- Local package checks are not enough. Operator review in Excel for Web wins.
- Protection is useful, but it must follow functional correctness.

## Anti-patterns

Avoid:

- bright traffic-light colors on routine rows
- random tab colors with no role meaning
- separate charts replacing embedded visual fields
- workbook-visible compatibility claims
- URL-encoded text such as `%20` in workbook titles or visible cells
- sheet protection before the functional view is proven
- style passes that rewrite formulas
- dashboards where important fields are off-screen on first open
- hidden helper mechanics with no README or repo notes

## Acceptance checks

A visually acceptable workbook must satisfy all of these:

1. The executive tab opens on a useful first-screen view.
2. Required visual fields are visible without searching.
3. The title is short and client-safe.
4. The workbook contains no generated compatibility bragging text.
5. Formula count and formula text are unchanged during style-only passes.
6. Tab colors communicate each sheet's role.
7. The artifact passes the operator's Excel for Web review before it is called successful.

## Generator adoption

Future workbook generators should load these configs:

```text
configs/workbook_visual_design_v1.json
configs/spreadsheet_style_v1.json
```

The generator should emit a small repo notes sheet or manifest entry recording:

- style config version
- visual design config version
- whether an executive visual field was generated
- formula count before/after style pass
- whether the artifact was operator-approved in Excel for Web
