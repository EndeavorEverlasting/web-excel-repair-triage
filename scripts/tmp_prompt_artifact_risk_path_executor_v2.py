#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tmp_prompt_artifact_risk_path_executor as base

ROOT = Path(__file__).resolve().parents[1]


def patch_p50() -> None:
    path = ROOT / "docs" / "prompts.json"
    prompts = json.loads(path.read_text(encoding="utf-8"))
    p50 = next(prompt for prompt in prompts if prompt.get("id") == "P50")
    copy_content = '''PROMPT SURFACE: STANDARD AI. THIS IS NOT A GOODNIGHT, HAVE FUN (GNHF) PROMPT.

ESTABLISH THE MACHINE, SHELL, LOCAL REPOSITORY ROOT, AND REMOTE FRESHNESS BEFORE GIVING OR RUNNING REPOSITORY COMMANDS.

Repository: xyz_repo_url_or_name
Known local path, if any: xyz_known_or_unknown
Requested task: xyz_task

MISSION
Prevent path, shell, platform, worktree, and stale-checkout assumptions from contaminating later work. Treat execution context as evidence that must be proved on the current box, not remembered from another machine, username, operating system, terminal, or prior chat.

MACHINE / OS / SHELL GATE
1. Resolve the actual execution environment before constructing commands: operating system/platform, active shell or command host, current directory, and Git availability. Distinguish Windows PowerShell, PowerShell 7+, CMD, Git Bash, WSL/Linux, macOS, and other materially different environments when present.
2. Do not infer OS, shell, path separator, home directory, drive letter, username, quoting rules, executable names, or privilege model from the repository name, a previous machine, or remembered context.
3. Emit commands in the syntax of the verified shell. Do not hand Bash syntax to PowerShell/CMD, Windows paths to a Linux/WSL context, or shell-specific quoting to the wrong host.
4. If the environment changes mid-task (new terminal, SSH/RDP target, container, WSL boundary, admin box, CI runner), re-run the environment and directory gates before continuing.

DIRECTORY GATE
1. Do not assume the current directory, remembered path, repository name, Desktop path, or newest checkout is correct.
2. Resolve the intended checkout by matching its remote to the requested repository and inspecting git worktree list when available.
3. When the root is reachable, verify it with git rev-parse --show-toplevel and git remote get-url origin.
4. When no matching checkout exists, route to P61 Existing Repository Clone + Working-Directory Bootstrapper rather than inventing a path.
5. When the root cannot be proven, return or run bounded discovery only. Do not start tests, builds, mutations, commits, cleanup, or deployment against an unverified directory.
6. After resolution, make the first executable task command Set-Location -LiteralPath "<verified-root>" in PowerShell or cd -- "<verified-root>" in Bash, then verify git rev-parse --show-toplevel again.

REMOTE FRESHNESS GATE
1. After the root is proven and before branch-sensitive analysis or iteration, inspect git status, branch, tracking branch, worktrees, and remotes.
2. Refresh remote truth with git fetch --all --prune --tags when the remote is reachable. Resolve the actual remote default branch from provider metadata or refs/remotes/origin/HEAD; do not assume main/master or reuse a remembered SHA.
3. Compare current HEAD, its tracking branch, and the refreshed default-branch floor. Inspect open/recent overlapping branches or PRs when the task could collide with them.
4. If a clean tracking branch is behind-only, use git pull --ff-only or the repository-approved equivalent. If dirty, diverged, detached, or separately owned work exists, preserve it and reconcile or isolate with a worktree; never force-reset merely to become current.
5. If remote freshness cannot be proved, state the exact limitation. Do not silently perform branch-sensitive mutation, build/repair decisions, or certification from a stale assumed floor.

COMMAND EMISSION GATE
- Every later command block must be valid for the verified OS/shell and begin from, or explicitly enter, the verified repository root.
- Prefer environment variables, repository-relative paths, manifests, and tracked launchers over person-specific absolute paths.
- Recheck root and shell before commands copied to another box or execution profile.

HARNESS CONTEXT
Name repo, branch or worktree, PR or sprint, lane, owned scope, forbidden scope, expected artifacts, validation order, proof level, and proof ceiling.
Search existing contracts, helpers, validators, scripts, manifests, and output patterns before inventing.

FINAL RESPONSE
Return the verified environment profile (OS/platform + shell), root evidence, root/remote/default-branch freshness evidence, branch/worktree state, the shell-correct directory-change command, and then the bounded task commands in execution order. Name any unproved environment or freshness assumption instead of guessing.'''
    p50.update(
        sprintRole="Resolve and verify the machine environment, local repository directory, shell, and remote freshness before emitting or executing repository commands",
        useWhen="The repository is known but the exact local checkout, operating system/shell context, worktree, or remote freshness is unknown, stale, or easy to confuse with another box or checkout.",
        inspectFirst="Repository URL or name; actual OS/platform and active shell; current directory; Git availability; Git worktrees; candidate remotes; branch/tracking/default-branch state; remote freshness; and any operator-supplied path.",
        expectedOutput="One verified execution profile (OS/platform + shell), one verified repository root, root/remote/default-branch evidence, reconciled freshness state, a shell-matched directory change, branch/worktree evidence, then bounded task commands.",
        nextStep="If no matching checkout exists, run P61. Otherwise continue to the task-specific prompt only after the environment, directory, and freshness gates pass; preserve dirty/diverged work instead of resetting it.",
        proofGate="The execution OS/platform and shell are explicitly resolved; the intended root is matched to the requested remote and git rev-parse --show-toplevel; remote refs/default branch are refreshed when reachable and compared with current/tracking HEAD; clean behind-only state is fast-forwarded or non-clean/diverged work is preserved and isolated/reconciled; and later commands use the verified shell and root rather than remembered machine paths.",
        keywords=["directory", "command guard", "directory first", "repo command", "repository path", "local repository", "local repo path", "working directory", "operating system", "os", "shell", "powershell", "cmd", "bash", "wsl", "worktree", "git fetch", "pull latest", "remote freshness", "stale checkout", "path problems"],
        copyContent=copy_content,
    )
    path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


base.patch_p50 = patch_p50
raise SystemExit(base.main())
