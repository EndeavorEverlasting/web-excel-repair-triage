[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'ExcelWindowContext.ps1')

function Assert-True {
    param([bool]$Condition, [Parameter(Mandatory = $true)][string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Equal {
    param($Actual, $Expected, [Parameter(Mandatory = $true)][string]$Message)
    if ([string]$Actual -ne [string]$Expected) {
        throw "$Message Expected '$Expected' but received '$Actual'."
    }
}

function New-TestWindow {
    param(
        [int]$Pid,
        [Int64]$Hwnd,
        [string]$Title,
        [bool]$Visible = $true
    )
    return [pscustomobject][ordered]@{
        pid = $Pid
        hwnd = $Hwnd
        title = $Title
        className = 'XLMAIN'
        visible = $Visible
        enabled = $true
        rect = [pscustomobject]@{ left = 0; top = 0; right = 1000; bottom = 700; width = 1000; height = 700 }
    }
}

function New-TestProcess {
    param(
        [int]$Pid,
        [object[]]$Windows = @(),
        [string]$Started = '2026-07-14T20:00:00Z'
    )
    $main = if ($Windows.Count -gt 0) { $Windows[0] } else { $null }
    return [pscustomobject][ordered]@{
        pid = $Pid
        processName = 'EXCEL'
        executablePath = 'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE'
        startTimeUtc = $Started
        mainWindowHandle = if ($main) { [Int64]$main.hwnd } else { 0 }
        mainWindowTitle = if ($main) { [string]$main.title } else { '' }
        windows = @($Windows)
    }
}

function New-TestSnapshot {
    param([string]$Label, [object[]]$Processes = @())
    return [pscustomobject][ordered]@{
        schema = 'ExcelProcessSnapshot.v1'
        label = $Label
        capturedAtUtc = '2026-07-14T20:00:00Z'
        processes = @($Processes)
    }
}

$launchUtc = [datetime]'2026-07-14T20:00:00Z'

# T1: exact Start-Process PID with the workbook title wins.
$before = New-TestSnapshot -Label 'S1'
$window = New-TestWindow -Pid 200 -Hwnd 20001 -Title 'roster_review_blank.xlsx - Excel'
$after = New-TestSnapshot -Label 'S2' -Processes @((New-TestProcess -Pid 200 -Windows @($window)))
$result = Resolve-ExcelWindowSelection -Before $before -After $after -WorkbookStem 'roster_review_blank' -PreferredProcessId 200 -LaunchRequestedUtc $launchUtc
Assert-True ([bool]$result.allowed) 'T1 expected the exact started Excel process to be selected.'
Assert-Equal $result.winner.pid 200 'T1 selected the wrong PID.'
Assert-Equal $result.winner.selectedWindow.hwnd 20001 'T1 selected the wrong HWND.'

# T2: Excel process reuse is discoverable from an S1/S2 window delta.
$beforeProcess = New-TestProcess -Pid 300 -Windows @()
$before = New-TestSnapshot -Label 'S1' -Processes @($beforeProcess)
$reusedWindow = New-TestWindow -Pid 300 -Hwnd 30001 -Title 'roster_review_blank.xlsx - Excel'
$afterProcess = New-TestProcess -Pid 300 -Windows @($reusedWindow) -Started '2026-07-14T19:30:00Z'
$after = New-TestSnapshot -Label 'S2' -Processes @($afterProcess)
$result = Resolve-ExcelWindowSelection -Before $before -After $after -WorkbookStem 'roster_review_blank' -LaunchRequestedUtc $launchUtc
Assert-True ([bool]$result.allowed) 'T2 expected a changed existing Excel process to be selected.'
Assert-True ([bool]$result.winner.isChangedAfterBaseline) 'T2 did not retain process-reuse evidence.'

# T3: equal candidates fail closed instead of choosing the foreground window.
$w1 = New-TestWindow -Pid 401 -Hwnd 40101 -Title 'roster_review_blank.xlsx - Excel'
$w2 = New-TestWindow -Pid 402 -Hwnd 40201 -Title 'roster_review_blank.xlsx - Excel'
$after = New-TestSnapshot -Label 'S2' -Processes @(
    (New-TestProcess -Pid 401 -Windows @($w1)),
    (New-TestProcess -Pid 402 -Windows @($w2))
)
$result = Resolve-ExcelWindowSelection -Before (New-TestSnapshot -Label 'S1') -After $after -WorkbookStem 'roster_review_blank' -LaunchRequestedUtc $launchUtc
Assert-True (-not [bool]$result.allowed) 'T3 must reject tied Excel candidates.'
Assert-Equal $result.reason 'multiple_tied_candidates' 'T3 returned the wrong blocked reason.'

# T4: an unrelated Excel window cannot win without a session-binding signal.
$unrelated = New-TestWindow -Pid 500 -Hwnd 50001 -Title 'Budget.xlsx - Excel'
$after = New-TestSnapshot -Label 'S2' -Processes @((New-TestProcess -Pid 500 -Windows @($unrelated)))
$result = Resolve-ExcelWindowSelection -Before (New-TestSnapshot -Label 'S1') -After $after -WorkbookStem 'roster_review_blank' -LaunchRequestedUtc $launchUtc
Assert-True (-not [bool]$result.allowed) 'T4 must reject an unrelated Excel window.'
Assert-Equal $result.reason 'no_candidate_above_threshold' 'T4 returned the wrong blocked reason.'

# T5: a stale or missing HWND cannot be selected even when the PID is preferred.
$noWindowProcess = New-TestProcess -Pid 600 -Windows @()
$after = New-TestSnapshot -Label 'S2' -Processes @($noWindowProcess)
$result = Resolve-ExcelWindowSelection -Before (New-TestSnapshot -Label 'S1') -After $after -WorkbookStem 'roster_review_blank' -PreferredProcessId 600 -LaunchRequestedUtc $launchUtc
Assert-True (-not [bool]$result.allowed) 'T5 must reject a process without a live HWND.'

# T6: a repair modal under the frozen PID is retained as exact evidence.
$main = New-TestWindow -Pid 700 -Hwnd 70001 -Title 'roster_review_blank.xlsx - Excel'
$repair = New-TestWindow -Pid 700 -Hwnd 70002 -Title 'Repaired Records'
$after = New-TestSnapshot -Label 'S2' -Processes @((New-TestProcess -Pid 700 -Windows @($main, $repair)))
$result = Resolve-ExcelWindowSelection -Before (New-TestSnapshot -Label 'S1') -After $after -WorkbookStem 'roster_review_blank' -PreferredProcessId 700 -LaunchRequestedUtc $launchUtc
Assert-True ([bool]$result.allowed) 'T6 expected the frozen repair-session PID to be selected.'
Assert-True (@($result.winner.evidenceSignals) -contains 'repair_surface_observed') 'T6 did not retain repair-surface evidence.'

Write-Host 'Excel window context tests: 6 passed'
