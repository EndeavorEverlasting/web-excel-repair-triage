# PowerShell wrapper for the Web Excel Triage Local AI Harness.
# Usage: .\scripts\harness.ps1 <command> [args...]

param(
    [string]$Command = "doctor",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PythonCmd = $VenvPython
} else {
    $PythonCmd = "python"
}

# Run the python harness CLI
if ($RemainingArgs) {
    & $PythonCmd -m triage.harness.cli $Command $RemainingArgs
} else {
    & $PythonCmd -m triage.harness.cli $Command
}

exit $LASTEXITCODE
