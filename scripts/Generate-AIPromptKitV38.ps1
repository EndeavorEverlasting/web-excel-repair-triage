#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$Source,

    [string]$OutDir = "Outputs/prompt_kit_v38",

    [ValidateRange(1, 999)]
    [int]$ExpectedPromptCount = 45
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
    & python -m triage.prompt_kit_v38_generator `
        --source $ResolvedSource `
        --out-dir $ResolvedOutDir `
        --expected-prompt-count $ExpectedPromptCount `
        --json

    if ($LASTEXITCODE -ne 0) {
        throw "AI Harness Prompt Kit V38 generation failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
