[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Source,

    [Parameter(Position = 1)]
    [string]$OutDir = "Outputs\prompt_kit_v39",

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$SourcePath = (Resolve-Path -LiteralPath $Source).Path
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

Set-Location -LiteralPath $RepoRoot
$GitRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $GitRoot) {
    throw "Unable to resolve the repository root from $RepoRoot."
}
$VerifiedGitRoot = (Resolve-Path -LiteralPath $GitRoot).Path
if ($VerifiedGitRoot -ne $RepoRoot) {
    throw "Directory gate failed. Script root resolves to '$RepoRoot' but Git resolves to '$VerifiedGitRoot'."
}

if ([System.IO.Path]::IsPathRooted($OutDir)) {
    $OutputPath = $OutDir
}
else {
    $OutputPath = Join-Path $RepoRoot $OutDir
}

Write-Host "Repository root: $RepoRoot"
Write-Host "Source V38: $SourcePath"
Write-Host "Output directory: $OutputPath"

& $Python -m triage.prompt_kit_v39_generator `
    --source $SourcePath `
    --out-dir $OutputPath `
    --spec (Join-Path $RepoRoot "configs\prompt_kit\v39_local_first_prompts.json") `
    --json

if ($LASTEXITCODE -ne 0) {
    throw "V39 generation failed with exit code $LASTEXITCODE."
}
