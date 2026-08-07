param(
    [Parameter(Mandatory)][string]$Branch,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{40}$')][string]$Commit,
    [string]$RepositoryFullName = 'EndeavorEverlasting/web-excel-repair-triage'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    $previous = Get-Location
    try {
        if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
            Set-Location -LiteralPath $WorkingDirectory
        }
        & $FilePath @ArgumentList
        $code = $LASTEXITCODE
    }
    finally {
        Set-Location -LiteralPath $previous
    }

    if ($code -ne 0) {
        throw "$FilePath $($ArgumentList -join ' ') failed with exit code $code."
    }
}

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    $previous = Get-Location
    try {
        if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
            Set-Location -LiteralPath $WorkingDirectory
        }
        $output = & $FilePath @ArgumentList 2>&1
        $code = $LASTEXITCODE
    }
    finally {
        Set-Location -LiteralPath $previous
    }

    if ($code -ne 0) {
        throw "$FilePath $($ArgumentList -join ' ') failed with exit code $code.`r`n$($output -join [Environment]::NewLine)"
    }
    return (($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine).Trim()
}

function Resolve-Python {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        return @{ File = 'py.exe'; Prefix = @('-3') }
    }
    if (Get-Command python.exe -ErrorAction SilentlyContinue) {
        return @{ File = 'python.exe'; Prefix = @() }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ File = 'python'; Prefix = @() }
    }
    throw 'Python 3 was not found.'
}

if (-not (Get-Command git.exe -ErrorAction SilentlyContinue) -and -not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git was not found.'
}
$Git = if (Get-Command git.exe -ErrorAction SilentlyContinue) { 'git.exe' } else { 'git' }
$Python = Resolve-Python

$ProofBase = if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    Join-Path $env:LOCALAPPDATA 'WebExcelTriage\HarnessProof'
}
elseif (-not [string]::IsNullOrWhiteSpace($env:TEMP)) {
    Join-Path $env:TEMP 'WebExcelTriage-HarnessProof'
}
else {
    throw 'Neither LOCALAPPDATA nor TEMP is available for an isolated proof checkout.'
}

New-Item -ItemType Directory -Force -Path $ProofBase | Out-Null
$Checkout = Join-Path $ProofBase ("web-excel-repair-triage-" + $Commit.Substring(0, 12))
$RepositoryUrl = 'https:' + '//' + 'github.com/' + $RepositoryFullName + '.git'

if (-not (Test-Path -LiteralPath $Checkout)) {
    Invoke-NativeChecked -FilePath $Git -ArgumentList @(
        'clone', '--no-checkout', $RepositoryUrl, $Checkout
    ) -WorkingDirectory $ProofBase
}
else {
    if (-not (Test-Path -LiteralPath (Join-Path $Checkout '.git'))) {
        throw "Preserving unexpected existing path; it is not a Git checkout: $Checkout"
    }
    $status = Invoke-NativeCapture -FilePath $Git -ArgumentList @(
        '-C', $Checkout, 'status', '--porcelain'
    )
    if (-not [string]::IsNullOrWhiteSpace($status)) {
        throw "Preserving dirty proof checkout instead of resetting or cleaning it: $Checkout"
    }
}

$origin = Invoke-NativeCapture -FilePath $Git -ArgumentList @(
    '-C', $Checkout, 'remote', 'get-url', 'origin'
)
$normalizedOrigin = (($origin -replace '\.git$', '') -replace '\\', '/').ToLowerInvariant()
$normalizedExpected = (('https:' + '//' + 'github.com/' + $RepositoryFullName) -replace '\.git$', '').ToLowerInvariant()
if ($normalizedOrigin -ne $normalizedExpected) {
    throw "Unexpected origin in proof checkout: $origin"
}

Invoke-NativeChecked -FilePath $Git -ArgumentList @(
    '-C', $Checkout, 'fetch', 'origin', $Branch, '--prune'
)

$remoteHead = Invoke-NativeCapture -FilePath $Git -ArgumentList @(
    '-C', $Checkout, 'rev-parse', 'FETCH_HEAD'
)
if ($remoteHead -ne $Commit) {
    throw "Remote branch moved. Expected $Commit but fetched $remoteHead."
}

Invoke-NativeChecked -FilePath $Git -ArgumentList @(
    '-C', $Checkout, 'checkout', '--detach', $Commit
)

$actualHead = Invoke-NativeCapture -FilePath $Git -ArgumentList @(
    '-C', $Checkout, 'rev-parse', 'HEAD'
)
if ($actualHead -ne $Commit) {
    throw "Detached checkout mismatch. Expected $Commit but found $actualHead."
}

$PythonPrefix = @($Python.Prefix)
Invoke-NativeChecked -FilePath $Python.File -ArgumentList (
    $PythonPrefix + @(
        'scripts\validate_operator_command_envelope.py',
        '--summary'
    )
) -WorkingDirectory $Checkout

Invoke-NativeChecked -FilePath $Python.File -ArgumentList (
    $PythonPrefix + @(
        'scripts\validate_harness.py',
        '--report',
        'Outputs\harness-completeness-report.json'
    )
) -WorkingDirectory $Checkout

Invoke-NativeChecked -FilePath $Python.File -ArgumentList (
    $PythonPrefix + @(
        '-m', 'unittest',
        'tests.test_operator_command_envelope',
        'tests.test_harness_contract',
        '-v'
    )
) -WorkingDirectory $Checkout

Invoke-NativeChecked -FilePath $Git -ArgumentList @(
    '-C', $Checkout, 'diff', '--check', 'origin/main...HEAD'
)

$artifactRegistryPath = Join-Path $Checkout 'harness\artifacts.v1.json'
$artifactRegistry = Get-Content -LiteralPath $artifactRegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$artifact = @($artifactRegistry.artifacts | Where-Object { $_.id -eq 'harness-completeness-report' })
if ($artifact.Count -ne 1) {
    throw 'Artifact registry must resolve exactly one harness-completeness-report.'
}
$artifactRelative = [string]$artifact[0].canonical_path
$artifactPath = Join-Path $Checkout ($artifactRelative -replace '/', '\')
if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) {
    throw "Validated harness artifact is missing: $artifactPath"
}

Write-Host "VERIFIED_REPOSITORY=$Checkout"
Write-Host "VERIFIED_BRANCH=$Branch"
Write-Host "VERIFIED_HEAD=$Commit"
Write-Host "HARNESS_ARTIFACT=$artifactPath"
Get-Content -LiteralPath $artifactPath -Raw -Encoding UTF8
