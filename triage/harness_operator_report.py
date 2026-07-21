"""Emit an English or JSON report for the repository AI harness."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Optional, Sequence
from . import harness_operational_discipline as discipline


def build_report(repo_root: Path) -> dict:
    policy = discipline.load_policy()
    issues = list(discipline.validate_policy(policy))
    issues.extend(discipline.validate_repository(repo_root))
    return {"valid": not issues, "repo_root": str(repo_root.resolve()), "issues": issues, "summary": "Repository AI harness is complete and discoverable." if not issues else "Repository AI harness requires repair."}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.repo_root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"# Harness Operator Report\n\n- Repository: `{report['repo_root']}`\n- Status: {'PASS' if report['valid'] else 'FAIL'}\n- Summary: {report['summary']}")
        for issue in report['issues']:
            print(f"- {issue}")
    return 0 if report['valid'] else 1

if __name__ == "__main__": raise SystemExit(main())
