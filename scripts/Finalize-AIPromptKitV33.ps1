[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceWorkbook,

    [string]$OutDir = "Outputs\prompt-kit-v33",

    [string]$OutputName = "AI_Harness_Prompt_Kit_v33_GNHF.xlsx"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SourcePath = [System.IO.Path]::GetFullPath($SourceWorkbook)
$OutputRoot = if ([System.IO.Path]::IsPathRooted($OutDir)) {
    [System.IO.Path]::GetFullPath($OutDir)
}
else {
    [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $OutDir))
}
$OutputPath = Join-Path $OutputRoot $OutputName
$ReportPath = Join-Path $OutputRoot "finalize-report.json"
$LayoutReportPath = Join-Path $OutputRoot "layout-report.json"

if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw "Source workbook not found: $SourcePath"
}
if ([System.IO.Path]::GetExtension($SourcePath) -ne ".xlsx") {
    throw "Source workbook must be an .xlsx file: $SourcePath"
}
if ($SourcePath -eq [System.IO.Path]::GetFullPath($OutputPath)) {
    throw "Output must not overwrite the source workbook."
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

Push-Location $RepoRoot
try {
    python -m triage.prompt_kit_v33_finalizer `
        --source $SourcePath `
        --output $OutputPath `
        --report $ReportPath
    if ($LASTEXITCODE -ne 0) {
        throw "Prompt-kit finalizer failed with exit code $LASTEXITCODE."
    }

    python -m triage.prompt_kit_v33_layout_finalizer `
        $OutputPath `
        --report $LayoutReportPath
    if ($LASTEXITCODE -ne 0) {
        throw "Prompt-kit layout finalizer failed with exit code $LASTEXITCODE."
    }

    $Validators = @(
        @("-m", "triage.prompt_kit_v33_artifact_contract", $OutputPath),
        @("-m", "triage.prompt_kit_operability_contract", $OutputPath),
        @("-m", "triage.workbook_package_hygiene", $OutputPath),
        @("-m", "triage.web_excel_compatibility_rules", $OutputPath)
    )
    foreach ($Validator in $Validators) {
        & python @Validator
        if ($LASTEXITCODE -ne 0) {
            throw "Validator failed: python $($Validator -join ' ')"
        }
    }
}
finally {
    Pop-Location
}

Write-Host "Generated: $OutputPath" -ForegroundColor Green
Write-Host "Report:    $ReportPath" -ForegroundColor Green
Write-Host "Layout:    $LayoutReportPath" -ForegroundColor Green
