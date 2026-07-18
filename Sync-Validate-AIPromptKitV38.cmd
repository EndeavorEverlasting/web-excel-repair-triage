@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "TARGET_BRANCH=feat/prompt-kit-v33-self-service-generator"
set "REPO_ROOT=%~dp0"
for %%I in ("%REPO_ROOT%.") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || (
  echo ERROR: Could not enter repository directory: %REPO_ROOT%
  set "EXIT_CODE=1"
  goto :finish
)

git rev-parse --show-toplevel >nul 2>&1
if errorlevel 1 (
  echo ERROR: This launcher is not inside a Git repository.
  set "EXIT_CODE=1"
  goto :finish
)

set "DIRTY_STATE="
for /f "delims=" %%I in ('git status --porcelain') do set "DIRTY_STATE=1"
if defined DIRTY_STATE (
  echo ERROR: The worktree has local changes. Commit, stash, or use an isolated worktree before syncing.
  git status --short
  set "EXIT_CODE=2"
  goto :finish
)

echo Fetching origin...
git fetch origin
if errorlevel 1 (
  set "EXIT_CODE=%ERRORLEVEL%"
  goto :finish
)

echo Switching to %TARGET_BRANCH%...
git switch "%TARGET_BRANCH%"
if errorlevel 1 (
  set "EXIT_CODE=%ERRORLEVEL%"
  goto :finish
)

echo Fast-forwarding from origin...
git pull --ff-only origin "%TARGET_BRANCH%"
if errorlevel 1 (
  set "EXIT_CODE=%ERRORLEVEL%"
  goto :finish
)

echo Running focused V38 validation...
python -m pytest tests/test_prompt_kit_v38_prompt_assets.py tests/test_prompt_kit_v38_generator.py tests/test_prompt_kit_v38_cmd_launchers.py -q
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto :finish

echo.
echo V38 branch sync and focused validation completed successfully.

:finish
if not defined EXIT_CODE set "EXIT_CODE=0"
echo.
if not defined WEB_EXCEL_NO_PAUSE pause
endlocal & exit /b %EXIT_CODE%
