#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


run("git", "fetch", "--all", "--prune", "--tags")
merge = run(
    "git",
    "-c",
    "user.name=github-actions[bot]",
    "-c",
    "user.email=41898282+github-actions[bot]@users.noreply.github.com",
    "merge",
    "--no-edit",
    "origin/main",
    check=False,
)
if merge.returncode != 0:
    conflicts = run("git", "diff", "--name-only", "--diff-filter=U").stdout.strip().splitlines()
    if conflicts != ["web/prompt-kit/index.html"]:
        raise SystemExit(
            "Unexpected current-main merge conflicts: " + ", ".join(conflicts or ["<none>"])
        )
    run("git", "checkout", "--ours", "web/prompt-kit/index.html")
    run("git", "add", "web/prompt-kit/index.html")
    run(
        "git",
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit",
        "--no-edit",
    )

print("P34 branch reconciled with current origin/main")
