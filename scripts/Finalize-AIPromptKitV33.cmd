@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 "C:\path\to\AI_Harness_Prompt_Kit_v33.xlsx" [output-directory]
  exit /b 2
)
set "SCRIPT_DIR=%~dp0"
set "OUT_DIR=%~2"
if "%OUT_DIR%"=="" set "OUT_DIR=Outputs\prompt-kit-v33"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Finalize-AIPromptKitV33.ps1" -SourceWorkbook "%~1" -OutDir "%OUT_DIR%"
exit /b %ERRORLEVEL%
