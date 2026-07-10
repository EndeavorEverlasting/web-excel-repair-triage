# AI Prompt Kit v10 XML and Clipboard Record

## Record purpose

This record connects the latest AI Harness Prompt Kit artifact to the broader Web-Excel Repair Triage doctrine.

Artifact examined locally:

```text
ai_harness_prompt_kit_v10_paste_only.xlsx
```

The workbook itself is not committed because generated binary artifacts and operator-specific working files do not belong in the repo by default. The reusable findings, package observations, validation contract, and operator workflow belong here.

Related doctrine:

```text
docs/WORKBOOK_COPY_SURFACE_AND_OOXML_TRIAGE_LESSONS.md
```

## Why this artifact matters to Triage

Triage is evolving into a spreadsheet harness: a set of contracts, package checks, acceptance gates, and operator evidence that helps generated workbooks remain healthy in Excel for Web.

The prompt kit adds a second future layer. It is also an AI harness artifact. Its spreadsheet structure controls how instructions are copied into agent chats, so workbook package health and copy-surface behavior directly affect software-agent behavior.

This makes the workbook a useful boundary artifact:

```text
spreadsheet package -> Excel UI/clipboard -> agent prompt interpretation -> repo action
```

A defect at the spreadsheet or clipboard layer can look like an agent reasoning failure. Triage should preserve enough evidence to distinguish those layers.

## Operator-observed clipboard behavior

Current successful workflow:

1. Open `P07_COPY_SAFE` or `P12_COPY_SAFE`.
2. Use the worksheet select-all control so all cells in the tab are selected.
3. Copy.
4. Paste into the agent chat.
5. The prompt arrives as executable text and agents are more likely to perform repo work.

Current risky workflow:

1. Copy a giant multiline prompt from the `Prompt_Library` cell.
2. Paste into the agent chat.
3. Excel may wrap the payload with a quote at the beginning and another at the end.
4. The agent may treat the payload as quoted material to rewrite instead of instructions to execute.

The operator also observed that removing one of the wrapper quotes can be enough to avoid this lazy rewrite behavior. That is useful diagnostic evidence, but it is not a stable product contract. The workbook should avoid creating the wrappers in the first place.

## Package inventory

The inspected artifact contains:

- 24 worksheets,
- 3 worksheet table objects,
- dedicated `P07_COPY_SAFE` and `P12_COPY_SAFE` sheets,
- a wide `Prompt_Library` table,
- no macros,
- no committed live/customer data in the examined package.

Relevant sheets:

```text
START_HERE
Prompt_Sequence
Prompt_Library
P07_COPY_SAFE
P12_COPY_SAFE
Copy_Mode_Rules
V10_PasteOnly_Fix
```

## Copy-surface XML shape

### `P07_COPY_SAFE`

Observed package shape:

- 86 populated cells,
- populated cells are in column `A`,
- first populated cell is `A1`,
- `A1` begins directly with:

```text
EXECUTE THE REPO SPRINT. DO NOT REWRITE THIS PROMPT.
```

- blank worksheet rows provide paragraph spacing,
- prompt lines are separate cells instead of one giant multiline cell,
- no title row precedes the executable payload,
- no `END PROMPT` sentinel appears in the copy surface.

### `P12_COPY_SAFE`

Observed package shape:

- 29 populated cells,
- populated cells are in column `A`,
- first populated cell is `A1`,
- `A1` begins directly with:

```text
COMPRESS THIS SPRINT INTO A NEXT-AGENT HANDOFF.
```

This is the intended closeout surface and remains separate from the build executor.

### `Prompt_Library`

The `Prompt_Library` retains large multiline prompt cells in column `N` for several prompt types.

Examples from package inspection:

| Cell | Approximate length | Embedded newlines | Role |
| --- | ---: | ---: | --- |
| `N2` | 1062 | 16 | general harness doctrine |
| `N4` | 1428 | 50 | conversation closeout mapper |
| `N5` | 1569 | 64 | repo-aware sprint distributor |
| `N6` | 1913 | 71 | sprint plan pack generator |
| `N7` | 1499 | 67 | repo/worktree hygiene coordinator |
| `N10` | 1638 | 49 | live/runtime proof sprint |
| `N11` | 1606 | 52 | read-only code intelligence |
| `N12` | 1618 | 47 | local hook/artifact hygiene |
| `N13` | 1481 | 55 | synthetic harness validator |
| `N15` | 847 | 29 | reusable rules review |

Those cells are useful as catalog/reference surfaces, but they are unsafe as the default executable clipboard surface.

The P07 and P12 rows now point the operator to their dedicated copy-safe sheets. That is directionally correct.

## OOXML table record

The artifact contains these table definitions:

| Part | Table name/displayName | Ref | Columns |
| --- | --- | --- | ---: |
| `xl/tables/table1.xml` | `StartHereV9` | `A4:H13` | 8 |
| `xl/tables/table2.xml` | `PromptSequenceV9` | `A1:L15` | 12 |
| `xl/tables/table3.xml` | `PromptLibraryV9` | `A1:N15` | 14 |

Positive findings:

- table IDs are unique: `1`, `2`, `3`,
- table refs match the current visible rectangular table ranges,
- table column counts match the declared table ranges,
- table headers match the visible header cells,
- table refs have matching `autoFilter` refs,
- the prior duplicate-table-ID and stale-column-count defects are not present.

Record-impact finding:

- the v10 artifact still uses `V9` in its table object names.

This does not by itself make the workbook invalid. It is provenance/version drift. The package is structurally describing a newer artifact with older internal object names. Triage should report this as metadata drift or a warning when artifact-version expectations are supplied, not automatically as corruption.

## Worksheet metadata record

On the inspected sheets `START_HERE`, `Prompt_Library`, `P07_COPY_SAFE`, and `P12_COPY_SAFE`:

- no worksheet `<dimension>` node was present,
- no worksheet `<pane>` node was present.

The workbook therefore does not currently provide XML proof for previously claimed freeze panes on these sheets.

Interpretation:

- missing dimensions are metadata drift and may be tolerated by Excel,
- missing panes mean the freeze-pane claim is not proven in the package,
- neither condition alone proves an Excel for Web repair event,
- the validator should distinguish `WARN` metadata drift from package-breaking `FAIL` conditions.

## Merge-range record

The current inspected artifact does not repeat the earlier overlapping merge defect on the key sheets.

Earlier failure pattern:

```text
A1:H1 overlapped A1:J1
```

Current relevant title merge on `START_HERE`:

```text
A1:J1
```

The package-hygiene validator should continue checking all merge rectangles pairwise because this defect can be introduced by a visual redesign even when the visible sheet looks reasonable.

## Acceptance-gate impact

This artifact reinforces that workbook acceptance needs separate gates:

| Gate | Current artifact evidence |
| --- | --- |
| ZIP/package readable | locally observed |
| XML well-formed | locally observed |
| table metadata consistent | locally observed for the three tables |
| merge ranges non-overlapping | locally observed on package scan |
| freeze panes proven | not proven on inspected sheets |
| copy-surface package shape | improved for P07/P12 |
| clipboard accepted | operator observed for copy-safe sheets |
| Prompt Library clipboard accepted | not accepted as default executable surface |
| Excel for Web accepted | not proven by this local package inspection |
| operator accepted | partial: copy-safe workflow works; broader workbook acceptance remains separate |

Do not replace these gates with one `valid` flag.

## New diagnostic surface

This PR adds:

```text
python -m triage.workbook_package_hygiene <workbook.xlsx>
```

Useful invocation for the prompt kit:

```powershell
python -m triage.workbook_package_hygiene `
  "<path>\ai_harness_prompt_kit_v10_paste_only.xlsx" `
  --expect-freeze START_HERE `
  --expect-freeze Prompt_Library `
  --copy-surface P07_COPY_SAFE `
  --copy-surface P12_COPY_SAFE
```

The validator is read-only and inspects the ZIP/XML package directly.

It checks:

- ZIP CRC integrity,
- XML and relationship-part well-formedness,
- table ID uniqueness,
- table name/displayName uniqueness,
- table refs and autoFilter refs,
- declared/range table column counts,
- visible headers against table XML columns,
- overlapping merge ranges,
- expected freeze panes,
- missing worksheet dimension nodes,
- formula/error literal markers,
- copy-surface package shape.

Copy-surface checks can identify risky shapes such as:

- multiple populated columns,
- giant multiline cells,
- `PASTE THIS DIRECTLY` guidance contamination,
- `END PROMPT` sentinels,
- missing copy-surface sheets.

They cannot prove what Microsoft Excel places on the system clipboard. That still requires operator evidence.

## Record update rule

When a prompt-kit workbook changes again, preserve the following in the record instead of committing the binary by default:

- artifact filename/version,
- worksheet inventory,
- table object names and refs,
- table IDs and column counts,
- merge-overlap result,
- pane/dimension inventory,
- nominated copy-surface sheets,
- operator clipboard outcome,
- Excel for Web outcome,
- package validator command/output,
- exact gap between package proof and operator proof.

## Next layer

The spreadsheet harness is now mature enough to support an AI-harness layer, but the two should remain distinguishable:

```text
Spreadsheet harness
  -> package validity
  -> semantic workbook contract
  -> presentation safety
  -> clipboard acceptance
  -> Web Excel acceptance

AI harness
  -> prompt classification
  -> copy-safe execution surfaces
  -> repo evidence
  -> bounded action
  -> committed work
  -> validation
  -> report / next decision
```

The AI layer should consume spreadsheet-harness evidence rather than declaring the workbook healthy on its own.
