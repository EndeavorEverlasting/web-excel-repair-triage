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

### Actionable next-command contract

The exact next command must advance the operator from reported evidence to the next useful, unproven state. It must consume, validate, launch, open, or otherwise exercise the work product. A command that merely reopens a PR, displays a PR page, repeats status already reported, lists branches, or shows logs is not a valid next command when a safe artifact-consumption or validation action is available.

When the completed work exists on a remote branch or unmerged commit, the next command must:

- set the repository location or safe destination explicitly;
- fetch without force and identify the exact branch and commit;
- preserve a dirty or separately owned primary checkout by using an isolated worktree or another non-destructive mechanism;
- run the exact validation, build, or launcher required to prove or consume the result;
- open or print the canonical latest artifact defined by the repository's artifact registry, manifest, builder, workflow, or operator documentation;
- propagate failures and the final exit code;
- must not execute production by default or silently promote a dry run into production.

The canonical artifact is the primary user-consumable output appropriate to the repository, such as a website, workbook, report, package, installer, binary, launcher, rendered documentation, test report, or another declared artifact. Do not guess from a generic filename, search for an arbitrary `index.html`, or open an unrelated build or dependency artifact. Resolve the artifact from tracked repository evidence.

If no renderable or launchable artifact exists, the next command must run the highest-value remaining validator or launcher and print the resulting evidence path. Use `none; cleanup complete` only when no safe and useful action remains. A PR-opening or PR-review command is acceptable only when PR review or merge is the actual blocking gate and the final report names that gate explicitly.

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
- write generated outputs into protected operator-input directories;
- offer a PR-opening, status-only, branch-listing, or log-view command as the sole next action when artifact retrieval, validation, build, launch, or opening is safely available;
- instruct the operator to guess the latest artifact from a generic filename instead of using the repository's canonical artifact contract.

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

### Prompt Kit web top/bottom navigation invariant

The operator-facing Prompt Kit website is a long-form browsing surface and must provide distributed page-end navigation inside the prompt results themselves. Endpoint-only navigation, workbook-sheet links, or a one-time control at the top of the page are insufficient.

- On every repeated prompt-group header row or equivalent repeated header marker rendered inside the main prompt results surface, the left-side header/control cluster must expose a `Top` anchor/control on the left side and the right-side header/control cluster must expose a `Bottom` anchor/control on the right side.
- These controls must be distributed throughout the rendered prompt surface through those repeated headers so the operator can jump to either page endpoint without first scrolling a long distance to find navigation.
- `Top` must jump directly to one canonical page-top anchor. `Bottom` must jump directly to one canonical page-bottom anchor.
- The contract applies under `All / Standard / GNHF / Doctrine`, section, type, and search filtering, and any future Reference/Browse panel filtering. Filtering may hide irrelevant header groups, but any header that remains visible must retain both controls.
- Page-end anchors must use stable, unique same-document targets and must not reload the page, change routes, or lose the active filter state.
- The controls must support both pointer and keyboard activation and must remain visually associated with the repeated header that exposes them.
- The canonical builder or generator owns this behavior. The generated HTML must not be hand-edited as the source of truth.
- Product-level validation must enumerate the repeated headers in the canonical generated page and fail when a rendered header lacks the expected left `Top` or right `Bottom` control, when either canonical endpoint target is missing or duplicated, or when filtering leaves a visible header without both controls.
- Workbook-only navigation does not satisfy this web-page contract. Historical Prompt Kit workbook links may remain useful, but they are separate from the required website behavior.

This subsection is a governance requirement. Builder, generated-site, browser, and interaction changes belong in a separately declared Prompt Kit product sprint; a governance-only sprint installs and enforces the contract but must not claim that the web behavior is already implemented.

## 8. Live certification execution topology

The Prompt Kit must retain a live-certification prompt because live certification is not confined to one execution location. The prompt and its downstream workflow must select a topology from repository and runtime evidence rather than assuming that every certification is local or remote.

### Local topology

Local live certification remains a supported execution topology when proof depends on the operator workstation, a locally attached device, local network reachability, a desktop or browser surface, private inputs that may not be published, or a runtime unavailable to the remote branch environment.

A local live-cert workflow must:

- use a repository-owned launcher, script, validator, or exact bounded command rather than asking a technician to reconstruct a workflow from fragments;
- identify the repository, commit, target, phase, expected artifacts, and proof ceiling before execution;
- run a dry run first when the operation can mutate a target, unless the repository contract proves that the requested action is read-only;
- propagate nonzero exit codes and name the failed phase;
- write only non-sensitive logs, receipts, and reports to repository-approved output locations;
- distinguish process start, command acknowledgment, observed behavior, local runtime proof, and production proof.

### Remote-branch topology

Remote-branch live certification remains a supported execution topology when the implementation, generated output, and deterministic validation can be produced safely on an isolated remote branch without access to a protected local or production-only runtime.

A remote-branch live-cert workflow must:

- create or reuse one isolated branch owned by the cert lane;
- commit the implementation, generated output, validators, and safe evidence required for the user to consume the result;
- push normally and report the exact branch and commit SHA;
- provide one copy-paste pull-and-test snippet in the final response so the user can retrieve the exact remote output and run its verification automatically;
- make that snippet set the repository location, fetch without force, pin the exact commit SHA, preserve a dirty primary checkout by using a clean worktree or other non-destructive mechanism, run the exact validator or test, propagate its exit code, and print or open the resulting artifact path;
- ensure the pull-and-test snippet must not execute production by default and cannot silently promote a dry run into a production action;
- refuse to publish secrets, credentials, private evidence, protected inputs, or unsafe production artifacts on the branch.

Remote branch proof is not local or target-runtime proof. A green remote branch may prove source, build, generated-output, schema, fixture, CI, or bounded remote-runtime behavior only. The final report must name every local, target, provider, GUI, device, network, or production gate that remains unproven.

When both topologies are viable, prefer the topology that produces the strongest safe evidence with the least operator reconstruction. Use remote production of deterministic artifacts plus a pinned pull-and-test snippet when that reduces technician steps; use local certification when the proof genuinely depends on the local or target runtime.

This section governs the future live-cert prompt, skill, capability, trigger, workflow, validators, and result artifacts. Their implementation belongs in separately declared harness and prompt-registry sprints, not in a governance-only sprint.

## 9. Collaborator prompt contribution governance

Collaborators must add or repair prompts through the canonical prompt registry source and its registered builder, never by editing generated HTML directly or by pasting an untracked prompt into documentation as the only implementation.

Before adding a prompt, the contributor must inspect existing governance, prompt IDs and sequences, registry extensions, builders, schemas, skills, capabilities, triggers, validators, generated-output policy, open PRs, and recent history. Existing prompt ownership must be reused, split, merged, retired, or rewired deliberately rather than duplicated.

Every committed prompt must define:

- a unique identifier and sequence;
- a clear name, type, class, deterministic use condition, and keywords;
- the files, contracts, or evidence to inspect first;
- owned scope, forbidden scope, expected artifacts, validation order, and proof ceiling;
- complete copy-safe prompt content;
- the next workflow or proof gate;
- focused tests that reject duplicate identity, incomplete records, stale generated output, and ownership drift.

The repository must provide a reusable prompt-contribution skill for collaborator guidance, a machine-readable prompt-contribution capability for the reusable operation, and a deterministic trigger that routes prompt-addition or prompt-repair requests to that skill, capability, and workflow. Collaborator self-service is not complete while those surfaces exist only as prose or while contributors must guess which registry, builder, or validator owns the change.

### Prompt language quality audit

The repository must also provide one canonical prompt-language-audit skill, one machine-readable prompt-language-audit capability, and one evaluation harness that passes through every prompt in the combined canonical base and extension registries. A sampled review, policy-marker check, or audit of selected prompts is insufficient. Every registered prompt must receive an explicit `pass`, `repair`, `defer`, or `not_applicable` disposition, and a skipped prompt must fail the audit.

The prompt-language-audit skill must define the reusable judgment and repair procedure for examining prompt metadata and complete copy-safe content. It must inspect at minimum the prompt identity, use condition, expected output, next step, proof gate, final-response contract, next commands, next-step lists, artifact references, validation language, ownership language, dependency language, and proof ceiling. It must preserve legitimate prompt-specific behavior while repairing language that permits non-action, ambiguity, operator reconstruction, or inflated proof.

The prompt-language-audit capability must expose explicit machine-readable inputs and outputs. Inputs must include the registry sources, policy version, builder, generated surface, and optional bounded prompt identifiers. Outputs must include the complete prompt inventory, one disposition per prompt, stable rule identifiers, severity, exact field or section, concise evidence, proposed or applied canonical-source repair, validation result, generated-artifact parity result, and aggregate pass or fail. Audit-only and repair modes must be distinct; repair mode must mutate canonical sources rather than generated HTML.

The evaluation harness must include positive fixtures, negative fixtures, and mutation tests that fail on at least these defects:

- empty, placeholder, optional-only, or non-executable next commands and next steps;
- PR-opening, status-only, branch-listing, log-viewing, waiting, monitoring, or permission-seeking as the sole action while safe executable work remains;
- generic verbs or nouns such as `test`, `review`, `merge`, `deploy`, `document`, `monitor`, `follow up`, or `continue` without an owner, exact target, dependency, command or operation, and completion gate;
- missing repository, branch or commit retrieval when the work is remote or unmerged;
- missing dirty-worktree preservation, validator, builder, launcher, artifact resolution, artifact opening or path output, failure propagation, or proof ceiling;
- instructions that require the operator or technician to reconstruct a workflow from command fragments;
- contradictions between owned scope, forbidden scope, expected artifacts, validation, proof claims, and the proposed next action;
- stale generated output, incomplete registry coverage, duplicate policy application, and non-idempotent regeneration.

The eval must report the total prompt count and prove that the disposition count equals that total. A prompt-language audit is complete only after all findings are repaired or explicitly deferred with an owner and blocking reason, focused evals pass, the canonical generated surface is rebuilt, exact parity passes, patch hygiene passes, and commit, push, and PR evidence are reported.

The skill, capability, schemas, fixtures, eval runner, registry integration, reports, and generated-surface wiring belong in a separately declared agent-harness and prompt-registry sprint. They may not exist only as prose inside a prompt, and this governance-only sprint must not implement them.

The factoring boundary is mandatory:

- skills describe reusable workflow guidance and judgment;
- capabilities expose reusable operations with explicit inputs and outputs;
- triggers route deterministic conditions to the correct skill, capability, or workflow;
- application and generator behavior remains in code, schemas, registries, services, and domain contracts;
- prompts orchestrate work but may not become the only implementation of product behavior.

The live-cert prompt must support both local and remote-branch certification topologies, including the pinned copy-paste pull-and-test snippet required by section 8. It must not collapse those topologies into a local-only command or a remote-only artifact workflow.

A prompt contribution is complete only after canonical source changes, focused validation, deterministic regeneration, Git diff review, commit, push, and PR evidence are reported. Generated website or workbook artifacts must be rebuilt from the canonical source and validated for exact parity.

This section is a governance requirement. The prompt-contribution skill, capability, trigger, prompt records, schemas, validators, fixtures, workflows, and generated surfaces must be implemented in a separately declared harness or prompt-registry sprint.

## 10. Prompt panels, chats, and parallel execution

A prompt panel is a copyable transport container for one complete executable prompt. A chat is the execution instance created when that prompt is submitted. When one panel is mapped to one new chat, the panel and chat are functionally equivalent to one independently schedulable execution unit for launch order, ownership, dependency, collision, validation, and proof planning.

Panels and chats are not competing orchestration mechanisms. Parallelism may be expressed as multiple panels in one parallel group, as multiple chats launched concurrently from those panels, or as directly created chats that carry the same complete sprint contracts. The same dependencies, proof gates, lane ownership, branch and worktree isolation, forbidden scope, validation duties, and convergence requirements apply in every representation.

A multi-sprint launch pack must state that one panel goes into one new chat. Every panel must be self-contained; the operator may not be required to combine it with a separately copied shared preamble. A chat created without a visible panel must still receive the same complete repository, lane, scope, dependency, safety, validation, commit, proof, and final-response contract.

Parallel execution is permitted only when repository evidence proves that the units are independent. Different panel titles do not prove that concurrent writes are safe. Before declaring panels or chats parallel-safe, the planner must identify:

- the branch or worktree owned by each unit;
- the files, schemas, manifests, workflows, registries, generated outputs, PRs, and runtime resources each unit may write;
- hard dependencies and proof gates;
- waiting lanes;
- collision risks and the single owner for every shared surface;
- the final convergence unit that validates the combined result.

Units that write the same file, shared schema, workflow, registry, generated artifact, branch, PR, deployment target, or mutable runtime must be serialized or assigned to one explicit writer. Read-only evidence collection may run in parallel with mutation only when it cannot change shared state or invalidate the writer's floor.

General build prompts, including P07, must accept work delivered either as a copyable panel or directly in a chat and must apply the same parallelism rules to both. They must not assume that “panel” means planning-only or that “chat” means serial-only. When a bounded build is one member of a parallel group, its sprint declaration must name its lane, branch or worktree, owned and forbidden scope, dependencies, safe parallel work, collision boundaries, validation, proof ceiling, and final convergence owner.

Each parallel unit must independently produce its required artifacts, validation evidence, commit or remote mutation proof, and handoff. Parallel execution does not lower proof requirements. Completion of individual units is not completion of the whole effort until the declared final convergence unit validates integration and reports the combined repository and PR state.

This section governs the future repair of P07 and any launch-pack, build, cleanup, validation, or closeout prompt that dispatches work through panels or chats. Updating those prompt records, registries, generated surfaces, skills, capabilities, triggers, or application behavior belongs in a separately declared prompt-registry or harness sprint, not in a governance-only sprint.

## 11. Billing pipeline directional contract

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

### Neuron Track Hours monthly task-distribution doctrine

For Neuron Track Hours work, semantic task attribution and source-of-truth correctness come before presentation polish or package mechanics. Spreadsheet/XML preservation remains important, but it must never substitute for correct hours, task distribution, role-specific work, or month-specific operating rules.

#### Permanent NTH attribution rules

- **Roster/attendance is the hours source of truth.** Scheduled project hours must reconcile to attendance before task allocation is accepted. Unscheduled, non-billable, or otherwise excluded support must not be inserted into schedule/project MTD merely to make a task distribution balance.
- **Device counts and device capacity are separate from labor hours.** Device throughput, deployed-device counts, configured-device counts, or site capacity may support context, but none of them creates labor hours.
- **Configuration and Deployment are distinct activities.** Do not treat a device being deployed as proof that the same hours were Configuration, and do not convert Configuration hours into Deployment merely because the work supported a go-live.
- Each paid shift has **one dominant primary workstream**. The primary assignment represents the dominant purpose of that shift or day.
- **Complimentary work may describe concurrent work but must not create additional hours.** Supporting notes can include unrelated concurrent work, secondary tasks, coordination, troubleshooting, staging, tickets, PM work, or cleanup without splitting or duplicating the paid shift unless stronger evidence supports a real hour-level split.
- A full-day primary assignment must not be invented merely because a supporting activity appears in notes. In particular, scattered emails, meetings, client follow-up, or ticket work on a technical day remain complimentary unless the applicable monthly rule pack or date-specific evidence establishes that they dominated the day.
- **PM / Operational Control is real work but not a catch-all.** Use it for prioritization, blocker resolution, resource/schedule decisions, site/delivery planning, operational control, and comparable PM duties when those duties dominate the period.
- **PM, client, and ticket work must not be mechanically spread across technicians.** Role-specific work must follow evidence and known role ownership; Rich's coordination/PM/service workload must not be copied onto Khadejah, Alejandro, Cyen, or other technicians without evidence.
- Evidence precedence for task attribution is: explicit date/person evidence and operator-confirmed facts; then the active month-specific rule pack and established role cadence; then aggregate allocation guardrails; then general fallback assumptions.
- An aggregate allocation rule is a reasonableness test, not a license to erase stronger evidence. Do not force a day into a category solely to hit a target ratio.
- **Do not expose internal task percentages** or allocation mechanics on management-facing NTH surfaces unless the operator explicitly requests them. Management-facing artifacts should show hours, primary workstream, and concise supporting-work context rather than internal allocation math.
- Semantic colors must correspond to the actual activity type, not alternating rows or decorative patterns. Configuration, Inventory Management, Logistics/Staging, Survey/Recon, Cleanup/Disposal, Client Correspondence/Coordination, PM/Operational Control, and other governed workstreams must retain their activity-based color meaning.
- Historical labor and historical categorization are separate questions. A historical categorization concern does not mean the labor did not occur.
- **Historical review language must not imply correction.** Do not call a historical review a reconciliation, correction, revised tracker, or updated historical workbook unless the historical source was actually changed. When the old workbook remains untouched, use `review`, `historical review`, or equivalent language.

#### NTH workbook delivery modes

There are exactly **two governed NTH spreadsheet delivery modes**. The mode must be declared before final packaging so an internal working workbook is never confused with a client-facing deliverable.

1. **Client-facing / management mode.**
   - Produce a separate derived send copy from the validated internal working artifact; do not overwrite, replace, or downgrade the internal workbook to create the client package.
   - Include only the operator-approved client-facing tabs for the active month. Internal-only sheets must be omitted from the delivered package, not merely hidden.
   - Keep the surface decision-ready: hours, primary workstream, concise complimentary work, and only the historical-review context needed by the recipient.
   - Do not expose internal task percentages, allocation mechanics, confidence fields, evidence-posture jargon, source notes, task ledgers, methodology, validator output, audit machinery, doctrine, or forensic detail unless the operator explicitly requests a specific item.
   - The client-facing copy must preserve the same attendance totals, primary-workstream truth, and governed task attribution as the internal workbook. Reducing detail must not change the math or invent a different operational story.

2. **Internal / working mode.**
   - Preserve the complete working record used to construct, audit, repair, and validate the NTH artifact.
   - Internal mode may contain attendance, task ledgers, task summaries, allocation basis, methodology, evidence indexes, device-capacity context, validation, doctrine, historical audit/review, source mapping, exceptions, and other supporting surfaces needed to prove the result.
   - Internal allocation math, evidence mapping, confidence or exception machinery may exist when useful for review, but it remains internal unless the operator explicitly promotes a specific field or tab into the client-facing contract.
   - Internal mode is the default during construction, analysis, repair, or audit. Client-facing mode is a derived delivery artifact created when a management/client send copy is requested.

The two modes must share one semantic source of truth. A client-facing workbook is a narrowed projection of the validated internal workbook, not an independently invented spreadsheet with different totals, dates, attendance, or task attribution.

#### Month-specific rule packs

Neuron Track Hours allocation rules are month-scoped. Each active month may have a different operating mix, role cadence, holiday/absence pattern, site phase, and management-delivery requirement.

Before generating or repairing an NTH artifact, identify the active **month-specific rule pack** and record at minimum:

- effective date or covered date range;
- attendance/roster source;
- aggregate task-allocation guardrails;
- known full-day role cadences;
- date/person exceptions, holidays, absences, and called-in support;
- primary-versus-complimentary work rules;
- workbook delivery mode and the approved client-facing tab contract;
- management-facing exposure rules;
- semantic activity-color rules;
- known historical-review boundaries.

A prior month's allocation rule **must not be silently carried into another month**. If the next month has no confirmed rule pack, preserve the current attendance truth, use explicit evidence first, and mark the task allocation as requiring month-specific confirmation rather than importing the prior month by habit.

#### July 2026 rule pack

The following rules govern the July 2026 NTH artifact unless stronger date/person evidence supplied by the operator supersedes them:

- For work from June 26 forward into the July operating period, the **60% Configuration / 40% other-work allocation** is the aggregate planning and reasonableness guardrail. It is not an exact per-person or per-day quota.
- The 60/40 rule is a **reasonableness guardrail, not permission to overwrite stronger date-specific evidence**. Real inventory relocation, survey/recon, logistics/staging, cleanup/disposal, client coordination, PM/operational control, ticket/service work, or other evidenced work remains distinct even when that makes the measured month land above or below exactly 60% Configuration.
- Rich Perez has **one full Client Correspondence / Coordination day per week**, usually Thursday. That is the weekly day on which meetings, escalations, client correspondence, status/data analysis, delivery/readiness coordination, and similar client-facing work may legitimately dominate the full scheduled shift.
- Known July anchors for the weekly correspondence cadence include **July 2** and **July 23**. For other July weeks, use the usual-Thursday cadence only when it is consistent with the available date-specific evidence; do not manufacture an additional full correspondence day elsewhere in the same week.
- On Rich's non-correspondence days, client follow-up, meetings, ticket/service work, and PM activity may appear as complimentary work when they occurred, but they must not turn an otherwise technical day into an all-day correspondence classification without evidence.
- A week must not show multiple 8-hour or 11-hour Client Correspondence / Coordination days merely because client work appears in supporting notes. One full correspondence day per week is the default July cadence; exceptions require explicit evidence.
- Early-July relocation and inventory work is real work, not Configuration by default. Inventory Management, Survey/Recon, Logistics/Staging, Cleanup/Disposal, and limited Configuration support may coexist on those days; the dominant workstream must follow the actual operational purpose and supporting work belongs in complimentary notes.
- July 10 is a mixed operational day and must not be represented as inventory-only when the evidence supports configuration/troubleshooting and logistics/staging alongside inventory reconciliation.
- **July 3 is a holiday** and contributes no scheduled Neuron project hours for the core team.
- **Alejandro Perales has no scheduled project hours on July 24**. His attendance/status may be represented as `A` on an internal attendance/status surface, but zero project hours must not be added to the NTH MTD total.
- Called-in support must follow the roster/attendance record. A technician appearing on July 24 or another exception date contributes only the hours actually supported by the attendance source.
- **July client-facing mode contains exactly two tabs: `Executive Summary` and `July 2026`.** Do not include or merely hide internal attendance, task-ledger, task-summary, allocation-basis, methodology, evidence-index, validation, doctrine, device-capacity, historical-audit, or other internal-only sheets in the client delivery workbook unless the operator explicitly changes the July client contract.
- **July internal mode preserves the complete supporting workbook** and may retain the internal attendance, task ledger, allocation basis, methodology, evidence, validation, doctrine, audit, device-capacity, and other proof surfaces needed to build and verify the two-tab client copy.
- July management surfaces must not expose internal percentage allocations, confidence machinery, evidence-posture jargon, or forensic mechanics. They should communicate hours, primary workstream, concise supporting work, and the management-relevant historical-review boundary.
- The May 26–29 question is a historical review of attribution. The historical May workbook remains historical source material unless separately and explicitly authorized for mutation; July work must not be presented as an update to May.

## 12. Operator source immutability

`Candidates/` and `Active/` are read-only operator inputs and backup/emulator files.

- Never write, overwrite, or copy engine output into these paths.
- Never set `--output` equal to `--input`.
- All generated workbooks, sidecars, and forensic reports go under `Outputs/`.
- Overwrites elsewhere require a timestamped backup under `Outputs/backups/`.
- Delivery requires baseline fingerprint comparison against the declared source and must fail if sheets are deleted.

See `docs/ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md` for the incident that motivated this rule.
