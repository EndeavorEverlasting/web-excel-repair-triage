[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TargetPath,
    [ValidateRange(0, 10080)]
    [int]$MinimumAgeMinutes = 60,
    [switch]$Apply,
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SchemaVersion = 'prompt-kit-browser-proof-cleanup-report/v1'
$LeafPattern = '^prompt-kit-browser-proof-[0-9a-fA-F]{16,64}$'
$RequiredMarkerRelative = 'web\prompt-kit\index.html'
$PathTrimChars = [char[]]'\/'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutputsRoot = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot 'Outputs')).TrimEnd($PathTrimChars)
$SystemTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd($PathTrimChars)

if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $ReportPath = Join-Path $OutputsRoot 'prompt-kit-browser-proof-cleanup-report.json'
}
$ResolvedReportPath = [System.IO.Path]::GetFullPath($ReportPath)
$ReportParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $ResolvedReportPath)).TrimEnd($PathTrimChars)
if ($ReportParent -ne $OutputsRoot -and -not $ReportParent.StartsWith($OutputsRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "ReportPath must stay under repository Outputs/: $ResolvedReportPath"
}

function New-CandidateRecord {
    param([string]$Path)

    $record = [ordered]@{
        path = $Path
        eligible = $false
        action = 'preserved'
        reason = $null
        age_minutes = $null
        marker = $null
    }

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        $record.reason = 'not_found'
        return [pscustomobject]$record
    }

    $item = Get-Item -LiteralPath $Path -Force
    $full = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd($PathTrimChars)
    $parent = [System.IO.Path]::GetFullPath($item.Parent.FullName).TrimEnd($PathTrimChars)
    $leaf = $item.Name

    if (-not $parent.Equals($SystemTemp, [System.StringComparison]::OrdinalIgnoreCase)) {
        $record.reason = 'outside_system_temp_root'
        return [pscustomobject]$record
    }
    if ($leaf -notmatch $LeafPattern) {
        $record.reason = 'unexpected_directory_name'
        return [pscustomobject]$record
    }
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        $record.reason = 'reparse_point_rejected'
        return [pscustomobject]$record
    }

    $marker = Join-Path $full $RequiredMarkerRelative
    $record.marker = $marker
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        $record.reason = 'required_prompt_kit_marker_missing'
        return [pscustomobject]$record
    }

    $age = [Math]::Floor(((Get-Date).ToUniversalTime() - $item.LastWriteTimeUtc).TotalMinutes)
    $record.age_minutes = [int]$age
    if ($age -lt $MinimumAgeMinutes) {
        $record.reason = 'younger_than_minimum_age'
        return [pscustomobject]$record
    }

    $record.eligible = $true
    $record.reason = 'eligible_browser_proof_scratch'
    return [pscustomobject]$record
}

$candidatePaths = @()
if (-not [string]::IsNullOrWhiteSpace($TargetPath)) {
    $candidatePaths = @([System.IO.Path]::GetFullPath($TargetPath))
} elseif (Test-Path -LiteralPath $SystemTemp -PathType Container) {
    $candidatePaths = @(
        Get-ChildItem -LiteralPath $SystemTemp -Directory -Force -ErrorAction Stop |
        Where-Object { $_.Name -match $LeafPattern } |
        ForEach-Object { $_.FullName } |
        Sort-Object
    )
}

$records = New-Object System.Collections.Generic.List[object]
foreach ($path in $candidatePaths) {
    $record = New-CandidateRecord -Path $path
    if ($Apply -and $record.eligible) {
        try {
            if ($PSCmdlet.ShouldProcess($record.path, 'Remove Prompt Kit browser-proof scratch directory')) {
                Remove-Item -LiteralPath $record.path -Recurse -Force -ErrorAction Stop
                if (Test-Path -LiteralPath $record.path) {
                    throw 'Path still exists after Remove-Item'
                }
                $record.action = 'deleted'
                $record.reason = 'deleted'
            } else {
                $record.action = 'preserved'
                $record.reason = 'should_process_declined'
            }
        } catch {
            $record.action = 'failed'
            $record.reason = 'delete_failed: ' + $_.Exception.Message
        }
    }
    $records.Add($record) | Out-Null
}

$eligibleCount = @($records | Where-Object { $_.eligible }).Count
$deletedCount = @($records | Where-Object { $_.action -eq 'deleted' }).Count
$failedCount = @($records | Where-Object { $_.action -eq 'failed' }).Count
$preservedCount = @($records | Where-Object { $_.action -eq 'preserved' }).Count

$report = [ordered]@{
    schema_version = $SchemaVersion
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    mode = if ($Apply) { 'apply' } else { 'preview' }
    system_temp_root = $SystemTemp
    target_path = if ([string]::IsNullOrWhiteSpace($TargetPath)) { $null } else { [System.IO.Path]::GetFullPath($TargetPath) }
    minimum_age_minutes = $MinimumAgeMinutes
    candidate_count = $records.Count
    eligible_count = $eligibleCount
    preserved_count = $preservedCount
    deleted_count = $deletedCount
    failed_count = $failedCount
    candidates = $records.ToArray()
    exclusions = @(
        'canonical repository checkouts',
        'GitHub Pages',
        'portable loopback runtime state',
        'browser profile data',
        'browser localStorage and Prompt Kit Favorites',
        'repository Outputs evidence'
    )
    proof_ceiling = 'filesystem classification and cleanup receipt only; browser profile/localStorage/Favorites state is not modified or proven'
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ResolvedReportPath) | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ResolvedReportPath -Encoding UTF8

Write-Host ("Prompt Kit browser-proof cleanup: mode={0} candidates={1} eligible={2} deleted={3} preserved={4} failed={5}" -f $report.mode, $report.candidate_count, $report.eligible_count, $report.deleted_count, $report.preserved_count, $report.failed_count)
Write-Host "Report: $ResolvedReportPath"

if ($failedCount -gt 0) {
    throw "One or more browser-proof scratch directories could not be deleted. See report: $ResolvedReportPath"
}
