# Bash Contract Validation — 2026-05-27

## Runtime

| Field | Value |
| --- | --- |
| OS | Microsoft Windows 11 Home (build 10.0.26200 family) |
| Shell (tests) | Git Bash — `C:\Program Files\Git\bin\bash.exe` |
| PowerShell (orchestration) | 7.6.1 |
| Repo | Web Excel Triage (not EndeavorEverlasting/SysAdminSuite) |
| Branch | `docs/post-convergence-validation-2026-05-27` |
| HEAD | `470486a99c365707e134e8491dc75623ee8674bf` |

## Commands Run

```bash
bash deployment-audit/tests/test_hostname_availability_contracts.sh
bash deployment-audit/tests/test_autologon_assessment_contracts.sh
bash deployment-audit/tests/test_live_serial_probe_contracts.sh
bash tests/bash/test_registry_install_diff_wrapper_contracts.sh
```

## Test Results

| Test script | Exit | Result |
| --- | ---: | --- |
| `deployment-audit/tests/test_hostname_availability_contracts.sh` | 127 | **Not run** — path missing |
| `deployment-audit/tests/test_autologon_assessment_contracts.sh` | 127 | **Not run** — path missing |
| `deployment-audit/tests/test_live_serial_probe_contracts.sh` | 127 | **Not run** — path missing |
| `tests/bash/test_registry_install_diff_wrapper_contracts.sh` | 127 | **Not run** — path missing |

WSL is installed on the host but was **not** used because failure mode is missing scripts in this repository, not Windows bash incompatibility.

## Failure Details

| Script | Exit | Error snippet | Likely cause | Recommended next branch |
| --- | ---: | --- | --- | --- |
| All four planned scripts | 127 | `No such file or directory` | Convergence bash contract suite lives in **SysAdminSuite**; this repo is **Web Excel Triage** and has no `deployment-audit/` or `tests/bash/` contract harness. | Run the same four commands from SysAdminSuite `main`, **or** add `fix/post-convergence-bash-contracts-2026-05-27` in the repo that owns those paths. |

## Verdict

**Fail** (for this workspace) — contracts were not executable here. Record is honest: validation plan step cannot pass until executed against the repository that contains the bash contract tests.
