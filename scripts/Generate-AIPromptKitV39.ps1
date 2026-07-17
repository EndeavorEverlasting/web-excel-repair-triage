#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$Source,

    [string]$OutDir = "Outputs/prompt_kit_v39",

    [string]$Python = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$ResolvedSource = (Resolve-Path -LiteralPath $Source).Path
$ResolvedOutDir = if ([System.IO.Path]::IsPathRooted($OutDir)) {
    $OutDir
}
else {
    Join-Path $RepoRoot $OutDir
}

Push-Location $RepoRoot
try {
    $GitRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
    if (-not $GitRoot) {
        throw "Unable to resolve the Git repository root from '$RepoRoot'."
    }
    $VerifiedGitRoot = (Resolve-Path -LiteralPath $GitRoot).Path
    if ($VerifiedGitRoot -ne $RepoRoot) {
        throw "Directory gate failed. Script root is '$RepoRoot' but Git resolved '$VerifiedGitRoot'."
    }

    Write-Host "Repository root: $RepoRoot"
    Write-Host "Source V38: $ResolvedSource"
    Write-Host "Output directory: $ResolvedOutDir"
    Write-Host "Standard-AI extension: P50-P55"
    Write-Host "GNHF harness/runtime section: P45-P49"

    & $Python -m triage.prompt_kit_v39_generator `
        --source $ResolvedSource `
        --out-dir $ResolvedOutDir `
        --standard-ai-spec (Join-Path $RepoRoot "configs/prompt_kit/v39_standard_ai_extensions.json") `
        --gnhf-spec (Join-Path $RepoRoot "configs/prompt_kit/v39_gnhf_harness_prompts.json") `
        --json

    if ($LASTEXITCODE -ne 0) {
        throw "AI Harness Prompt Kit V39 generation failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
