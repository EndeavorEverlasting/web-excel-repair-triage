@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 "C:\path\to\AI_Harness_Prompt_Kit_v33.xlsx" [output-directory]
  exit /b 2
)
set "SCRIPT_DIR=%~dp0"
echo Finalize-AIPromptKitV33.cmd is a compatibility alias for the canonical generator.
call "%SCRIPT_DIR%Generate-AIPromptKitV33.cmd" "%~1" "%~2" "%~3"
exit /b %ERRORLEVEL%
