Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:ExcelWindowSelectionThreshold = 50

function Test-ExcelWindowsHost {
    return ($env:OS -eq 'Windows_NT')
}

function Initialize-ExcelWindowNative {
    if (-not (Test-ExcelWindowsHost)) { return }
    if ('ExcelWindowNative' -as [type]) { return }

    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class ExcelWindowNative
{
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }

    public class WindowInfo
    {
        public long Hwnd;
        public int ProcessId;
        public string Title;
        public string ClassName;
        public bool Visible;
        public bool Enabled;
        public RECT Rect;
    }

    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] private static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int maxCount);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassName(IntPtr hWnd, StringBuilder text, int maxCount);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool IsWindowEnabled(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);

    private static string ReadText(IntPtr hWnd)
    {
        int length = GetWindowTextLength(hWnd);
        var sb = new StringBuilder(Math.Max(512, length + 2));
        GetWindowText(hWnd, sb, sb.Capacity);
        return sb.ToString();
    }

    private static string ReadClass(IntPtr hWnd)
    {
        var sb = new StringBuilder(512);
        GetClassName(hWnd, sb, sb.Capacity);
        return sb.ToString();
    }

    public static List<WindowInfo> Enumerate()
    {
        var result = new List<WindowInfo>();
        EnumWindows((hWnd, lParam) =>
        {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            RECT rect;
            GetWindowRect(hWnd, out rect);
            result.Add(new WindowInfo {
                Hwnd = hWnd.ToInt64(),
                ProcessId = (int)pid,
                Title = ReadText(hWnd),
                ClassName = ReadClass(hWnd),
                Visible = IsWindowVisible(hWnd),
                Enabled = IsWindowEnabled(hWnd),
                Rect = rect
            });
            return true;
        }, IntPtr.Zero);
        return result;
    }
}
'@ -ErrorAction Stop
}

function Get-ExcelWindowRecords {
    param([int]$ProcessId = 0)

    if (-not (Test-ExcelWindowsHost)) { return @() }
    Initialize-ExcelWindowNative

    $records = New-Object System.Collections.Generic.List[object]
    foreach ($window in @([ExcelWindowNative]::Enumerate())) {
        if ($ProcessId -gt 0 -and [int]$window.ProcessId -ne $ProcessId) { continue }
        try {
            $process = Get-Process -Id ([int]$window.ProcessId) -ErrorAction Stop
        }
        catch { continue }
        if ([string]$process.ProcessName -notmatch '^EXCEL$') { continue }
        if (-not [bool]$window.Visible -and [string]::IsNullOrWhiteSpace([string]$window.Title)) { continue }

        $records.Add([pscustomobject][ordered]@{
            pid = [int]$window.ProcessId
            hwnd = [Int64]$window.Hwnd
            title = [string]$window.Title
            className = [string]$window.ClassName
            visible = [bool]$window.Visible
            enabled = [bool]$window.Enabled
            rect = [pscustomobject][ordered]@{
                left = [int]$window.Rect.Left
                top = [int]$window.Rect.Top
                right = [int]$window.Rect.Right
                bottom = [int]$window.Rect.Bottom
                width = [int]$window.Rect.Right - [int]$window.Rect.Left
                height = [int]$window.Rect.Bottom - [int]$window.Rect.Top
            }
        }) | Out-Null
    }
    return @($records.ToArray())
}

function Get-ExcelProcessSnapshot {
    param([string]$Label = '')

    $windowRecords = @(Get-ExcelWindowRecords)
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($process in @(Get-Process -Name EXCEL -ErrorAction SilentlyContinue)) {
        try { $process.Refresh() } catch { }
        $startTimeUtc = $null
        $path = $null
        try { $startTimeUtc = $process.StartTime.ToUniversalTime().ToString('o') } catch { }
        try { $path = [string]$process.Path } catch { }
        $pidWindows = @($windowRecords | Where-Object { [int]$_.pid -eq [int]$process.Id })
        $records.Add([pscustomobject][ordered]@{
            pid = [int]$process.Id
            processName = [string]$process.ProcessName
            executablePath = $path
            startTimeUtc = $startTimeUtc
            mainWindowHandle = [Int64]$process.MainWindowHandle
            mainWindowTitle = [string]$process.MainWindowTitle
            windows = $pidWindows
        }) | Out-Null
    }

    return [pscustomobject][ordered]@{
        schema = 'ExcelProcessSnapshot.v1'
        label = $Label
        capturedAtUtc = [DateTime]::UtcNow.ToString('o')
        processes = @($records.ToArray())
    }
}

function Get-ExcelProcessFingerprint {
    param([Parameter(Mandatory = $true)]$ProcessRecord)
    $windows = @($ProcessRecord.windows | ForEach-Object {
        '{0}|{1}|{2}|{3}' -f [Int64]$_.hwnd, [string]$_.title, [string]$_.className, [bool]$_.visible
    } | Sort-Object)
    return ('{0}|{1}|{2}' -f [Int64]$ProcessRecord.mainWindowHandle, [string]$ProcessRecord.mainWindowTitle, ($windows -join ';'))
}

function Compare-ExcelProcessSnapshots {
    param(
        [Parameter(Mandatory = $true)]$Before,
        [Parameter(Mandatory = $true)]$After
    )

    $beforeByPid = @{}
    foreach ($record in @($Before.processes)) { $beforeByPid[[int]$record.pid] = $record }
    $new = New-Object System.Collections.Generic.List[object]
    $changed = New-Object System.Collections.Generic.List[object]

    foreach ($record in @($After.processes)) {
        $pid = [int]$record.pid
        if (-not $beforeByPid.ContainsKey($pid)) {
            $new.Add($record) | Out-Null
            continue
        }
        $beforeRecord = $beforeByPid[$pid]
        if ((Get-ExcelProcessFingerprint -ProcessRecord $beforeRecord) -ne (Get-ExcelProcessFingerprint -ProcessRecord $record)) {
            $changed.Add([pscustomobject][ordered]@{ pid = $pid; before = $beforeRecord; after = $record }) | Out-Null
        }
    }

    return [pscustomobject][ordered]@{
        schema = 'ExcelProcessDelta.v1'
        beforeLabel = [string]$Before.label
        afterLabel = [string]$After.label
        newProcesses = @($new.ToArray())
        changedProcesses = @($changed.ToArray())
    }
}

function Get-ExcelWindowCandidateScore {
    param(
        [Parameter(Mandatory = $true)]$ProcessRecord,
        [Parameter(Mandatory = $true)]$Delta,
        [string]$WorkbookStem = '',
        [int]$PreferredProcessId = 0,
        [Nullable[datetime]]$LaunchRequestedUtc = $null
    )

    $signals = New-Object System.Collections.Generic.List[string]
    $missing = New-Object System.Collections.Generic.List[string]
    $score = 0
    $pid = [int]$ProcessRecord.pid
    $isNew = @($Delta.newProcesses | Where-Object { [int]$_.pid -eq $pid }).Count -gt 0
    $isChanged = @($Delta.changedProcesses | Where-Object { [int]$_.pid -eq $pid }).Count -gt 0

    if ($PreferredProcessId -gt 0 -and $pid -eq $PreferredProcessId) { $score += 45; $signals.Add('preferred_start_process') | Out-Null }
    if ($isNew) { $score += 30; $signals.Add('new_pid_after_baseline') | Out-Null }
    elseif ($isChanged) { $score += 20; $signals.Add('existing_pid_window_changed') | Out-Null }
    else { $missing.Add('not_new_or_changed') | Out-Null }

    $visibleWindows = @($ProcessRecord.windows | Where-Object { [bool]$_.visible -and [Int64]$_.hwnd -ne 0 })
    if ($visibleWindows.Count -gt 0) { $score += 15; $signals.Add('visible_excel_window') | Out-Null }
    else { $missing.Add('no_visible_excel_window') | Out-Null }

    $allTitles = @($ProcessRecord.mainWindowTitle) + @($ProcessRecord.windows | ForEach-Object { [string]$_.title })
    if (-not [string]::IsNullOrWhiteSpace($WorkbookStem) -and @($allTitles | Where-Object { [string]$_ -like "*$WorkbookStem*" }).Count -gt 0) {
        $score += 20; $signals.Add('workbook_title_match') | Out-Null
    }
    if (@($allTitles | Where-Object { [string]$_ -match '(?i)repaired|repair|recover|problem with some content' }).Count -gt 0) {
        $score += 15; $signals.Add('repair_surface_observed') | Out-Null
    }

    if ($LaunchRequestedUtc -and $ProcessRecord.startTimeUtc) {
        try {
            $started = [datetime]::Parse([string]$ProcessRecord.startTimeUtc, $null, [Globalization.DateTimeStyles]::RoundtripKind)
            if ($started.ToUniversalTime() -ge $LaunchRequestedUtc.Value.ToUniversalTime().AddSeconds(-5)) {
                $score += 10; $signals.Add('started_after_launch_request') | Out-Null
            }
        } catch { }
    }

    if ([string]$ProcessRecord.executablePath -match '(?i)\\EXCEL\.EXE$') { $score += 5; $signals.Add('excel_executable_path') | Out-Null }

    $rankedWindows = @($ProcessRecord.windows | ForEach-Object {
        $windowScore = 0
        if ([bool]$_.visible) { $windowScore += 20 }
        if ([Int64]$_.hwnd -ne 0) { $windowScore += 10 }
        if (-not [string]::IsNullOrWhiteSpace($WorkbookStem) -and [string]$_.title -like "*$WorkbookStem*") { $windowScore += 30 }
        if ([string]$_.title -match '(?i)repaired|repair|recover|problem with some content') { $windowScore += 25 }
        [pscustomobject][ordered]@{
            pid = $pid
            hwnd = [Int64]$_.hwnd
            title = [string]$_.title
            className = [string]$_.className
            visible = [bool]$_.visible
            enabled = [bool]$_.enabled
            score = $windowScore
        }
    } | Sort-Object score -Descending, hwnd)

    return [pscustomobject][ordered]@{
        pid = $pid
        processName = [string]$ProcessRecord.processName
        executablePath = [string]$ProcessRecord.executablePath
        startTimeUtc = [string]$ProcessRecord.startTimeUtc
        score = [Math]::Min(100, $score)
        isNewAfterBaseline = $isNew
        isChangedAfterBaseline = $isChanged
        evidenceSignals = @($signals.ToArray())
        missingSignals = @($missing.ToArray())
        selectedWindow = if ($rankedWindows.Count -gt 0) { $rankedWindows[0] } else { $null }
    }
}

function Resolve-ExcelWindowSelection {
    param(
        [Parameter(Mandatory = $true)]$Before,
        [Parameter(Mandatory = $true)]$After,
        [string]$WorkbookStem = '',
        [int]$PreferredProcessId = 0,
        [Nullable[datetime]]$LaunchRequestedUtc = $null
    )

    $delta = Compare-ExcelProcessSnapshots -Before $Before -After $After
    $candidateRecords = New-Object System.Collections.Generic.List[object]
    $seen = @{}
    foreach ($record in @($delta.newProcesses) + @($delta.changedProcesses | ForEach-Object { $_.after })) {
        $pid = [int]$record.pid
        if (-not $seen.ContainsKey($pid)) { $seen[$pid] = $true; $candidateRecords.Add($record) | Out-Null }
    }
    if ($PreferredProcessId -gt 0) {
        foreach ($record in @($After.processes | Where-Object { [int]$_.pid -eq $PreferredProcessId })) {
            if (-not $seen.ContainsKey([int]$record.pid)) { $seen[[int]$record.pid] = $true; $candidateRecords.Add($record) | Out-Null }
        }
    }

    $candidates = @($candidateRecords.ToArray() | ForEach-Object {
        Get-ExcelWindowCandidateScore -ProcessRecord $_ -Delta $delta -WorkbookStem $WorkbookStem `
            -PreferredProcessId $PreferredProcessId -LaunchRequestedUtc $LaunchRequestedUtc
    } | Sort-Object score -Descending, pid)

    $eligible = @($candidates | Where-Object {
        [int]$_.score -ge $script:ExcelWindowSelectionThreshold -and $null -ne $_.selectedWindow -and [Int64]$_.selectedWindow.hwnd -ne 0
    })
    if ($eligible.Count -eq 0) {
        return [pscustomobject][ordered]@{ allowed = $false; reason = 'no_candidate_above_threshold'; winner = $null; tied = @(); candidates = $candidates; delta = $delta }
    }
    $maxScore = ($eligible | Measure-Object -Property score -Maximum).Maximum
    $winners = @($eligible | Where-Object { [int]$_.score -eq [int]$maxScore })
    if ($winners.Count -ne 1) {
        return [pscustomobject][ordered]@{ allowed = $false; reason = 'multiple_tied_candidates'; winner = $null; tied = $winners; candidates = $candidates; delta = $delta }
    }
    return [pscustomobject][ordered]@{ allowed = $true; reason = 'confidence_ok'; winner = $winners[0]; tied = @(); candidates = $candidates; delta = $delta }
}

function Close-ExcelProbeProcess {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [switch]$AllowTerminate
    )

    if (-not (Test-ExcelWindowsHost)) { return [pscustomobject]@{ closed = $false; reason = 'windows_host_required' } }
    Initialize-ExcelWindowNative
    foreach ($window in @(Get-ExcelWindowRecords -ProcessId $ProcessId)) {
        if ([Int64]$window.hwnd -ne 0 -and [ExcelWindowNative]::IsWindow([IntPtr]([Int64]$window.hwnd))) {
            [void][ExcelWindowNative]::PostMessage([IntPtr]([Int64]$window.hwnd), 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        }
    }
    Start-Sleep -Milliseconds 500
    $remaining = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($remaining -and $AllowTerminate) {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 200
        $remaining = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    }
    return [pscustomobject][ordered]@{
        closed = ($null -eq $remaining)
        reason = if ($null -eq $remaining) { 'exact_probe_process_closed' } elseif ($AllowTerminate) { 'probe_process_survived_terminate' } else { 'termination_not_authorized' }
    }
}
