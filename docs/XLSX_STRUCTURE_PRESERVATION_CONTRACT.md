# XLSX Structure Preservation Contract

Date: 2026-07-01

## Purpose

Codify the deeper rule behind Web Excel-safe workbook triage:

The OOXML package structure is part of the artifact, not an implementation detail.

A workbook may look correct in a screenshot and still be unacceptable if its package shape changes in ways Excel Web rejects, silently repairs, or interprets differently. Formatting work should preserve the known-good workbook architecture unless a deliberate structural migration is being performed.

## Core doctrine

Do not treat `.xlsx` as a simple table export.

An `.xlsx` workbook is a ZIP package of XML parts, relationships, content-type declarations, workbook metadata, sheet parts, styles, shared strings, tables, drawings, charts, and calculation state. These parts have assumptions. When those assumptions are disturbed, the triage team pays the cost by having to learn and validate a new workbook pathway.

Therefore:

- Prefer in-place mutation of a known-good workbook over wholesale regeneration.
- When only one tab needs adjustment, only that tab and its directly required style ranges should change.
- Do not rebuild unrelated sheets, chart parts, table definitions, content types, shared strings, or relationship graphs unless that is the explicit goal.
- A visually correct workbook is not accepted until its package structure passes the structural contract.

## Known-good structure is an asset

The existing April/May or last-accepted workbook is not just a design reference. It is a compatibility fixture.

Preserve its assumptions where possible:

| Area | Preserve unless deliberately migrating |
|---|---|
| Sheet order and names | Downstream formulas, references, and user expectations depend on them. |
| Existing tab roles | Dashboard, task tracking, summaries, and detail tabs should keep their responsibilities. |
| Styles and theme references | Reusing styles is safer than inventing new XML style records. |
| Shared-string behavior | Avoid switching text storage models during cosmetic edits. |
| Table names and table refs | Duplicate/stale table definitions can trigger repair or incorrect filters. |
| Drawing and chart relationship structure | Chart parts and drawing rels are fragile in Excel Web. |
| Content type declarations | Bad content type defaults/overrides can make the package invalid before repair. |
| Workbook relationships | Broken, absolute, or unexpected relationship targets can break Web Excel open behavior. |
| Calculation state | Stale `calcChain.xml` must not survive programmatic edits. |

## Mutation classes

Classify every workbook change before touching the artifact.

### Class A: Value-only update

Examples:

- update task rows
- update dates, names, hours, task text
- correct a total stored as a value

Allowed posture:

- preserve workbook package shape
- preserve existing sheet XML where possible
- do not introduce formulas unless required
- do not touch tables/charts/content types/relationships

### Class B: Style-only update

Examples:

- copy old task-tracking color bands
- set row heights
- wrap notes columns
- apply borders/fills/alignment

Allowed posture:

- preserve values
- reuse existing style IDs where possible
- avoid creating large new style sets
- do not rebuild unrelated sheets

### Class C: Sheet-local rebuild

Examples:

- rebuild only the `June 2026` task-tracking sheet from accepted source rows
- preserve all other tabs exactly

Allowed posture:

- snapshot package manifest before and after
- confirm only expected worksheet/style/shared-string parts changed
- confirm workbook relationships remain intact
- render the changed sheet

### Class D: Structural migration

Examples:

- add/remove sheets
- add tables
- add charts/drawings
- replace workbook generation engine
- change shared-string strategy
- change formulas, named ranges, or table refs

Allowed posture:

- requires a new compatibility lane
- requires explicit structural manifest
- requires Excel Web field validation
- should not be bundled with billing/data changes

## Stop-ship package smells

These are not cosmetic issues. They are package-level defects or high-risk signals.

| Smell | Why it matters |
|---|---|
| Missing `[Content_Types].xml` | Package lacks the map Excel needs to interpret parts. |
| Bad XML default content type | A default `.xml` type of workbook-main is structurally wrong; workbook should be an explicit override. |
| Missing workbook content-type override | `xl/workbook.xml` must be explicitly declared as workbook-main. |
| Chart parts under `xl/drawings/charts/` | Chart parts should live under `xl/charts/chartN.xml`. |
| Drawing rels targeting bad chart paths | Broken chart relationships can trigger repair or rejection. |
| Chart relationship without chart parts | Drawing references a chart that does not exist. |
| `calcChain.xml` present after edits | Stale recalculation state can contradict workbook contents. |
| External links | Web Excel may block, repair, or behave unpredictably. |
| Duplicate table names | Tables must remain uniquely addressable. |
| Inline string cells when shared strings are expected | Text storage model drift is avoidable structural churn. |
| `ns0` namespace pollution | Serializer artifacts can corrupt or destabilize XML expectations. |
| Formula error text | `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A` are stop-ship unless intentionally documented. |

## Package manifest requirements

Every generated or repaired workbook candidate should emit or record a structural manifest with at least:

- file name
- SHA-256
- size in bytes
- sheet names and order
- package part list
- changed package parts compared to the source fixture
- content-type override summary
- relationship target audit
- chart part audit
- table name/ref audit
- calcChain presence
- formula/error-token scan
- Web Excel stop-ship term scan
- screenshot/render targets

For sheet-local work, the diff should prove that unrelated package areas did not change.

## One-tab adjustment rule

When the user says only one tab needs adjustment, treat that as a hard scope boundary.

Required behavior:

1. Start from the latest accepted workbook, not a blank workbook.
2. Preserve all non-target tabs.
3. Modify only the target sheet's values/styles and any unavoidable shared resources.
4. Compare package parts before/after.
5. Explain any non-target package changes.
6. Reject the artifact if unrelated workbook structure changed without justification.

This rule exists because workbook XML assumptions are expensive. Every unnecessary structural change creates a new avenue of failure and forces new triage knowledge.

## Roster-to-Neuron example

For June 2026 Neuron Track Hours, the correct operation was not to invent a new workbook.

Correct lane:

- use the last accepted Neuron Track workbook as the structural fixture
- update only the June task-tracking tab
- preserve dashboard/summary/detail tabs unless totals must be updated as values
- restore Val rows from live snapshot when derived attribution broke
- correct Alejandro's June 18 hours
- remove executive-facing internal residue
- keep package structure Web Excel-safe

Wrong lane:

- regenerate the full workbook from scratch
- introduce new chart/table/drawing structure
- trust derived tabs when live snapshot proves they dropped rows
- surface internal reconciliation deltas in the dashboard
- claim validity from screenshots alone

## Validation ladder

A workbook candidate must climb this ladder in order:

1. ZIP opens as a package.
2. XML and `.rels` parts parse.
3. Required package parts exist.
4. Content types are valid.
5. Relationship targets resolve and are not unexpectedly absolute.
6. Sheet names/order match expected contract.
7. Tables and charts have valid part relationships.
8. `calcChain.xml` is absent after programmatic edits.
9. Stop-ship terms and formula errors are absent.
10. Target sheet renders correctly.
11. Non-target sheets remain visually and structurally stable.
12. Excel Web field validation passes.

Do not skip from step 1 to "send it". That is how the artifact goes to the firing squad.

## Acceptance sentence

A workbook is not accepted because it looks right. It is accepted when its data, presentation, and OOXML structure all remain inside the known-good compatibility contract.
