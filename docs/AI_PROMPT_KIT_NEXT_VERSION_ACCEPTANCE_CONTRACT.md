# AI Prompt Kit Version-Aware Acceptance Contract

Date: 2026-07-14

## Supported profiles

The prompt-kit validators use explicit profiles instead of a single hard-coded workbook count.

| Profile | Required prompt IDs | Prompt tabs | Forward links | Drawing backlinks |
|---|---:|---:|---:|---:|
| V20 | P00-P20 | 21 | 42 | not required |
| V21 | P00-P21 | 22 | 44 | 22 |

The Prompt Library header is `Color`, not `Color Meaning`. Validator output and CLI reports name the selected profile rather than claiming every workbook is V19.

## Source inheritance

V21 is transformed from the exact field-accepted V20 package with SHA-256:

```text
9b0934ef7bca9b308bf605c9be0c98f75f420c92d5a3f6e1995df1465747c076
```

Do not reconstruct the production workbook from a blank package or save it through a general workbook serializer. Preserve Microsoft-normalized package topology, shared-string strategy, styles, formulas, calculation metadata, synchronized `calcChain.xml`, `x14` validation, conditional formatting, protection, freeze panes, and existing exact-range links.

## Copy-surface contract

Every `Pxx_COPY_SAFE` worksheet:

- begins at row 1;
- uses populated cells only in column A;
- uses one logical prompt line per populated cell;
- has no internal blank rows;
- has no explicit blank or styled payload cells after the endpoint;
- has no explicit cells after the final payload row;
- has a dimension exactly equal to `A1:A<last_payload_row>`;
- contains no duplicate cell coordinate.

Required invariant:

```text
last_payload_row - first_payload_row + 1 == populated_payload_row_count
```

## Navigation contract

Both `Prompt ID` and `Copy-Safe Sheet` link to the exact prompt payload range. V21 therefore has 44 cell hyperlinks.

Every V21 prompt tab has one drawing-layer `Back to Prompt Library` control anchored outside column A and linked to the matching library row. Drawing text is not worksheet cell text and does not change the copy endpoint. V21 therefore has 22 drawing backlinks and 66 total internal navigation controls.

Package inspection proves relationship targets and visible drawing content. Actual Excel-for-Web click behavior remains a field gate.

## Typography and color

Visible fonts use `Aptos`; bold is represented by `<b/>`, not an `Aptos Bold` font family. Prompt Library column H body cells use 12-point regular Aptos. Every library color maps to exactly one nonempty operational meaning in `Prompt_Class_Legend`.

## Static and field gates

Static acceptance includes ZIP CRC, XML parsing, relationship resolution, cell-coordinate uniqueness, dimension coverage, merge overlap checks, formula and calculation-chain checks, copy-surface bounds, exact forward links, backlink targets, fonts, and color semantics.

Field acceptance is separate. For the exact candidate SHA, Excel for Web must open without repair, preserve exact-range selection, produce clean clipboard text, preserve whole-sheet fallback, navigate P21/P00/P07/P12/P20 backlinks, and produce a downloaded package that passes the static suite again.
