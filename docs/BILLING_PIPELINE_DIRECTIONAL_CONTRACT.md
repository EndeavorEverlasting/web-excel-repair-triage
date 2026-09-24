# Billing Pipeline Directional Contract

This document defines the supported billing and task-tracking workflow directions for Web Excel repair and triage work.

The central rule: direction matters. A clean admin submission export is not the same thing as internal task contextualization, and neither is the same thing as a reviewed roster backfill.

## Direction Map

```mermaid
flowchart TD
    RL["Roster Log: hours, punches, assignments, overrides"]
    AS["Admin Sheet: one-shot Project Team submission output"]
    TT["Task Tracker: hours context, contribution notes, project evidence"]

    RL --> AS
    RL --> TT
    TT --> RL
```

## Priority Order

1. Roster Log to Admin Sheet
2. Roster Log to Task Tracker
3. Task Tracker to Roster Log

Agents must identify the requested direction before generating scripts, workbook patches, summaries, or corrections.

---

## 1. Roster Log to Admin Sheet

High-priority submission workflow.

```mermaid
flowchart TD
    A["Roster Log"] --> B["Read live month tabs"]
    B --> C["Read assignments and overrides"]
    C --> D["Resolve worked project"]
    D --> E["Filter to admin submission scope"]
    E --> F["Populate Project Team tab only"]
    F --> G["Generate admin-facing workbook"]
    G --> H["Friday submission"]
```

### Purpose

Create a clean admin-facing workbook for Friday billing or submission review.

### Rules

| Rule | Requirement |
|---|---|
| Output scope | Admin-facing only |
| Default workbook scope | Project Team tab only unless explicitly requested |
| Project classification | Use resolved worked-project logic, including assignments and overrides |
| Internal notes | Do not expose |
| Confidence fields | Do not expose |
| Exception machinery | Keep internal unless it blocks submission |
| Priority | High |

### Contract

Roster Log to Admin Sheet is a one-shot submission export. It should produce a clean admin-facing Project Team workbook from resolved roster data. It should not expose internal logic, review scaffolding, confidence notes, private notes, or task-tracker context.

---

## 2. Roster Log to Task Tracker

Medium-priority contextualization workflow.

```mermaid
flowchart TD
    A["Roster Log"] --> B["Read staff, date, and hour records"]
    B --> C["Resolve project assignment and override"]
    C --> D["Attach hours to task-tracker context"]
    D --> E["Map hours to work categories"]
    E --> F["Support narratives and weekly summaries"]
    F --> G["Task Tracker"]
```

### Purpose

Explain what the hours supported.

The admin sheet says who worked, when, and how much. The task tracker adds what the labor supported: configuration, deployment, logistics, project coordination, exceptions, and documented contributions.

### Rules

| Rule | Requirement |
|---|---|
| Output scope | Internal context |
| Goal | Explain hours through task and project activity |
| Acceptable context | Project notes, contribution notes, deployment context, configuration work, logistics, exceptions |
| Admin-ready by default | No |
| Priority | Medium |

### Contract

Roster Log to Task Tracker is for contextualizing hours. It should help explain what work the hours supported, including project activity, configuration, deployment, logistics, exceptions, and contribution narratives. It is not the admin submission artifact.

---

## 3. Task Tracker to Roster Log

Low-priority reviewed backfill workflow.

```mermaid
flowchart TD
    A["Task Tracker"] --> B["Identify noted contribution"]
    B --> C["Extract staff, date, project, and work context"]
    C --> D{"Does roster already reflect it?"}
    D -- "Yes" --> E["No action"]
    D -- "No" --> F["Create proposed roster update"]
    F --> G["Review queue"]
    G --> H{"Approved?"}
    H -- "No" --> I["Keep as tracker-only note"]
    H -- "Yes" --> J["Update roster override, note, or assignment"]
```

### Purpose

Propose roster updates based on noted contributions.

This is a backfill workflow, not the normal direction. The task tracker can suggest that the roster needs an update, but it must not silently rewrite the roster.

### Rules

| Rule | Requirement |
|---|---|
| Output scope | Proposed roster corrections |
| Automation level | Review-gated |
| Direct write allowed | No, unless explicitly approved |
| Typical updates | Override, project note, assignment clarification |
| Priority | Low |

### Contract

Task Tracker to Roster Log is a low-priority backfill path. It should only propose roster updates based on noted contributions. It must not silently mutate the roster log. All updates should pass through a review queue before becoming roster data.

---

## Agent Decision Rule

```mermaid
flowchart TD
    A["Agent receives billing or task-tracking request"] --> B{"Which direction is requested?"}
    B --> C["Roster Log to Admin Sheet"]
    B --> D["Roster Log to Task Tracker"]
    B --> E["Task Tracker to Roster Log"]
    C --> F["Generate clean submission artifact"]
    D --> G["Generate internal context and contribution mapping"]
    E --> H["Generate proposed roster updates only"]
```

## Recommended Script Names

```text
roster_to_admin_submission.py
roster_to_task_context.py
task_tracker_to_roster_backfill.py
```

## Friday Reporting Rule

Friday is the reporting batch marker. Work performed Monday through Friday maps to that Friday's reporting or submission batch. Weekend work generally rolls into the next Friday reporting batch unless explicitly handled otherwise.

## Implementation Notes

- Overrides beat default assignment.
- Resolved worked-project logic beats raw assumption.
- Raw notes that conflict with resolved logic should create exceptions.
- Admin-facing output should remain clean and narrow.
- Internal task-tracker context can be richer, but it must not leak into admin submission artifacts.
- Backfill from Task Tracker into Roster Log must be proposed, reviewed, and approved before mutation.
