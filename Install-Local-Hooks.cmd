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
  py -3 "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  python "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)

echo [harness] local hook setup failed: Python 3 was not found on PATH. 1>&2
exit /b 2
