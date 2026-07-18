# Agent Instructions

## Prompt execution-surface directional contract

Before generating a prompt-kit artifact, classify the requested execution surface:

1. `regular_ai_prompt` — instructions pasted into an interactive AI chat.
2. `gnhf_runtime_objective` — compact repository objective supplied to GNHF.
3. `gnhf_launch_artifact` — executable shell content that enters the repository, selects the route, applies bounds, and supplies or references the runtime objective.

A literal request for a Good Night Have Fun prompt or GNHF prompt means `gnhf_launch_artifact` unless the operator explicitly requests only the inner objective.

Do not substitute a regular AI sprint prompt or objective-only prose for a GNHF launch artifact.

GNHF launch artifacts must:

- resolve and enter the intended repository before Git, installation, validation, provider, or GNHF logic;
- use variable-based user and repository paths rather than a machine-specific username;
- use the reviewed AgentSwitchboard provider route when an exact provider/model is requested;
- keep the provider/model distinct from the GNHF agent adapter;
- include worktree posture, iteration and token caps, bounded provider preflight, positive stop condition, tracked deliverable, validation, and proof ceiling;
- disable push by default;
- reject process completion as repository-delivery proof.

Run:

```text
python -m triage.prompt_execution_surface_contract <artifact-path>
```

The deterministic validator is the acceptance gate. Follow `.ai/skills/prompt-surface-routing/SKILL.md` for the scoped procedure.

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

## Operator source immutability

**Candidates/** and **Active/** are read-only operator inputs (backup/emulator files).

- Never write, overwrite, or copy engine output into these paths.
- Never set `--output` equal to `--input`.
- All generated workbooks, sidecars, and forensic reports go under **Outputs/**.
- Overwrites elsewhere require timestamped backup under `Outputs/backups/`.
- Delivery requires baseline fingerprint compare against the declared source; fail if sheets are deleted.

See [`docs/ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md`](docs/ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md) for the incident that motivated this rule.
