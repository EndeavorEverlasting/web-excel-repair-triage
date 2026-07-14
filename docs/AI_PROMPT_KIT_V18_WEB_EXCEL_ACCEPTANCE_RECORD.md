# AI Prompt Kit v18 Web Excel Acceptance Record

Date: 2026-07-14

## Result

`AI_Harness_Prompt_Kit_v18.xlsx` opened successfully in Excel for Web without a repair event.

This is field acceptance for that exact artifact. It is not a blanket claim that every workbook produced by the same Python libraries or every later prompt-kit version will open cleanly.

## Evidence chain

The compatibility investigation progressed through distinct artifacts instead of treating every valid ZIP as Web Excel-safe:

1. The earlier prompt-kit artifact opened in Google Sheets but failed to open in Excel for Web.
2. Local package preflight passed, proving that the preflight did not yet model every Web Excel requirement.
3. Validation and column-normalization probes A, B, and C also failed to load.
4. Scalar/table probes D, E, and F reached Excel for Web but were returned as repaired workbooks.
5. The three repaired outputs were compared against their exact inputs part by part and cell by cell.
6. V18 was produced from Microsoft's repaired D workbook as the structural fixture, with bounded byte-safe metadata updates rather than workbook regeneration.
7. The operator confirmed that V18 opened successfully in Excel for Web.

## Confirmed package defect

The strongest common repair trigger was overlapping merged-cell geometry.

The failed probes contained these collisions:

```text
START_HERE
A1:J1 overlaps A1:H1

Prompt_Class_Legend
A2:F2 overlaps A2:H2
```

Excel for Web removed one range from each collision in every repaired D/E/F output. No cell values or worksheet formulas changed during those repairs.

Therefore:

- intersecting `mergeCell` rectangles are a generation failure;
- applying a wider title or subtitle merge must first remove the stale narrower merge;
- visual correctness in a renderer does not excuse invalid merge geometry.

The package-hygiene validator already detects this defect and must keep it as a hard failure.

## Separate stale-table defect

The failed v17 lineage also carried three native Excel table objects whose stored column schemas no longer matched the visible worksheet headers:

```text
StartHereV9
PromptLibraryV9
PromptSequenceV9
```

The scalar probes removed those table objects. Their removal alone did not prevent repair because the merge collisions remained.

The supported conclusion is:

- stale or mismatched table XML is unsafe;
- table-free output is not proven to be universally required;
- when a table is present, its `ref`, `autoFilter`, column count, column names, visible headers, and actual row bounds must remain synchronized.

## Features that survived and are allowed

The repaired D workbook and the clean-opening V18 artifact prove that Web Excel can accept these features together:

- eight ordinary scalar worksheet formulas;
- zero array formulas;
- zero shared formulas;
- no dynamic-array spill metadata;
- 18 cross-sheet dropdown validations represented in Microsoft's `x14:dataValidations` extension;
- conditional formatting;
- protected worksheets;
- frozen panes;
- 21 internal hyperlinks from `Prompt_Library` to the matching `Pxx_COPY_SAFE` tabs;
- shared strings and Microsoft-generated calculation metadata.

Consequently, the correct contract is not "remove every formula and rule." It is "use compatible scalar structures and keep package relationships internally consistent."

## Microsoft repair normalization that is not yet a proven trigger

The repaired D/E/F workbooks also received broad normalization:

- dimensions added to worksheets;
- default sheet views added where absent;
- overlapping column-definition records normalized;
- style records deduplicated;
- document properties added;
- calculation metadata generated for surviving scalar formulas.

These are useful diagnostics and known-good fixture characteristics. They were common to Microsoft's rewrite, but the current evidence does not prove that any one of them independently caused the repair event.

Do not turn correlation into a stop-ship rule without a single-variable field test.

## Generation method that succeeded

V18 was not exported from a blank workbook and was not round-tripped through a general workbook serializer after Microsoft repair.

The successful posture was:

1. use the Microsoft-repaired D workbook as the structural fixture;
2. preserve its package topology and Microsoft-native extension records;
3. keep native tables absent until a clean table-bearing control is field-tested;
4. update only bounded shared-string metadata, core properties, and one existing shared-string cell reference;
5. verify ZIP CRC, XML parsing, merge non-overlap, scalar formula shape, calculation-chain targets, dropdown count, conditional-formatting count, and internal hyperlink count;
6. perform the real Excel-for-Web open gate.

## Prompt copy-surface payload bounds

A separate operator problem remains for the next prompt-kit version: copy-safe sheets may contain hundreds or thousands of package rows below the final prompt line. Spreadsheet applications can include those rows when the whole sheet is copied, producing enormous pasted payloads.

For every declared copy surface:

- find the final populated prompt row;
- compare it with the worksheet dimension end row;
- compare it with the highest explicit `<row r="...">` node;
- compare it with the highest cell reference, including styled blank cells;
- report the largest package row as the effective copy-surface end;
- require zero trailing rows by default for production prompt tabs.

The dedicated validator reports each sheet's `last_payload_row`, `package_end_row`, and `trailing_rows`.

Use the strict generation gate:

```powershell
python -m triage.copy_surface_bounds `
  "<prompt-kit.xlsx>" `
  --sheet P00_COPY_SAFE `
  --sheet P01_COPY_SAFE `
  --max-trailing-rows 0
```

The generator should also avoid formatting or protection operations over full-column or full-sheet row ranges when a bounded prompt range is sufficient.

## Acceptance model

Keep these claims separate:

| Gate | V18 evidence |
| --- | --- |
| ZIP readable | passed |
| XML well-formed | passed |
| tables internally consistent or absent | tables absent |
| merge ranges non-overlapping | passed |
| scalar formula structure | passed |
| dropdown and conditional-formatting surfaces preserved | passed |
| internal copy-tab links preserved | passed |
| Excel for Web opens without repair | operator confirmed |
| clipboard contains no trailing-row bloat | not yet accepted; next-version gate |

## Canonical lessons

1. Google Sheets acceptance does not prove Excel for Web acceptance.
2. A valid ZIP and parseable XML do not prove Excel for Web acceptance.
3. Overlapping merged ranges are a hard package defect.
4. Stale table schemas are a separate hard package defect.
5. Ordinary scalar formulas, x14 dropdowns, conditional formatting, protection, and internal hyperlinks are compatible when the package is coherent.
6. A Microsoft-repaired workbook can be a valuable known-good structural fixture.
7. Bounded byte-safe edits preserve that fixture more reliably than full regeneration.
8. Copy-surface row bounds are an operator and token-efficiency contract, not merely a cosmetic concern.
9. Field acceptance must remain the final gate.

## V18 copy-surface audit

Running the new strict payload-bound check across all 21 `P00_COPY_SAFE` through `P20_COPY_SAFE` sheets found two concrete trailing-row defects:

| Sheet | Final populated row | Package end row | Extra rows | Cause |
| --- | ---: | ---: | ---: | --- |
| `P07_COPY_SAFE` | 112 | 113 | 1 | styled blank cell at `A113` |
| `P14_COPY_SAFE` | 58 | 160 | 102 | styled blank cells from `A59:A160`, including custom-height row records |

The other 19 prompt tabs ended at their final populated row.

This proves that the bloat is not hypothetical and is not caused only by how a spreadsheet application renders an empty grid. The OOXML package itself contains explicit styled cells and row records below the prompt payload. A whole-sheet copy can therefore include those rows.

For the next prompt-kit version, remove the trailing `<row>` and `<c>` records and reduce each affected `<dimension ref="...">` to the final populated prompt row. Preserve intentional blank rows inside the prompt; remove only rows after the final populated cell.
