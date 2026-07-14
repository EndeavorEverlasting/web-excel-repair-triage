# AI Prompt Kit V19 Repair and V20 Generation Record

Date: 2026-07-14

## Scope

This record captures the Excel-for-Web repair delta for `AI_Harness_Prompt_Kit_v19.xlsx` and the bounded generation posture used for V20.

No private workbook binary is committed. The evidence below is derived from package-level comparison of the original V19 artifact and the Excel-for-Web repaired V19 download.

## Direct repair findings

### 1. Duplicate worksheet cell coordinates

`Prompt_Class_Legend` contained 38 duplicate cell records:

```text
J4:K22
```

Each coordinate appeared twice:

1. an existing blank styled `<c>` record from the Microsoft fixture;
2. a later appended value-bearing `<c>` record added by the V19 transformation.

Excel for Web retained the first blank record and discarded the later duplicate value-bearing record. This explains why the workbook could appear correct in a parser that selected the later record while Excel repaired the sheet and removed the color/meaning values.

**Stop-ship rule:** a worksheet coordinate may have at most one `<c>` element. Updating a cell must replace the existing element in place rather than appending another element with the same `r` value.

### 2. Worksheet dimension excluded existing cells

V19 declared:

```text
Prompt_Class_Legend dimension = A1:K23
```

The sheet still contained explicit styled cells through:

```text
Z100
```

Excel for Web restored the dimension to `A1:Z100`.

**Stop-ship rule:** when a dimension node is present, it must cover every explicit cell record. A generator must not shrink the dimension merely to the visible content when styled or structural cells remain outside that range.

## Preserved features

The repair did not invalidate the V19 design conclusions for:

- 42 internal exact-range hyperlinks;
- 21 dense and bounded prompt copy surfaces;
- eight ordinary scalar formulas;
- Microsoft-generated calculation-chain metadata;
- 18 extended data-validation rules;
- 14 conditional-formatting blocks;
- Aptos typography and 12-point Prompt Library column H.

## Correlated normalization, not isolated causes

Excel also:

- reduced `cellXfs` from 148 to 144 by removing unused styles and deduplicating equivalent styles;
- normalized default row heights from 14.25 to 15 and from 34.5 to 36;
- reserialized worksheet and shared-string XML.

These changes are recorded as save normalization. They are not promoted to independent compatibility laws because they were not isolated in single-variable field tests.

## V20 generation posture

V20 uses the repaired V19 download as its structural fixture.

The V20 transformation:

1. defines the intended workbook changes through the workbook editing surface;
2. replaces existing worksheet cell records in place;
3. preserves the repaired worksheet dimension and package topology;
4. adds no duplicate cell coordinates;
5. keeps the dense prompt tabs and exact-range links unchanged;
6. repairs the color legend mapping so each of the 18 library colors has one operational meaning;
7. adds package gates for coordinate uniqueness and dimension coverage.

V20 package preflight passed. Excel-for-Web clean-open, range-selection behavior, text-box clipboard behavior, and whole-sheet clipboard behavior remain separate field gates.

## Executable repo changes

- `triage/worksheet_cell_integrity.py`
- `tests/test_worksheet_cell_integrity.py`
- `.github/workflows/worksheet-cell-integrity.yml`

The synthetic regression reproduces the V19 failure shape with duplicate `J4` records and a stale `A1:K23` dimension while a `Z100` cell exists.
