# Scoped Skills

## Skill: Roster to Admin Submission

**Trigger:** User needs admin-facing Project Team sheet for Friday billing

**Inputs:**
- Roster log file (.xlsx)
- Date range (optional)
- Project filter (optional)

**Outputs:**
- Admin-facing Project Team sheet (.xlsx)
- Validation report

**Procedure:**
1. Validate input roster log format
2. Extract worked-project logic including assignments and overrides
3. Generate clean admin-facing output
4. Validate output meets admin requirements
5. Save to `Outputs/` with timestamp

**Validation:**
- Output contains only admin-facing data
- No internal exception machinery exposed
- No confidence fields exposed
- No private notes exposed

**Example:**
```bash
python scripts/roster_to_admin_submission.py roster.xlsx
```

---

## Skill: Roster to Task Context

**Trigger:** User needs task tracker context for hours

**Inputs:**
- Roster log file (.xlsx)
- Date range (optional)

**Outputs:**
- Task tracker context (.json)
- Validation report

**Procedure:**
1. Validate input roster log format
2. Map staff, date, hours, project assignment, and override logic
3. Preserve contribution evidence
4. Generate task tracker context
5. Save to `Outputs/` with timestamp

**Validation:**
- Staff, date, hours, project assignment mapped
- Override logic preserved
- Contribution evidence preserved

**Example:**
```bash
python scripts/roster_to_task_context.py roster.xlsx
```

---

## Skill: Task Tracker to Roster Backfill

**Trigger:** User needs proposed roster updates from task tracker

**Inputs:**
- Task tracker file (.xlsx or .json)
- Date range (optional)

**Outputs:**
- Proposed roster updates (.json)
- Review report

**Procedure:**
1. Validate input task tracker format
2. Analyze contributions and map to roster fields
3. Generate proposed updates (NOT applied)
4. Generate review report
5. Save to `Outputs/` with timestamp

**Validation:**
- Updates are proposed, not applied
- Rejected updates stay as tracker-only context
- No silent roster mutation

**Example:**
```bash
python scripts/task_tracker_to_roster_backfill.py task_tracker.xlsx
```

---

## Skill: Workbook Forensic Analysis

**Trigger:** User needs to understand why Excel repaired a workbook

**Inputs:**
- Original workbook (.xlsx)
- Repaired workbook (optional, can be generated)

**Outputs:**
- Forensic report (.html)
- Patch recipe (.json)

**Procedure:**
1. Validate input workbook format
2. Analyze ZIP/XML structure
3. Identify structural defects
4. Generate forensic report
5. Generate patch recipe if applicable
6. Save to `Outputs/` with timestamp

**Validation:**
- Report accurately describes defects
- Patch recipe is minimal and byte-safe
- No XML reserialization

**Example:**
```bash
python scripts/generate_forensic.py workbook.xlsx
```

---

## Skill: Workbook Repair

**Trigger:** User needs to repair a workbook that triggers Excel repair

**Inputs:**
- Workbook to repair (.xlsx)
- Patch recipe (optional, can be generated)

**Outputs:**
- Repaired workbook (.xlsx)
- Repair report

**Procedure:**
1. Validate input workbook format
2. Generate or use provided patch recipe
3. Apply patch using byte-safe operations
4. Validate repaired workbook
5. Save to `Repaired/` with timestamp

**Validation:**
- Repaired workbook opens without Excel repair
- No data loss
- Formulas preserved
- Conditional formatting preserved

**Example:**
```bash
python scripts/repair_workbook.py workbook.xlsx
```

---

## Skill: Billing Context Reconciliation

**Trigger:** User needs to reconcile billing context between roster and task tracker

**Inputs:**
- Roster log file (.xlsx)
- Task tracker file (.xlsx)

**Outputs:**
- Reconciliation report (.html)
- Discrepancy list

**Procedure:**
1. Validate both input files
2. Extract hours from both sources
3. Compare and identify discrepancies
4. Generate reconciliation report
5. Save to `Outputs/` with timestamp

**Validation:**
- All hours accounted for
- Discrepancies clearly identified
- Recommendations provided

**Example:**
```bash
python scripts/reconcile_billing.py roster.xlsx task_tracker.xlsx
```
