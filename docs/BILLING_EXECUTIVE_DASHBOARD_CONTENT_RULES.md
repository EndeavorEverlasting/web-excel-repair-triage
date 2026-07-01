# Billing Executive Dashboard Content Rules

Date: 2026-07-01

## Purpose

Codify the content rules learned from the June 2026 Neuron Track Hours cleanup.

Executive-facing billing workbooks should report what can be acted on or reviewed. They should not praise individuals, expose internal reconciliation residue, or invite performance-ranking questions.

## Core rule

The executive dashboard is a delivery surface, not a scratchpad.

Anything shown there must meet at least one of these tests:

1. It explains the final month-end posture.
2. It identifies a real review flag.
3. It states a delivery or reconciliation status.
4. It helps the recipient validate the package quickly.

If a field does not meet one of those tests, clear it or move it to an internal QA/audit sheet.

## Do not show

Do not show these items on executive dashboard surfaces:

| Item | Why it fails |
|---|---|
| `Top Technician` / `Top Tech` | Sounds like performance ranking and creates HR-style questions unrelated to billing. |
| Individual praise/glaze | Makes a billing workbook feel subjective and invites avoidable scrutiny. |
| `Billing Difference` | Internal reconciliation term; useful during QA, confusing in delivery. |
| Prior billing baseline delta | Internal audit context, not final executive posture. |
| Debug or pipeline notes | Belongs in a reconciliation report or hidden/internal tab. |
| Formula/error scan details | Belongs in artifact manifest or QA notes, not the executive summary. |

## Allowed executive content

Prefer neutral operational language:

| Allowed field | Example |
|---|---|
| Month status | `Final` / `Ready for review` / `Pending Web Excel validation` |
| Tracked hours | Final month-end tracked hours total. |
| Rows included | Count of task-tracking rows included in the workbook. |
| Reconciliation status | `Roster corrections applied` or `No unresolved task attribution gaps`. |
| Review flags | Only real blockers or items requiring recipient action. |
| Source posture | `Derived from latest roster log and Neuron task attribution`. |

## Better replacement for observations

If an executive note block is needed, use `Action Items / Review Flags`, not `Executive Observations`.

Acceptable entries:

- `Roster corrections applied.`
- `Valentyn Nykoliuk June 9-12 rows restored from live snapshot.`
- `Alejandro Perales June 18 hour correction applied.`
- `June 30 advance hours included.`
- `No unresolved task attribution gaps.`
- `Pending Excel Web field validation.`

Unacceptable entries:

- `Top Technician: <name>`
- `Best performer: <name>`
- `Highest contributor: <name>`
- `Billing Difference: -1.00`
- `Old billing baseline was short by 1.00 hour`

## Internal reconciliation handling

Internal deltas are valid, but they do not belong in the executive-facing dashboard.

Examples of internal-only fields:

- old baseline total
- corrected total delta
- missing row count
- added/restored row count
- live snapshot vs derived tab mismatch
- source pipeline failure point
- Web Excel package scan output

These should live in one of these places:

1. reconciliation report workbook
2. artifact manifest markdown
3. internal QA sheet
4. hidden audit sheet, if the workbook owner wants it preserved in the workbook

## Roster pipeline guardrail

For Neuron Track Hours generation, the live roster snapshot is the controlling source when derived tabs disagree.

Pipeline shape:

```text
Live - June 2026
        ↓
Automated - June 2026
        ↓
Assignments - June 2026
        ↓
Worked Projects - June 2026
        ↓
Neuron Track Hours
```

Required guardrail:

- Compare live snapshot rows against derived project/task attribution before generating final Neuron Track Hours.
- If live rows exist but derived project/task cells are broken, do not silently drop the technician's hours.
- Emit a reconciliation report showing the failure point.
- Restore legitimate live rows when the roster source supports them.

June 2026 example:

- Valentyn Nykoliuk had four 1-hour live snapshot rows for June 9-12.
- Derived project attribution broke across those dates.
- Strict import dropped the rows.
- Correct behavior was to restore the four hours and document the derived-tab failure.

## Lunch deduction rule

Lunch deductions apply to Neuron Track Hours only when the Neuron shift owns the lunch.

Core Neuron team:

- Rich Perez
- Khadejah Harrison
- Alejandro Perales

For the core team, apply normal lunch deduction thresholds.

For non-core or borrowed techs:

- Do not deduct lunch from Neuron rows when the Neuron work is supplemental, split, after-hours, or presumed attached to another primary shift.
- Deduct lunch only if the roster explicitly shows a standalone Neuron shift long enough to own its own lunch.

This rule prevents borrowed-tech Neuron support from being double-deducted when another project already consumed the primary shift lunch.

## Acceptance checklist

Before delivering a billing workbook:

- Executive dashboard contains no individual ranking language.
- Executive dashboard contains no internal baseline or billing-difference fields.
- Executive notes are blank or action/review oriented.
- Final tracked hours match the latest accepted roster reconciliation.
- Live snapshot mismatches are checked before derived project tabs are trusted.
- Internal reconciliation detail is moved to a report, manifest, or QA surface.
- Web Excel package checks pass before delivery.

## Cold judge verdict

A billing dashboard should be boring, legible, and defensible.

If a label makes the recipient ask, "Why is this here?", it probably loses.
