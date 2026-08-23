Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$LauncherPath = Join-Path $Root 'Open-Latest-PromptKit.cmd'
$AcquireScriptPath = Join-Path $Root 'scripts\Acquire-LatestPromptKit.ps1'
$PortableScriptPath = Join-Path $Root 'scripts\Open-LatestPromptKitPortable.ps1'
$launcher = Get-Content -LiteralPath $LauncherPath -Raw -Encoding UTF8
$acquire = Get-Content -LiteralPath $AcquireScriptPath -Raw -Encoding UTF8
$portable = Get-Content -LiteralPath $PortableScriptPath -Raw -Encoding UTF8

$requiredLauncher = @(
    'set "PREFERRED_REPO="',
    'if exist "%~dp0.git" if exist "%~dp0web\prompt-kit\index.html" set "PREFERRED_REPO=%~dp0"',
    'canonical Desktop\dev\web-excel-repair-triage',
    'Open-LatestPromptKitPortable.ps1',
    '-File "%SCRIPT%" -Destination "%PREFERRED_REPO%"',
    '"%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"'
)
foreach ($marker in $requiredLauncher) {
    if (-not $launcher.Contains($marker)) {
        throw "Open-Latest-PromptKit.cmd is missing deterministic portable path marker: $marker"
    }
}

$requiredAcquire = @(
    '[Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)',
    "Join-Path `$desktop 'dev'",
    "Join-Path `$root `$RepositoryFolderName",
    "no '-latest' sibling clone was created"
)
foreach ($marker in $requiredAcquire) {
    if (-not $acquire.Contains($marker)) {
        throw "Acquisition helper is missing canonical Desktop dev marker: $marker"
    }
}

$requiredPortable = @(
    'http://${StableHost}:$Port/',
    'Update-RepositorySafely -Destination $destinationPath',
    'scripts\serve_prompt_kit_portable.py',
    '--build-only',
    'scripts\validate_prompt_kit_portability.py',
    'Start-PortableServer',
    'PROMPT_KIT_PORTABLE_ARTIFACT=',
    "no '-latest' sibling clone was created"
)
foreach ($marker in $requiredPortable) {
    if (-not $portable.Contains($marker)) {
        throw "Portable quick-open script is missing marker: $marker"
    }
}

$forbiddenScatterMarkers = @(
    '%~dp0dev\web-excel-repair-triage',
    '$RepositoryFolderName-latest',
    '"$RepositoryFolderName-$suffix"',
    "Join-Path `$oneDriveRoot 'Desktop\dev'",
    "Join-Path `$oneDriveRoot 'OG Laptop Backup\Desktop\dev'"
)
foreach ($marker in $forbiddenScatterMarkers) {
    if ($launcher.Contains($marker) -or $acquire.Contains($marker) -or $portable.Contains($marker)) {
        throw "Prompt Kit acquisition still contains a checkout-scattering marker: $marker"
    }
}

if ($launcher.Contains('call "%BOOTSTRAP%" -Quick')) {
    throw 'Quick launcher still uses the old direct-file acquisition entry point.'
}
if ($portable.Contains('Start-Process -FilePath (Join-Path $repositoryRoot ''web\prompt-kit\index.html'')')) {
    throw 'Portable quick-open still opens the unstable file URL directly.'
}

Write-Host 'Prompt Kit stable-origin canonical Desktop dev path: PASS'
