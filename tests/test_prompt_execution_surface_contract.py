from __future__ import annotations

from triage.prompt_execution_surface_contract import (
    GNHF_LAUNCH_ARTIFACT,
    GNHF_RUNTIME_OBJECTIVE,
    REGULAR_AI_PROMPT,
    classify_prompt_surface,
    validate_gnhf_launch_artifact,
)


def valid_provider_launch() -> str:
    return r'''$DevRoot = Join-Path $HOME "Desktop\dev"
$RepoPath = Join-Path $DevRoot "AxTask"
if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) {
    throw "Repository directory not found: $RepoPath"
}
Set-Location -LiteralPath $RepoPath
$PromptPath = Join-Path $RepoPath "docs\ops\gnhf\axtask-night-sprint.md"
$Launcher = Join-Path $env:LOCALAPPDATA "AgentSwitchboard\GnhfFleet\Start-ProviderRoutedGnhfSprint.ps1"
& $Launcher `
  -RepoPath $RepoPath `
  -PromptPath $PromptPath `
  -Model "deepseek/deepseek-v4-pro" `
  -MaxIterations 8 `
  -MaxTokens 800000 `
  -ProbeTimeoutSeconds 30 `
  -StopWhen "One bounded repair or blocker report is committed and the worktree is clean."
'''


def test_classifies_three_execution_surfaces() -> None:
    regular = "EXECUTE THE REPOSITORY SPRINT. Inspect the repo, repair it, and report."
    objective = """Repo: EndeavorEverlasting/AxTask
Sprint: bounded repair
Lane: one cluster
Owned scope:
- tests
Forbidden scope:
- deployment
Objective:
Repair one root cause.
"""

    assert classify_prompt_surface(regular) == REGULAR_AI_PROMPT
    assert classify_prompt_surface(objective) == GNHF_RUNTIME_OBJECTIVE
    assert classify_prompt_surface(valid_provider_launch()) == GNHF_LAUNCH_ARTIFACT


def test_accepts_directory_first_agentswitchboard_launch() -> None:
    report = validate_gnhf_launch_artifact(valid_provider_launch())
    assert report.valid, report.findings
    assert report.surface == GNHF_LAUNCH_ARTIFACT


def test_rejects_regular_ai_prompt_as_gnhf_prompt() -> None:
    report = validate_gnhf_launch_artifact(
        "EXECUTE THE REPO SPRINT. DO NOT RETURN A PLAN. Change files, validate, and commit."
    )
    assert not report.valid
    assert report.surface == REGULAR_AI_PROMPT
    assert any(item["rule"] == "execution surface" for item in report.findings)


def test_rejects_runtime_objective_without_launcher() -> None:
    report = validate_gnhf_launch_artifact(
        """Repo: EndeavorEverlasting/AxTask
Sprint: repair
Lane: one cluster
Owned scope:
- tests
Forbidden scope:
- deployment
Objective:
Commit one repair.
"""
    )
    assert not report.valid
    assert report.surface == GNHF_RUNTIME_OBJECTIVE


def test_rejects_hardcoded_username() -> None:
    text = valid_provider_launch().replace(
        '$DevRoot = Join-Path $HOME "Desktop\\dev"',
        '$DevRoot = "C:\\Users\\Cheex\\Desktop\\dev"',
    )
    report = validate_gnhf_launch_artifact(text)
    assert not report.valid
    assert any(item["rule"] == "variable-based user path" for item in report.findings)


def test_rejects_git_before_directory_entry() -> None:
    text = "git status --short\n" + valid_provider_launch()
    report = validate_gnhf_launch_artifact(text)
    assert not report.valid
    assert any(item["rule"] == "directory first" for item in report.findings)


def test_rejects_direct_deepseek_bypass() -> None:
    text = r'''$RepoPath = Join-Path (Join-Path $HOME "Desktop\dev") "AxTask"
Set-Location -LiteralPath $RepoPath
gnhf `
  --agent opencode `
  --model deepseek/deepseek-v4-pro `
  --worktree `
  --max-iterations 8 `
  --max-tokens 800000 `
  --prevent-sleep on `
  --stop-when "A repair is committed and the worktree is clean." `
  "Repo: EndeavorEverlasting/AxTask"
'''
    report = validate_gnhf_launch_artifact(text)
    assert not report.valid
    assert any(item["rule"] == "reviewed provider route" for item in report.findings)


def test_rejects_fictional_deepseek_adapter() -> None:
    text = valid_provider_launch().replace(
        '-Model "deepseek/deepseek-v4-pro"',
        '-Agent deepseek\n  -Model "deepseek/deepseek-v4-pro"',
    )
    report = validate_gnhf_launch_artifact(text)
    assert not report.valid
    assert any(item["rule"] == "truthful adapter" for item in report.findings)


def test_rejects_unbounded_launch() -> None:
    text = valid_provider_launch().replace("  -MaxTokens 800000 `\n", "")
    report = validate_gnhf_launch_artifact(text)
    assert not report.valid
    assert any(item["rule"] == "bounded runtime: tokens" for item in report.findings)
