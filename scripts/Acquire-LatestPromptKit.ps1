Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$RepositoryUrl = 'https://github.com/EndeavorEverlasting/web-excel-repair-triage.git'
$DefaultBranch = 'main'
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

function Invoke-Git {
    param(
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string[]]$Arguments
    )

    $previous = Get-Location
    try {
        Set-Location -LiteralPath $WorkingDirectory
        $output = & git @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Set-Location -LiteralPath $previous
    }

    $text = ($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode.`r`n$text"
    }
    return $text.Trim()
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
    $previous = Get-Location
    try {
        Set-Location -LiteralPath $RepositoryRoot
        $validationOutput = & $python.File @arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Set-Location -LiteralPath $previous
    }
    if ($exitCode -ne 0) {
        $text = ($validationOutput | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
        throw "Prompt Kit exact-output validation failed.`r`n$text"
    }
}

function Update-RepositorySafely {
    param(
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][scriptblock]$WriteLog
    )

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git was not found. Install Git for Windows and try again.'
    }

    $destinationPath = [System.IO.Path]::GetFullPath($Destination)
    $gitPath = Join-Path $destinationPath '.git'

    if (-not (Test-Path -LiteralPath $destinationPath)) {
        $parent = Split-Path -Parent $destinationPath
        if (-not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        & $WriteLog "Cloning the canonical repository into $destinationPath"
        Invoke-Git -WorkingDirectory $parent -Arguments @(
            'clone', '--branch', $DefaultBranch, '--single-branch', $RepositoryUrl, $destinationPath
        ) | Out-Null
    }
    else {
        if (-not (Test-Path -LiteralPath $gitPath -PathType Container)) {
            throw "The destination exists but is not a Git repository: $destinationPath"
        }

        $origin = Invoke-Git -WorkingDirectory $destinationPath -Arguments @('remote', 'get-url', 'origin')
        if ((Normalize-RepositoryUrl $origin) -ne (Normalize-RepositoryUrl $RepositoryUrl)) {
            throw "The existing repository has an unexpected origin: $origin"
        }

        $status = Invoke-Git -WorkingDirectory $destinationPath -Arguments @('status', '--porcelain')
        if (-not [string]::IsNullOrWhiteSpace($status)) {
            throw 'The repository has local modifications or untracked files. Preserve or commit that work before updating.'
        }

        $branch = Invoke-Git -WorkingDirectory $destinationPath -Arguments @('branch', '--show-current')
        if ($branch -ne $DefaultBranch) {
            throw "The repository is on branch '$branch', not '$DefaultBranch'. Switch safely before updating."
        }

        & $WriteLog 'Fetching the latest main branch.'
        Invoke-Git -WorkingDirectory $destinationPath -Arguments @('fetch', 'origin', $DefaultBranch, '--prune') | Out-Null

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
            throw "Local main contains $localAhead commit(s) not on origin/main. No reset or overwrite was attempted."
        }

        if ($remoteAhead -gt 0) {
            & $WriteLog "Fast-forwarding main by $remoteAhead commit(s)."
            Invoke-Git -WorkingDirectory $destinationPath -Arguments @('merge', '--ff-only', "origin/$DefaultBranch") | Out-Null
        }
        else {
            & $WriteLog 'Repository is already current.'
        }
    }

    $finalBranch = Invoke-Git -WorkingDirectory $destinationPath -Arguments @('branch', '--show-current')
    if ($finalBranch -ne $DefaultBranch) {
        throw "Acquisition finished on unexpected branch '$finalBranch'."
    }

    Test-RequiredFiles -RepositoryRoot $destinationPath
    & $WriteLog 'Repository and Prompt Kit validation passed.'
    return $destinationPath
}

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Get Latest Prompt Kit'
$form.StartPosition = 'CenterScreen'
$form.Size = New-Object System.Drawing.Size(760, 520)
$form.MinimumSize = New-Object System.Drawing.Size(760, 520)

$title = New-Object System.Windows.Forms.Label
$title.Text = 'Clone or safely update the Prompt Kit repository'
$title.Font = New-Object System.Drawing.Font('Segoe UI', 14, [System.Drawing.FontStyle]::Bold)
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(20, 18)
$form.Controls.Add($title)

$description = New-Object System.Windows.Forms.Label
$description.Text = 'This tool never resets, cleans, force-pushes, or discards local work.'
$description.AutoSize = $true
$description.Location = New-Object System.Drawing.Point(22, 52)
$form.Controls.Add($description)

$destinationLabel = New-Object System.Windows.Forms.Label
$destinationLabel.Text = 'Destination folder'
$destinationLabel.AutoSize = $true
$destinationLabel.Location = New-Object System.Drawing.Point(22, 91)
$form.Controls.Add($destinationLabel)

$destinationBox = New-Object System.Windows.Forms.TextBox
$destinationBox.Location = New-Object System.Drawing.Point(22, 114)
$destinationBox.Size = New-Object System.Drawing.Size(602, 27)
$destinationBox.Text = Join-Path $env:USERPROFILE 'Desktop\dev\web-excel-repair-triage'
$form.Controls.Add($destinationBox)

$browseButton = New-Object System.Windows.Forms.Button
$browseButton.Text = 'Browse...'
$browseButton.Location = New-Object System.Drawing.Point(636, 111)
$browseButton.Size = New-Object System.Drawing.Size(92, 32)
$form.Controls.Add($browseButton)

$openLabel = New-Object System.Windows.Forms.Label
$openLabel.Text = 'After validation'
$openLabel.AutoSize = $true
$openLabel.Location = New-Object System.Drawing.Point(22, 157)
$form.Controls.Add($openLabel)

$openChoice = New-Object System.Windows.Forms.ComboBox
$openChoice.DropDownStyle = 'DropDownList'
$openChoice.Location = New-Object System.Drawing.Point(22, 180)
$openChoice.Size = New-Object System.Drawing.Size(340, 28)
[void]$openChoice.Items.Add('Open Prompt Kit website')
[void]$openChoice.Items.Add('Open generator selection GUI')
$openChoice.SelectedIndex = 0
$form.Controls.Add($openChoice)

$runButton = New-Object System.Windows.Forms.Button
$runButton.Text = 'Get Latest and Open'
$runButton.Location = New-Object System.Drawing.Point(380, 177)
$runButton.Size = New-Object System.Drawing.Size(180, 34)
$form.Controls.Add($runButton)

$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Text = 'Close'
$closeButton.Location = New-Object System.Drawing.Point(572, 177)
$closeButton.Size = New-Object System.Drawing.Size(90, 34)
$form.Controls.Add($closeButton)

$logBox = New-Object System.Windows.Forms.TextBox
$logBox.Location = New-Object System.Drawing.Point(22, 230)
$logBox.Size = New-Object System.Drawing.Size(706, 235)
$logBox.Multiline = $true
$logBox.ReadOnly = $true
$logBox.ScrollBars = 'Vertical'
$logBox.Font = New-Object System.Drawing.Font('Consolas', 9)
$form.Controls.Add($logBox)

$writeLog = {
    param([string]$Message)
    $timestamp = Get-Date -Format 'HH:mm:ss'
    $logBox.AppendText("[$timestamp] $Message`r`n")
    $logBox.SelectionStart = $logBox.TextLength
    $logBox.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
}

$browseButton.Add_Click({
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = 'Choose the parent folder for web-excel-repair-triage'
    $current = Split-Path -Parent $destinationBox.Text
    if (Test-Path -LiteralPath $current) {
        $dialog.SelectedPath = $current
    }
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $destinationBox.Text = Join-Path $dialog.SelectedPath 'web-excel-repair-triage'
    }
})

$closeButton.Add_Click({ $form.Close() })

$runButton.Add_Click({
    $runButton.Enabled = $false
    $browseButton.Enabled = $false
    try {
        & $writeLog 'Starting safe acquisition.'
        $repositoryRoot = Update-RepositorySafely -Destination $destinationBox.Text -WriteLog $writeLog
        if ($openChoice.SelectedIndex -eq 1) {
            & $writeLog 'Opening generator selection GUI.'
            Start-Process -FilePath (Join-Path $repositoryRoot 'Run-PromptKitGenerator.cmd')
        }
        else {
            & $writeLog 'Opening Prompt Kit website.'
            Start-Process -FilePath (Join-Path $repositoryRoot 'web\prompt-kit\index.html')
        }
        [System.Windows.Forms.MessageBox]::Show(
            'The latest validated Prompt Kit is ready.',
            'Prompt Kit ready',
            'OK',
            'Information'
        ) | Out-Null
    }
    catch {
        & $writeLog "FAILED: $($_.Exception.Message)"
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            'Prompt Kit acquisition failed',
            'OK',
            'Error'
        ) | Out-Null
    }
    finally {
        $runButton.Enabled = $true
        $browseButton.Enabled = $true
    }
})

[void]$form.ShowDialog()
