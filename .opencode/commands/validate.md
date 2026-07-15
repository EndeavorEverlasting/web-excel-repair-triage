---
description: Run validators: full suite, or specific test file/gate check
agent: build
---

Run validators against the repository or a specific workbook.

## Usage

- `/validate` — run full CI gate + gitignore hygiene + imports check
- `/validate static` — run static tests only (safe, no Excel dependency)
- `/validate file.xlsx` — run gate checks on a specific workbook
- `/validate tests/test_cf_engine.py` — run specific test file

## Commands

Based on $ARGUMENTS:

### Full suite
```bash
python -m pytest tests/test_cybernet_targets.py tests/test_nw_prj_neuron_track_hours.py tests/test_nw_prj_neuron_track_hours_bonita.py tests/test_admin_billing_summary.py tests/test_one_marcus_recon.py tests/test_one_marcus_generate.py tests/test_one_marcus_immutability.py tests/test_sidecar_html_portal.py tests/test_artifact_compare.py tests/test_roster_log_compare.py tests/test_same_family_compare.py tests/test_gitignore_hygiene.py tests/test_roster_log_review_queue.py -q && python -m triage.gitignore_hygiene && python -c "import triage.cybernet_targets.cli; import triage.nw_prj_neuron_track_hours.cli; import triage.nw_prj_neuron_track_hours.bonita_cli; import triage.admin_billing_summary.cli; import triage.one_marcus_recon.cli; import triage.sidecar_html; import triage.artifact_fingerprint; import triage.artifact_profiles; import triage.artifact_compare; import triage.same_family_compare; import triage.roster_log_compare.compare; import triage.roster_log_review_queue.cli; import triage.gitignore_hygiene; print('imports ok')"
```

### Static only
```bash
python -m pytest tests/test_cf_engine.py tests/test_roster_log_review_queue.py tests/test_patcher.py tests/test_xlsx_utils.py tests/test_dv_engine.py tests/test_roster_parser.py -q
```

### Single file
```bash
python -m pytest $ARGUMENTS -q
```

### Workbook gate checks
```bash
python -c "from triage.gate_checks import run_gate_checks; import json; print(json.dumps(run_gate_checks('$ARGUMENTS'), indent=2))"
```
