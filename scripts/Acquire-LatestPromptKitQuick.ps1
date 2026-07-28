param(
    [switch]$Quick,
    [string]$Destination
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryUrl = 'https://github.com/EndeavorEverlasting/web-excel-repair-triage.git'
$DefaultBranch = 'main'
$RepositoryFolderName = 'web-excel-repair-triage'
$RequiredFiles = @(
    'web\prompt-kit\index.html',
    'Run-PromptKitGenerator.cmd',
    'Build-PromptKitWebsite.cmd',
    'configs\prompt_kit\generators.v1.json',
    'scripts\build_prompt_kit_registry.py'
)

function Normalize-RepositoryUrl {
    param([Parameter(Mandatory)][string]$Url)
    return (($Url.Trim() -replace '\.git$', '') -replace '\\', '/').ToLowerInvariant()
}

function Invoke-NativeCommandSafely {
    param(
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$Arguments
    )

    $previousLocation = Get-Location
    $previousErrorActionPreference = $ErrorActionPreference
    $output = @()
    $exitCode = 0

    try {
        Set-Location -LiteralPath $WorkingDirectory

        # Windows PowerShell 5.1 promotes native stderr records to PowerShell
        # errors. Git writes normal progress such as "Cloning into ..." to
        # stderr even when it exits successfully. Capture both streams while
        # judging success exclusively by the native process exit code.
        $ErrorActionPreference = 'Continue'
        $output = & $FilePath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        Set-Location -LiteralPath $previousLocation
    }

    $text = ($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
    if ($exitCode -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed with exit code $exitCode.`r`n$text"
    }

    return $text.Trim()
}

function Invoke-Git {
    param(
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string[]]$Arguments
    )

    return Invoke-NativeCommandSafely `
        -WorkingDirectory $WorkingDirectory `
        -FilePath 'git' `
        -Arguments $Arguments
}

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ File = 'py'; Prefix = @('-3') }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ File = 'python'; Prefix = @() }
    }
    throw 'Python 3 was not found. Install Python 3 and select Add Python to PATH.'
}

function Resolve-DefaultDestination {
    $localAppData = [Environment]::GetFolderPath(
        [Environment+SpecialFolder]::LocalApplicationData
    )
    if ([string]::IsNullOrWhiteSpace($localAppData)) {
        $localAppData = $env:LOCALAPPDATA
    }
    if ([string]::IsNullOrWhiteSpace($localAppData)) {
        throw 'Could not resolve LOCALAPPDATA for a non-OneDrive checkout.'
    }

    return Join-Path `
        $localAppData `
        "EndeavorEverlasting\Repos\$RepositoryFolderName"
}

function Test-RequiredFiles {
    param([Parameter(Mandatory)][string]$RepositoryRoot)

    foreach ($relativePath in $RequiredFiles) {
        $fullPath = Join-Path $RepositoryRoot $relativePath
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            throw "Required Prompt Kit file is missing: $relativePath"
        }
    }

    $manifestPath = Join-Path $RepositoryRoot 'configs\prompt_kit\generators.v1.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.schema_version -ne 'prompt-kit-generators/v1') {
        throw 'Generator manifest schema is missing or unsupported.'
    }
    if (-not $manifest.generators -or $manifest.generators.Count -lt 1) {
        throw 'Generator manifest contains no registered generators.'
    }

    $python = Resolve-PythonCommand
    $arguments = @($python.Prefix) + @(
        'scripts\build_prompt_kit_registry.py',
        '--output',
        'web\prompt-kit\index.html',
        '--check'
    )
    Invoke-NativeCommandSafely `
        -WorkingDirectory $RepositoryRoot `
        -FilePath $python.File `
        -Arguments $arguments | Out-Null
}

function Update-RepositorySafely {
    param([Parameter(Mandatory)][string]$RequestedDestination)

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git was not found. Install Git for Windows and try again.'
    }

    $destinationPath = [System.IO.Path]::GetFullPath($RequestedDestination)
    $gitPath = Join-Path $destinationPath '.git'

    if (-not (Test-Path -LiteralPath $destinationPath)) {
        $parent = Split-Path -Parent $destinationPath
        if (-not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }

        Write-Host "Cloning canonical main into $destinationPath"
        Invoke-Git -WorkingDirectory $parent -Arguments @(
            'clone',
            '--branch', $DefaultBranch,
            '--single-branch',
            $RepositoryUrl,
            $destinationPath
        ) | Out-Null
    }
    else {
        if (-not (Test-Path -LiteralPath $gitPath -PathType Container)) {
            throw "Destination exists but is not a Git repository: $destinationPath"
        }

        $origin = Invoke-Git -WorkingDirectory $destinationPath -Arguments @(
            'remote', 'get-url', 'origin'
        )
        if ((Normalize-RepositoryUrl $origin) -ne (Normalize-RepositoryUrl $RepositoryUrl)) {
            throw "Existing repository has an unexpected origin: $origin"
        }

        $status = Invoke-Git -WorkingDirectory $destinationPath -Arguments @(
            'status', '--porcelain'
        )
        if (-not [string]::IsNullOrWhiteSpace($status)) {
            throw 'Repository has local modifications or untracked files. Nothing was reset or deleted.'
        }

        $branch = Invoke-Git -WorkingDirectory $destinationPath -Arguments @(
            'branch', '--show-current'
        )
        if ($branch -ne $DefaultBranch) {
            throw "Repository is on branch '$branch', not '$DefaultBranch'. Nothing was switched or overwritten."
        }

        Write-Host 'Fetching latest main.'
        Invoke-Git -WorkingDirectory $destinationPath -Arguments @(
            'fetch', 'origin', $DefaultBranch, '--prune'
        ) | Out-Null

        $counts = Invoke-Git -WorkingDirectory $destinationPath -Arguments @(
            'rev-list', '--left-right', '--count', "HEAD...origin/$DefaultBranch"
        )
        $parts = $counts -split '\s+'
        if ($parts.Count -lt 2) {
            throw "Could not determine branch divergence: $counts"
        }

        $localAhead = [int]$parts[0]
        $remoteAhead = [int]$parts[1]
        if ($localAhead -gt 0) {
            throw "Local main has $localAhead commit(s) not on origin/main. No reset was attempted."
        }

        if ($remoteAhead -gt 0) {
            Write-Host "Fast-forwarding main by $remoteAhead commit(s)."
            Invoke-Git -WorkingDirectory $destinationPath -Arguments @(
                'merge', '--ff-only', "origin/$DefaultBranch"
            ) | Out-Null
        }
        else {
            Write-Host 'Repository is already current.'
        }
    }

    $finalBranch = Invoke-Git -WorkingDirectory $destinationPath -Arguments @(
        'branch', '--show-current'
    )
    if ($finalBranch -ne $DefaultBranch) {
        throw "Acquisition finished on unexpected branch '$finalBranch'."
    }

    Test-RequiredFiles -RepositoryRoot $destinationPath
    return $destinationPath
}

if (-not $Quick) {
    throw 'This entrypoint supports -Quick only. Use Acquire-LatestPromptKit.ps1 for the advanced GUI.'
}

if ([string]::IsNullOrWhiteSpace($Destination)) {
    $Destination = Resolve-DefaultDestination
}

Write-Host 'Locating or safely updating the Prompt Kit checkout.'
$repositoryRoot = Update-RepositorySafely -RequestedDestination $Destination
$site = Join-Path $repositoryRoot 'web\prompt-kit\index.html'
Write-Host "Opening validated Prompt Kit website: $site"
Start-Process -FilePath $site
