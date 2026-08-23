@echo off
setlocal

set "ROOT=%~dp0"
set "SCRIPT=%ROOT%scripts\install_local_hooks.py"

if not exist "%SCRIPT%" (
  echo [harness] local hook setup failed: missing %SCRIPT% 1>&2
  exit /b 2
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  py -3 -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)" >nul 2>&1
  if %ERRORLEVEL% EQU 0 (
    py -3 "%SCRIPT%" %*
    exit /b %ERRORLEVEL%
  )
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  python -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)" >nul 2>&1
  if %ERRORLEVEL% EQU 0 (
    python "%SCRIPT%" %*
    exit /b %ERRORLEVEL%
  )
)

echo [harness] local hook setup failed: usable Python 3 was not found. 1>&2
exit /b 2
