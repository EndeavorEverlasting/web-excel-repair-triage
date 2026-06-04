# Web-Excel Repair Triage

> **Diagnose, diff, patch, and verify `.xlsx` workbooks that trigger the
> "Fix this workbook?" / WORKBOOK REPAIRED banner in Excel for Web —
> without touching OneDrive manually.**

---

## What Is This?

When you open an `.xlsx` file in Excel for Web (OneDrive / SharePoint), the
browser sometimes shows a green banner:  

> **"We found a problem with some content in 'MyFile.xlsx'. Do you want us to
> try to recover as much as we can?"**

or silently repairs the file and shows **WORKBOOK REPAIRED** in the title bar.  
This means Excel for Web found a structural defect in the OOXML package and
auto-corrected it — often changing the file in ways that break formulas,
conditional formatting, or shared-string references.

**Web-Excel Repair Triage** is a local, browser-based tool that:

| Capability | How |
|-----------|-----|
| 🔍 **Diagnoses** the exact structural defect | 10 gate checks scan the raw ZIP/XML |
| 🔀 **Diffs** your file against Excel's repaired version | SHA-256 per ZIP part + unified XML diff |
| 🧩 **Classifies** the repair into named patterns | 7 known Excel-for-Web repair behaviours |
| 🩹 **Generates** a minimal byte-level patch recipe | JSON recipe — no XML reserialization |
| ⚙️ **Applies** the patch and exports a clean `.xlsx` | Byte-safe patcher, no openpyxl/lxml |
| 🌐 **Verifies** the fix via Microsoft Graph API | Upload → createSession → listWorksheets |
| 🤖 **Exposes all phases as MCP tools** | Augment Code ("auggie") can call them directly |

### Who is it for?

- **Excel power users** who build complex workbooks and need to understand why
  OneDrive keeps repairing them.
- **Developers** who generate `.xlsx` files programmatically and need to
  validate OOXML compliance before deployment.
- **IT / SharePoint admins** who need a repeatable, auditable repair workflow.

### Key design decisions

- **No XML reserialization** — all patches are byte/string-level (`str.replace`,
  slice-and-splice). Zero risk of whitespace or attribute-order drift.
- **Python stdlib only** for the core engine — `zipfile`, `hashlib`, `re`,
  `difflib`, `urllib`. Streamlit is the only UI dependency.
- **Patch recipes are plain JSON** — version-control them, share them, apply
  them in CI pipelines.
- **MCP-first** — every triage phase is also an MCP tool, so Augment Code can
  orchestrate the full pipeline from a chat prompt.

### Candidate Neuron Track Hours

Generate the clean candidate Neuron Track Hours workbook from the roster log:

- Docs: [`docs/CANDIDATE_NEURON_TRACK_HOURS_CONTRACT.md`](docs/CANDIDATE_NEURON_TRACK_HOURS_CONTRACT.md)
- Run: `python -m triage.nw_prj_neuron_track_hours.candidate_cli --roster-log "<roster>.xlsx" --months 2026-04 2026-05 --out-dir Outputs/candidate_neuron_track_hours_2026_06_04 --websafe`
- Output: `Candidate_Neuron Track Hours_April-May_2026_Rezaul_ColorCoded.xlsx`
- Rules: unauthorized `Client Coordination` rows are removed from clean time sheets; only Richard/Rich Perez, Khadejah Harrison, Alejandro Perales, and Geoff Gerber may remain in that assignment type. Rezaul Roman April 2026 Neuron work is split into Inventory Management and Configurations, with visible row/color formatting.

### Billing context exporter (April/May contextualized artifacts)

Generate leadership-safe contextualized billing workbooks, mismatch reports, and a browser dashboard:

- **Rules (canonical):** [`docs/BILLING_WORK_CONTEXT_RULES.md`](docs/BILLING_WORK_CONTEXT_RULES.md)
- **Output quality:** [`docs/CONTEXTUALIZED_BILLING_ARTIFACTS.md`](docs/CONTEXTUALIZED_BILLING_ARTIFACTS.md)
- **CLI / usage:** [`docs/BILLING_CONTEXT_EXPORTER.md`](docs/BILLING_CONTEXT_EXPORTER.md)
- **Sprint carryover:** [`docs/ARTIFACT_SPRINT_CARRYOVER_2026-05-30.md`](docs/ARTIFACT_SPRINT_CARRYOVER_2026-05-30.md)
- **Run:** `python -m triage.billing_context.cli --track-hours ... --april-context ... --out-dir Outputs --html --zip`
- **Real workbook E2E:** [`docs/BILLING_CONTEXT_REAL_WORKBOOK_E2E_RUNBOOK.md`](docs/BILLING_CONTEXT_REAL_WORKBOOK_E2E_RUNBOOK.md)

Related admin posture pipeline: [`docs/2026-05-20-admin-billing-context-pipeline.md`](docs/2026-05-20-admin-billing-context-pipeline.md)

### NW PRJ dashboard v6 (Tech Roster)

Contract, configs, generator, and validators for the NW PRJ Tech Roster Dashboard workflow:

- Docs: `docs/NW_PRJ_DASHBOARD_V6_CONTRACT.md`
- Configs: `configs/nw_prj_dashboard_v6_schema.json`
- Validate: `python -m triage.nw_prj_dashboard_validator <workbook.xlsx>` (via API: `validate_nw_prj_dashboard`)
- Generate: `python -m triage.nw_prj_dashboard_generator --admin-scratch <scratch.xlsx> [--dashboard ...] [--roster ...]`
- Compare: `python -m triage.nw_prj_artifact_compare --admin-scratch <scratch.xlsx> [--dashboard ...]`

### Cybernet target sprint (Wave 3 configuration)

Scope-filtered sprint target workbook from All-Wave upstream + live sprint dashboard:

- Docs: [`docs/CYBERNET_TARGET_SPRINT_CONTRACT.md`](docs/CYBERNET_TARGET_SPRINT_CONTRACT.md)
- Configs: `configs/cybernet_sprint_scope_2026_06.json`, `configs/cybernet_targets_schema.json`
- Run: `python -m triage.cybernet_targets.cli --all-wave "Candidates/configuration targets/ALL WAVE ANESTHESIA MACHINES for Tim 6-1-2026.xlsx" --existing-dashboard "Candidates/configuration targets/Targets_Wave3_Live_Dashboard_WebExcelSafe_2026-05-26.xlsx" --scope configs/cybernet_sprint_scope_2026_06.json --out-dir Outputs --as-of 2026-06-01 --websafe`

### NW PRJ Neuron Track Hours engine

Generate `Neuron_Track_Hours_April_May_2026_WEBSAFE.xlsx` locally from the private roster log:

- Docs: [`docs/NW_PRJ_NEURON_TRACK_HOURS_CONTRACT.md`](docs/NW_PRJ_NEURON_TRACK_HOURS_CONTRACT.md)
- Run: `python -m triage.nw_prj_neuron_track_hours.cli --roster-log "<roster>.xlsx" --out-dir Outputs/nw_prj_neuron_track_hours_2026_06_01 --months 2026-04 2026-05 --websafe --zip`
- Neuron scope uses Worked-Project per-date classification (not default team membership); totals: April 1048.19, May 697.83, total 1746.02, Go Live weekend 2 rows / 22h.

#### Bonita submission workbook (clean two-tab)

Generate the admin-facing Bonita submission workbook from the same package:

- Docs: [`docs/BONITA_NEURON_TRACK_HOURS_CONTRACT.md`](docs/BONITA_NEURON_TRACK_HOURS_CONTRACT.md)
- Run: `python -m triage.nw_prj_neuron_track_hours.bonita_cli --roster-log "<roster>.xlsx" --months 2026-04 2026-05 --out-dir Outputs/neuron_track_hours_2026_06_02 --websafe`
- Output: exactly two tabs (`Apr 26` / `May 26`), two-line headers, one values-only row per Neuron shift; off-project (`/ Bonita`), non-work markers, excluded names and long shifts go to a gitignored review-queue sidecar. `PROJECT NAME` is the `Neuron Deployments → Northwell - Neurons` display alias; `ASSIGNMENT TYPE` defaults to `Neuron Installation`.

### Admin Billing Summary (My Preferred Format)

Generate the monthly admin billing summary in the April "My Preferred Format" (with charts) for any month, with an embedded Neuron Track Hours tracker tab:

- Docs: [`docs/ADMIN_BILLING_SUMMARY_PREFERRED_FORMAT_CONTRACT.md`](docs/ADMIN_BILLING_SUMMARY_PREFERRED_FORMAT_CONTRACT.md) and roster mechanics in [`docs/ACTIVE_ROSTER_LOG_MECHANICS.md`](docs/ACTIVE_ROSTER_LOG_MECHANICS.md)
- Run: `python -m triage.admin_billing_summary.cli --roster-log "<roster>.xlsx" --months 2026-04 2026-05 --out-dir Outputs/admin_billing_summary_2026_06_02 --prior "<April preferred-format copy>.xlsx" --websafe`

### Same-family compare and roster log compare (internal)

- Docs: [`docs/SAME_FAMILY_COMPARE.md`](docs/SAME_FAMILY_COMPARE.md), [`docs/ROSTER_LOG_COMPARE.md`](docs/ROSTER_LOG_COMPARE.md)
- Scan intake: `python -m triage.same_family_compare --intake-root ArtifactIntake/2026-06-03 --scan-only --out-dir artifacts/intake_scan`
- Compare roster candidates: `python -m triage.roster_log_compare.compare --left <older.xlsx> --right <newer.xlsx> --out artifacts/roster_log_comparison.xlsx --json-out artifacts/roster_log_comparison.json`
- Submit delivery artifacts only from `outputs/admin-ready/`
- Optional approved-reference gate: `--reference References/approved/<blessed Client xlsx>` — see [`docs/ARTIFACT_FINGERPRINT_AND_COMPARE.md`](docs/ARTIFACT_FINGERPRINT_AND_COMPARE.md)
- Multi-project, override-aware per-day resolution (Assignments Override > Worked Projects > Assignments main > Live default); net = gross − lunch. Produces Executive/Project/Tech/Tech-by-Project summaries with two native bar charts, internal QA/detail tabs, and an embedded `Mon YY` Neuron Track Hours tracker tab. `--prior` emits a delta report for the refreshed month.

### Artifact acceptance doctrine

Generated workbooks pass through distinct gates. Do not treat one gate as proof of the others.

| Term | Meaning |
|------|---------|
| **Package validity** | Workbook opens; OOXML preflight passes (no calc chain hazards, sharedStrings invariants, etc.). |
| **Semantic correctness** | Required operational surfaces exist — sheet names, headers, formulas, profile checks. |
| **Presentation quality** | Calm styling and hierarchy match design configs without rewriting logic. |
| **Web Excel acceptance** | Opens in Excel for Web without repair banner or silent corruption. |
| **Operator acceptance** | Human validated in the real target environment — **field judge**. |

**Valid** means the workbook opens. **Correct** means the requested operational surface exists and behaves. **Accepted** means the operator validated it in Excel for Web (or the stated target).

Design configs (distinct roles):

| Config | Role |
|--------|------|
| [`configs/spreadsheet_style_v1.json`](configs/spreadsheet_style_v1.json) | Palette and style primitives ([`docs/SPREADSHEET_STYLE_SYSTEM.md`](docs/SPREADSHEET_STYLE_SYSTEM.md)) |
| [`configs/workbook_visual_design_v1.json`](configs/workbook_visual_design_v1.json) | Visual hierarchy and design doctrine ([`docs/WORKBOOK_VISUAL_DESIGN_SYSTEM.md`](docs/WORKBOOK_VISUAL_DESIGN_SYSTEM.md)) |
| [`configs/inventory_visual_aid_chart_v1.json`](configs/inventory_visual_aid_chart_v1.json) | Inventory executive `Visual` field and optional chart doctrine ([`docs/INVENTORY_VISUAL_AID_CHART_SYSTEM.md`](docs/INVENTORY_VISUAL_AID_CHART_SYSTEM.md)) |

Repo hygiene: `python -m triage.gitignore_hygiene` fails if private binaries are tracked outside sanitized fixture paths.

### 1 Marcus inventory recon (part-number relink)

See the existing docs and CLI contracts in the repository for the current 1 Marcus recon workflow.
