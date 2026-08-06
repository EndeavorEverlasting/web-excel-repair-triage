[CmdletBinding()]
param(
    [ValidateSet('harness', 'pre_commit', 'pre_push')]
    [string]$Profile = 'harness',

    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),

    [string]$ExpectedHead = '',

    [string]$RunRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-AtomicJson {
    param(
        [Parameter(Mandatory)]
        [object]$Value,

        [Parameter(Mandatory)]
        [string]$Path
    )

    $temporaryPath = "$Path.tmp"
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $temporaryPath -Encoding UTF8
    Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
}

function Add-RunLog {
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [string]$Message
    )

    $timestamp = [DateTimeOffset]::Now.ToString('o')
    "[$timestamp] $Message" | Add-Content -LiteralPath $Path -Encoding UTF8
}

function Get-SafeStepId {
    param(
        [Parameter(Mandatory)]
        [string]$Value
    )

    $safe = $Value -replace '[^A-Za-z0-9._-]', '-'
    return $safe.Trim('-')
}

function Invoke-CapturedCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [Parameter(Mandatory)]
        [string]$StepId,

        [Parameter(Mandatory)]
        [string]$WorkingDirectory,

        [Parameter(Mandatory)]
        [string]$StepsDirectory,

        [Parameter(Mandatory)]
        [string]$RunLogPath
    )

    $safeStepId = Get-SafeStepId -Value $StepId
    $commandPath = Join-Path $StepsDirectory "$safeStepId.cmd"
    $stdoutPath = Join-Path $StepsDirectory "$safeStepId.stdout.log"
    $stderrPath = Join-Path $StepsDirectory "$safeStepId.stderr.log"

    @(
        '@echo off'
        'setlocal EnableExtensions DisableDelayedExpansion'
        $Command
        'set "HARNESS_STEP_EXIT=%ERRORLEVEL%"'
        'endlocal & call exit /b %HARNESS_STEP_EXIT%'
    ) | Set-Content -LiteralPath $commandPath -Encoding ASCII

    Add-RunLog -Path $RunLogPath -Message "START $StepId :: $Command"
    Write-Host "[harness] START $StepId"
    Write-Host "[harness] command: $Command"
    Write-Host "[harness] stdout: $stdoutPath"
    Write-Host "[harness] stderr: $stderrPath"

    $escapedCommandPath = $commandPath.Replace('"', '""')
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $env:ComSpec
    $startInfo.Arguments = "/d /s /c call `"$escapedCommandPath`""
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $startedAt = [DateTimeOffset]::Now.ToString('o')
    if (-not $process.Start()) {
        throw "Unable to start child command for step '$StepId'."
    }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $finishedAt = [DateTimeOffset]::Now.ToString('o')

    $stdout | Set-Content -LiteralPath $stdoutPath -Encoding UTF8
    $stderr | Set-Content -LiteralPath $stderrPath -Encoding UTF8

    if ($stdout) {
        Write-Host $stdout.TrimEnd()
        Add-Content -LiteralPath $RunLogPath -Value $stdout -Encoding UTF8
    }
    if ($stderr) {
        Write-Warning $stderr.TrimEnd()
        Add-Content -LiteralPath $RunLogPath -Value $stderr -Encoding UTF8
    }

    Add-RunLog -Path $RunLogPath -Message "END $StepId :: exit_code=$($process.ExitCode)"

    return [ordered]@{
        id = $StepId
        command = $Command
        started_at = $startedAt
        finished_at = $finishedAt
        exit_code = [int]$process.ExitCode
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        command_file = $commandPath
    }
}

if (-not $RunRoot) {
    $evidenceBase = if ($env:LOCALAPPDATA) {
        Join-Path $env:LOCALAPPDATA 'EndeavorEverlasting\web-excel-repair-triage\harness-runs'
    }
    else {
        Join-Path ([IO.Path]::GetTempPath()) 'EndeavorEverlasting\web-excel-repair-triage\harness-runs'
    }
    $runId = '{0}-{1}-{2}' -f [DateTimeOffset]::Now.ToString('yyyyMMddTHHmmssfff'), $PID, ([guid]::NewGuid().ToString('N').Substring(0, 8))
    $RunRoot = Join-Path $evidenceBase $runId
}

$resolvedRunRoot = [IO.Path]::GetFullPath($RunRoot)
$stepsDirectory = Join-Path $resolvedRunRoot 'steps'
$runLogPath = Join-Path $resolvedRunRoot 'run.log'
$summaryPath = Join-Path $resolvedRunRoot 'summary.json'
New-Item -ItemType Directory -Path $stepsDirectory -Force | Out-Null
New-Item -ItemType File -Path $runLogPath -Force | Out-Null

$summary = [ordered]@{
    schema_version = 'powershell-command-envelope-result/v1'
    repository_root_requested = $RepositoryRoot
    repository_root = $null
    profile = $Profile
    expected_head = $ExpectedHead
    actual_head = $null
    started_at = [DateTimeOffset]::Now.ToString('o')
    finished_at = $null
    status = 'RUNNING'
    failed_step = $null
    run_root = $resolvedRunRoot
    run_log = $runLogPath
    summary = $summaryPath
    steps = @()
}
Write-AtomicJson -Value $summary -Path $summaryPath
Add-RunLog -Path $runLogPath -Message "RUN START profile=$Profile requested_root=$RepositoryRoot"

try {
    $resolvedRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
    $summary.repository_root = $resolvedRoot
    Write-AtomicJson -Value $summary -Path $summaryPath

    $manifestPath = Join-Path $resolvedRoot 'harness\manifest.v1.json'
    $validatorRegistryPath = Join-Path $resolvedRoot 'harness\validators.v1.json'

    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Repository root gate failed; missing $manifestPath. Evidence: $summaryPath"
    }
    if (-not (Test-Path -LiteralPath $validatorRegistryPath -PathType Leaf)) {
        throw "Repository root gate failed; missing $validatorRegistryPath. Evidence: $summaryPath"
    }

    $headStep = Invoke-CapturedCommand `
        -Command 'git rev-parse HEAD' `
        -StepId '00-git-head' `
        -WorkingDirectory $resolvedRoot `
        -StepsDirectory $stepsDirectory `
        -RunLogPath $runLogPath
    $summary.steps += $headStep
    Write-AtomicJson -Value $summary -Path $summaryPath

    if ($headStep.exit_code -ne 0) {
        $summary.failed_step = $headStep.id
        throw "Git HEAD probe failed with exit code $($headStep.exit_code). Evidence: $summaryPath"
    }

    $headOutput = Get-Content -LiteralPath $headStep.stdout_log -Raw
    $summary.actual_head = $headOutput.Trim()
    Write-AtomicJson -Value $summary -Path $summaryPath

    if ($ExpectedHead -and $summary.actual_head -ne $ExpectedHead) {
        $summary.failed_step = $headStep.id
        throw "Expected HEAD $ExpectedHead but found $($summary.actual_head). Evidence: $summaryPath"
    }

    $registry = Get-Content -LiteralPath $validatorRegistryPath -Raw | ConvertFrom-Json
    $validatorsById = @{}
    foreach ($validator in $registry.validators) {
        $validatorsById[[string]$validator.id] = $validator
    }

    $profileIds = @($registry.profiles.$Profile)
    if ($profileIds.Count -eq 0) {
        throw "Validator profile '$Profile' is empty or missing. Evidence: $summaryPath"
    }

    $index = 1
    foreach ($validatorId in $profileIds) {
        $id = [string]$validatorId
        if (-not $validatorsById.ContainsKey($id)) {
            $summary.failed_step = $id
            throw "Validator profile references unknown ID '$id'. Evidence: $summaryPath"
        }

        $stepId = '{0:D2}-{1}' -f $index, $id
        $step = Invoke-CapturedCommand `
            -Command ([string]$validatorsById[$id].command) `
            -StepId $stepId `
            -WorkingDirectory $resolvedRoot `
            -StepsDirectory $stepsDirectory `
            -RunLogPath $runLogPath
        $summary.steps += $step
        Write-AtomicJson -Value $summary -Path $summaryPath

        if ($step.exit_code -ne 0) {
            $summary.failed_step = $step.id
            throw "Harness validator '$id' failed with exit code $($step.exit_code). Evidence: $summaryPath"
        }
        $index += 1
    }

    $summary.status = 'PASS'
}
catch {
    $summary.status = 'FAIL'
    Add-RunLog -Path $runLogPath -Message "RUN FAIL :: $($_.Exception.Message)"
    throw
}
finally {
    $summary.finished_at = [DateTimeOffset]::Now.ToString('o')
    Write-AtomicJson -Value $summary -Path $summaryPath
    Add-RunLog -Path $runLogPath -Message "RUN END status=$($summary.status) summary=$summaryPath"
    Write-Host "[harness] status: $($summary.status)"
    Write-Host "[harness] durable summary: $summaryPath"
    Write-Host "[harness] durable run log: $runLogPath"
}

[pscustomobject]$summary
