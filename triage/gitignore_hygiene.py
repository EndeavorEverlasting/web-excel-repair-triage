"""Validate that tracked paths comply with artifact and local-junk policy."""
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

from triage.artifact_hygiene_policy import scan_paths
from triage.path_policy import repo_root


@dataclass
class HygieneFinding:
    path: str
    reason: str


@dataclass
class HygieneReport:
    findings: List[HygieneFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "finding_count": len(self.findings),
            "findings": [
                {"path": finding.path, "reason": finding.reason}
                for finding in self.findings
            ],
        }


def _git_ls_files(root: Path) -> List[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git ls-files exited with code {proc.returncode}")
    return [
        item
        for item in proc.stdout.decode("utf-8", errors="replace").split("\0")
        if item
    ]


def scan_tracked_binaries(
    paths: Iterable[str] | None = None,
    *,
    root: Path | None = None,
) -> HygieneReport:
    """Compatibility entry point that now scans every tracked path."""
    root = root or repo_root()
    tracked = list(paths) if paths is not None else _git_ls_files(root)
    findings = [
        HygieneFinding(item.path, item.reason)
        for item in scan_paths(tracked)
    ]
    return HygieneReport(findings=findings)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="triage.gitignore_hygiene",
        description=(
            "Fail when generated/runtime evidence, secrets, crash dumps, or "
            "machine-local junk are tracked outside approved fixture/docs paths."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a path-only JSON report to stdout.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        report = scan_tracked_binaries()
    except RuntimeError as exc:
        print(f"gitignore hygiene: ERROR: {exc}")
        return 2

    if args.json:
        import json

        print(json.dumps(report.to_dict(), indent=2))
    elif report.ok:
        print("gitignore hygiene: OK")
    else:
        print("gitignore hygiene: FAIL")
        for finding in report.findings:
            print(f"  {finding.path}: {finding.reason}")
        print(
            "Move live/generated evidence back to ignored local output, or "
            "commit a sanitized fixture under an approved fixture/docs path."
        )
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
