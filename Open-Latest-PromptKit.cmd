@echo off
setlocal

set "LOCAL_SCRIPT=%~dp0scripts\Open-LatestPromptKitPortable.ps1"
set "CACHE_DIR=%TEMP%\WebExcelPromptKit"
set "CACHED_SCRIPT=%CACHE_DIR%\Open-LatestPromptKitPortable.ps1"
set "SCRIPT_URL=https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/scripts/Open-LatestPromptKitPortable.ps1"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "PREFERRED_REPO=%~dp0dev\web-excel-repair-triage"

rem If this launcher is run from inside a tracked checkout, use that checkout.
if exist "%~dp0.git" if exist "%~dp0web\prompt-kit\index.html" set "PREFERRED_REPO=%~dp0"

rem A Desktop launcher resolves deterministically to Desktop\dev\web-excel-repair-triage.
if exist "%~dp0dev\web-excel-repair-triage\.git" set "PREFERRED_REPO=%~dp0dev\web-excel-repair-triage"

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
        echo Could not download the canonical portable Prompt Kit launcher.
        echo Check network access to GitHub and try again.
        pause
        exit /b 1
    )
    set "SCRIPT=%CACHED_SCRIPT%"
)

echo Prompt Kit repository: %PREFERRED_REPO%
"%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -Destination "%PREFERRED_REPO%"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo Prompt Kit portable quick-open failed with exit code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%
