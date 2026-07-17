@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 "C:\path\to\AI_Harness_Prompt_Kit_v38.xlsx" [output-directory]
  exit /b 2
)
set "SCRIPT_DIR=%~dp0"
set "OUT_DIR=%~2"
if "%OUT_DIR%"=="" set "OUT_DIR=Outputs\prompt_kit_v39"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Generate-AIPromptKitV39.ps1" -Source "%~1" -OutDir "%OUT_DIR%"
exit /b %ERRORLEVEL%
