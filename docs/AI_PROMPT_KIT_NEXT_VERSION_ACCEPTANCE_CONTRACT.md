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

## Prompt Library navigation and selected payload ranges

Both compact identifiers that name the destination must navigate to and select the exact copyable payload range, not merely activate the destination sheet.

For every prompt row:

- `Prompt ID` must be an internal hyperlink to `Pxx_COPY_SAFE!A1:A<last_payload_row>`;
- `Copy-Safe Sheet` must remain an internal hyperlink to the same exact range;
- the displayed Prompt ID remains compact, for example `P07`;
- the displayed sheet name remains explicit, for example `P07_COPY_SAFE`;
- use a direct internal range location rather than adding a defined name unless a field test proves the direct range unreliable;
- hyperlink targets must be validated for all prompt rows before delivery;
- the final target row must equal the last populated row reported by the copy-surface validator.

Expected invariant for a prompt ending on row 88:

```text
Prompt_Library Prompt ID Pxx -> Pxx_COPY_SAFE!A1:A88
Prompt_Library Copy-Safe Sheet Pxx_COPY_SAFE -> Pxx_COPY_SAFE!A1:A88
```

The intended operator flow is:

1. click either link in `Prompt_Library`;
2. arrive with the exact payload range selected;
3. copy immediately without worksheet select-all;
4. paste only the prompt payload into a text box or terminal.

Range selection is a separate field gate. Package inspection can prove that the hyperlink `location` names the correct range, but it cannot prove that Excel for Web or another spreadsheet application preserves the multi-cell selection after navigation.

If a tested application collapses the target to one active cell, the bounded and dense copy surface remains the fallback protection.

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

## Copy-surface physical row bounds

Every `P00_COPY_SAFE` through `P20_COPY_SAFE` sheet must physically end at its final populated prompt row.

For each copy-safe sheet:

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

## Copy-surface payload density

Physical trimming alone is insufficient. Text boxes preserve empty rows inside the selected range even when terminals visually collapse or trim some whitespace.

The V18 prompt tabs contain:

- 1,222 rows between the first and final populated cells;
- 1,016 populated rows;
- 206 internal blank rows;
- an overall internal blank-row ratio of approximately 16.9 percent.

Representative V18 density:

| Sheet | Payload span | Populated rows | Internal blank rows |
| --- | ---: | ---: | ---: |
| `P03_COPY_SAFE` | 142 | 127 | 15 |
| `P06_COPY_SAFE` | 133 | 113 | 20 |
| `P07_COPY_SAFE` | 112 | 88 | 24 |
| `P13_COPY_SAFE` | 30 | 20 | 10 |

V19 should use a dense copy surface:

- remove empty spacer rows inside the payload range;
- preserve readability with explicit headings, labels, punctuation, and contiguous instruction rows rather than empty worksheet rows;
- keep one logical prompt line per populated cell;
- do not replace empty rows with giant multiline cells, because that can reintroduce clipboard wrapper-quote behavior;
- target zero internal blank rows for every production copy-safe sheet;
- if an internal blank row is retained, it requires an explicit documented reason and field evidence that the resulting paste is desirable.

The strict payload-density invariant is:

```text
last_payload_row - first_payload_row + 1 == populated_payload_row_count
```

For the current prompt design, `first_payload_row` should remain row 1.

## Why all three controls are required

The row and link controls solve different failure modes:

| Control | Failure prevented |
| --- | --- |
| physical package bound | styled or explicit rows below the prompt are included by whole-sheet copy |
| dense payload | empty spacer rows inside the prompt are preserved by text boxes |
| range-target hyperlink | the user can copy the intended range without selecting the whole sheet |

Do not rely on the range-target hyperlink alone. Other spreadsheet tools may ignore or collapse a multi-cell target, and users may still use whole-sheet selection.

Do not rely on physical trimming alone. A perfectly bounded sheet can still paste many blank lines when its payload contains spacer rows.

## Acceptance gates

The next version is accepted only when all of these gates pass:

1. ZIP CRC integrity passes.
2. Every XML and relationship part parses.
3. All relationship targets resolve.
4. Merge rectangles do not overlap.
5. Native table metadata is absent or fully synchronized.
6. No dynamic-array, shared-formula, or stop-ship formula structure is introduced.
7. All 21 Prompt ID hyperlinks resolve to the exact matching copy-safe payload range.
8. All 21 Copy-Safe Sheet hyperlinks resolve to the exact matching copy-safe payload range.
9. Clicking each hyperlink in Excel for Web selects the intended multi-cell range, or the result is explicitly recorded as unsupported.
10. Every Prompt Library color has an authoritative meaning in `Prompt_Class_Legend`.
11. Visible fonts are Aptos/Aptos Bold-compatible.
12. Prompt Library column H body text is 12-point Aptos.
13. Every copy-safe sheet reports zero trailing package rows.
14. Every production copy-safe sheet reports zero internal blank rows.
15. Formula, validation, conditional-formatting, protection, and hyperlink counts remain semantically intact.
16. The exact artifact opens in Excel for Web without repair or silent structural rewrite.
17. The operator confirms that clicking a library link and copying immediately produces only the intended prompt payload in a text box.
18. The operator confirms that the whole-sheet fallback also produces only the intended dense prompt payload.

## Claim boundaries

A local package pass does not prove Excel for Web acceptance.

A correct range string in OOXML does not prove that the Web Excel interface will preserve the selected range.

A clean Excel for Web open does not prove clipboard payload bounds.

A successful range-copy test does not prove the whole-sheet fallback is clean.

A clipboard test on one prompt tab does not prove all prompt tabs are bounded and dense.

Keep package validity, Web Excel acceptance, navigation acceptance, range-selection behavior, semantic presentation, payload density, and clipboard acceptance as separate recorded gates.
