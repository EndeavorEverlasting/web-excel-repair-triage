"""Classify prompt execution surfaces and validate copy-ready GNHF launch artifacts.

A regular AI prompt, a compact GNHF runtime objective, and an executable GNHF
launch artifact are intentionally different products.  This module fails closed
when one surface is substituted for another.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional, Sequence

REGULAR_AI_PROMPT = "regular_ai_prompt"
GNHF_RUNTIME_OBJECTIVE = "gnhf_runtime_objective"
GNHF_LAUNCH_ARTIFACT = "gnhf_launch_artifact"
UNKNOWN = "unknown"

HARDCODED_WINDOWS_USER = re.compile(r"(?i)\bC:\\Users\\(?![$%{<])[A-Za-z0-9._-]+")
POWERSHELL_SET_LOCATION = re.compile(r"(?mi)^\s*Set-Location\s+-LiteralPath\s+\$[A-Za-z_][A-Za-z0-9_]*\s*$")
CMD_SET_LOCATION = re.compile(r'(?mi)^\s*cd\s+/d\s+"%~dp0')
GIT_OR_INSTALL = re.compile(r"(?mi)^\s*(?:git\b|npm\b|pnpm\b|winget\b|pwsh\b.*-File\b)")
DIRECT_GNHF = re.compile(r"(?mi)^\s*(?:&\s+)?(?:\$[A-Za-z_][A-Za-z0-9_]*|gnhf)(?:\.ps1|\.cmd)?\s+(?:`\s*)?(?:--agent\b|@)")
PROVIDER_LAUNCHER = "Start-ProviderRoutedGnhfSprint.ps1"

OBJECTIVE_MARKERS = (
    "Repo:",
    "Sprint:",
    "Lane:",
    "Owned scope:",
    "Forbidden scope:",
    "Objective:",
)


@dataclass(frozen=True)
class SurfaceReport:
    surface: str
    valid: bool
    findings: list[dict] = field(default_factory=list)
    proof_ceiling: str = (
        "static prompt-surface and command-shape proof only; local shell, provider, "
        "GNHF, repository mutation, Excel, and Excel for Web remain runtime gates"
    )

    def to_dict(self) -> dict:
        return asdict(self)


def _line_index(text: str, pattern: re.Pattern[str]) -> int | None:
    match = pattern.search(text)
    return match.start() if match else None


def classify_prompt_surface(text: str) -> str:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return UNKNOWN

    has_location = bool(POWERSHELL_SET_LOCATION.search(normalized) or CMD_SET_LOCATION.search(normalized))
    has_launcher = (
        PROVIDER_LAUNCHER in normalized
        or bool(re.search(r"(?mi)^\s*gnhf\s+`?\s*$", normalized))
        or bool(re.search(r"(?mi)^\s*&\s+\$[A-Za-z_][A-Za-z0-9_]*\s+`?\s*$", normalized))
    )
    if has_location and has_launcher:
        return GNHF_LAUNCH_ARTIFACT

    marker_count = sum(marker in normalized for marker in OBJECTIVE_MARKERS)
    if marker_count >= 4 and not has_location:
        return GNHF_RUNTIME_OBJECTIVE

    return REGULAR_AI_PROMPT


def validate_gnhf_launch_artifact(text: str) -> SurfaceReport:
    normalized = text.replace("\r\n", "\n").strip()
    findings: list[dict] = []
    surface = classify_prompt_surface(normalized)

    if surface != GNHF_LAUNCH_ARTIFACT:
        findings.append(
            {
                "rule": "execution surface",
                "expected": GNHF_LAUNCH_ARTIFACT,
                "actual": surface,
                "message": "A GNHF prompt request requires an executable launch artifact, not an AI prompt or objective-only prose.",
            }
        )
        return SurfaceReport(surface=surface, valid=False, findings=findings)

    if HARDCODED_WINDOWS_USER.search(normalized):
        findings.append({"rule": "variable-based user path", "message": "Hardcoded C:\\Users\\<name> is forbidden."})

    ps_location = _line_index(normalized, POWERSHELL_SET_LOCATION)
    cmd_location = _line_index(normalized, CMD_SET_LOCATION)
    location = ps_location if ps_location is not None else cmd_location
    if location is None:
        findings.append({"rule": "directory first", "message": "Set-Location or cd /d is missing."})
    else:
        first_logic = _line_index(normalized, GIT_OR_INSTALL)
        if first_logic is not None and first_logic < location:
            findings.append(
                {
                    "rule": "directory first",
                    "message": "Git, installation, or child-script logic occurs before repository entry.",
                }
            )

    variable_markers = ("$HOME", "$env:LOCALAPPDATA", "$PSScriptRoot", "%USERPROFILE%", "%~dp0")
    if not any(marker in normalized for marker in variable_markers):
        findings.append({"rule": "portable path variables", "message": "No approved user/repository path variable was found."})

    provider_requested = bool(re.search(r"(?i)deepseek(?:/|\b)", normalized))
    if provider_requested:
        if PROVIDER_LAUNCHER not in normalized:
            findings.append(
                {
                    "rule": "reviewed provider route",
                    "message": "DeepSeek launch artifacts must use the AgentSwitchboard provider-routed launcher.",
                }
            )
        if re.search(r"(?i)(?:--agent|-Agent)\s+deepseek\b", normalized):
            findings.append(
                {
                    "rule": "truthful adapter",
                    "message": "DeepSeek is a provider/model, not a native GNHF agent adapter.",
                }
            )
        if not re.search(r"(?i)(?:-Model|--model)\s+[\"']?deepseek/[^\s\"']+", normalized):
            findings.append({"rule": "exact provider/model", "message": "An exact deepseek/<model> route is required."})

    required_controls = {
        "iterations": r"(?i)(?:-MaxIterations|--max-iterations)\s+\d+",
        "tokens": r"(?i)(?:-MaxTokens|--max-tokens)\s+\d+",
        "stop condition": r"(?i)(?:-StopWhen|--stop-when)\s+[\"']",
    }
    for name, pattern in required_controls.items():
        if not re.search(pattern, normalized):
            findings.append({"rule": f"bounded runtime: {name}"})

    if PROVIDER_LAUNCHER in normalized:
        if not re.search(r"(?i)-PromptPath\s+\$[A-Za-z_][A-Za-z0-9_]*", normalized):
            findings.append({"rule": "runtime objective reference", "message": "Provider route must receive a prompt path variable."})
        if not re.search(r"(?i)-ProbeTimeoutSeconds\s+\d+", normalized):
            findings.append({"rule": "bounded provider preflight"})
    else:
        if not re.search(r"(?mi)^\s*--worktree\s+`?\s*$", normalized):
            findings.append({"rule": "worktree isolation"})
        if not re.search(r"(?mi)^\s*--prevent-sleep\s+on\s+`?\s*$", normalized):
            findings.append({"rule": "prevent sleep"})

    if re.search(r"(?i)(?:-PushBranch|--push)(?:\s|$)", normalized):
        findings.append({"rule": "no default push"})
    if re.search(r"(?i)git\s+push\s+--force|git\s+reset\s+--hard|git\s+clean\s+-[a-z]*f", normalized):
        findings.append({"rule": "destructive Git forbidden"})

    if "process exit zero" not in normalized.lower() and "commit" not in normalized.lower():
        findings.append(
            {
                "rule": "delivery proof",
                "message": "Launch artifact must require a tracked commit or explicitly reject exit-code-only success.",
            }
        )

    return SurfaceReport(surface=surface, valid=not findings, findings=findings)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="UTF-8 prompt or launch artifact")
    parser.add_argument("--classify", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    text = args.path.read_text(encoding="utf-8")
    if args.classify:
        payload = {"path": str(args.path), "surface": classify_prompt_surface(text)}
        print(json.dumps(payload, indent=2) if args.json else payload["surface"])
        return 0

    report = validate_gnhf_launch_artifact(text)
    print(json.dumps(report.to_dict(), indent=2) if args.json else f"surface={report.surface} valid={str(report.valid).lower()}")
    if not args.json:
        for finding in report.findings:
            print(f"- {finding}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
