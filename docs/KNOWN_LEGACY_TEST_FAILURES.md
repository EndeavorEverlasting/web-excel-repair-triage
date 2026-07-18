# Known legacy test failures

This file records reproducible failures that remain outside the active artifact-engine merge gate. Do not classify a failure as legacy from an aggregate red check alone; capture the exact workflow run, test family, failing node, and current evidence.

## Artifact engine merge gate

The canonical `Artifact engine tests` workflow is green on the V38 branch. The former aggregate failure was not a valid legacy waiver: it came from malformed OOXML in the sanitized One Marcus fixture. The fixture injected `<externalReference r:id="rIdExt1"/>` without declaring the Office document relationships namespace, so `openpyxl` failed before reconciliation began. The fixture now declares the namespace and a regression loads it before mutation.

The workflow keeps each artifact family in a separately named step so future red checks identify the affected lane directly.

## Outside the artifact-engine merge gate

| Test module | Classification | Reason |
|-------------|----------------|--------|
| `tests/test_billing_regression.py` | `TEST_STACK_UNDOCUMENTED` | Requires `attached_assets/` reference xlsx paths not shipped in repo; layout drift vs current generator |
| `tests/test_invoice_parser.py` | Environment | Needs `python-docx` from `requirements.txt`; passes in CI/venv when installed |

## Artifact engine command families

```powershell
python -m pytest tests/test_cybernet_targets.py -q
python -m pytest tests/test_nw_prj_neuron_track_hours.py -q
python -m pytest tests/test_nw_prj_neuron_track_hours_bonita.py -q
python -m pytest tests/test_admin_billing_summary.py -q
python -m pytest tests/test_one_marcus_recon.py tests/test_one_marcus_recon_rename_contract.py -q
python -m pytest tests/test_one_marcus_generate.py tests/test_one_marcus_immutability.py -q
python -m pytest tests/test_sidecar_html_portal.py tests/test_artifact_compare.py -q
python -m pytest tests/test_roster_log_compare.py tests/test_same_family_compare.py -q
python -m pytest tests/test_gitignore_hygiene.py tests/test_roster_log_review_queue.py -q
```
