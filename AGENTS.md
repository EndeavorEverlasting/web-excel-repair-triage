# Agent Instructions

## Billing Pipeline Directional Contract

This repository supports Web Excel-safe repair and triage workflows for roster, billing, admin-sheet, and task-tracker artifacts.

Agents must identify the requested workflow direction before generating scripts, workbook patches, summaries, or corrections.

## Supported Directions

### 1. Roster Log to Admin Sheet

High-priority submission workflow.

Use the roster log to generate a clean admin-facing Project Team sheet for Friday billing/submission review. This is a one-shot output path.

Rules:

- Produce admin-facing output only.
- Default workbook scope is Project Team tab only unless explicitly requested.
- Use resolved worked-project logic, including assignments and overrides.
- Do not expose internal exception machinery.
- Do not expose confidence fields.
- Do not expose private notes.
- Do not leak task-tracker context into the admin artifact.

### 2. Roster Log to Task Tracker

Medium-priority contextualization workflow.

Use the roster log to contextualize hours inside the task tracker. This path explains what the hours supported: configuration, deployment, logistics, project coordination, exceptions, and documented contributions.

Rules:

- Treat this as internal context, not submission output.
- Map staff, date, hours, project assignment, and override logic into task context.
- Preserve useful contribution evidence.
- Do not reshape this into an admin-facing workbook unless explicitly requested.

### 3. Task Tracker to Roster Log

Low-priority reviewed backfill workflow.

Use the task tracker to propose roster updates based on noted contributions. This direction must be review-gated.

Rules:

- Propose updates only unless direct roster mutation is explicitly approved.
- Typical proposed updates include project overrides, assignment clarifications, and notes.
- Never silently mutate the roster log.
- Rejected updates stay as tracker-only context.

## Note-Tolerant Roster Parsing

Roster users may write human notes directly in punch cells when operational reality demands it. Scripts must treat this as valid input, not corruption.

Examples of valid note-bearing punch values:

```text
9:28:00 AM / Client support
9:28 AM - off-project coverage
17:30 / inventory follow-up
```

Parsing requirements:

- Extract the time portion for hour calculations.
- Preserve the note portion for internal context and exception review.
- Do not allow the note portion to break admin artifact generation.
- If a note implies a project classification different from the resolved worked project, create an exception or proposed override.
- Do not silently reclassify admin output from a raw note alone unless an approved override or resolved worked-project rule supports it.
- Do not expose raw private notes in admin-facing outputs unless explicitly requested.

## Priority Order

1. Roster Log to Admin Sheet
2. Roster Log to Task Tracker
3. Task Tracker to Roster Log

## Recommended Script Names

```text
roster_to_admin_submission.py
roster_to_task_context.py
task_tracker_to_roster_backfill.py
```

## Friday Reporting Rule

Friday is the reporting batch marker. Work performed Monday through Friday maps to that Friday's reporting/submission batch. Weekend work generally rolls into the next Friday reporting batch unless explicitly handled otherwise.

## Core Logic Rules

- Overrides beat default assignment.
- Resolved worked-project logic beats raw assumption.
- Raw notes that conflict with resolved logic should create exceptions.
- Admin-facing output stays narrow and clean.
- Internal task-tracker context may be richer, but it must not leak into admin submission artifacts.
- Backfill into the roster log must be proposed, reviewed, and approved before mutation.
