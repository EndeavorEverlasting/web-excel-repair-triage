# AI Prompt Kit Next-Version Acceptance Contract

Date: 2026-07-14

## Purpose

This contract defines the required workbook behavior for the version following the clean-opening `AI_Harness_Prompt_Kit_v18.xlsx` artifact.

The next version must preserve the Microsoft-native package posture that succeeded in Excel for Web while improving prompt navigation, semantic color labeling, font compatibility, readability, and clipboard payload bounds.

## Structural inheritance

Use the clean-opening V18 workbook as the structural fixture.

Do not regenerate the workbook from a blank package or round-trip it through a general serializer after applying the compatibility fixes.

Preserve:

- non-overlapping merge geometry;
- absence of stale native table objects unless a synchronized table-bearing control is field-tested;
- ordinary scalar formulas only;
- Microsoft `x14:dataValidations` dropdown structures;
- conditional formatting;
- worksheet protection;
- freeze panes;
- internal worksheet hyperlinks;
- valid calculation metadata;
- Microsoft-normalized dimensions, sheet views, columns, and styles unless an intentional bounded change requires otherwise.

## Prompt Library navigation

Both compact identifiers that name the destination must navigate to the corresponding copy-safe tab.

For every prompt row:

- `Prompt ID` must be an internal hyperlink to `Pxx_COPY_SAFE!A1`;
- `Copy-Safe Sheet` must remain an internal hyperlink to the same destination;
- the displayed Prompt ID remains compact, for example `P07`;
- the displayed sheet name remains explicit, for example `P07_COPY_SAFE`;
- hyperlink targets must be validated for all prompt rows before delivery.

Expected invariant:

```text
Prompt_Library Prompt ID Pxx -> Pxx_COPY_SAFE!A1
Prompt_Library Copy-Safe Sheet Pxx_COPY_SAFE -> Pxx_COPY_SAFE!A1
```

## Color semantics

The Prompt Library must not present a field named `Color Meaning` whose values are only raw color names.

Use the compact two-surface design:

1. Rename the Prompt Library field to `Color`.
2. Store the short color name in that field, such as `Green`, `Amber`, or `Gray`.
3. Keep the authoritative semantic explanation in `Prompt_Class_Legend`.
4. Ensure every color used by the Prompt Library has exactly one corresponding legend entry.
5. The legend must explain what the color communicates operationally, not merely repeat the color name.

A hyperlink from the Prompt Library color cell or header to the legend is desirable when it can be added without widening the table or destabilizing the package.

## Web-compatible typography

Only the following workbook font families are approved for the next version:

- `Aptos` for regular text;
- `Aptos Display` only when already present in the Microsoft fixture and proven harmless, otherwise normalize it to `Aptos`;
- `Aptos` with bold weight for headings and emphasized text.

The intended visible contract is `Aptos` and `Aptos Bold`. Do not introduce custom, bundled, legacy, or environment-dependent fonts.

Font validation must inspect `xl/styles.xml` and fail when an unexpected font family is referenced by a visible cell style.

## Prompt Library readability

On `Prompt_Library`, column H (`Use This When`) must use a 12-point font for its body cells.

Requirements:

- preserve the existing column width unless a field test demonstrates clipping;
- use Aptos at 12 points for body cells in column H;
- keep the header visually distinct with Aptos Bold;
- do not apply the larger font through an unbounded whole-column style that creates cells or rows below the actual data range;
- apply the style only to the populated Prompt Library range.

## Copy-surface row bounds

Every `P00_COPY_SAFE` through `P20_COPY_SAFE` sheet must end at its final populated prompt row.

For each copy-safe sheet:

- preserve intentional blank rows inside the prompt;
- remove every explicit row node after the final populated row;
- remove every blank or styled cell after the final populated row;
- trim the worksheet dimension to the final payload row;
- avoid full-column or full-sheet formatting and protection operations that recreate trailing cells;
- pass `triage.copy_surface_bounds` with `--max-trailing-rows 0`.

Known V18 defects to remove:

| Sheet | Final payload row | V18 package end | Required next-version end |
| --- | ---: | ---: | ---: |
| `P07_COPY_SAFE` | 112 | 113 | 112 |
| `P14_COPY_SAFE` | 58 | 160 | 58 |

## Acceptance gates

The next version is accepted only when all of these gates pass:

1. ZIP CRC integrity passes.
2. Every XML and relationship part parses.
3. All relationship targets resolve.
4. Merge rectangles do not overlap.
5. Native table metadata is absent or fully synchronized.
6. No dynamic-array, shared-formula, or stop-ship formula structure is introduced.
7. All 21 Prompt ID hyperlinks resolve to the matching copy-safe tab.
8. All 21 Copy-Safe Sheet hyperlinks resolve to the matching copy-safe tab.
9. Every Prompt Library color has an authoritative meaning in `Prompt_Class_Legend`.
10. Visible fonts are Aptos/Aptos Bold-compatible.
11. Prompt Library column H body text is 12-point Aptos.
12. Every copy-safe sheet reports zero trailing package rows.
13. Formula, validation, conditional-formatting, protection, and hyperlink counts remain semantically intact.
14. The exact artifact opens in Excel for Web without repair or silent structural rewrite.
15. The operator confirms that copying an entire prompt tab produces only the intended prompt payload.

## Claim boundaries

A local package pass does not prove Excel for Web acceptance.

A clean Excel for Web open does not prove clipboard payload bounds.

A clipboard test on one prompt tab does not prove all prompt tabs are bounded.

Keep package validity, Web Excel acceptance, navigation acceptance, semantic presentation, and clipboard acceptance as separate recorded gates.
