@echo off
setlocal

set "ROOT=%~dp0"
set "SCRIPT=%ROOT%scripts\install_local_hooks.py"

if not exist "%SCRIPT%" goto missing_script

where py >nul 2>&1
if errorlevel 1 goto try_python
py -3 -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)" >nul 2>&1
if errorlevel 1 goto try_python
py -3 "%SCRIPT%" %*
exit /b %errorlevel%

:try_python
where python >nul 2>&1
if errorlevel 1 goto no_python
python -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)" >nul 2>&1
if errorlevel 1 goto no_python
python "%SCRIPT%" %*
exit /b %errorlevel%

:missing_script
echo [harness] local hook setup failed: missing %SCRIPT% 1>&2
exit /b 2

:no_python
echo [harness] local hook setup failed: usable Python 3 was not found. 1>&2
exit /b 2
