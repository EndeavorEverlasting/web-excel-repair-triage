# Roster Workbook Generation Doctrine

Date: 2026-07-12

## Purpose

This document is the single authoritative reference for generating, mutating, and
delivering Active Roster Log workbooks. It codifies the build strategy proven
during the July 2026 Wave 3 build, the failure patterns discovered in prior
attempts, and the acceptance gates that every generated roster artifact must pass.

A fresh operator or agent should be able to read this document and understand
what the deliverable is, how to build it safely, what rules govern lunch and
overnight handling, what must stay private, and how to prove the artifact is
acceptable.

This document does not duplicate the full content of referenced docs. It states
the rules inline and points to the canonical source for deeper detail.

---

## 1. The deliverable is the actual roster workbook

The generated roster workbook is the primary artifact. Not a companion
workbook. Not a sidecar report. Not a summary spreadsheet. The actual roster
that management opens, reviews, and trusts.

**Rules:**

- The output must be an .xlsx file that opens in desktop Excel and Excel for
  Web without repair prompts.
- The roster must be recognizably based on the original workbook layout.
- Attendance must be populated month-to-date for the target wave.
- Billing totals must reconcile.
- Distributed task hours must equal billable hours.
- Private rationale must stay on hidden or internal tabs.
- Client-facing tabs must remain clean.
- A diagnostic report must accompany every generated artifact.

**Reference:** [ACTIVE_ROSTER_LOG_MECHANICS.md](ACTIVE_ROSTER_LOG_MECHANICS.md)

---

## 2. Build from the original workbook

Every roster build starts from the latest accepted workbook. Never build from
scratch when an accepted source exists. Never use a known-failed workbook as a
source fixture.

**Rules:**

- Identify the latest accepted workbook before starting.
- Preserve its sheet order, tab roles, styles, shared-string behavior, table
  names, drawing/chart structure, and content types unless performing a
  deliberate structural migration.
- Treat the accepted workbook as a compatibility fixture, not just a design
  reference.
- Failed workbooks (files that triggered Excel Web repair, refused to open, or
  produced structural defects) must be quarantined, not reused.

**Mutation classes** (from [XLSX_STRUCTURE_PRESERVATION_CONTRACT.md](XLSX_STRUCTURE_PRESERVATION_CONTRACT.md)):

| Class | Description | Posture |
|-------|-------------|---------|
| A: Value-only | Update task rows, dates, names, hours | Preserve package shape |
| B: Style-only | Color bands, row heights, borders | Reuse existing style IDs |
| C: Sheet-local rebuild | Rebuild one tab from accepted source rows | Snapshot manifest before/after |
| D: Structural migration | Add/remove sheets, charts, tables | Requires new compatibility lane |

Default to the lightest mutation class that accomplishes the task.

**Failed artifact quarantine:**

- Reject outputs with basenames containing epaired_, Deprecated_repaired_,
  or web_repaired_.
- Record the failure path in the diagnostic report.
- Never feed a failed artifact back into the build pipeline as a source.

**Reference:** [XLSX_STRUCTURE_PRESERVATION_CONTRACT.md](XLSX_STRUCTURE_PRESERVATION_CONTRACT.md),
[WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md](WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md)

---

## 3. Prove a no-op round trip before mutation

Before any workbook modification, prove that a no-op save and reopen does not
corrupt the artifact. This is a mandatory build gate, not an optional check.

**Required gate:**

1. Load the source workbook.
2. Save it to a temporary path without changing any values.
3. Reopen the temporary file.
4. Compare: sheet names, sheet order, cell values on every populated sheet,
   package parts, and structural metadata.
5. If the no-op round trip introduces drift, do not proceed with the original
   workbook. Investigate the corruption vector first.

**Why this exists:** openpyxl and other programmatic editors can silently alter
shared strings, calc chain state, CF priorities, table definitions, or
relationship targets during a save. The no-op gate catches these before
business logic is layered on top.

**Reference:** [XLSX_STRUCTURE_PRESERVATION_CONTRACT.md](XLSX_STRUCTURE_PRESERVATION_CONTRACT.md)

---

## 4. Attendance checkpoint before task distribution

Populate attendance data first. Verify totals. Only then add task-distribution
features. This prevents task logic from masking attendance errors.

**Required sequence:**

1. **No-op round trip** (gate 3 above).
2. **Attendance population:** Fill clock-in/out pairs, resolve projects using
   the 4-level precedence hierarchy, compute gross hours, apply lunch
   deductions, compute net hours.
3. **Attendance checkpoint:** Save a checkpoint artifact. Verify:
   - Expected staff rows are present.
   - Expected date range is covered.
   - Gross and net totals reconcile against roster source.
   - Overnight shifts are handled correctly.
   - Lunch deductions match policy.
4. **Task distribution:** Apply task-hour distribution rules after checkpoint
   passes. Populate event log, daily narrative, and review flags on internal
   tabs.

**Checkpoint naming pattern:**

`
Active_Roster_Log_ReviewQueue_CF_{date}_{wave}_Attendance_Checkpoint.xlsx
`

**Project resolution precedence** (from [ACTIVE_ROSTER_LOG_MECHANICS.md](ACTIVE_ROSTER_LOG_MECHANICS.md)):

1. Assignments Overrides sub-table (highest priority)
2. Worked Projects - {Month} cell
3. Assignments - {Month} main-table cell
4. Live default Project column (fallback)

**Reference:** [ACTIVE_ROSTER_LOG_MECHANICS.md](ACTIVE_ROSTER_LOG_MECHANICS.md),
[ROSTER_BILLING_PIPELINE_INSIGHTS.md](ROSTER_BILLING_PIPELINE_INSIGHTS.md)

---

## 5. Final task-distribution integration

After the attendance checkpoint passes, apply task-hour distribution rules to
populate the task tracker, event log, and daily narrative.

**Rules:**

- Task-hour distribution rules live in
  [	riage/neuron_task_hour_distribution_rules.py](../triage/neuron_task_hour_distribution_rules.py).
  Full rule definitions: [NEURON_TASK_HOUR_DISTRIBUTION_RULES.md](NEURON_TASK_HOUR_DISTRIBUTION_RULES.md).
- Distributed task hours must sum to the billable hours for each row.
- Do not distribute hours uniformly across all tasks; use declared distributions.
- Month-specific rules apply (April deployment-heavy vs May config/inventory).
- Private cohort labels (e.g. may_deployment_field_team) identify rows that
  use special distributions; the public repo must not hardcode names.
- Internal rationale (rule names, override flags, distribution decisions)
  belongs on internal/hidden tabs, not client-facing surfaces.

**Final artifact naming pattern:**

`
Active_Roster_Log_ReviewQueue_CF_{date}_{wave}_Task_Distribution_v{N}.xlsx
`

**Reference:** [NEURON_TASK_HOUR_DISTRIBUTION_RULES.md](NEURON_TASK_HOUR_DISTRIBUTION_RULES.md)

---

## 6. Generation engine policy

| Engine | Acceptable for | Notes |
|--------|---------------|-------|
| openpyxl | New blank workbooks, bounded Class A value edits | Must not save when modifying existing workbooks via XML graft path |
| XML/ZIP surgical graft | Existing workbook mutations (Class A-C) | Preferred for production roster edits |
| Excel COM (Windows) | Strongest Windows build engine | Evaluate for production; not available in sandbox environments |
| LibreOffice CLI | Import/export testing, format round-trip validation | Not equivalent to desktop Excel or Excel for Web acceptance |

**Rules:**

- Never hand-splice OOXML parts without a documented reason and package
  manifest diff.
- New blank workbooks may be generated with openpyxl. Record
  openpyxl_save_used: true in provenance.
- Existing workbook mutations must use the XML/ZIP graft path. Record
  openpyxl_save_used: false in provenance.
- When openpyxl is used for a new workbook, the output still must pass the
  full validation ladder before delivery.

**Reference:** [XLSX_STRUCTURE_PRESERVATION_CONTRACT.md](XLSX_STRUCTURE_PRESERVATION_CONTRACT.md)

---

## 7. Lunch deduction rules

### Standard deduction table

| Gross shift span | Deduction | Net calculation |
|------------------|-----------|-----------------|
| >= 8.0 hours | 1.0 hour | gross - 1.0 |
| >= 6.0 and < 8.0 hours | 0.5 hour | gross - 0.5 |
| < 6.0 hours | 0.0 hours | gross |

Implementation: [	riage/hours_basis_policy.py](../triage/hours_basis_policy.py)
(lunch_deduction, 
et_hours_from_gross).

### Core vs non-core team policy (name-agnostic)

The lunch rule is driven by **role and assignment state**, not by person names.

- **Core Neuron shifts:** Apply standard lunch deduction thresholds. A shift
  is core when the tech's default project is Neuron Deployments AND the work
  is a primary standalone shift.
- **Borrowed/non-core support shifts:** Do NOT deduct lunch from Neuron rows
  when the work is supplemental, split, after-hours, or attached to another
  primary shift. Deduct lunch only when the roster shows a standalone shift
  long enough to own its own lunch.

**How to determine core vs non-core without hardcoding names:**

1. Check the Live sheet's default Project column for the tech.
2. If the default project is Neuron and the worked project is Neuron, the
   shift is a core Neuron shift.
3. If the tech's default project is something else (e.g. Delivery, Projects
   Team) but they worked a Neuron shift, it is a borrowed support shift.
4. If assignment overrides exist, use them to determine whether the Neuron
   work is standalone or supplemental.

Implementation: [	riage/hours_basis_policy.py](../triage/hours_basis_policy.py)
(lunch_deduction_with_policy).

### Hours basis rule

| Artifact family | Hours basis |
|----------------|-------------|
| Billing Summary | Net hours |
| Delta Dashboard | Net hours |
| Neuron Track Hours | Gross hours |

Do not silently normalize Neuron Track Hours into net billing hours.

**Reference:** [HOURS_BASIS_POLICY.md](HOURS_BASIS_POLICY.md),
[BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md](BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md)

---

## 8. Overnight shift handling

Management prefers non-rollover entries. Overnight shifts should be split
into non-rollover entries where operationally appropriate.

**Rules:**

- An overnight shift is detected when clock-out < clock-in (crosses midnight).
- Gross span = clock-out + 24.0 - clock-in.
- Split at midnight: Segment 1 = midnight - clock-in; Segment 2 = clock-out.
- Distribute the original total lunch deduction to preserve the exact
  total-hour impact.
- Preserve the total hours; do not lose or gain hours during the split.
- Record the original span, split segments, and preserved total in the
  diagnostic report.

Implementation: [	riage/hours_basis_policy.py](../triage/hours_basis_policy.py)
(split_overnight_shift).

**Reference:** [ACTIVE_ROSTER_LOG_MECHANICS.md](ACTIVE_ROSTER_LOG_MECHANICS.md),
[HOURS_BASIS_POLICY.md](HOURS_BASIS_POLICY.md)

---

## 9. Core team vs support techs (name-agnostic)

Eligibility for core-team treatment comes from roster state, default projects,
assignment overrides, and worked-project overrides. Not from person names.

**Rules:**

- Never hardcode technician names into eligibility logic in the public repo.
- Determine core vs borrowed status from:
  - Default project column on the Live sheet.
  - Worked Projects override for that date.
  - Assignment Overrides sub-table.
  - Whether the Neuron shift is standalone or supplemental.
- Private workbooks or local config may pass role/cohort labels (e.g.
  may_deployment_field_team) for specific rows.
- The public repo stores the rule, not the names.

**Reference:** [BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md](BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md),
[NEURON_TASK_HOUR_DISTRIBUTION_RULES.md](NEURON_TASK_HOUR_DISTRIBUTION_RULES.md)

---

## 10. Private vs client-facing surfaces

Internal assumptions, staffing restrictions, reconciliation logic, and
narrative derivation belong only on private or hidden tabs.

**Rules:**

- Client-facing tabs must be clean: no internal rationale, no confidence
  fields, no pipeline notes, no raw task notes, no pay-petition framing.
- Internal reconciliation detail belongs in a report, manifest, QA surface,
  or hidden audit sheet.

**Private sheet naming pattern:**

| Sheet | Contents |
|-------|----------|
| _Wave3 Task Rules | Task distribution rule selections, override flags |
| _Wave3 Event Log | Per-event context derivation and confidence |
| _Wave3 Daily Narrative | Daily work-context narrative for internal review |
| _Wave3 Review Flags | Items requiring operator attention |
| _Wave3 Build Audit | Build manifest, fingerprints, validator results |

The underscore prefix signals internal/private. These sheets must not appear
in client-facing delivery unless explicitly requested.

**Do not show on executive surfaces:**

- Top Technician / Top Tech rankings
- Individual praise or performance language
- Billing Difference or prior baseline deltas
- Debug or pipeline notes
- Formula/error scan details

**Allowed on executive surfaces:**

- Month status
- Tracked hours totals
- Row counts
- Reconciliation status
- Review flags (real blockers only)
- Source posture

**Reference:** [BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md](BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md),
[ROSTER_BILLING_PIPELINE_INSIGHTS.md](ROSTER_BILLING_PIPELINE_INSIGHTS.md)

---

## 11. Validation ladder

A workbook candidate must climb this ladder in order. Do not skip from step 1
to delivery.

| Step | Check |
|------|-------|
| 1 | ZIP opens as a package |
| 2 | XML and .rels parts parse |
| 3 | Required package parts exist |
| 4 | Content types are valid |
| 5 | Relationship targets resolve inside the package |
| 6 | Sheet names and order match expected contract |
| 7 | Tables and charts have valid part relationships |
| 8 | calcChain.xml is absent after programmatic edits |
| 9 | Stop-ship terms and formula errors are absent |
| 10 | Target sheet renders correctly |
| 11 | Non-target sheets remain visually and structurally stable |
| 12 | Excel Web field validation passes |

**Stop-ship tokens** (from [WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md](WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md)):

- _xlfn., _xludf., _xlpm. (unsupported function namespaces)
- AGGREGATE( (known Web hazard)
- #REF!, #VALUE!, #NAME? (formula errors in stored XML)

**Package-shape drift signals:**

- Missing [Content_Types].xml or bad default content type
- Relationship targets that escape the package root
- Unexpected absolute internal relationship targets
- Chart parts under unexpected drawing subpaths
- Duplicate table names
- Stale calcChain.xml
- External workbook links
- Namespace pollution (
s0: or xmlns:ns0)

**Reference:** [WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md](WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md),
[XLSX_STRUCTURE_PRESERVATION_CONTRACT.md](XLSX_STRUCTURE_PRESERVATION_CONTRACT.md),
[insights/web-excel-compatibility-artifact-lessons-2026-07-01.md](insights/web-excel-compatibility-artifact-lessons-2026-07-01.md)

---

## 12. Diagnostic report requirements

Every generated roster artifact must be accompanied by a sidecar diagnostic
report in JSON format.

**Naming pattern:**

`
Active_Roster_Log_ReviewQueue_CF_{date}_{wave}_Task_Distribution_v{N}_diagnostic_report.json
`

**Required fields:**

`json
{
  "generated_at": "ISO-8601 timestamp",
  "timezone": "America/New_York",
  "mode": "full | blank | checkpoint | task_distribution",
  "source_workbook": {
    "path": "string",
    "sha256": "string",
    "size_bytes": 0,
    "is_failed_artifact": false
  },
  "no_op_round_trip": {
    "passed": true,
    "drift_detected": [],
    "package_parts_before": 0,
    "package_parts_after": 0
  },
  "attendance_checkpoint": {
    "saved": true,
    "path": "string",
    "staff_row_count": 0,
    "date_range": "YYYY-MM-DD to YYYY-MM-DD",
    "gross_hours_total": 0.0,
    "net_hours_total": 0.0,
    "overnight_splits": 0,
    "lunch_deductions_applied": 0
  },
  "task_distribution": {
    "applied": true,
    "billable_hours_total": 0.0,
    "distributed_hours_total": 0.0,
    "hours_reconciled": true,
    "distribution_rules_used": []
  },
  "validation": {
    "zip_opens": true,
    "xml_parses": true,
    "content_types_valid": true,
    "relationships_valid": true,
    "calc_chain_absent": true,
    "stop_ship_tokens_absent": true,
    "target_sheets_render": true,
    "non_target_sheets_stable": true,
    "excel_web_opens": true,
    "excel_web_repairs_needed": false
  },
  "proof_level": "fixture | package | desktop_excel | excel_web | operator_acceptance",
  "skipped_gates": [],
  "git": {
    "branch": "string",
    "commit_sha": "string",
    "dirty": false
  },
  "failed_artifacts": []
}
`

**Why this exists:** A diagnostic report provides an auditable record of what
was built, what was validated, what was skipped, and what the proof ceiling is.
It prevents vague claims of safety and gives the next operator or agent the
context to continue safely.

---

## 13. Artifact naming conventions

### Final artifact

`
Active_Roster_Log_ReviewQueue_CF_{date}_{wave}_Task_Distribution_v{N}.xlsx
`

Example:
`
Active_Roster_Log_ReviewQueue_CF_2026-07-12_Wave3_Task_Distribution_v3.xlsx
`

### Attendance checkpoint

`
Active_Roster_Log_ReviewQueue_CF_{date}_{wave}_Attendance_Checkpoint.xlsx
`

### Diagnostic report

`
Active_Roster_Log_ReviewQueue_CF_{date}_{wave}_Task_Distribution_v{N}_diagnostic_report.json
`

### Failed artifact quarantine

Failed artifacts must not be used as source fixtures. Label failure evidence
clearly and store separately from accepted outputs.

---

## 14. Explicitly rejected behaviors

The following behaviors are forbidden in roster workbook generation:

- Building from known-failed workbooks.
- Generating a companion workbook as the primary deliverable.
- Claiming Excel safety from ZIP/XML scans alone.
- Hardcoding technician names into eligibility or billing logic.
- Exposing private billing rationale on client-facing sheets.
- Manually splicing worksheets into the OOXML package.
- Silently changing billing math.
- Using _xlfn, _xlws, _xludf, LAMBDA, LET, FILTER, UNIQUE, SORT,
  or other unsupported formula features.
- Committing private workbook binaries to the repo.
- Committing generated client artifacts to the repo.
- Writing into Candidates/ or Active/ source directories.
- Claiming field validation without actual Excel Desktop/Web open evidence.

---

## Appendix: Related documents

| Document | Scope |
|----------|-------|
| [ACTIVE_ROSTER_LOG_MECHANICS.md](ACTIVE_ROSTER_LOG_MECHANICS.md) | Roster schema, tab families, project resolution |
| [HOURS_BASIS_POLICY.md](HOURS_BASIS_POLICY.md) | Lunch deduction, net vs gross, artifact hours basis |
| [NEURON_TASK_HOUR_DISTRIBUTION_RULES.md](NEURON_TASK_HOUR_DISTRIBUTION_RULES.md) | Task lane distributions, month-specific rules |
| [BILLING_WORK_CONTEXT_RULES.md](BILLING_WORK_CONTEXT_RULES.md) | Work context classification hierarchy |
| [BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md](BILLING_EXECUTIVE_DASHBOARD_CONTENT_RULES.md) | Executive surface rules, core-team lunch policy |
| [ROSTER_BILLING_PIPELINE_INSIGHTS.md](ROSTER_BILLING_PIPELINE_INSIGHTS.md) | Pipeline philosophy, resolution hierarchy, admin output contract |
| [XLSX_STRUCTURE_PRESERVATION_CONTRACT.md](XLSX_STRUCTURE_PRESERVATION_CONTRACT.md) | Mutation classes, structural preservation, validation ladder |
| [WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md](WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md) | Stop-ship tokens, package smells, minimum acceptance ladder |
| [insights/web-excel-compatibility-artifact-lessons-2026-07-01.md](insights/web-excel-compatibility-artifact-lessons-2026-07-01.md) | Compatibility insights, relationship audit, field-judge rule |
| [ARTIFACT_GENERATION_LEDGER.md](ARTIFACT_GENERATION_LEDGER.md) | Generation history, lessons, template row |
| [CF_DICTIONARY_AND_VISUAL_SYSTEM.md](CF_DICTIONARY_AND_VISUAL_SYSTEM.md) | Conditional formatting color system |
| [WORKBOOK_VISUAL_DESIGN_SYSTEM.md](WORKBOOK_VISUAL_DESIGN_SYSTEM.md) | Visual design system for workbook artifacts |
| [HOURS_BASIS_POLICY.md](HOURS_BASIS_POLICY.md) | Hours basis implementation |
| 	riage/hours_basis_policy.py | Lunch deduction, overnight split, core/non-core policy implementation |
| 	riage/neuron_task_hour_distribution_rules.py | Task-hour distribution implementation |
| 	riage/admin_billing_summary/reader.py | Canonical project resolution reader |
| 	riage/roster_parser.py | Low-level roster parsing |
| .ai/workflow-registry.json | Harness workflow registry |
| .ai/HARNESS.md | Harness spine documentation |
