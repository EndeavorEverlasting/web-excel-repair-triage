param(
    [string]$Destination,
    [ValidateRange(1, 65535)][int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryUrl = 'https://github.com/EndeavorEverlasting/web-excel-repair-triage.git'
$DefaultBranch = 'main'
$RepositoryFolderName = 'web-excel-repair-triage'
$RequiredFiles = @(
    'web\prompt-kit\index.html',
    'docs\prompt-kit-favorites-portability.js',
    'harness\contracts\prompt-kit-portability.v1.json',
    'scripts\serve_prompt_kit_portable.py',
    'scripts\validate_prompt_kit_portability.py',
    'Run-PromptKitGenerator.cmd',
    'Build-PromptKitWebsite.cmd',
    'configs\prompt_kit\generators.v1.json',
    'scripts\build_prompt_kit_registry.py'
)
$AcquireScriptUrl = 'https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/scripts/Acquire-LatestPromptKit.ps1'
$StableHost = '127.0.0.1'
$StableUrl = "http://${StableHost}:$Port/"
$HealthUrl = "${StableUrl}healthz"

function Write-OperatorLog {
    param([Parameter(Mandatory)][string]$Message)
    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$timestamp] $Message"
}

function Resolve-AcquisitionScript {
    $local = Join-Path $PSScriptRoot 'Acquire-LatestPromptKit.ps1'
    if (Test-Path -LiteralPath $local -PathType Leaf) {
        return $local
    }

    $cache = Join-Path $env:TEMP 'WebExcelPromptKit\Acquire-LatestPromptKit.ps1'
    $parent = Split-Path -Parent $cache
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Write-OperatorLog 'Downloading the canonical acquisition helper.'
    Invoke-WebRequest -UseBasicParsing -Uri $AcquireScriptUrl -OutFile $cache
    return $cache
}

function Import-AcquisitionFunctions {
    param([Parameter(Mandatory)][string]$ScriptPath)

    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $ScriptPath,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors.Count -gt 0) {
        throw "Acquisition helper has PowerShell syntax errors: $($errors -join '; ')"
    }

    $requiredFunctions = @(
        'Normalize-RepositoryUrl',
        'Invoke-Git',
        'Resolve-PythonCommand',
        'Test-RequiredFiles',
        'Update-RepositorySafely',
        'Add-UniquePath',
        'Get-PromptKitDevRoots',
        'Get-ExistingPromptKitRepositories'
    )
    foreach ($name in $requiredFunctions) {
        $functionAst = $ast.Find(
            {
                param($node)
                $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
                    $node.Name -eq $name
            },
            $true
        )
        if (-not $functionAst) {
            throw "Acquisition helper is missing required function: $name"
        }
        Invoke-Expression $functionAst.Extent.Text
    }
}

function Resolve-RepositoryDestination {
    param([string]$RequestedDestination)

    if (-not [string]::IsNullOrWhiteSpace($RequestedDestination)) {
        return [System.IO.Path]::GetFullPath($RequestedDestination)
    }

    $devRoots = @(Get-PromptKitDevRoots)
    if ($devRoots.Count -lt 1) {
        throw 'Could not resolve a Windows Desktop or development root.'
    }

    $existing = @(Get-ExistingPromptKitRepositories -DevRoots $devRoots)
    if ($existing.Count -gt 0) {
        return $existing[0]
    }

    $preferred = Join-Path $devRoots[0] $RepositoryFolderName
    if (-not (Test-Path -LiteralPath $preferred)) {
        return $preferred
    }

    $counter = 1
    do {
        $suffix = if ($counter -eq 1) { 'latest' } else { "latest-$counter" }
        $candidate = Join-Path $devRoots[0] "$RepositoryFolderName-$suffix"
        $counter++
    } while (Test-Path -LiteralPath $candidate)

    Write-OperatorLog "Default destination is occupied; preserving it and using $candidate"
    return $candidate
}

function Invoke-PythonChecked {
    param(
        [Parameter(Mandatory)][hashtable]$Python,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string[]]$Arguments,
        [string]$FailureLabel = 'Python command'
    )

    $allArguments = @($Python.Prefix) + $Arguments
    $previous = Get-Location
    try {
        Set-Location -LiteralPath $WorkingDirectory
        $output = & $Python.File @allArguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Set-Location -LiteralPath $previous
    }
    $text = ($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
    if ($exitCode -ne 0) {
        throw "$FailureLabel failed with exit code $exitCode.`r`n$text"
    }
    if (-not [string]::IsNullOrWhiteSpace($text)) {
        Write-Host $text
    }
    return $text
}

function Test-PortableServer {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 2
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function ConvertTo-NativeArgument {
    param([Parameter(Mandatory)][string]$Value)
    return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function Start-PortableServer {
    param(
        [Parameter(Mandatory)][hashtable]$Python,
        [Parameter(Mandatory)][string]$RepositoryRoot
    )

    if (Test-PortableServer) {
        Write-OperatorLog "Portable Prompt Kit server is already available at $StableUrl"
        return
    }

    $scriptPath = Join-Path $RepositoryRoot 'scripts\serve_prompt_kit_portable.py'
    $arguments = @($Python.Prefix) + @(
        $scriptPath,
        '--repo-root', $RepositoryRoot,
        '--host', $StableHost,
        '--port', $Port.ToString(),
        '--serve'
    )
    $nativeArguments = ($arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '

    Write-OperatorLog "Starting portable Prompt Kit server at $StableUrl"
    Start-Process `
        -FilePath $Python.File `
        -ArgumentList $nativeArguments `
        -WorkingDirectory $RepositoryRoot `
        -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 300
        if (Test-PortableServer) {
            return
        }
    }
    throw "Portable Prompt Kit server did not become healthy at $HealthUrl"
}

$acquisitionScript = Resolve-AcquisitionScript
Import-AcquisitionFunctions -ScriptPath $acquisitionScript

$destinationPath = Resolve-RepositoryDestination -RequestedDestination $Destination
Write-OperatorLog "Prompt Kit repository: $destinationPath"
$writeLog = { param([string]$Message) Write-OperatorLog $Message }
$repositoryRoot = Update-RepositorySafely -Destination $destinationPath -WriteLog $writeLog
$python = Resolve-PythonCommand

Write-OperatorLog 'Generating the portable Prompt Kit artifact and receipt.'
Invoke-PythonChecked `
    -Python $python `
    -WorkingDirectory $repositoryRoot `
    -Arguments @(
        'scripts\serve_prompt_kit_portable.py',
        '--repo-root', $repositoryRoot,
        '--host', $StableHost,
        '--port', $Port.ToString(),
        '--build-only'
    ) `
    -FailureLabel 'Portable Prompt Kit build' | Out-Null

Write-OperatorLog 'Validating the portable Favorites and harness contract.'
Invoke-PythonChecked `
    -Python $python `
    -WorkingDirectory $repositoryRoot `
    -Arguments @(
        'scripts\validate_prompt_kit_portability.py',
        '--artifact', 'Outputs\prompt-kit-portable\index.html',
        '--manifest', 'Outputs\prompt-kit-portable\manifest.json',
        '--summary'
    ) `
    -FailureLabel 'Prompt Kit portability validation' | Out-Null

Start-PortableServer -Python $python -RepositoryRoot $repositoryRoot
Write-OperatorLog "Opening the stable Prompt Kit origin: $StableUrl"
Start-Process -FilePath $StableUrl

$artifact = Join-Path $repositoryRoot 'Outputs\prompt-kit-portable\index.html'
$manifest = Join-Path $repositoryRoot 'Outputs\prompt-kit-portable\manifest.json'
Write-Host "PROMPT_KIT_PORTABLE_ARTIFACT=$artifact"
Write-Host "PROMPT_KIT_PORTABLE_MANIFEST=$manifest"
Write-Host "PROMPT_KIT_PORTABLE_URL=$StableUrl"
