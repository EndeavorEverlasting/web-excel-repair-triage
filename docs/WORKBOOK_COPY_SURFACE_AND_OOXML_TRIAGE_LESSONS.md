# Workbook Copy Surface and OOXML Triage Lessons

## Purpose

Capture recent workbook-generation failures from the AI harness prompt kit sprint and turn them into reusable triage doctrine.

These lessons belong in this repo because they sit at the intersection of:

- generated `.xlsx` artifacts,
- Excel for Web repair behavior,
- clipboard behavior from spreadsheet cells,
- table metadata drift,
- freeze-pane and merge-range claims,
- and artifact acceptance language.

The point is not to make workbooks prettier. The point is to keep generated artifacts healthy, easy to operate, and honest about what has actually been proven.

Latest artifact-specific evidence is recorded in:

```text
docs/AI_PROMPT_KIT_V10_XML_AND_CLIPBOARD_RECORD.md
```

The executable package diagnostic is:

```text
python -m triage.workbook_package_hygiene <workbook.xlsx>
```

## Background

A generated prompt-library workbook went through multiple iterations. The visible workbook looked increasingly polished, but two classes of failures emerged:

1. Excel/Sheets clipboard behavior changed how executable prompts were interpreted by agents.
2. The workbook package layer drifted behind the visible sheet layer, creating Excel repair risk.

The symptoms were practical:

- Agents copied prompts out of spreadsheet cells and responded by rewriting the prompt instead of doing repo work.
- A workbook could not be opened cleanly after visual/classification changes.
- Claimed freeze panes were not actually present in the XML.
- Visible table columns no longer matched `xl/tables/table*.xml` metadata.
- Overlapping merge ranges appeared after layout changes.

The failure is a useful pattern: a workbook can look organized while the backend package is structurally wrong.

## Lesson 1: executable copy surfaces are not normal documentation cells

A giant multiline cell is a poor place to store a prompt that must be copied into an agent chat and obeyed.

Common spreadsheet clipboard behavior can wrap a multiline cell in leading and trailing quotes. Once pasted into an AI chat, that makes the instruction look like a quoted artifact. The next agent may interpret the payload as text to revise instead of an instruction to execute.

### Bad shape

```text
"EXECUTE THE REPO SPRINT...
...
Do the repo work. Commit it."
```

### Better shape

Use a dedicated paste-only sheet:

```text
P07_COPY_SAFE
```

Rules for paste-only sheets:

- No title row above the executable text.
- No instruction banner that says `paste this` or `do not paste`.
- No Markdown fence around the prompt.
- No beginning or ending quote markers.
- No end sentinel such as `END PROMPT` unless the target agent explicitly needs it.
- One prompt line per worksheet row when possible.
- Keep guidance and metadata in a separate index/control sheet.

A catalog sheet can describe the prompt. A paste-only sheet should only contain the prompt.

## Lesson 2: prompt-library workbooks need separate index and execution surfaces

Do not make one sheet do everything.

Recommended separation:

| Surface | Purpose | Clipboard posture |
| --- | --- | --- |
| `START_HERE` | human control board | not pasted |
| `Prompt_Library` | index, classification, prompt metadata | not pasted as executable text |
| `Prompt_Class_Legend` | taxonomy and color rules | not pasted |
| `P07_COPY_SAFE` | executable build prompt | safe to Ctrl+A / Ctrl+C / paste |
| `P12_COPY_SAFE` | executable closeout prompt | safe to Ctrl+A / Ctrl+C / paste |
| `Validation_Report` | package checks and operator notes | not pasted |

This prevents prompt contamination. It also prevents agents from treating a prompt as a document artifact to rewrite.

## Lesson 3: build prompts must not contain closeout escape hatches

A sprint-executor prompt that asks for a next-agent handoff inside the same response may accidentally teach the agent that a handoff is the deliverable.

Use a strict split:

```text
P07 builds.
P12 hands off.
```

For build prompts:

- The deliverable is changed repo files, validation, commit, and push or PR when available.
- A prompt for another agent is not the work.
- Final responses should not include a next-agent prompt unless the sprint is explicitly a closeout sprint.

For closeout prompts:

- The deliverable is compressed context and a next-agent prompt.
- Do not pretend closeout equals implementation.

## Lesson 4: visible layout changes must reconcile table XML

When adding/removing/reordering visible workbook columns, update the table definitions too.

Repair-banner risk appears when the visible sheet says one thing and `xl/tables/table*.xml` says another.

Check at least:

- each table has a unique `id`,
- each table has a unique `name` and `displayName`,
- each table `ref` matches the actual rectangular used range,
- `autoFilter ref` matches the table `ref`,
- table column count matches visible headers,
- table column names match visible headers,
- table refs do not point to stale v4/v5/v6 layouts after a visual redesign.

Example failure pattern:

| XML part | Failure |
| --- | --- |
| `xl/tables/table1.xml` | old `ref` after added columns |
| `xl/tables/table2.xml` | stale table name from prior version |
| `xl/tables/table3.xml` | duplicate `id="1"` across tables |

A workbook can look correct in a generator preview and still be invalid at the package layer.

## Lesson 5: merge ranges are package contracts, not decoration

Overlapping merge ranges are not a harmless style detail.

If a style pass modifies titles, section bars, or widened banner rows, validate:

- no duplicate merge ranges,
- no overlapping merge ranges,
- no merge range extends past the intended sheet width,
- no prior-version merge range remains after a new wider title range is added.

Bad pattern:

```text
A1:H1 overlaps A1:J1
```

Correct pattern:

```text
A1:J1 only
```

Delete or replace the old merge range rather than layering another one on top.

## Lesson 6: freeze panes must be verified in XML, not claimed in prose

It is easy for a workbook generator to claim that headers or decision columns are frozen while the worksheet XML contains no actual `sheetViews/pane` entry.

Validation should inspect the package for actual pane nodes:

```text
xl/worksheets/sheet*.xml -> sheetViews -> sheetView -> pane
```

For control-board sheets, preferred posture:

- freeze the top row for normal table sheets,
- freeze key left columns for wide decision matrices,
- verify the freeze survives export/import,
- do not count visual preview screenshots as freeze-pane proof.

## Lesson 7: style-only passes still need package validation

The repo already treats style as a safe presentation layer only when it does not change formulas or workbook logic. Add package hygiene checks to that same standard.

A style/classification pass should verify:

1. ZIP integrity.
2. Workbook opens through local import tools.
3. No overlapping merge ranges.
4. Table refs match visible ranges.
5. Table column counts match headers.
6. Table IDs and names are unique.
7. Freeze panes exist where claimed.
8. Formula count did not change during a style-only pass.
9. No unexpected formulas/errors such as `#REF!`, `#VALUE!`, `#NAME?`, or `#N/A` appeared.
10. Operator-facing copy surfaces do not include contaminating guidance text.

## Lesson 8: add clipboard acceptance as its own gate

The repo already distinguishes package validity, semantic correctness, presentation quality, Web Excel acceptance, and operator acceptance.

Prompt-library and operator-runbook workbooks need another gate:

| Gate | Meaning |
| --- | --- |
| Clipboard acceptance | Ctrl+A / Ctrl+C from the intended paste surface produces only the intended payload, with no wrapper quotes, guidance banners, hidden labels, or markdown fences. |

This is not the same as package validity. A workbook can open and still produce a bad pasted prompt.

Clipboard acceptance should be tested manually until the repo has a deterministic clipboard harness.

Minimum manual test:

1. Open the workbook in the intended environment.
2. Go to the copy-safe sheet.
3. Press Ctrl+A, then Ctrl+C.
4. Paste into a plain text editor.
5. Confirm the first line is executable content, not a guidance banner.
6. Confirm there are no leading/trailing quotes around the entire payload.
7. Confirm there are no markdown fences unless intentionally required.
8. Confirm the pasted text does not include hidden control-board labels.

## Lesson 9: semantic color needs routing columns, not just pretty rows

Color should classify the prompt or sheet before the user reads paragraphs.

For prompt-library workbooks, key frozen columns should answer:

- What kind of prompt is this?
- Is it for preflight, sprint/build, validation, closeout, safety, runtime proof, or navigation?
- Does it move repo progress?
- What proof gate applies?
- Which prompt should be used next?

The row color should reinforce those answers, not replace them.

Recommended roles:

| Role | Meaning |
| --- | --- |
| Preflight / floor | clear repo, branch, PR, worktree, dirty-state risk |
| Sprint / build | implement tracked repo changes |
| Validate / gate | prove the harness or artifact |
| Closeout / handoff | compress context after work is complete or blocked |
| Safety / hygiene | prevent leaks, runtime artifacts, bad commits, or destructive actions |
| Runtime / prove | live or environment-dependent proof, with stricter proof language |
| Leverage / navigate | code intelligence, MCP/LSP, read-only discovery |
| Planning / distribute | break work into lanes, not a substitute for implementation |

## Lesson 10: acceptance language must stay humble

A generated workbook may pass package checks and still fail as an operational artifact.

Use precise claims:

- `Package-valid`: the `.xlsx` package opens and passes structural checks.
- `Semantically correct`: the expected sheets, headers, prompts, tables, and commands exist.
- `Presentation-safe`: style communicates role/state/hierarchy without changing logic.
- `Clipboard-accepted`: the intended paste surface copies clean executable text.
- `Web Excel accepted`: Excel for Web opens it without repair.
- `Operator accepted`: the user validated it in the real workflow.

Do not collapse these gates into `done`.

## Executable validator

The read-only package validator now lives at:

```text
triage/workbook_package_hygiene.py
```

Run it with:

```text
python -m triage.workbook_package_hygiene <workbook.xlsx>
```

Optional evidence expectations:

```text
--expect-freeze <sheet>
--copy-surface <sheet>
--json
```

It inspects the OOXML ZIP directly and does not rewrite the workbook.

Checks include:

- ZIP integrity,
- XML well-formedness,
- table IDs and names,
- table refs and autoFilter refs,
- table column counts,
- visible table headers,
- overlapping merge ranges,
- expected freeze panes,
- missing worksheet dimensions as metadata warnings,
- formula/error literal markers,
- copy-surface package shape.

The copy-surface check is deliberately limited. It can identify a risky shape, but only the operator's actual Ctrl+A/Ctrl+C workflow proves clipboard acceptance.

## Practical rule

If a workbook is meant to generate action in another tool, the paste surface is part of the product.

Treat it like a UI, not like a note cell.
