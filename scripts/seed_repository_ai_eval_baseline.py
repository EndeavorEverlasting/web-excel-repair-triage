#!/usr/bin/env python3
"""Seed a repository AI eval baseline report from an exact Git commit."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (ROOT / "Outputs").resolve()
DEFAULT_OUTPUT = ROOT / "Outputs/repository-ai-eval-baseline.json"
REPORT_SCHEMA = "repository-ai-eval-report/v1"


class BaselineSeedError(RuntimeError):
    pass


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def resolve_output(path: Path) -> Path:
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(OUTPUTS)
    except ValueError as exc:
        raise BaselineSeedError(f"baseline output must remain under Outputs/: {resolved}") from exc
    if relative == Path("."):
        raise BaselineSeedError("baseline output must name a file below Outputs/")
    return resolved


def run_git(*args: str, cwd: Path = ROOT, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BaselineSeedError(f"git {' '.join(args)} failed to execute: {exc}") from exc


def resolve_commit(ref: str) -> str:
    result = run_git("rev-parse", "--verify", f"{ref}^{{commit}}")
    value = result.stdout.strip()
    if result.returncode != 0 or len(value) != 40:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise BaselineSeedError(f"cannot resolve baseline ref {ref!r}: {detail}")
    return value


def current_head() -> str:
    result = run_git("rev-parse", "HEAD")
    value = result.stdout.strip()
    if result.returncode != 0 or len(value) != 40:
        raise BaselineSeedError("cannot resolve current HEAD")
    return value


def validate_baseline_report(payload: dict[str, Any], expected_sha: str) -> None:
    if payload.get("schema_version") != REPORT_SCHEMA:
        raise BaselineSeedError("seeded baseline report has unsupported schema")
    if payload.get("commit_sha") != expected_sha:
        raise BaselineSeedError(
            "seeded baseline report commit does not match resolved baseline ref: "
            f"expected={expected_sha} actual={payload.get('commit_sha')}"
        )
    if payload.get("status") != "PASS":
        raise BaselineSeedError(
            "refusing to seed a degraded baseline; refreshed baseline ref must evaluate PASS"
        )


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        temporary.replace(path)
    except OSError as exc:
        raise BaselineSeedError(f"failed to write baseline report atomically: {exc}") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                # The primary write error, if any, is already converted above. A stale temp file is
                # preferable to replacing that controlled error with a cleanup traceback.
                pass


def seed_baseline(ref: str, output: Path, timeout_seconds: int) -> dict[str, Any]:
    baseline_sha = resolve_commit(ref)
    candidate_sha = current_head()
    if baseline_sha == candidate_sha:
        raise BaselineSeedError(
            "baseline ref resolves to the candidate HEAD; choose refreshed default-branch history instead"
        )

    destination = resolve_output(output)
    runner_timeout = max(300, min(timeout_seconds * 4 + 60, 1100))

    with tempfile.TemporaryDirectory(prefix="repository-ai-eval-baseline-") as tmp:
        worktree_path = Path(tmp) / "worktree"
        add = run_git("worktree", "add", "--detach", str(worktree_path), baseline_sha, timeout=90)
        if add.returncode != 0:
            detail = add.stderr.strip() or add.stdout.strip() or f"exit {add.returncode}"
            raise BaselineSeedError(f"failed to create detached baseline worktree: {detail}")

        try:
            relative_report = Path("Outputs/repository-ai-eval-baseline.json")
            command = [
                sys.executable,
                "scripts/run_repository_ai_evals.py",
                "--output",
                str(relative_report),
                "--timeout-seconds",
                str(timeout_seconds),
                "--summary",
            ]
            try:
                evaluated = subprocess.run(
                    command,
                    cwd=worktree_path,
                    text=True,
                    capture_output=True,
                    timeout=runner_timeout,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise BaselineSeedError(f"baseline evaluator failed to execute: {exc}") from exc

            if evaluated.returncode != 0:
                detail = _text(evaluated.stderr).strip() or _text(evaluated.stdout).strip()
                raise BaselineSeedError(
                    f"refreshed baseline ref did not produce a passing repository AI eval: {detail}"
                )

            source = worktree_path / relative_report
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise BaselineSeedError("baseline evaluator did not produce its report") from exc
            except json.JSONDecodeError as exc:
                raise BaselineSeedError(f"baseline evaluator produced invalid JSON: {exc}") from exc
            except OSError as exc:
                raise BaselineSeedError(f"failed to read seeded baseline report: {exc}") from exc
            if not isinstance(payload, dict):
                raise BaselineSeedError("baseline evaluator report must be a JSON object")
            validate_baseline_report(payload, baseline_sha)
            write_json_atomic(destination, payload)
        finally:
            remove = run_git("worktree", "remove", "--force", str(worktree_path), timeout=90)
            if remove.returncode != 0:
                run_git("worktree", "prune", timeout=30)

    return {
        "status": "PASS",
        "baseline_ref": ref,
        "baseline_sha": baseline_sha,
        "candidate_sha": candidate_sha,
        "output": str(destination.relative_to(ROOT)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    if args.timeout_seconds < 1:
        print("repository AI eval baseline seed error: timeout must be positive", file=sys.stderr)
        return 2

    try:
        result = seed_baseline(args.baseline_ref, args.output, args.timeout_seconds)
    except BaselineSeedError as exc:
        print(f"repository AI eval baseline seed error: {exc}", file=sys.stderr)
        return 2

    if args.summary:
        print(
            "repository_ai_eval_baseline_seed "
            f"status={result['status']} ref={result['baseline_ref']} "
            f"sha={result['baseline_sha']} output={result['output']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
