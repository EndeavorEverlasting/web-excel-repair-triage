@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 scripts\run_repo_native_update.py %*
) else (
    where python >nul 2>&1
    if not %errorlevel%==0 (
        echo Python 3 was not found. Install Python 3 or add it to PATH.
        pause
        exit /b 1
    )
    python scripts\run_repo_native_update.py %*
)

if not %errorlevel%==0 (
    echo.
    echo Repo-native update generator failed with exit code %errorlevel%.
    pause
    exit /b %errorlevel%
)
endlocal
