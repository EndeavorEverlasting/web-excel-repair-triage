Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$LauncherPath = Join-Path $Root 'Open-Latest-PromptKit.cmd'
$launcher = Get-Content -LiteralPath $LauncherPath -Raw -Encoding UTF8

$required = @(
    'set "PREFERRED_REPO=%~dp0dev\web-excel-repair-triage"',
    'if exist "%~dp0.git" if exist "%~dp0web\prompt-kit\index.html" set "PREFERRED_REPO=%~dp0"',
    'if exist "%~dp0dev\web-excel-repair-triage\.git" set "PREFERRED_REPO=%~dp0dev\web-excel-repair-triage"',
    'call "%BOOTSTRAP%" -Quick -Destination "%PREFERRED_REPO%"'
)

foreach ($marker in $required) {
    if (-not $launcher.Contains($marker)) {
        throw "Open-Latest-PromptKit.cmd is missing deterministic path marker: $marker"
    }
}

if ($launcher.Contains('call "%BOOTSTRAP%" -Quick`r`n')) {
    throw 'Quick launcher still invokes auto-discovery without an explicit destination.'
}

Write-Host 'Prompt Kit quick-open deterministic launcher path: PASS'
