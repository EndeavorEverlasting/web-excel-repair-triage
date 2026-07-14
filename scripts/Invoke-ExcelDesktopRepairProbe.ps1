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
$outPath = [System.IO.Path]::GetFullPath($OutDir)
New-Item -ItemType Directory -Force -Path $outPath | Out-Null

$scanRoots = @($env:TEMP, (Split-Path -Parent $resolvedWorkbook)) | Where-Object { $_ -and (Test-Path $_) }
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

Start-Sleep -Milliseconds 750
$newLogs = @()
foreach ($root in $scanRoots) {
    Get-ChildItem -LiteralPath $root -Filter "error*.xml" -File -ErrorAction SilentlyContinue | ForEach-Object {
        $isNew = -not $before.ContainsKey($_.FullName) -or $_.LastWriteTimeUtc -gt $startedUtc
        if ($isNew) {
            $destination = Join-Path $outPath $_.Name
            Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
            $newLogs += $destination
        }
    }
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
    triage_json = $jsonOut
    triage_markdown = $markdownOut
    triage_exit_code = $triageExitCode
    proof_ceiling = "Automated Excel desktop open attempt plus captured recovery logs and read-only OOXML triage. No operator acceptance is implied."
}
$probe | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $outPath "desktop_probe.json") -Encoding UTF8

if (-not $openSucceeded -or $triageExitCode -ne 0) {
    exit 1
}
exit 0
