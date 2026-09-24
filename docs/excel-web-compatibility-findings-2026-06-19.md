# Excel Web Compatibility Findings

Date: 2026-06-19

Source workbook inspected: `repaired_recon_views_v5_19_active_queue_repair_websafe_6-19-2026.xlsx`

Purpose: capture compatibility findings from the recon tracker repair cycle so future generated workbooks survive Excel desktop, Excel Web, and Excel's repair pass with less drama.

## Executive finding

The workbook design should avoid formula patterns that make Excel introduce compatibility wrappers such as `_xlfn.SINGLE`, `_xlws`, or `_xludf`. The business model was sound after moving the active queue into helper/source tabs, but the quality-control sheet still contained an array-style `AGGREGATE` pattern. Excel repaired that area and reintroduced `_xlfn.SINGLE` wrappers.

Cold judge score: the queue mechanism passed; the QA formulas did not.

## Inspection summary

The uploaded repaired workbook contained 22 worksheets. The compatibility issue was localized.

| Finding | Result |
|---|---:|
| Sheets in workbook | 22 |
| Sheets containing `_xlfn` | 1 |
| `_xlfn` occurrences | 160 |
| `AGGREGATE` occurrences | 40 formulas plus 1 shared-string mention |
| `_xlws` occurrences | 0 |
| `_xludf` occurrences | 0 |
| Literal formula error tokens found in XML scan | 0 |
| `calcChain.xml` present | Yes |

Affected sheet:

- `Queue Integrity Check`

Notably, the issue was not spread across the main queue, dashboard, or active queue source. It was the integrity check logic.

## Offending pattern

The risky pattern was a filtered-list formula using `AGGREGATE` over a divided array expression:

```excel
=IFERROR(AGGREGATE(15,6,ROW('Part Numbers'!$S$81:$S$107)/(UPPER(TRIM('Part Numbers'!$S$81:$S$107))="YES"),ROWS($H$14:H14)),"")
```

In the repaired workbook, Excel wrapped this style with compatibility markers similar to:

```excel
=IFERROR(_xlfn.SINGLE(_xlfn.AGGREGATE(15,6,_xlfn.SINGLE(ROW(...))/(...),ROWS(...))),"")
```

That is the smell. Once `_xlfn.SINGLE` appears in saved XML, assume Excel Web compatibility is suspect until proven otherwise.

## Working replacement pattern

Prefer explicit helper/source rows over array extraction formulas.

### Helper/source tab

Use a durable helper table, for example `Active Queue Source`:

| Column | Example formula | Purpose |
|---|---|---|
| Source Row | `=ROW('Part Numbers'!S81)` | Keeps a stable pointer to the source row |
| Active Flag | `=--(UPPER(TRIM('Part Numbers'!S81))="YES")` | Converts active requirement to 1/0 |
| Queue Rank | `=IF(B2=1,COUNTIF($B$2:B2,1),"")` | Creates stable sequence without array division |
| Display fields | `='Part Numbers'!U81` etc. | Carries business fields forward |

### Queue tab

Then render the queue with ordinary lookup formulas:

```excel
=IFERROR(INDEX('Active Queue Source'!$D$2:$D$200,MATCH(ROWS($A$5:A5),'Active Queue Source'!$C$2:$C$200,0)),"")
```

This is boring. Boring is good. Excel Web likes boring.

## Compatibility rules learned

1. Do not use `AGGREGATE` as a filtered-list engine when Excel Web compatibility matters.
2. Do not use dynamic array formulas for production trackers unless the audience is guaranteed to be on modern Excel.
3. Avoid formulas that divide a range by a boolean condition, such as `ROW(range)/(condition)`. Excel may preserve the logic but wrap it with compatibility markers.
4. Avoid `_xlfn`, `_xlws`, and `_xludf` in final `.xlsx` XML. Treat them as build failures unless deliberately targeting new Excel-only features.
5. Remove stale `calcChain.xml` after programmatic workbook edits. It is a recalculation cache, not business logic.
6. Keep QA sheets formula-light. A hidden or secondary validation sheet can still trigger repair warnings.
7. Preserve inactive business rows. `NO` should mean `Not Active Now`, not `delete this requirement`.
8. Keep the human edit surface small. In the recon tracker pattern, tech-facing updates should happen in one visible surface, with helper tabs calculating downstream views.
9. Use explicit fields such as `Actively Required?` and `Active Required Qty` instead of hidden global multipliers.
10. Use source tabs and helper ranks to generate views, not nested formulas that require users to reverse-engineer the workbook.

## Recommended safe formula set

Generally safe for Excel Web and desktop compatibility:

- `IF`
- `IFERROR`
- `INDEX`
- `MATCH`
- `COUNTIF`
- `COUNTIFS`
- `SUMIF`
- `SUMIFS`
- `TRIM`
- `UPPER`
- `ROW`
- direct sheet references

Use cautiously:

- `AGGREGATE`
- structured references in generated tables
- complex conditional formatting formulas over large ranges

Avoid for broad compatibility unless intentionally required:

- `FILTER`
- `SORT`
- `UNIQUE`
- `SEQUENCE`
- `LET`
- `LAMBDA`
- `BYROW`
- `BYCOL`
- formulas that rely on implicit intersection

## Post-generation XML scan

Add a hard scan after generating a workbook:

```python
import zipfile
from collections import Counter, defaultdict

path = "workbook.xlsx"
terms = [
    "_xlfn", "_xlws", "_xludf",
    "#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#N/A",
    "AGGREGATE", "FILTER(", "LET(", "LAMBDA", "UNIQUE(", "SORT(", "SEQUENCE(",
]

counts = Counter()
files = defaultdict(list)

with zipfile.ZipFile(path) as z:
    for name in z.namelist():
        if not name.startswith("xl/") or not name.endswith((".xml", ".rels")):
            continue
        text = z.read(name).decode("utf-8", "ignore")
        for term in terms:
            count = text.count(term)
            if count:
                counts[term] += count
                files[term].append((name, count))

print(counts)
print(dict(files))
```

Build should fail or require manual review when these appear:

- `_xlfn`
- `_xlws`
- `_xludf`
- `calcChain.xml`
- `#REF!`
- `#VALUE!`
- `#NAME?`

## Tracker-specific architecture note

For the recon tracker, the stable architecture is:

1. `Part Numbers` remains the technician-facing edit surface.
2. Techs update active requirement fields only.
3. `Deployment Requirements`, `Data Support`, and queue source tabs are derived.
4. `Active Queue Source` precomputes row eligibility and queue rank.
5. `Shortage Queue` displays every active requirement, not only items already known to be short.
6. Integrity checks should use simple count comparisons, not filtered-list generators.

## Next repair target

Rewrite `Queue Integrity Check` so it does not use `AGGREGATE`. It should either:

- reference the already-built `Active Queue Source` helper ranks, or
- use plain count checks only, or
- be stored as values generated during build-time validation.

The QA sheet cannot use the same fragile extraction logic it is supposed to catch. That is putting the referee in skates and asking why the ice is slippery.
