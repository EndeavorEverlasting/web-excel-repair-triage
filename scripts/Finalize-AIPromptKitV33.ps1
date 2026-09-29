[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceWorkbook,

    [string]$OutDir = "Outputs\prompt-kit-v33",

    [string]$OutputName = "AI_Harness_Prompt_Kit_v33_GNHF.xlsx"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$CanonicalLauncher = Join-Path $PSScriptRoot "Generate-AIPromptKitV33.ps1"
if (-not (Test-Path -LiteralPath $CanonicalLauncher -PathType Leaf)) {
    throw "Canonical V33 generator launcher not found: $CanonicalLauncher"
}

Write-Warning "Finalize-AIPromptKitV33.ps1 is a compatibility shim; use Generate-AIPromptKitV33.ps1 for workbook or bundle input."
& $CanonicalLauncher -Source $SourceWorkbook -OutDir $OutDir -OutputName $OutputName
exit $LASTEXITCODE
