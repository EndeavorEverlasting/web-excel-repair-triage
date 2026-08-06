# PowerShell Command Safety

## Incident class

An operator-facing PowerShell command must not call `exit`, terminate the caller's host, or lose the only copy of failure output. A command that closes the terminal before evidence is persisted is a harness failure even when its underlying child process correctly returns nonzero.

## Canonical runner

Use:

```powershell
& .\scripts\Invoke-HarnessProfile.ps1 -Profile harness -ExpectedHead '<commit-sha>'
```

The invocation returns to the caller. It does not call `exit`, `Stop-Process`, `[Environment]::Exit()`, reset or clean Git state, or install missing dependencies.

## Durable evidence

Each run creates a unique machine-local directory under:

```text
%LOCALAPPDATA%\EndeavorEverlasting\web-excel-repair-triage\harness-runs\<run-id>\
```

When `LOCALAPPDATA` is unavailable, the runner uses the operating-system temporary directory. The run contains:

- `summary.json` — machine-readable status, exact repository root, profile, expected and actual HEAD, failed step, timestamps, and every child exit code;
- `run.log` — durable combined run chronology and captured output;
- `steps/<step-id>.stdout.log` — complete standard output for one command;
- `steps/<step-id>.stderr.log` — complete standard error for one command;
- `steps/<step-id>.cmd` — exact registry command executed in the child process.

`summary.json` is written before the first child command, updated after every command, and finalized in `finally` on success or failure.

## Failure behavior

The runner executes registered commands in child `cmd.exe` processes. A child may exit nonzero without terminating the operator's PowerShell host. After stdout, stderr, step metadata, the combined run log, and final summary are persisted, the runner throws an exception that returns control to the caller and leaves the evidence paths visible.

Missing Node.js, Python, Git, network, credentials, or another dependency is therefore diagnosable from the retained logs. The runner does not attempt surprise installation or environment mutation.

## Validation

```text
python -m unittest tests.test_powershell_command_envelope -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
```

The contract tests reject standalone `exit`, `[Environment]::Exit()`, `Stop-Process`, process killing, automatic package installation, destructive Git cleanup, missing per-step stdout/stderr, missing summary finalization, missing expected-HEAD gating, and missing hook/registry integration.

## Proof ceiling

Static tests prove the tracked runner and contract markers. Native execution on a Windows workstation proves only the exercised PowerShell command envelope and captured child-process behavior. It does not prove Prompt Kit browser behavior, workbook behavior, provider behavior, deployment, or production success.
