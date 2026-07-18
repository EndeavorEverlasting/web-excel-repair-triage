@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "REPO_ROOT=%~dp0"
for %%I in ("%REPO_ROOT%.") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || (
  echo ERROR: Could not enter repository directory: %REPO_ROOT%
  set "EXIT_CODE=1"
  goto :finish
)

set "SOURCE=%~1"
set "OUT_DIR=%~2"
set "EXPECTED_PROMPTS=%~3"

if not defined OUT_DIR set "OUT_DIR=Outputs\prompt_kit_v38"
if not defined EXPECTED_PROMPTS set "EXPECTED_PROMPTS=45"

if not defined SOURCE (
  echo.
  echo AI Harness Prompt Kit V38 Asset Generator
  echo ------------------------------------------
  echo Drag a V37 .xlsx workbook or single-workbook .zip bundle onto this file,
  echo or paste its full path below.
  echo.
  set /p "SOURCE=V37 workbook or bundle path: "
)

set "SOURCE=%SOURCE:"=%"
if not defined SOURCE (
  echo ERROR: No V37 source was provided.
  set "EXIT_CODE=2"
  goto :finish
)

for %%I in ("%SOURCE%") do set "SOURCE=%%~fI"
if not exist "%SOURCE%" (
  echo ERROR: Source file not found: %SOURCE%
  set "EXIT_CODE=2"
  goto :finish
)

for %%I in ("%OUT_DIR%") do set "OUTPUT_ROOT=%%~fI"

call "%REPO_ROOT%\scripts\Generate-AIPromptKitV38.cmd" "%SOURCE%" "%OUT_DIR%" "%EXPECTED_PROMPTS%"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto :finish

echo.
echo V38 assets are ready:
echo   %OUTPUT_ROOT%\AI_Harness_Prompt_Kit_v38.xlsx
echo   %OUTPUT_ROOT%\AI_Harness_Prompt_Kit_v38_local_runtime_build.md
echo   %OUTPUT_ROOT%\AI_Harness_Prompt_Kit_v38_manifest.json
echo   %OUTPUT_ROOT%\AI_Harness_Prompt_Kit_v38_bundle.zip

:finish
if not defined EXIT_CODE set "EXIT_CODE=0"
echo.
if not defined WEB_EXCEL_NO_PAUSE pause
endlocal & exit /b %EXIT_CODE%
