@echo off
setlocal
set "LOCAL_SCRIPT=%~dp0scripts\Acquire-LatestPromptKit.ps1"
set "CACHE_DIR=%TEMP%\WebExcelPromptKit"
set "CACHED_SCRIPT=%CACHE_DIR%\Acquire-LatestPromptKit.ps1"
set "SCRIPT_URL=https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/scripts/Acquire-LatestPromptKit.ps1"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%POWERSHELL%" (
    echo Windows PowerShell was not found.
    pause
    exit /b 1
)

if exist "%LOCAL_SCRIPT%" (
    set "SCRIPT=%LOCAL_SCRIPT%"
) else (
    if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
    "%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing -Uri '%SCRIPT_URL%' -OutFile '%CACHED_SCRIPT%'"
    if errorlevel 1 (
        echo.
        echo Could not download the acquisition GUI from the canonical repository.
        echo Check network access to GitHub and try again.
        pause
        exit /b 1
    )
    set "SCRIPT=%CACHED_SCRIPT%"
)

"%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo Prompt Kit acquisition failed with exit code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%
