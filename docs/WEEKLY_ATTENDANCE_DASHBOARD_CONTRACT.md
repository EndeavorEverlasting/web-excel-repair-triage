# Weekly Attendance Dashboard Automation Contract

This document records the contract for generating weekly attendance/action dashboards from roster logs, admin workbooks, and review artifacts.

The goal is repeatable dashboard generation for tech-facing attendance targets, not one-off spreadsheet heroics. The dashboard should tell reviewers exactly what needs action, what needs review, and what has already been dismissed as a false flag.

## Scope

Use this contract when building weekly dashboards that help a team review attendance, roster punches, partial hours, admin mismatches, and submission blockers before a leadership-facing admin workbook is finalized.

The dashboard is an internal action artifact. It may contain review scaffolding, confidence fields, false-flag dispositions, and work-order definitions that should not appear in a clean admin submission workbook.

## Core workflow

```text
Roster log + admin workbook + prior review dashboard
        ↓
Parse roster punches, notes, defaults, assignments, worked projects, and overrides
        ↓
Compare admin-facing hours against roster evidence
        ↓
Classify review/action targets deterministically
        ↓
Generate Web Excel-safe dashboard with definitions, dropdowns, and conditional formatting
        ↓
Reviewers update admin workbook first, then roster log after admin reality is stable
```

## Authority hierarchy

Project expectations must not be inferred from the admin workbook tab name.

Use this hierarchy for project classification:

1. Approved explicit override
2. Resolved worked-project rule
3. Assignment or default project from the roster log
4. Raw notes as evidence only
5. Exception or review queue if conflict remains

The admin workbook can be authoritative for leadership-facing hours or correction intent when the user identifies it as the control record. It is not automatically authoritative for project assignment.

## Corrected Project Override rule

Do not create a Project Override action merely because an admin workbook tab is named `Project Team` or a similar submission label.

A Project Override row is actionable only when independent roster evidence supports a project mismatch, such as:

- explicit roster default conflict
- assignment tab conflict
- worked-project conflict
- approved override conflict
- note-derived project signal that conflicts with resolved project logic and requires review

If the only evidence is the admin workbook tab name, classify the row as a false flag.

## False flag semantics

Gray means false flag, dismissed, intentionally ignored, or not applicable.

Gray does not mean unresolved.

A row marked gray should not return to the action queue unless new evidence appears. Scripts should preserve gray classifications from prior reviewed dashboards where possible.

Recommended false-flag dispositions:

| Disposition | Meaning |
|---|---|
| `False flag - project expectation wrong` | The row came from incorrect project inference logic |
| `Dismissed - roster default already correct` | Roster default/assignment/worked project already supports the current value |
| `Dismissed - admin lingering only` | The row is residue in the admin/control workbook, not a tech correction |
| `Not applicable` | The row does not apply to the submission scope |
| `Needs new evidence` | Keep out of the action queue unless more evidence is supplied |

## Dashboard lane definitions

Every generated dashboard must include definitions for its lanes. Labels without definitions are not acceptable.

Minimum lane definitions:

| Lane | Definition | Typical action |
|---|---|---|
| `Action Console rows` | Master working queue. Includes blockers and review targets. Not every row is an error. | Filter by blocker, severity, owner, and issue family. |
| `Red must-fix blockers` | Rows that can materially corrupt submitted hours or prevent a trustworthy submission. | Fix before leadership submission. |
| `Amber review before submit` | Plausible rows that require human confirmation before submission. | Confirm, dismiss, or escalate. |
| `Partial-hour review rows` | Roster-derived hours are greater than zero and below the configured full-day threshold. | Review before submission. Do not auto-expand. |
| `Note-bearing punch rows` | Punch cells contain both time and human notes, such as `9:28 AM / coverage`. | Extract time for calculations and preserve note internally. |
| `Lead/reviewer protection rows` | Short days, afternoon clock-outs, or weekend rows for known full-day/long-day reviewers. | Do not silently downgrade without explicit exception evidence. |
| `Punch edit / mismatch rows` | Admin and roster time evidence differ or cannot be reconciled cleanly. | Compare evidence and propose exact punch/admin correction. |
| `Retired project false flags` | Rows produced by known-bad Project Override assumptions. | Keep gray unless new roster evidence supports action. |
| `Admin lingering rows` | Admin/control workbook rows that linger outside the active tech correction scope. | Separate from direct punch edits; review only if they affect submission. |

## Partial-hours rule

Partial hours must be flagged before leadership submission.

Default rule:

```text
roster_derived_hours > 0 and roster_derived_hours < full_day_threshold
```

The default full-day threshold should be configurable. A common initial value is `8.0` hours.

Partial hours are not automatically wrong. They are review targets.

A good dashboard separates these from hard errors so reviewers can protect legitimate partial work without letting accidental short days slip through.

## Reviewer protection rule

Some reviewers or leads may routinely work full days, long days, or weekend coverage. For those people, short or afternoon clock-outs should be treated as high-priority review targets when admin/control evidence indicates a full or long day.

This rule should be configurable and data-driven. Do not hardcode private names in public docs.

Required behavior:

- detect short days for configured protected reviewers
- detect afternoon clock-outs when admin/control hours indicate a full or long day
- detect Saturday/weekend rows rather than silently excluding them
- require explicit exception evidence before accepting a shortened day
- never silently downgrade admin/control values from roster assumptions alone

## Note-bearing punch behavior

Punch cells may contain human notes. This is valid input, not corruption.

Required behavior:

- extract the time portion for hour calculations
- preserve the note portion for internal context
- keep admin-facing output clean unless raw notes are explicitly requested
- compare note-derived project signals against resolved worked-project logic
- create exceptions or proposed overrides when notes conflict with resolved logic
- do not fail dashboard or admin generation because a punch cell contains a note

## Required dashboard fields

Dashboard outputs should include enough fields to guide action without forcing reviewers to inspect every source workbook manually.

Minimum recommended fields:

```text
Month
Date
Tech
Issue Family
Issue Type
Severity
Submission Blocker
Priority
Status
Result
Owner
Confidence
Evidence Status
Resolution Decision
False Flag Disposition
Root Cause
Update Target
Tech Confirmation
Admin Sheet
Admin Cell
Admin Value
Roster Sheet
Roster Row
Clock In Cell
Clock Out Cell
Roster Clock In
Roster Clock Out
Roster Derived Hours
Expected Hours
Roster Default Project
Roster Assignment
Worked Project
Resolved Project
Expected Project
Note Signal
Review Note
Correction Instruction
```

## Required dropdowns

Dashboard columns that humans must edit should use dropdowns.

Recommended dropdown groups:

| Dropdown | Recommended values |
|---|---|
| `Status` | `Open`, `In Review`, `Resolved`, `Dismissed`, `Blocked`, `Needs Evidence` |
| `Result` | `Update Admin`, `Update Roster`, `No Change`, `False Flag`, `Escalate`, `Defer` |
| `Submission Blocker` | `Yes`, `No`, `Review` |
| `Priority` | `P0`, `P1`, `P2`, `P3` |
| `Confidence` | `High`, `Medium`, `Low` |
| `Evidence Status` | `Admin Only`, `Roster Only`, `Admin + Roster`, `Notes Only`, `Conflict`, `Confirmed` |
| `Resolution Decision` | `Accept Admin`, `Accept Roster`, `Correct Punch`, `Preserve Note`, `Create Override`, `Dismiss` |
| `False Flag Disposition` | `False flag - project expectation wrong`, `Dismissed - roster default already correct`, `Dismissed - admin lingering only`, `Not applicable`, `Needs new evidence` |
| `Root Cause` | `Missing punch`, `Partial hours`, `Note-bearing punch`, `Admin mismatch`, `Roster mismatch`, `Project inference error`, `Lingering admin row`, `Weekend review`, `Protected reviewer short day` |
| `Update Target` | `Admin workbook`, `Roster log`, `Both`, `No workbook change`, `Review only` |
| `Tech Confirmation` | `Confirmed`, `Unconfirmed`, `Needs tech follow-up`, `Not needed` |
| `Issue Family` | `Punch`, `Partial Hours`, `Notes`, `Project`, `Admin Lingering`, `False Flag`, `Reviewer Protection`, `Reconciled` |

## Conditional formatting contract

Dashboard colors must match documented meaning.

Minimum color meanings:

| Color | Meaning |
|---|---|
| Red | Must fix before submission |
| Amber | Review before submission |
| Gray | False flag, dismissed, intentionally ignored, or not applicable |
| Blue | Admin lingering or out-of-scope context |
| Green | Reconciled or no action |
| Purple | Explicit note/override/context lane |

The workbook must include a CF dictionary sheet explaining every color. If a color exists without a definition, the dashboard is not ready for handoff.

## Weekly automation target

The repo should eventually support a repeatable weekly command that emits review artifacts before the Friday submission cycle.

Suggested command shape:

```bash
python scripts/generate_weekly_attendance_dashboard.py \
  --admin-workbook Candidates/admin.xlsx \
  --roster-log Candidates/roster.xlsx \
  --prior-dashboard Candidates/prior_dashboard.xlsx \
  --week-ending 2026-05-29 \
  --output Outputs/weekly_attendance_dashboard_2026-05-29.xlsx \
  --scan-report Outputs/weekly_attendance_dashboard_2026-05-29.json
```

Suggested output set:

```text
Outputs/weekly_attendance_dashboard_<YYYY-MM-DD>.xlsx
Outputs/weekly_attendance_dashboard_<YYYY-MM-DD>.json
Outputs/weekly_attendance_targets_<YYYY-MM-DD>.csv
Outputs/weekly_false_flags_<YYYY-MM-DD>.csv
Outputs/weekly_submission_blockers_<YYYY-MM-DD>.csv
```

## Web Excel-safe requirements

Generated dashboards must follow the workbook generation guidance in this repo.

Minimum checks:

- no `inlineStr` unless explicitly allowed and documented
- no `ns0:` or `xmlns:ns0`
- no `_xlfn.`
- no `_xludf.`
- no `_xlpm`
- no `#REF!`
- no broken relationships
- no calcChain
- no unsupported formulas
- dropdowns and conditional formatting survive Excel for Web
- definitions and CF dictionary are included
- repaired Web Excel copies become the new base if Web Excel normalizes the file

## Review flow

Recommended weekly workflow:

1. Generate dashboard from roster/admin/prior dashboard evidence.
2. Review red blockers first.
3. Review amber partial-hours and protected-reviewer rows second.
4. Preserve gray false flags; do not resurrect dismissed rows.
5. Update admin workbook first when preparing leadership-facing submission.
6. Update roster log after the admin workbook is stable and evidence is clear.
7. Feed confirmed false flags and resolved rows into the next dashboard generation.

## Implementation notes

Future implementation should keep classification deterministic and testable.

Suggested modules:

```text
scripts/generate_weekly_attendance_dashboard.py
scripts/classify_attendance_targets.py
scripts/parse_roster_punches.py
scripts/resolve_worked_project.py
scripts/generation_preflight.py
```

Suggested test cases:

- Project Override false positive when only admin tab name suggests `Project Team`
- gray false-flag row remains dismissed in next weekly dashboard
- partial-hours row is flagged before submission
- note-bearing punch cell parses time and preserves note
- protected reviewer short day is flagged when admin/control evidence shows full day
- Saturday/weekend row is reviewed rather than silently excluded
- admin lingering row is separated from direct tech correction target
- dropdown definitions exist for every human-editable review field
- CF dictionary defines every fill color used in the workbook

## Operating principle

The dashboard should reduce manual work, not outsource confusion to the reviewer.

If a reviewer has to ask what a lane means, the workbook failed.

If a false flag returns every week after being dismissed, the classifier failed.

If Web Excel repairs the file and removes controls, the generator failed.

No spreadsheet snakes.