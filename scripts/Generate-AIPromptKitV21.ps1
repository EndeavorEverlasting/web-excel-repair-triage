param(
    [Parameter(Mandatory=$true)]
    [string]$SourceBundle,

    [Parameter(Mandatory=$false)]
    [string]$OutDir = "Outputs"
)

$ErrorActionPreference = 'Stop'

Write-Host "Running AI Harness Prompt Kit V21 self-service generator..." -ForegroundColor Cyan
Write-Host "Source Bundle: $SourceBundle"
Write-Host "Output Directory: $OutDir"

# Ensure python is available
try {
    & python --version | Out-Null
} catch {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# Run generator
& python -m triage.prompt_kit_v21_generator --source-bundle "$SourceBundle" --out-dir "$OutDir"
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "V21 workbook and delivery bundle successfully generated." -ForegroundColor Green
    exit 0
} else {
    Write-Host "V21 generation failed with exit code $exitCode." -ForegroundColor Red
    exit 1
}
