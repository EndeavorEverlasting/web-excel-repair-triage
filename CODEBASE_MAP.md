# Codebase Map

## Repository Structure

```
web-excel-repair-triage/
├── AGENTS.md                    # Agent operating contract
├── README.md                    # Project documentation
├── app.py                       # Main Streamlit application
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── ArtifactIntake/              # Input artifact handling
├── Candidates/                  # Read-only operator inputs (backup/emulator files)
├── configs/                     # Configuration files
├── Deprecated/                  # Deprecated code
├── docs/                        # Documentation and prompt kit
│   ├── prompt-kit.html          # AI Harness Prompt Kit web interface
│   ├── prompt-kit.js            # Prompt Kit JavaScript
│   ├── prompts.json             # Prompt definitions
│   ├── reference.json           # Reference data for prompt kit
│   └── architecture/            # Architecture documentation
│
├── notes/                       # Working notes
├── Outputs/                     # Generated workbooks, sidecars, forensic reports
│   └── backups/                 # Timestamped backups
├── References/                  # Reference materials
├── Repaired/                    # Repaired workbook outputs
├── scripts/                     # Utility scripts
│   ├── admin_context_to_billing.py
│   ├── billing_to_admin_context.py
│   ├── extract_roster_operator_pack.py
│   ├── github-credential-helper.sh
│   ├── post-merge.sh
│   ├── run_april_2026_attendance.py
│   └── verify_pr35_release_proof.py
│
├── tests/                       # Test suite
│   ├── fixtures/                # Test fixtures
│   └── test_*.py                # Test files
│
├── triage/                      # Triage engine modules
├── web/                         # Web interface components
│
├── autofix_loop.py              # Auto-fix loop logic
├── mcp_server.py                # MCP server implementation
├── refactor_spec.json           # Refactoring specification
├── replit.md                    # Replit configuration
└── tracker_tooling.py           # Tracker tooling
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `ArtifactIntake/` | Handles input artifact parsing and validation |
| `Candidates/` | Read-only operator inputs (NEVER write here) |
| `configs/` | Configuration files for various workflows |
| `docs/` | Documentation, prompt kit, architecture docs |
| `Outputs/` | Generated workbooks, sidecars, forensic reports |
| `Outputs/backups/` | Timestamped backups before mutations |
| `References/` | Reference materials and schemas |
| `Repaired/` | Repaired workbook outputs |
| `scripts/` | Utility scripts for billing, roster, verification |
| `tests/` | Test suite with fixtures |
| `triage/` | Core triage engine modules |
| `web/` | Web interface components |

## Entry Points

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application entry point |
| `mcp_server.py` | MCP server for Augment Code integration |
| `autofix_loop.py` | Auto-fix loop for workbook repairs |
| `scripts/*.py` | Utility scripts for specific workflows |

## Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `.gitignore` | Git ignore rules |
| `refactor_spec.json` | Refactoring specification |
| `configs/` | Workflow-specific configurations |

## Build/Test/Deploy Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py

# Run tests
pytest tests/

# Run specific test
pytest tests/test_billing_rules.py

# Run with coverage
pytest tests/ --cov=triage --cov-report=html
```

## Workflow Directions

1. **Roster Log to Admin Sheet** (High Priority)
   - Script: `scripts/roster_to_admin_submission.py`
   - Output: Admin-facing Project Team sheet

2. **Roster Log to Task Tracker** (Medium Priority)
   - Script: `scripts/roster_to_task_context.py`
   - Output: Task tracker context

3. **Task Tracker to Roster Log** (Low Priority)
   - Script: `scripts/task_tracker_to_roster_backfill.py`
   - Output: Proposed roster updates (requires review)

## Safety Rules

- **Candidates/** and **Active/** are read-only operator inputs
- Never write engine output into read-only paths
- All generated workbooks go under **Outputs/**
- Overwrites require timestamped backup under `Outputs/backups/`
- Delivery requires baseline fingerprint compare
