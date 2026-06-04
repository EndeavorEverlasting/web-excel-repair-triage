"""Validate that git-tracked binary artifacts match repo ignore policy."""
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from triage.path_policy import repo_root

_BINARY_EXTENSIONS = (".xlsx", ".xlsm", ".xls", ".docx", ".zip", ".doc")

# Paths where tracked workbook/archive bytes are allowed (sanitized fixtures only).
_TRACKED_BINARY_ALLOWLIST_PREFIXES: Tuple[str, ...] = (
    "tests/fixtures/",
)

# Paths that must never appear in `git ls-files` for binary types.
_FORBIDDEN_TRACKED_PREFIXES: Tuple[str, ...] = (
    "attached_assets/",
    "Candidates/",
    "Outputs/",
    "outputs/",
    "References/",
    "ArtifactIntake/",
    "Repaired/",
    "artifacts/",
    "billing_runs/",
    "Workbook Payload Artifacts/",
    "RecoveredArtifacts/",
)


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
            "findings": [{"path": f.path, "reason": f.reason} for f in self.findings],
        }


def _git_ls_files(root: Path) -> List[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=str(root),
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _is_binary_tracked(path: str) -> bool:
    lower = path.lower()
    return any(lower.endswith(ext) for ext in _BINARY_EXTENSIONS)


def _allowed_tracked_binary(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _TRACKED_BINARY_ALLOWLIST_PREFIXES)


def scan_tracked_binaries(
    paths: Iterable[str] | None = None,
    *,
    root: Path | None = None,
) -> HygieneReport:
    """Return policy violations for tracked binary artifact paths."""
    root = root or repo_root()
    tracked = list(paths) if paths is not None else _git_ls_files(root)
    report = HygieneReport()

    for rel in tracked:
        if not _is_binary_tracked(rel):
            continue
        if any(rel.startswith(prefix) for prefix in _FORBIDDEN_TRACKED_PREFIXES):
            report.findings.append(
                HygieneFinding(rel, "forbidden_tracked_binary_prefix")
            )
            continue
        if not _allowed_tracked_binary(rel):
            report.findings.append(
                HygieneFinding(rel, "unexpected_tracked_binary_outside_allowlist")
            )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="triage.gitignore_hygiene",
        description="Fail if private/binary artifacts are tracked outside allowlisted fixture paths.",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON report to stdout",
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    report = scan_tracked_binaries()
    if args.json:
        import json

        print(json.dumps(report.to_dict(), indent=2))
    else:
        if report.ok:
            print("gitignore hygiene: OK")
        else:
            print("gitignore hygiene: FAIL")
            for finding in report.findings:
                print(f"  {finding.path}: {finding.reason}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
