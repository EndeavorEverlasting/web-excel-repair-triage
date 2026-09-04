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

Every non-external package relationship target must resolve inside the package. Reject missing targets, absolute internal targets, and targets that escape the package root. Same-workbook hyperlink fragments such as `#Prompt_Library!B23` are workbook locations rather than package-part paths and must be classified separately. Drawing relationships add many small parts, so relationship validation is a stop-ship gate rather than a spot check.

## Markup-compatibility prefixes are data too

Office markup compatibility stores namespace prefixes inside attribute values such as:

```xml
mc:Ignorable="x15 xr xr6 xr10 xr2"
mc:Choice Requires="x15"
```

Those values are lexical prefix lists. A generic XML serializer may rename the actual declarations to `ns1`, `ns2`, and similar generated names while leaving the string values unchanged. `ElementTree` still parses the XML because the attribute values are plain text, but Office may refuse to open the workbook because the referenced prefixes no longer exist.

Therefore:

- validate prefixes referenced by `Ignorable`, `MustUnderstand`, `Requires`, `ProcessContent`, `PreserveAttributes`, and `PreserveElements`;
- do not treat ZIP success, XML parse success, or non-Office rendering as proof that Excel can open the file;
- preserve Microsoft namespace prefixes when patching an accepted package;
- prefer bounded byte-level edits or a serializer proven to preserve markup-compatibility semantics.

The Prompt Kit V24 incident is recorded in `docs/AI_PROMPT_KIT_V24_OFFICE_OPEN_FAILURE.md`.

## Calculation chains

The accepted prompt-kit package uses worksheet `sheetId` values in `calcChain.xml`, not the sheet's ordinal position in workbook display order. A retained chain entry must map its `i` value to `xl/workbook.xml` `sheet/@sheetId`, then resolve the referenced cell to an actual formula.

## Cell replacement safety

Do not append a new `<c>` element when a coordinate already exists. Replace the existing element and preserve or intentionally select its style. Validate duplicate coordinates and worksheet dimensions after every bounded edit.

## Evidence levels

- Package valid: ZIP/XML/relationship, markup-compatibility prefix, and structural checks pass.
- Contract valid: prompt IDs, surfaces, links, typography, colors, and prompt content pass.
- Render validated: a workbook engine imports and renders key surfaces without error.
- Desktop accepted: desktop Excel opens the exact hash without refusal or repair.
- Web accepted: Excel for Web opens the exact hash without repair.
- Operator accepted: navigation, clipboard behavior, and required user workflows are confirmed.

A lower level must not be promoted to a higher one. In particular, render validation is not desktop or Web Excel acceptance.
