# Workbook Copy Surface and OOXML Triage Lessons

## Dense copy surfaces

A copy-safe prompt sheet should contain only contiguous column-A payload cells from row 1 through the final line. Styled blanks, trailing cells, stale dimensions, or convenience navigation cells can pollute whole-sheet clipboard output even when the visible sheet looks harmless.

## Drawing-layer navigation

A hyperlink-bearing drawing can provide visible navigation without adding worksheet cell text. The validator must follow the complete chain:

```text
worksheet drawing r:id
-> worksheet .rels drawing target
-> drawing a:hlinkClick r:id
-> drawing .rels hyperlink target
```

The shape label and target are checked separately. Rendering proves the control is visible; only the target application can prove it is clickable and preserves clipboard behavior.

## Relationship hygiene

Every non-external relationship target must resolve inside the package. Reject missing targets, absolute internal targets, and targets that escape the package root. Drawing relationships add many small parts, so relationship validation is a stop-ship gate rather than a spot check.

## Calculation chains

The accepted prompt-kit package uses one-based worksheet indexes in `calcChain.xml`. Inserting P21 before the formula-bearing opportunity sheets shifts the chain index by one. A calculation chain is not rejected merely for existing; each entry must resolve to an actual formula cell.

## Cell replacement safety

Do not append a new `<c>` element when a coordinate already exists. Replace the existing element and preserve or intentionally select its style. Validate duplicate coordinates and worksheet dimensions after every bounded edit.

## Evidence levels

- Package valid: ZIP/XML/relationship and structural checks pass.
- Contract valid: prompt IDs, surfaces, links, typography, colors, and P21 content pass.
- Render validated: a workbook engine imports and renders key surfaces without error.
- Field accepted: Excel for Web opens without repair and the operator confirms navigation and clipboard behavior.
