@echo off
setlocal

if "%~1"=="" (
  echo Usage: %~nx0 ^<source-workbook-or-bundle^> [output-directory] [output-name]
  echo Example: %~nx0 "C:\Artifacts\AI_Harness_Prompt_Kit_v33_bundle.zip"
  pause
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "SOURCE=%~1"
set "OUT_DIR=%~2"
set "OUTPUT_NAME=%~3"

if "%OUT_DIR%"=="" set "OUT_DIR=Outputs\prompt-kit-v33"
if "%OUTPUT_NAME%"=="" set "OUTPUT_NAME=AI_Harness_Prompt_Kit_v33.xlsx"

pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Generate-AIPromptKitV33.ps1" -Source "%SOURCE%" -OutDir "%OUT_DIR%" -OutputName "%OUTPUT_NAME%"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
  echo V33 generation failed with exit code %EXIT_CODE%.
) else (
  echo V33 generation completed.
)
pause
exit /b %EXIT_CODE%
