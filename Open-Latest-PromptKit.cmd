@echo off
setlocal

set "LOCAL_SCRIPT=%~dp0scripts\Open-LatestPromptKitPortable.ps1"
set "CACHE_DIR=%TEMP%\WebExcelPromptKit"
set "CACHED_SCRIPT=%CACHE_DIR%\Open-LatestPromptKitPortable.ps1"
set "BOOTSTRAP_COMMIT=2e8795f1136d2737461c0770127728496eaa4edc"
set "BOOTSTRAP_BLOB=eee14a8da3a96dc3ca6e671e65b4b87255718500"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "PREFERRED_REPO="

rem If this launcher is run from inside a tracked checkout, use that checkout.
if exist "%~dp0.git" if exist "%~dp0web\prompt-kit\index.html" set "PREFERRED_REPO=%~dp0"

rem Otherwise the PowerShell launcher resolves the single canonical Desktop\dev checkout.
rem The download location of this CMD must never become an implicit repository root.

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
        "$ErrorActionPreference='Stop'; $h=@{'User-Agent'='PromptKit-Pinned-Bootstrap';'Accept'='application/vnd.github+json'}; $u='https://api.github.com/repos/EndeavorEverlasting/web-excel-repair-triage/contents/scripts/Open-LatestPromptKitPortable.ps1?ref=%BOOTSTRAP_COMMIT%'; $r=Invoke-RestMethod -Method Get -Uri $u -Headers $h; if($r.sha -ne '%BOOTSTRAP_BLOB%'){throw ('Pinned Prompt Kit launcher blob mismatch. Expected %BOOTSTRAP_BLOB%; received '+$r.sha)}; [IO.File]::WriteAllBytes('%CACHED_SCRIPT%',[Convert]::FromBase64String(($r.content -replace '\s','')))"
    if errorlevel 1 (
        echo.
        echo Could not acquire the pinned Prompt Kit launcher.
        echo Check GitHub network access and try again.
        pause
        exit /b 1
    )
    set "SCRIPT=%CACHED_SCRIPT%"
)

if defined PREFERRED_REPO (
    echo Prompt Kit repository: %PREFERRED_REPO%
    "%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -Destination "%PREFERRED_REPO%"
) else (
    echo Prompt Kit repository: canonical Desktop\dev\web-excel-repair-triage
    "%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
)
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo Prompt Kit portable quick-open failed with exit code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%
