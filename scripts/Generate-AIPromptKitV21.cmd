@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Error: Missing required source bundle argument.
    echo Usage: Generate-AIPromptKitV21.cmd ^<path_to_v20_bundle.zip^> [^<output_dir^>]
    exit /b 1
)

set "SOURCE_BUNDLE=%~1"
set "OUT_DIR=%~2"
if "!OUT_DIR!"=="" set "OUT_DIR=Outputs"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Generate-AIPromptKitV21.ps1" -SourceBundle "!SOURCE_BUNDLE!" -OutDir "!OUT_DIR!"
exit /b %ERRORLEVEL%
