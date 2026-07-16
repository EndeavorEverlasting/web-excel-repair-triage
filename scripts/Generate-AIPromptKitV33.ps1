#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$Source,

    [string]$OutDir = "Outputs/prompt_kit_v33",

    [ValidatePattern('^P\d{2}$')]
    [string]$GnhfBuildPrompt = "P39"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ResolvedSource = (Resolve-Path -LiteralPath $Source).Path
$ResolvedOutDir = if ([System.IO.Path]::IsPathRooted($OutDir)) {
    $OutDir
}
else {
    Join-Path $RepoRoot $OutDir
}

Push-Location $RepoRoot
try {
    & python -m triage.prompt_kit_v33_generator `
        --source $ResolvedSource `
        --out-dir $ResolvedOutDir `
        --gnhf-build-prompt $GnhfBuildPrompt `
        --json

    if ($LASTEXITCODE -ne 0) {
        throw "AI Harness Prompt Kit V33 generation failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
