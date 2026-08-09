#!/usr/bin/env python3
"""Resolve a shell-safe Prompt Kit route from repository, profile, target, and intent."""
from __future__ import annotations

import argparse
import json
import ntpath
import posixpath
import re
from dataclasses import asdict, dataclass

PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
LAUNCHER_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/"
TRIAGE_REPO = "EndeavorEverlasting/web-excel-repair-triage"
AGENT_SWITCHBOARD_REPO = "EndeavorEverlasting/AgentSwitchboard"
_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")


@dataclass
class Route:
    schema: str
    active_repository: str
    related_repository: str
    host_profile: str
    shell: str
    target_profile: str
    intent: str
    status: str
    execution_surface: str | None
    associated_repo_path: str | None
    path_source: str | None
    command: str | None
    next_action: str
    proof_ceiling: str


def _short_sha(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not _SHA_RE.fullmatch(value):
        raise ValueError("main_sha must contain only 7-64 hexadecimal characters")
    return value[:8].lower()


def _url(base: str, main_sha: str | None) -> str:
    short = _short_sha(main_sha)
    return f"{base}?v={short}" if short else base


def _ps_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sh_literal(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _associated_path(
    profile: str,
    triage_repo: str | None,
    agent_switchboard_repo: str | None,
) -> tuple[str | None, str | None]:
    if triage_repo:
        return triage_repo, "explicit-triage-path"
    if agent_switchboard_repo:
        if profile == "windows":
            return (
                ntpath.join(
                    ntpath.dirname(agent_switchboard_repo.rstrip("\\/")),
                    "web-excel-repair-triage",
                ),
                "agent-switchboard-sibling",
            )
        if profile == "android":
            return (
                posixpath.join(
                    posixpath.dirname(agent_switchboard_repo.rstrip("/")),
                    "web-excel-repair-triage",
                ),
                "agent-switchboard-sibling",
            )
    if profile == "windows":
        return r"%USERPROFILE%\dev\web-excel-repair-triage", "profile-default"
    if profile == "android":
        return "$HOME/web-excel-repair-triage", "profile-default"
    return None, None


def _windows_path_expression(path: str, path_source: str | None) -> str:
    if path_source == "profile-default":
        return "(Join-Path $env:USERPROFILE 'dev\\web-excel-repair-triage')"
    return _ps_literal(path)


def _android_path_expression(path: str, path_source: str | None) -> str:
    if path_source == "profile-default":
        return '"$HOME/web-excel-repair-triage"'
    return _sh_literal(path)


def _blocked(
    host_profile: str,
    shell: str,
    target_profile: str,
    intent: str,
    next_action: str,
    *,
    associated_repo_path: str | None = None,
    path_source: str | None = None,
) -> Route:
    return Route(
        schema="prompt-kit-profile-route/v1",
        active_repository=TRIAGE_REPO,
        related_repository=AGENT_SWITCHBOARD_REPO,
        host_profile=host_profile,
        shell=shell,
        target_profile=target_profile,
        intent=intent,
        status="BLOCKED",
        execution_surface=None,
        associated_repo_path=associated_repo_path,
        path_source=path_source,
        command=None,
        next_action=next_action,
        proof_ceiling="Routing classification only; no command executed.",
    )


def resolve_route(
    host_profile: str,
    shell: str,
    target_profile: str,
    intent: str,
    *,
    triage_repo: str | None = None,
    agent_switchboard_repo: str | None = None,
    main_sha: str | None = None,
) -> Route:
    expected_shell = {
        "windows": "powershell",
        "android": "termux-bash",
        "browser": "browser",
    }[host_profile]
    target_surface = {
        "windows": "windows-powershell",
        "android": "android-termux",
        "browser": "browser",
    }[target_profile]
    use_url = _url(PUBLIC_URL, main_sha)
    install_url = _url(LAUNCHER_URL, main_sha)
    associated_path, path_source = _associated_path(
        target_profile, triage_repo, agent_switchboard_repo
    )

    if shell != expected_shell:
        return _blocked(
            host_profile,
            shell,
            target_profile,
            intent,
            f"Use the shell associated with host profile {host_profile}: {expected_shell}.",
        )

    if target_profile != host_profile:
        return Route(
            schema="prompt-kit-profile-route/v1",
            active_repository=TRIAGE_REPO,
            related_repository=AGENT_SWITCHBOARD_REPO,
            host_profile=host_profile,
            shell=shell,
            target_profile=target_profile,
            intent=intent,
            status="HANDOFF",
            execution_surface=target_surface,
            associated_repo_path=(
                associated_path if intent in {"edit", "local-app"} else None
            ),
            path_source=path_source if intent in {"edit", "local-app"} else None,
            command=None,
            next_action=(
                f"Continue on the {target_profile} device/surface ({target_surface}); "
                f"do not execute {target_profile}-specific shell text in the current {shell} session."
            ),
            proof_ceiling=(
                "Cross-profile handoff classification only; target-device execution is unproved."
            ),
        )

    if host_profile == "browser" and intent in {"edit", "local-app"}:
        return _blocked(
            host_profile,
            shell,
            target_profile,
            intent,
            "Browser-only execution cannot perform local repository or launcher work; hand off to a Windows or Android local profile.",
        )

    command: str | None
    if intent in {"use", "install"}:
        route_url = install_url if intent == "install" else use_url
        if host_profile == "windows":
            command = f"Start-Process {_ps_literal(route_url)}"
        elif host_profile == "android":
            command = f"termux-open-url {_sh_literal(route_url)}"
        else:
            command = route_url
        associated_path = None
        path_source = None
    elif intent == "local-app":
        if host_profile != "windows":
            return _blocked(
                host_profile,
                shell,
                target_profile,
                intent,
                "The stable local-app launcher is Windows-only; use browser use or an editable checkout on this profile.",
                associated_repo_path=associated_path,
                path_source=path_source,
            )
        assert associated_path is not None
        base_expr = _windows_path_expression(associated_path, path_source)
        command = f"& (Join-Path {base_expr} 'Open-Latest-PromptKit.cmd')"
    elif intent == "edit":
        assert associated_path is not None
        if host_profile == "windows":
            command = (
                "Set-Location -LiteralPath "
                + _windows_path_expression(associated_path, path_source)
            )
        elif host_profile == "android":
            command = "cd " + _android_path_expression(associated_path, path_source)
        else:
            return _blocked(
                host_profile,
                shell,
                target_profile,
                intent,
                "Browser-only execution cannot edit a repository; hand off to a supported local profile.",
            )
    else:
        raise ValueError(f"Unsupported intent: {intent}")

    return Route(
        schema="prompt-kit-profile-route/v1",
        active_repository=TRIAGE_REPO,
        related_repository=AGENT_SWITCHBOARD_REPO,
        host_profile=host_profile,
        shell=shell,
        target_profile=target_profile,
        intent=intent,
        status="ROUTED",
        execution_surface=target_surface,
        associated_repo_path=associated_path,
        path_source=path_source,
        command=command,
        next_action=(
            "Execute only on the declared execution surface and then capture runtime proof separately."
        ),
        proof_ceiling=(
            "Deterministic route and path resolution only; filesystem, browser, Git, launcher, and device runtime remain unproved."
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host-profile", choices=("windows", "android", "browser"), required=True
    )
    parser.add_argument(
        "--shell", choices=("powershell", "termux-bash", "browser"), required=True
    )
    parser.add_argument(
        "--target-profile", choices=("windows", "android", "browser"), required=True
    )
    parser.add_argument(
        "--intent", choices=("use", "install", "local-app", "edit"), required=True
    )
    parser.add_argument("--triage-repo")
    parser.add_argument("--agent-switchboard-repo")
    parser.add_argument("--main-sha")
    args = parser.parse_args()
    try:
        route = resolve_route(
            args.host_profile,
            args.shell,
            args.target_profile,
            args.intent,
            triage_repo=args.triage_repo,
            agent_switchboard_repo=args.agent_switchboard_repo,
            main_sha=args.main_sha,
        )
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "schema": "prompt-kit-profile-route-error/v1",
                    "status": "BLOCKED",
                    "error": str(exc),
                },
                indent=2,
            )
        )
        return 2
    print(json.dumps(asdict(route), indent=2))
    return 0 if route.status == "ROUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
