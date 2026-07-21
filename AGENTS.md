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

## Repo-local AI harness

Use [`HARNESS.md`](HARNESS.md) and [`configs/harness/harness_manifest_v1.json`](configs/harness/harness_manifest_v1.json). Prompts are artifacts inside the harness, not the harness itself.

- Inspect registered rules, maps, workflows, run context, artifact registry, validators, hooks, skills, code intelligence, reports, generated-output policy, and branch/PR conventions before inventing.
- Name repo, branch/worktree, PR/sprint, lane, owned scope, forbidden scope, expected artifacts, and user-specified validation order.
- Execute `request -> evidence review -> bounded decision -> repo/Git/GitHub mutation -> artifacts -> validation -> report -> next decision`.
- Generate the requested artifact or mutation; a rewritten prompt, plan, handoff, or acknowledgment is not completion.
- Preserve useful work, validate focused then broad, commit and push coherent contributions, update the intended PR, and report exact proof and ceiling.
- For troubleshooting, use P54: prefer validated runtime and current repository evidence, identify the first confirmed divergence, derive commands and paths from live contracts, and mutate only when repair is requested.
- For website/spreadsheet work, run the registered input analyzer first; implement website-to-spreadsheet before the reverse lane, route both through the shared IR, and never call analysis or a plan a converted artifact.
- Task-specific execution rules override generic closeout behavior.

Prompt Kit ergonomics remain enforced: bare `xyz_under_score_placeholders`; Prompt Library B:O exact-range links and semantic row colors; A/P sparse navigation; matching prompt-tab RGB colors.
