# Workbook Generation Insights for Web Excel Safety

This note captures hard-won lessons from generating admin-facing roster/hour workbooks that must survive Excel for Web without repair prompts, silent rewrites, or lost presentation logic.

The goal is prevention first, triage second. Do not wait for Excel Web to become the judge, executioner, and sloppy copy editor.

## Scope

Use this guidance when generating clean `.xlsx` outputs from roster, attendance, billing, task-tracking, or project-hours data.

This document is intentionally public-safe. It records workbook-generation rules and pipeline behavior, not client names, staff names, protected data, or internal billing details.

## Core rule

A generated workbook is not acceptable merely because desktop Excel opens it. It must satisfy three tests:

1. The package passes structural gate checks.
2. Excel for Web opens it without a repair prompt or `WORKBOOK REPAIRED` banner.
3. The visible workbook still tells the business truth after upload, copy/paste, download, and reopen.

If any of those fail, the workbook is still a candidate. It is not production.

## Lessons from roster/hour workbook generation

### 1. Generate only the tabs required for the submission

For administrative submissions, unnecessary tabs are attack surface.

If the target user only needs a `Project Team` style tab, generate that tab cleanly instead of hauling along dashboards, formulas, named ranges, legacy tabs, and stale workbook relationships.

Practical effect:

- fewer workbook parts
- fewer relationship targets
- lower repair risk
- faster review
- less chance of exposing internal logic

### 2. Preserve the workbook's human-facing format, but rebuild the XML cleanly

When a source workbook has the right visual contract but suspect internals, treat it as a layout reference, not a safe base.

Recommended pattern:

1. Read the source workbook for tab shape, headers, merged regions, period labels, and expected rows.
2. Read the roster or attendance workbook for data.
3. Rebuild the required output tab into a fresh workbook.
4. Apply explicit formatting intentionally.
5. Run gate checks before any handoff.

Do not keep broken XML alive because it has nice borders. Pretty poison is still poison.

### 3. Add missing date coverage deliberately

If the existing workbook starts mid-period, do not pretend the missing days are implied.

Example pattern:

- A workbook may include weekly blocks beginning after the first day of the month.
- The generator must add an opening partial-week block when needed.
- The month should reconcile from the actual first day through the actual last day.

Do not silently omit early-month days because the inherited layout forgot them.

### 4. Separate time values from status markers

Roster data often mixes numeric time entries with operational status markers.

Treat these as separate classes:

| Class | Examples | Count as hours? | Preserve visually? |
|---|---|---:|---:|
| Work interval | `8:00 AM - 5:00 PM` | Yes | Yes |
| Non-time status | `OUT SICK`, `OFF`, `N/A`, `NON-PTO` | No | Yes |
| Review target | malformed, incomplete, implausible span | No, until resolved | Yes, prominently |

The generator should preserve non-time markers because they explain why a cell is not hours. It should not convert them into zeros that look like missing work.

### 5. Detect implausible long shifts before export

Attendance parsing must flag shifts that look mathematically possible but operationally wrong.

Typical danger case:

- A missing PM marker makes `8:00 - 5:00` parse as a 21-hour or 9-hour error depending on the parser assumptions.
- A clock-out crossing midnight may be real, but it must be classified intentionally.

Minimum safeguards:

- configurable long-shift threshold
- distinct overnight handling
- explicit review log for normalized punches
- no silent correction without an audit note

A workbook that gets the total right by accident is not good enough. Accuracy without explainability is a booby trap.

### 6. Prefer shared strings over inline strings

For generated workbooks intended for Excel for Web, avoid `inlineStr` output when possible.

The safer generation target is a workbook package that includes `xl/sharedStrings.xml` and stores repeated text through the shared-string table.

Why this matters:

- Excel for Web has historically been less forgiving with generated workbook packages that mix fragile XML patterns.
- Shared strings make generated text-heavy admin workbooks more predictable.
- The repo already treats `inlineStr` as a STOP-SHIP concern in its compatibility methodology.

### 7. Keep formulas out unless they are required

For submission workbooks, static calculated values are often safer than formulas.

Use formulas only when the recipient needs live recalculation.

If the workbook is meant to be pasted into an admin/shared workbook, formulas are liability:

- references can break after paste
- formulas can trigger unsupported-function prefixes
- copied formulas can drag stale sheet names
- Web Excel may rewrite calc chains or shared formulas

When totals are known at generation time, write the values and style the audit trail.

### 8. Do not use high-level writers to repair existing broken workbooks

High-level libraries are fine for generating a new minimal workbook, but not for repairing an existing complex workbook in place.

Repair rules remain:

- do not reserialize existing XML
- do not introduce `ns0:` namespace leakage
- do not reorder attributes in untouched parts
- do not pretty-print OOXML parts
- do not assume desktop Excel acceptance means Web Excel acceptance

When repairing, use this repo's byte-level diff, recipe, and patch approach.

When generating fresh, keep the output simple enough that it does not require surgery.

## Recommended generator contract

Every workbook-generation script should emit three artifacts:

1. The `.xlsx` output.
2. A machine-readable scan report, such as JSON.
3. A human-readable summary of assumptions and review targets.

Minimum JSON scan report fields:

```json
{
  "source_workbook": "name of layout/source workbook",
  "data_workbook": "name of roster/attendance workbook",
  "output_workbook": "generated workbook name",
  "generated_at": "ISO timestamp",
  "tabs_generated": ["Project Team"],
  "period_start": "YYYY-MM-DD",
  "period_end": "YYYY-MM-DD",
  "hours_by_month": {},
  "status_markers_preserved": 0,
  "review_targets": [],
  "stopship_tokens": {
    "inlineStr": 0,
    "ns0:": 0,
    "_xlfn.": 0,
    "_xludf.": 0,
    "_xlpm": 0,
    "#REF!": 0
  },
  "shared_strings_present": true
}
```

## Preflight checklist before handoff

Run this before the file leaves the workbench:

- [ ] The output contains only the required submission tabs.
- [ ] Period coverage starts on the true first required date.
- [ ] Period coverage ends on the true last required date.
- [ ] Non-time markers are preserved but excluded from hour totals.
- [ ] Long shifts and overnight shifts are reviewed or logged.
- [ ] Totals reconcile by month and by person/project where applicable.
- [ ] `xl/sharedStrings.xml` exists.
- [ ] No `inlineStr` tokens exist unless intentionally allowed for a specific controlled case.
- [ ] No `ns0:` or `xmlns:ns0` namespace leakage exists.
- [ ] No `_xlfn.`, `_xludf.`, `_xlpm`, `AGGREGATE(`, or `FORMULATEXT` tokens exist in formulas.
- [ ] No `#REF!` exists in formulas, defined names, conditional formatting, or data validation.
- [ ] Excel for Web opens the uploaded file without repair prompts.
- [ ] Downloading the opened Web copy and diffing it does not show structural rewrites that matter.

## Workflow with this repo

### Generation lane

Use this lane when the source data is good enough and the target output is simple.

1. Put source workbooks in `Candidates/` or a run-specific input folder.
2. Generate a clean output workbook with only the required tabs.
3. Save the output under `Outputs/` with a timestamped name.
4. Run gate checks against the output workbook.
5. If clean, upload/open in Excel for Web.
6. If Web opens cleanly, promote a copy to `Active/`.
7. If Web repairs it, move the Web-repaired export to `Repaired/` and switch to the repair lane.

### Repair lane

Use this lane when Web Excel repairs the candidate.

1. Candidate goes in `Candidates/`.
2. Web-repaired copy goes in `Repaired/`.
3. Run part diff.
4. Classify repair patterns.
5. Generate a patch recipe.
6. Apply the recipe to a copy, not the only working file.
7. Re-run gate checks.
8. Re-test in Excel for Web.
9. Promote only after Web opens cleanly.

## Implementation notes for future scripts

Good scripts should do the following:

- discover date columns by headers, not hardcoded indexes
- discover staff/project rows by labels, not fixed row numbers
- classify markers before calculating durations
- normalize only with explicit notes
- use deterministic filenames with date/time suffixes
- write a scan report next to the workbook
- preserve source files untouched
- keep internal logic separate from admin-facing output

Bad scripts do this:

- overwrite the source workbook
- preserve all tabs by default
- hardcode date columns
- silently coerce text into zero
- hide review targets in comments only
- depend on desktop Excel to clean the package
- declare victory without an Excel Web open test

The judge awards no points for elegant lies.

## Suggested future tool enhancement

Add a dedicated `generation_preflight` module that can scan newly generated workbooks before they enter the normal repair flow.

Potential function signature:

```python
def generation_preflight(path: str) -> dict:
    """Return Web Excel generation-safety findings for a newly generated workbook."""
```

Suggested checks:

- shared strings present
- inline strings absent
- namespace leakage absent
- unsupported formula tokens absent
- required tabs present
- unexpected tabs absent when a target tab list is supplied
- period/date coverage matches expected range when metadata is supplied
- review-target sheet or JSON report exists for corrected/normalized records

That would turn this workflow from heroic recovery into boring repeatability. Boring is good. Boring ships.
