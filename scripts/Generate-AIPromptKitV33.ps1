#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$Source,

    [string]$OutDir = "Outputs\prompt-kit-v33",

    [ValidatePattern('^[^\\/:*?"<>|]+\.xlsx$')]
    [string]$OutputName = "AI_Harness_Prompt_Kit_v33.xlsx"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ResolvedSource = (Resolve-Path -LiteralPath $Source).Path
$SourceExtension = [System.IO.Path]::GetExtension($ResolvedSource).ToLowerInvariant()
if ($SourceExtension -notin @(".xlsx", ".zip")) {
    throw "Source must be an .xlsx workbook or .zip bundle: $ResolvedSource"
}
$ResolvedOutDir = if ([System.IO.Path]::IsPathRooted($OutDir)) {
    [System.IO.Path]::GetFullPath($OutDir)
}
else {
    [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $OutDir))
}
$OutputPath = Join-Path $ResolvedOutDir $OutputName
if ($SourceExtension -eq ".xlsx" -and $ResolvedSource -eq [System.IO.Path]::GetFullPath($OutputPath)) {
    throw "Output must not overwrite the source workbook."
}

Push-Location $RepoRoot
try {
    & python -m triage.prompt_kit_v33_generator `
        --source $ResolvedSource `
        --out-dir $ResolvedOutDir `
        --output-name $OutputName `
        --json
    if ($LASTEXITCODE -ne 0) {
        throw "AI Harness Prompt Kit V33 generation failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

Write-Host "Generated and validated: $OutputPath" -ForegroundColor Green
