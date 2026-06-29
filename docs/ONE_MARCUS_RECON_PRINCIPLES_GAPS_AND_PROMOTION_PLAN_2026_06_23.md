# One Marcus Recon Principles, Gaps, and Promotion Plan - 2026-06-23

## Status

No workbook is promoted to golden yet.

This document captures the operating doctrine from the v5.22 through v5.28 One Marcus recon workbook sprint and defines the remaining gates before any artifact can be treated as a golden standard.

The current candidate family improved the workbook in these areas:

- executive Cybernet posture view for 1 Marcus
- `Part Numbers` as the primary operator update surface
- active requirement fields on `Part Numbers`
- derived `Deployment Requirements` status
- shortage queue generated from active requirements
- exceptions-only shortage graphing
- label-first graph fallback
- simple native chart reintroduction for graph usability
- compatibility baseline against Excel Web repair triggers

The current candidate is still a candidate, not gold. Operator acceptance in the real Excel Web environment is still required.

## Controlling principles

### 1. Part Numbers is the human edit surface

Operators and technicians should not chase fields across helper tabs.

`Part Numbers` is the primary update surface for stock and requirement intent. The workbook may have derived tabs, but humans should not need to reverse-engineer them for normal updates.

Current intended edit fields:

| Sheet | Field | Meaning |
|---|---|---|
| `Part Numbers` | `Actively Required?` | Whether this part is required for the current use case |
| `Part Numbers` | `Active Required Qty` | Current active need for the current use case |

Rules:

- Do not put pivot-key helper formulas in `Part Numbers!S:AD`.
- Do not put a control table at the bottom of `Part Numbers`.
- Do not block users from appending new parts or shipment rows.
- Keep helper logic in support tabs.
- Keep find/replace usable in `Part Numbers`.

### 2. NO means inactive now, not deleted

Inactive requirement rows are future-use rows.

`NO` means `Not Active Now`.

It does not mean:

- delete this row
- archive this requirement
- erase the future mapping
- remove this item from the model

The workbook must preserve inactive requirement rows so the operator can reactivate them later without rebuilding the table from memory.

### 3. YES means actively required now

`YES` means the item is actively required for the current use case.

Every actively required row must surface in the operational queue. The queue can classify it as OK, short, pending review, or no clean match, but it should not silently omit active requirements.

### 4. Requirement quantity must be explicit

Do not silently multiply every requirement by a global deployment count.

The prior global multiplier pattern was too crude. Some parts are per deployment, some are fixed totals, and some are review-only or conditional. When the operator says the active need is 2, the shortage queue should show 2.

Requirement math should be visible enough that an operator can explain it without tracing nested support formulas.

### 5. Shortage graphs are exceptions-only

A shortage-facing graph should not show stock-OK rows as if they are shortages.

Example rule:

- `NEURON MEDICAL-GRADE POWER CABLES` with 150 available and 0 shortage must not appear as a shortage bar.
- Stock-OK rows may appear in a separate `Stock OK items excluded` section.

Shortage graph inclusion should be based on exception posture:

- confirmed shortage greater than 0
- review exposure greater than 0
- no clean inventory match
- verify-before-stage state

### 6. Charts are useful, but the label-first table is the fallback

Native Excel charts are allowed only when they are simple and Web Excel-safe.

Allowed chart posture:

- simple native bar charts
- static or boring source ranges
- no dynamic array formulas
- no `AGGREGATE` extraction engines
- no hidden formula caches with error tokens
- labels visible directly in the chart axis or adjacent label-first table

The label-first in-cell graph/table remains the durable fallback and preferred screenshot range. Native charts are presentation aids, not the only evidence surface.

### 7. Requirement Subset Pivots should have charts

`Requirement Subset Pivots` should include visual summaries because operators can widen rows and columns manually, but rebuilding chart objects is slower and easier to break.

The chart doctrine should be codified before any artifact is promoted:

- chart source range is visible or clearly documented
- categories are readable
- quantities are not hidden in legends
- charts do not replace the underlying table
- charts do not introduce repair prompts

### 8. Compatibility validation is a gate, not a courtesy

Known stop-ship terms in workbook package XML:

- `_xlfn`
- `_xlws`
- `_xludf`
- `AGGREGATE` used as a filtered-list engine
- `SINGLE`
- `FILTER(`
- `SORT(`
- `UNIQUE(`
- `LET(`
- `LAMBDA`
- stale `calcChain.xml`
- formula error tokens such as `#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`

A workbook can be valid locally and still fail the field judge in Excel Web. Treat package validity, semantic correctness, presentation quality, Web Excel acceptance, and operator acceptance as separate gates.

## Known gaps

| Gap | Impact | Next action |
|---|---|---|
| v5.28 native charts need Excel Web field validation | Chart XML may still trigger repair even when formula scans pass | Upload v5.28 to Excel Web, capture repaired copy if a banner appears |
| Row heights and column widths still need a sweep | Some tabs hide data, hurting operator review | Run v5.29 readability pass after chart behavior is settled |
| Requirement Subset Pivots chart behavior is not codified in tests | Charts can drift or disappear between versions | Add chart-presence and source-range checks |
| No sanitized golden fixture yet | Cannot regression-test without private data risk | Build a sanitized fixture that preserves workbook structure, formulas, and chart surfaces |
| No automated promotion manifest for candidate artifacts | Candidate quality is hard to compare over time | Emit manifest JSON with sheets, formulas, chart parts, package scan, and screenshot targets |
| Duplicate part rows can confuse active requirement marking | Operator may mark duplicate shipment rows inconsistently | Add duplicate-key review checks before promotion |
| DB9/DB15 mapping remains a no-clean-match posture | Candidate inventory such as 9-pin monitor cables should not reduce shortage without verification | Keep `NO CLEAN MATCH` until explicitly verified |
| Cable rows require strict separation | Cat6 Ethernet and GREY/DIM Cat5 patch cables are operationally different | Preserve separate rows and add regression check |

## Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Native charts trigger Excel Web repair | Charts are harder to validate by formula scans alone | Keep charts simple; compare original vs repaired packages; keep label-first fallback |
| Helper logic creeps back into `Part Numbers` | Find/replace and appending new shipments become painful | Fail builds when `Part Numbers!U:AD` is populated or bottom control blocks appear |
| QA formulas become the repair trigger | Prior issue came from validation formulas, not business formulas | Keep QA formula-light; prefer static build-time PASS/FAIL values or simple counts |
| Stock-OK items appear in shortage views | Leaders read graph rows as shortages | Shortage graphs must filter to exceptions only |
| Global requirement multiplier returns | Quantities become inflated and untrustworthy | Active required quantity must be explicit and visible |
| Local validation is mistaken for operator acceptance | Local package scans do not prove Excel Web acceptance | Require field validation before golden promotion |

## Candidate artifacts and golden status

No gold yet.

Current candidate artifacts from the workbook sprint may be used as evidence, but not as golden standards until they pass promotion gates.

| Artifact type | Current status | Golden status |
|---|---|---|
| v5.28 workbook candidate | Candidate | Not gold |
| v5.28 screenshot / preview | Candidate evidence | Not gold |
| Excel Web repaired copy, if produced | Triage evidence | Not gold |
| Compatibility scan output | Evidence | Not gold |
| Sanitized fixture preserving structure | Needed | Not created |
| Generator/regression tests | Needed | Not complete |
| Operator acceptance note | Needed | Not complete |

## Golden promotion gates

A One Marcus recon artifact may be promoted only after all gates pass:

1. **Package validity**
   - workbook opens locally
   - no broken OOXML relationships
   - no stale `calcChain.xml`

2. **Semantic correctness**
   - `Part Numbers` is the stock and requirement edit surface
   - `Deployment Requirements` derives active status from `Part Numbers`
   - inactive rows are preserved
   - every active requirement appears in the queue
   - medical-grade power cables with 150 available do not appear as a shortage
   - Cat6 Ethernet and GREY/DIM Cat5 patch cable rows remain separate
   - DB9/DB15 remains no-clean-match unless verified

3. **Presentation quality**
   - executive Cybernet posture is visible
   - shortage graph is exceptions-only
   - graph labels are readable directly beside bars or on axes
   - Requirement Subset Pivots include charts
   - row heights and column widths are usable without manual rescue

4. **Web Excel acceptance**
   - upload to Excel Web produces no repair banner
   - no silent repair copy is generated
   - formulas and charts remain intact after browser open/save

5. **Operator acceptance**
   - operator confirms in the real target environment
   - screenshot range is usable for delivery
   - live recon link and workbook view tell the same story

## Next sprint sequence

### v5.29 - Readability sweep

Scope:

- increase row heights on crowded tabs
- enable wrap text where useful
- widen essential columns
- avoid touching business logic

Priority: medium. Important, but charts were the harder failure.

### v5.30 - Chart compatibility codification

Scope:

- verify native chart XML after Excel Web field test
- add chart source-range documentation
- add checks for charts on `Shortage Graphs` and `Requirement Subset Pivots`
- keep label-first fallback as mandatory

Priority: high.

### v5.31 - Golden fixture preparation

Scope:

- create sanitized workbook fixture with same sheet architecture
- preserve representative formulas, named tables, support tabs, and chart parts
- remove client/private operational data
- add package scan report

Priority: high before generator work.

### v5.32 - Regression harness

Scope:

- assert no repair-trigger tokens
- assert `Part Numbers!U:AD` blank
- assert active requirement queue coverage
- assert shortage graph is exceptions-only
- assert chart objects exist where required
- assert medical power cables are stock-OK, not shortage

Priority: high before promotion.

### v5.33 - Promotion review

Scope:

- compare candidate workbook, repaired copy, manifest, and screenshot evidence
- decide whether candidate becomes golden
- if accepted, promote sanitized fixture and generator behavior only
- do not commit private workbook data

Priority: after operator field acceptance.

## Do-not-do list

- Do not promote v5.28 or any current candidate to golden yet.
- Do not commit private client workbooks.
- Do not delete inactive requirement rows.
- Do not hide helper formulas in `Part Numbers`.
- Do not use charts as a substitute for visible tables.
- Do not claim Web Excel acceptance without operator validation.
- Do not mark candidate screenshots as golden proof by themselves.

## Codified acceptance sentence

A One Marcus recon workbook is not golden because it opens, looks good, or passes a local XML scan. It becomes golden only when the package, formulas, presentation, Excel Web behavior, and operator field review all agree.
