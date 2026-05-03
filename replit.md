# Web-Excel Repair Triage

## Overview
A Streamlit-based diagnostic and repair toolset for `.xlsx` files that trigger repair prompts in Excel for the Web (OneDrive/SharePoint). It allows users to diagnose, diff, and patch workbooks without manual XML serialization, ensuring byte-level accuracy.

## Tech Stack
- **Language**: Python 3.12
- **UI Framework**: Streamlit (served on port 5000)
- **Package Manager**: pip (requirements.txt)
- **Key Libraries**: streamlit, mcp[cli]

## Project Structure
- `app.py` — Main Streamlit web application (entry point)
- `mcp_server.py` — FastMCP server for AI agent tool integration
- `triage/` — Core logic modules (gate_checks, patcher, diff, patterns, report, etc.)
- `Candidates/` — Input .xlsx files to triage
- `Repaired/` — Files repaired by Excel for Web (used for diffing)
- `Active/` — Known-good golden standard workbooks
- `Outputs/` — Generated reports, patch recipes, and fixed .xlsx files
- `Deprecated/` — Archive for old iterations
- `tests/` — Test suite
- `docs/` — Documentation

## Running the App
```
python -m streamlit run app.py
```

## Configuration
- `.streamlit/config.toml` — Streamlit server config (port 5000, host 0.0.0.0, CORS disabled)
- Workflow: "Start application" runs `python -m streamlit run app.py` on port 5000

## Deployment
- Target: autoscale
- Run command: `python -m streamlit run app.py`
