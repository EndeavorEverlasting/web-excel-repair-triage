[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$Root = (git rev-parse --show-toplevel).Trim()
if (-not $Root) { throw 'Not inside a Git repository.' }
Set-Location -LiteralPath $Root
git config core.hooksPath .githooks
Write-Host 'Installed repo-local hooks: core.hooksPath=.githooks'
