# Known legacy test failures (outside PR #35 artifact lane)

PR #35 merge gate uses **Artifact engine tests** CI job only. Full `pytest tests/` may fail for reasons unrelated to Bonita / Admin Billing / artifact compare.

## Out of scope — do not block PR #35

| Test module | Classification | Reason |
|-------------|----------------|--------|
| `tests/test_billing_regression.py` | `TEST_STACK_UNDOCUMENTED` | Requires `attached_assets/` reference xlsx paths not shipped in repo; layout drift vs current generator |
| `tests/test_invoice_parser.py` | Environment | Needs `python-docx` from `requirements.txt`; passes in CI/venv when installed |

## Merge gate command

```powershell
python -m pytest `
  tests/test_cybernet_targets.py `
  tests/test_nw_prj_neuron_track_hours.py `
  tests/test_nw_prj_neuron_track_hours_bonita.py `
  tests/test_admin_billing_summary.py `
  tests/test_one_marcus_recon.py `
  tests/test_sidecar_html_portal.py `
  tests/test_artifact_compare.py `
  -q
```
