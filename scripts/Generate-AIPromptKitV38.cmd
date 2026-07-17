@echo off
setlocal

if "%~1"=="" (
  echo Usage: %~nx0 ^<V37-workbook-or-bundle^> [output-directory] [expected-prompt-count]
  echo Example: %~nx0 "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx"
  pause
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "SOURCE=%~1"
set "OUT_DIR=%~2"
set "EXPECTED_PROMPTS=%~3"

if "%OUT_DIR%"=="" set "OUT_DIR=Outputs\prompt_kit_v38"
if "%EXPECTED_PROMPTS%"=="" set "EXPECTED_PROMPTS=45"

pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Generate-AIPromptKitV38.ps1" -Source "%SOURCE%" -OutDir "%OUT_DIR%" -ExpectedPromptCount %EXPECTED_PROMPTS%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
  echo V38 generation failed with exit code %EXIT_CODE%.
) else (
  echo V38 generation completed.
)

endlocal & exit /b %EXIT_CODE%
