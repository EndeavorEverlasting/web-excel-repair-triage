# Validation Contracts — 2026-05-27

## Scope

This record replaces the Keen plan’s **bash contract** step (`deployment-audit/tests/*.sh`, `tests/bash/*.sh`). Those paths belong to **SysAdminSuite**, not **web-excel-repair-triage**. This document runs the validation contracts that **actually exist** in this repository.

| Field | Value |
| --- | --- |
| Repository | EndeavorEverlasting/web-excel-repair-triage |
| Baseline | `origin/main` @ `470486a` |
| Audit branch | `docs/post-convergence-validation-2026-05-27` |
| OS | Windows 11 (build 10.0.26200) |
| Python | 3.x (project stdlib + pytest) |

## Contracts Not Present (honest record)

| Planned (Keen/SysAdminSuite) | Status on this repo |
| --- | --- |
| `bash deployment-audit/tests/test_hostname_availability_contracts.sh` | **Missing** — no `deployment-audit/` tree |
| `bash deployment-audit/tests/test_autologon_assessment_contracts.sh` | **Missing** |
| `bash deployment-audit/tests/test_live_serial_probe_contracts.sh` | **Missing** |
| `bash tests/bash/test_registry_install_diff_wrapper_contracts.sh` | **Missing** — no `tests/bash/` |
| `python -m triage.compat_catalog --check` | **Missing** — module not implemented (Cursor rule reference only) |

These are **N/A** for this workspace, not failures to fix in this docs-only PR.

## Contracts Executed

### 1. Python syntax (stdlib parse)

```powershell
python -c "import ast, pathlib
for f in pathlib.Path('.').rglob('*.py'):
    if any(p.name in {'.venv','venv','env','__pycache__'} for p in f.parents): continue
    ast.parse(f.read_text(encoding='utf-8', errors='ignore'))
print('All OK')"
```

| Result | Exit |
| --- | ---: |
| **Pass** — all tracked `.py` modules parse | 0 |

### 2. Core triage / OOXML pytest subset

```powershell
python -m pytest tests/test_patcher.py tests/test_xlsx_utils.py tests/test_storage_policy.py `
  tests/test_repo_engine.py tests/test_billing_bridge_validator.py `
  tests/test_cf_policy_deploymenttracker.py tests/test_promote.py `
  tests/test_roster_parser.py tests/test_attendance_report.py `
  tests/test_admin_billing_context_rules.py -q --tb=no
```

| Result | Exit |
| --- | ---: |
| **Pass** — 117 passed | 0 |

Modules covered: patcher, xlsx utils, storage policy, repo engine, billing bridge validator, CF policy, promote, roster parser, attendance report, admin billing context rules.

### 3. Full pytest suite (regression snapshot)

```powershell
python -m pytest -q --tb=no
```

| Result | Exit |
| --- | ---: |
| **Partial fail** — 199 passed, 5 skipped, 12 failed, 51 errors | 1 |

Failure clusters (consistent with `docs/reviews/BASELINE_TEST_RESULTS_2026-05-04.md`):

| Cluster | Tests affected | Likely cause |
| --- | --- | --- |
| Billing summary generator | `tests/test_billing_summary_generator.py` | Layout/structure assertions vs Agilant reference template |
| Billing regression pivots | `tests/test_billing_regression.py` | Pivot totals / vendor section mismatches |
| Invoice DOCX parser | `tests/test_invoice_parser.py` | `ModuleNotFoundError` / package read errors on `attached_assets/*.docx` fixtures |

**Targeted roster + attendance baseline** (prior sprint gate):

```powershell
python -m pytest tests/test_roster_parser.py tests/test_attendance_report.py -q --tb=no
```

| Result | Exit |
| --- | ---: |
| **Pass** — 75 passed | 0 |

### 4. Gate checks (read-only OOXML contract)

Manual invocation of `triage.gate_checks.run_all` against tracked billing reference workbook in `attached_assets/`:

| Workbook class | `pass_all` | Notes |
| --- | --- | --- |
| Agilant billing summary template | **False** | `calcchain_invalid` findings only; no stop-ship tokens |

Gate check battery (`triage/gate_checks.py`) is the repo’s primary **STOP-SHIP** contract documented in README and `docs/billing_bridge/WEB_EXCEL_VALIDATION.md`.

### 5. Billing Bridge CLI (contract surface)

```powershell
python -m triage.billing_bridge_validator --help
```

| Result | Exit |
| --- | ---: |
| **Pass** — CLI entrypoint present | 0 |

Read-only validator documented in `docs/billing_bridge/WEB_EXCEL_VALIDATION.md`; writes to `billing_runs/` (gitignored).

### 6. Documented contracts not run in this pass

| Contract | Reason skipped |
| --- | --- |
| Microsoft Graph probe | Requires live bearer token — out of scope for docs-only audit |
| Desktop Excel COM probe | Requires Windows Excel + pywin32 — not CI-safe |
| Playwright browser probe | Optional dependency; covered by skipped unit test when absent |
| Batch runner folder sweep | Requires workbook corpus paths; gate subset above suffices |

## Summary Table

| Contract | Verdict |
| --- | --- |
| Python syntax | **Pass** |
| Core triage pytest subset (117) | **Pass** |
| Roster + attendance targeted (75) | **Pass** |
| Full pytest suite | **Partial fail** (billing/invoice clusters) |
| Gate checks on billing template | **Partial** (calcchain warnings, no stop-ship) |
| Billing Bridge CLI | **Pass** |
| SysAdminSuite bash contracts | **N/A** (wrong repository) |
| `compat_catalog --check` | **N/A** (not implemented) |

## Recommended Follow-Up Lanes

| Lane | Branch suggestion | Action |
| --- | --- | --- |
| Billing test stabilization | `fix/billing-pytest-regression-2026-05-27` | Repair invoice DOCX fixture loading and billing summary layout assertions |
| Gate + corpus hygiene | `chore/redact-attached-assets-2026-05-27` | Redact/untrack live `attached_assets/`; re-run gate checks on SAMPLE fixtures |
| Catalog tooling | `feat/compat-catalog-or-drop-ref` | Implement `triage.compat_catalog` or remove stale Cursor rule reference |
| Branch retirement | `chore/delete-retired-branches-2026-05-27` | After doc merges validated, tag and delete absorbed branches (see ledger) |

## Verdict

**Partial pass** — core OOXML/triage contracts and roster/attendance baseline are green; **full-suite billing regressions remain red**. SysAdminSuite bash contracts were correctly **not** faked for this repo.
