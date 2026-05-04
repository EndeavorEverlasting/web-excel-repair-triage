# Web-Excel Repair Triage

## Overview
A Streamlit-based diagnostic and repair toolset for `.xlsx` files that trigger repair prompts in Excel for the Web (OneDrive/SharePoint). It allows users to diagnose, diff, and patch workbooks without manual XML serialization, ensuring byte-level accuracy. Also includes a full Billing & Attendance pipeline for generating weekly attendance reports and monthly billing summaries.

## Tech Stack
- **Language**: Python 3.12
- **UI Framework**: Streamlit (served on port 5000)
- **Package Manager**: pip (requirements.txt)
- **Key Libraries**: streamlit, mcp[cli], openpyxl, python-docx

## Project Structure
- `app.py` — Main Streamlit web application (entry point)
- `mcp_server.py` — FastMCP server for AI agent tool integration
- `triage/` — Core logic modules:
  - `gate_checks.py` — 11-gate structural gate battery for OOXML/Web-Excel compatibility
  - `patcher.py` — Byte-safe patch engine
  - `diff.py` — ZIP-level part diff
  - `patterns.py` — Diff pattern detection
  - `report.py` — Patch recipe builder
  - `billing_bridge_validator.py` — Billing workbook gate-check wrapper
  - `billing_workbook_profile.py` — Billing workbook structure profiler
  - `roster_parser.py` — Active Roster Log (.xlsx) parser; extracts clock-in/out + lunch deductions; handles string clock values with appended notes (e.g. "9:28:00 AM/ Bonita")
  - `invoice_parser.py` — Vendor .docx invoice parser (AAA Disposal, NYM Courier, AGL, Cybernet)
  - `attendance_report.py` — Weekly attendance .xlsx report generator
  - `billing_summary_generator.py` — Monthly billing summary .xlsx generator (2-sheet: Billing Summary + Invoice Pivots)
  - `batch_runner.py` — Batch pipeline runner
  - `billing_workbook_profile.py` — Billing profile detector
  - `xlsx_utils.py` — Shared OOXML helpers
- `Candidates/` — Input .xlsx files to triage
- `Repaired/` — Files repaired by Excel for Web (used for diffing)
- `Active/` — Known-good golden standard workbooks
- `Outputs/` — Generated reports, patch recipes, and fixed .xlsx files
- `billing_runs/` — Auto-created; contains YYYY-MM/ subfolders with attendance/, workbook/, validation/, and run_manifest.json
- `Deprecated/` — Archive for old iterations
- `tests/` — Test suite
- `docs/` — Documentation
- `attached_assets/` — Sample files (Roster Log, Billing Summary, invoice .docx files)

## Running the App
```
python -m streamlit run app.py
```

## Configuration
- `.streamlit/config.toml` — Streamlit server config (port 5000, host 0.0.0.0, CORS disabled)
- Workflow: "Start application" runs `python -m streamlit run app.py` on port 5000

## Billing & Attendance Pipeline
### Weekly Attendance Report
- Tab: "💳 Billing & Attendance" → "📅 Weekly Attendance"
- Input: Active Roster Log (.xlsx) with "Live - {Month YYYY}" sheet
- Output: `billing_runs/YYYY-MM/attendance/attendance_week_{date}.xlsx`
- Lunch deduction policy: 0h if <6h gross, 0.5h if 6–<8h, 1h if ≥8h

### Monthly Billing Summary
- Tab: "💳 Billing & Attendance" → "🧾 Monthly Billing"
- Inputs: Roster Log (.xlsx) + vendor invoices (.docx)
- Output: `billing_runs/YYYY-MM/workbook/billing_summary_{YYYY-MM}.xlsx`
- Sheet 1: "Billing Summary - {Mon YYYY}" — Monthly Rollup + Hours by Project
- Sheet 2: "Invoice Pivots - Candidate" — Invoice pivots by month, PO, project, vendor

### Gate Checks
All generated files pass through `billing_bridge_validator.py` before download is offered. Files failing blocking gates are deleted; non-blocking warnings are shown as yellow expanders.

### Manifest
Every run writes `billing_runs/YYYY-MM/run_manifest.json` tracking inputs, outputs, status, and metadata.

## Deployment
- Target: autoscale
- Run command: `python -m streamlit run app.py`
