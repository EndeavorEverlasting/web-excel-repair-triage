Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $Root 'scripts\Acquire-LatestPromptKit.ps1'

$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $ScriptPath,
    [ref]$tokens,
    [ref]$parseErrors
)

if ($parseErrors.Count -gt 0) {
    throw "Acquire-LatestPromptKit.ps1 has PowerShell parse errors: $($parseErrors -join '; ')"
}

$addUniquePath = $ast.Find(
    {
        param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
            $node.Name -eq 'Add-UniquePath'
    },
    $true
)

if (-not $addUniquePath) {
    throw 'Add-UniquePath was not found in Acquire-LatestPromptKit.ps1.'
}

Invoke-Expression $addUniquePath.Extent.Text

$paths = [System.Collections.Generic.List[string]]::new()
$expected = [System.IO.Path]::GetFullPath((Join-Path ([System.IO.Path]::GetTempPath()) 'prompt-kit-dev'))

# Regression: this exact call failed in the released launcher because PowerShell
# rejected the initially empty List[string] before Add-UniquePath could run.
Add-UniquePath -Paths $paths -Path $expected

if ($paths.Count -ne 1) {
    throw "Expected one resolved path after first insertion; got $($paths.Count)."
}
if ($paths[0] -ne $expected) {
    throw "Resolved path drifted. Expected '$expected', got '$($paths[0])'."
}

# Preserve uniqueness as the helper's original contract.
Add-UniquePath -Paths $paths -Path $expected
if ($paths.Count -ne 1) {
    throw "Duplicate path was added; expected one entry, got $($paths.Count)."
}

Write-Host 'Prompt Kit quick-open empty-list path resolution: PASS'
