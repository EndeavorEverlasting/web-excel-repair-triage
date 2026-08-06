Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$LauncherPath = Join-Path $Root 'Open-Latest-PromptKit.cmd'
$PortableScriptPath = Join-Path $Root 'scripts\Open-LatestPromptKitPortable.ps1'
$launcher = Get-Content -LiteralPath $LauncherPath -Raw -Encoding UTF8
$portable = Get-Content -LiteralPath $PortableScriptPath -Raw -Encoding UTF8

$requiredLauncher = @(
    'set "PREFERRED_REPO=%~dp0dev\web-excel-repair-triage"',
    'if exist "%~dp0.git" if exist "%~dp0web\prompt-kit\index.html" set "PREFERRED_REPO=%~dp0"',
    'if exist "%~dp0dev\web-excel-repair-triage\.git" set "PREFERRED_REPO=%~dp0dev\web-excel-repair-triage"',
    'Open-LatestPromptKitPortable.ps1',
    '-File "%SCRIPT%" -Destination "%PREFERRED_REPO%"'
)
foreach ($marker in $requiredLauncher) {
    if (-not $launcher.Contains($marker)) {
        throw "Open-Latest-PromptKit.cmd is missing deterministic portable path marker: $marker"
    }
}

$requiredPortable = @(
    'http://${StableHost}:$Port/',
    'Update-RepositorySafely -Destination $destinationPath',
    'scripts\serve_prompt_kit_portable.py',
    '--build-only',
    'scripts\validate_prompt_kit_portability.py',
    'Start-PortableServer',
    'PROMPT_KIT_PORTABLE_ARTIFACT='
)
foreach ($marker in $requiredPortable) {
    if (-not $portable.Contains($marker)) {
        throw "Portable quick-open script is missing marker: $marker"
    }
}

if ($launcher.Contains('call "%BOOTSTRAP%" -Quick')) {
    throw 'Quick launcher still uses the old direct-file acquisition entry point.'
}
if ($portable.Contains('Start-Process -FilePath (Join-Path $repositoryRoot ''web\prompt-kit\index.html'')')) {
    throw 'Portable quick-open still opens the unstable file URL directly.'
}

Write-Host 'Prompt Kit stable-origin quick-open path: PASS'
