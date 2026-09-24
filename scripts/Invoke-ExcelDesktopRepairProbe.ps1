[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Workbook,

    [string]$OutDir = "Outputs/excel_desktop_repair_probe",

    [string]$Python = ""
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "Excel desktop COM probing requires Windows. Use python -m triage.excel_recovery_triage for static/log-only triage."
}

$resolvedWorkbook = (Resolve-Path -LiteralPath $Workbook).Path
$workbookLeaf = [System.IO.Path]::GetFileName($resolvedWorkbook)
$workbookStem = [System.IO.Path]::GetFileNameWithoutExtension($resolvedWorkbook)
$outPath = [System.IO.Path]::GetFullPath($OutDir)
New-Item -ItemType Directory -Force -Path $outPath | Out-Null

$scanRoots = @($env:TEMP, (Split-Path -Parent $resolvedWorkbook)) |
    Where-Object { $_ -and (Test-Path $_) } |
    Select-Object -Unique
$before = @{}
foreach ($root in $scanRoots) {
    Get-ChildItem -LiteralPath $root -Filter "error*.xml" -File -ErrorAction SilentlyContinue | ForEach-Object {
        $before[$_.FullName] = $_.LastWriteTimeUtc
    }
}

$startedUtc = [DateTime]::UtcNow
$excel = $null
$openedWorkbook = $null
$openSucceeded = $false
$openError = ""

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AskToUpdateLinks = $false
    try { $excel.AutomationSecurity = 3 } catch { }

    # UpdateLinks=0, ReadOnly=$true. No save is performed.
    $openedWorkbook = $excel.Workbooks.Open($resolvedWorkbook, 0, $true)
    $openSucceeded = $true
}
catch {
    $openError = $_.Exception.Message
}
finally {
    if ($null -ne $openedWorkbook) {
        try { $openedWorkbook.Close($false) } catch { }
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($openedWorkbook)
    }
    if ($null -ne $excel) {
        try { $excel.Quit() } catch { }
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($excel)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

# Excel recovery logs use shared locations and may arrive after COM returns. Poll
# briefly, but accept only fresh logs whose own text names this workbook.
$deadline = (Get-Date).AddSeconds(5)
$lastSignature = ""
$stablePasses = 0
$attributedLogs = @{}
do {
    $current = @{}
    foreach ($root in $scanRoots) {
        Get-ChildItem -LiteralPath $root -Filter "error*.xml" -File -ErrorAction SilentlyContinue | ForEach-Object {
            $isFresh = -not $before.ContainsKey($_.FullName) -or $_.LastWriteTimeUtc -gt $startedUtc
            if ($isFresh) {
                try {
                    $text = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 -ErrorAction Stop
                }
                catch {
                    $text = $null
                }
                if ($null -ne $text) {
                    $mentionsWorkbook =
                        $text.IndexOf($workbookLeaf, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $text.IndexOf($workbookStem, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
                    if ($mentionsWorkbook) {
                        $current[$_.FullName] = [pscustomobject]@{
                            FullName = $_.FullName
                            Length = $_.Length
                            LastWriteTimeUtc = $_.LastWriteTimeUtc
                        }
                    }
                }
            }
        }
    }

    $signature = (@($current.Values) |
        Sort-Object FullName |
        ForEach-Object { '{0}|{1}|{2:o}' -f $_.FullName, $_.Length, $_.LastWriteTimeUtc }) -join ';'
    if ($signature -and $signature -eq $lastSignature) {
        $stablePasses++
    }
    else {
        $stablePasses = 0
        $lastSignature = $signature
    }
    foreach ($item in $current.Values) { $attributedLogs[$item.FullName] = $item }
    if ($stablePasses -ge 1) { break }
    Start-Sleep -Milliseconds 250
} while ((Get-Date) -lt $deadline)

$newLogs = @()
foreach ($item in @($attributedLogs.Values | Sort-Object FullName)) {
    $source = [string]$item.FullName
    $name = [System.IO.Path]::GetFileName($source)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha256.ComputeHash([Text.Encoding]::UTF8.GetBytes($source))
    }
    finally {
        $sha256.Dispose()
    }
    $sourceId = (([BitConverter]::ToString($hashBytes)) -replace '-', '').Substring(0, 8).ToLowerInvariant()
    $destination = Join-Path $outPath ("{0}-{1}" -f $sourceId, $name)
    Copy-Item -LiteralPath $source -Destination $destination -Force
    $newLogs += $destination
}
$newLogs = @($newLogs | Sort-Object -Unique)

if (-not $Python) {
    $venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
    $Python = if (Test-Path $venvPython) { $venvPython } else { "python" }
}

$jsonOut = Join-Path $outPath "excel_recovery_triage.json"
$markdownOut = Join-Path $outPath "excel_recovery_triage.md"
$arguments = @(
    "-m", "triage.excel_recovery_triage",
    $resolvedWorkbook,
    "--json-out", $jsonOut,
    "--markdown-out", $markdownOut
)
foreach ($log in $newLogs) {
    $arguments += @("--recovery-log", $log)
}

& $Python @arguments
$triageExitCode = $LASTEXITCODE

$probe = [ordered]@{
    generated_at_utc = [DateTime]::UtcNow.ToString("o")
    workbook = $resolvedWorkbook
    workbook_open_succeeded = $openSucceeded
    workbook_open_error = $openError
    recovery_logs = $newLogs
    recovery_log_attribution = "fresh log text must name the target workbook; unrelated shared-directory logs are ignored"
    triage_json = $jsonOut
    triage_markdown = $markdownOut
    triage_exit_code = $triageExitCode
    proof_ceiling = "Automated Excel desktop open attempt plus workbook-attributed recovery logs and read-only OOXML triage. No operator acceptance is implied."
}
$probe | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $outPath "desktop_probe.json") -Encoding UTF8

if (-not $openSucceeded -or $triageExitCode -ne 0) {
    exit 1
}
exit 0
