# Agent Governance Contract

This file is the single repository governance authority for agents working in `EndeavorEverlasting/web-excel-repair-triage`. Domain rules later in this file remain binding within their scope.

## 1. Agent operating principles

1. **Evidence before action.** Inspect repository law, current Git and PR state, relevant files, tests, validators, artifacts, and recent history before changing anything.
2. **Floor before furniture.** Repair unsafe repository state, broken shared contracts, or missing validation floors before building dependent features.
3. **Bounded sprints.** Every writing sprint must declare its mission, owned scope, forbidden scope, expected artifacts, validation order, and proof ceiling.
4. **One writer per branch.** Each active writing lane owns one branch or isolated worktree. Never share uncommitted state between agents.
5. **Reuse before replacing.** Preserve healthy code, contracts, helpers, launchers, registries, workflows, and documentation before inventing competing implementations.
6. **No completion without proof.** Plans, acknowledgments, summaries, or successful process exits are not completion. Completion requires tracked evidence, validation, and Git or PR proof.

## 2. Instruction precedence

When instructions conflict, apply this order:

1. Platform, security, legal, and repository-owner instructions.
2. This governance contract, including the closest nested `AGENTS.md` for a subtree when one exists.
3. Task-specific prompts and sprint instructions.
4. Generic agent defaults.

A lower-precedence instruction may strengthen safety or narrow scope, but it may not weaken a higher-precedence rule. When a conflict cannot be resolved safely, stop the conflicting action, preserve evidence, and report the exact conflict.

## 3. Mandatory sprint declaration

Before modifying tracked files, state:

- repository and branch or worktree;
- lane and mission;
- owned scope and forbidden scope;
- expected artifacts;
- validation commands and their order;
- proof ceiling;
- whether push, PR update, merge, deployment, or release authority exists.

If the primary worktree is dirty, conflicted, stale, or owned by another lane, preserve it and use an isolated branch or worktree. Never discard unrelated work merely to obtain a clean base.

## 4. Completion standard

A sprint is complete only when all applicable items are reported:

- exact files changed;
- validation commands actually run and their results;
- commit SHA;
- push state;
- PR URL and state when applicable;
- blockers and skipped checks with exact reasons;
- proof achieved and proof ceiling;
- final Git status or an explicit statement that local Git state was unavailable;
- one exact next command, or `none; cleanup complete`.

Static validation proves only static behavior. CI proves only the exercised CI surface. Neither may be represented as live operator, provider, Windows GUI, or production-runtime proof.

## 5. Forbidden behaviors

Agents must not:

- acknowledge without making the authorized mutation;
- return a plan when implementation is authorized and safe;
- claim completion without running the stated checks;
- expose secrets, credentials, private workbook contents, or machine-local evidence;
- force-push, rewrite default-branch history, or destructively clean unknown work unless explicitly authorized;
- delete branches, worktrees, PRs, or unique commits before preservation proof;
- hide deterministic application behavior exclusively in prompts or skills;
- weaken validators, fixtures, or proof requirements merely to make a check pass;
- write generated outputs into protected operator-input directories.

## 6. Repository mutation discipline

1. Inspect existing patterns before creating new files or authorities.
2. Repair the canonical implementation rather than creating a competing one.
3. Keep changes bounded to the declared owned scope.
4. Add or update tests, validators, schemas, manifests, or CI when they enforce changed behavior.
5. Run focused checks before broad or expensive suites.
6. Run `git diff --check` before commit.
7. Commit coherent tracked changes with a useful message.
8. Push normally and open or update a PR when authorized.
9. Merge only after required checks and review findings are resolved.

## 7. Technician acquisition and update surface

Technician-facing delivery of the Prompt Kit website and generators must include a mouse-accessible Windows CMD entry point that provides one safe action:

- when the repository is absent, clone the canonical GitHub repository into a clearly displayed destination;
- when the repository already exists, fetch and fast-forward the configured default branch only;
- refuse to reset, overwrite, or discard dirty or divergent local work;
- verify that the checked-out branch is the intended default branch and that required site/generator files exist;
- open the current Prompt Kit website or generator selection GUI only after acquisition or update succeeds;
- use repository-relative paths after cloning and avoid embedded user-specific paths;
- report authentication, network, Git, divergence, and file-validation failures clearly;
- never embed credentials or automate provider authentication.

If destination or behavior choices are required, they must be presented through a GUI rather than command-line questions. A direct CMD is appropriate only for a single safe default action.

This section is a governance requirement. Its implementation belongs in a separately declared launcher or operator-enablement sprint, not in a governance-only sprint.

## 8. Billing pipeline directional contract

This repository supports Web Excel-safe repair and triage workflows for roster, billing, admin-sheet, and task-tracker artifacts.

Agents must identify the requested workflow direction before generating scripts, workbook patches, summaries, or corrections.

### Supported directions

#### 1. Roster Log to Admin Sheet

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

#### 2. Roster Log to Task Tracker

Medium-priority contextualization workflow.

Use the roster log to contextualize hours inside the task tracker. This path explains what the hours supported: configuration, deployment, logistics, project coordination, exceptions, and documented contributions.

Rules:

- Treat this as internal context, not submission output.
- Map staff, date, hours, project assignment, and override logic into task context.
- Preserve useful contribution evidence.
- Do not reshape this into an admin-facing workbook unless explicitly requested.

#### 3. Task Tracker to Roster Log

Low-priority reviewed backfill workflow.

Use the task tracker to propose roster updates based on noted contributions. This direction must be review-gated.

Rules:

- Propose updates only unless direct roster mutation is explicitly approved.
- Typical proposed updates include project overrides, assignment clarifications, and notes.
- Never silently mutate the roster log.
- Rejected updates stay as tracker-only context.

### Priority order

1. Roster Log to Admin Sheet
2. Roster Log to Task Tracker
3. Task Tracker to Roster Log

### Recommended script names

```text
roster_to_admin_submission.py
roster_to_task_context.py
task_tracker_to_roster_backfill.py
```

### Friday reporting rule

Friday is the reporting batch marker. Work performed Monday through Friday maps to that Friday's reporting/submission batch. Weekend work generally rolls into the next Friday reporting batch unless explicitly handled otherwise.

### Core logic rules

- Overrides beat default assignment.
- Resolved worked-project logic beats raw assumption.
- Raw notes that conflict with resolved logic should create exceptions.
- Admin-facing output stays narrow and clean.
- Internal task-tracker context may be richer, but it must not leak into admin submission artifacts.
- Backfill into the roster log must be proposed, reviewed, and approved before mutation.

## 9. Operator source immutability

`Candidates/` and `Active/` are read-only operator inputs and backup/emulator files.

- Never write, overwrite, or copy engine output into these paths.
- Never set `--output` equal to `--input`.
- All generated workbooks, sidecars, and forensic reports go under `Outputs/`.
- Overwrites elsewhere require a timestamped backup under `Outputs/backups/`.
- Delivery requires baseline fingerprint comparison against the declared source and must fail if sheets are deleted.

See `docs/ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md` for the incident that motivated this rule.
