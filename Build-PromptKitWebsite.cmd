@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>&1
    if not %errorlevel%==0 (
        echo Python 3 was not found. Install Python 3 or add it to PATH.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html
if not %errorlevel%==0 goto :fail

%PYTHON_CMD% scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
if not %errorlevel%==0 goto :fail

start "" web\prompt-kit\index.html
echo Prompt Kit website built and validated from the combined registry.
endlocal
exit /b 0

:fail
echo.
echo Prompt Kit website build failed with exit code %errorlevel%.
pause
endlocal
exit /b %errorlevel%
