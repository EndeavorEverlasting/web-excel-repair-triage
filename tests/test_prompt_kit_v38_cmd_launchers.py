from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_LAUNCHER = REPO_ROOT / "Run-AIPromptKitV38.cmd"
SYNC_LAUNCHER = REPO_ROOT / "Sync-Validate-AIPromptKitV38.cmd"


def _text(path: Path) -> str:
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_v38_asset_launcher_is_click_ready_and_prints_artifacts() -> None:
    text = _text(RUN_LAUNCHER)

    assert "%~dp0" in text
    assert 'cd /d "%REPO_ROOT%"' in text
    assert "set /p \"SOURCE=" in text
    assert "scripts\\Generate-AIPromptKitV38.cmd" in text
    assert "AI_Harness_Prompt_Kit_v38.xlsx" in text
    assert "AI_Harness_Prompt_Kit_v38_local_runtime_build.md" in text
    assert "AI_Harness_Prompt_Kit_v38_manifest.json" in text
    assert "AI_Harness_Prompt_Kit_v38_bundle.zip" in text
    assert "WEB_EXCEL_NO_PAUSE" in text
    assert "endlocal & exit /b %EXIT_CODE%" in text
    assert "C:\\Users\\" not in text


def test_v38_sync_launcher_replaces_manual_next_command() -> None:
    text = _text(SYNC_LAUNCHER)

    assert "%~dp0" in text
    assert 'cd /d "%REPO_ROOT%"' in text
    assert "git status --porcelain" in text
    assert "git fetch origin" in text
    assert 'git switch "%TARGET_BRANCH%"' in text
    assert 'git pull --ff-only origin "%TARGET_BRANCH%"' in text
    assert "tests/test_prompt_kit_v38_prompt_assets.py" in text
    assert "tests/test_prompt_kit_v38_generator.py" in text
    assert "tests/test_prompt_kit_v38_cmd_launchers.py" in text
    assert "WEB_EXCEL_NO_PAUSE" in text
    assert "endlocal & exit /b %EXIT_CODE%" in text
    assert "C:\\Users\\" not in text


def test_sync_launcher_refuses_dirty_worktrees_before_fetch() -> None:
    text = _text(SYNC_LAUNCHER)

    dirty_check = text.index("git status --porcelain")
    dirty_refusal = text.index("The worktree has local changes")
    fetch = text.index("git fetch origin")
    assert dirty_check < dirty_refusal < fetch
