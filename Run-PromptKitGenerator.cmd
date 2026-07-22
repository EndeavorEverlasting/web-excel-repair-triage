@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 scripts\prompt_kit_generator_gui.py
) else (
    where python >nul 2>&1
    if not %errorlevel%==0 (
        echo Python 3 was not found. Install Python 3 or add it to PATH.
        pause
        exit /b 1
    )
    python scripts\prompt_kit_generator_gui.py
)

if not %errorlevel%==0 (
    echo.
    echo Prompt Kit Generator failed with exit code %errorlevel%.
    pause
    exit /b %errorlevel%
)
endlocal
