#!/usr/bin/env python3
"""Aggregate safe offline harness checks into an honest PASS/SKIP/FAIL matrix."""
from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

PROOF_CEILING = (
    "Offline/synthetic repository validation only; no live runtime, browser, launcher, "
    "network, target, save/account, or production proof."
)
REQUIRED_FILES = (
    "AGENTS.md",
    "CODEBASE_MAP.md",
    "WORKFLOW.md",
    "ARTIFACT_REGISTRY.md",
    "harness/manifest.v1.json",
    "harness/workflows.v1.json",
    "harness/artifacts.v1.json",
    "harness/validators.v1.json",
    "scripts/validate_harness.py",
    ".githooks/pre-commit",
    ".githooks/pre-push",
)
FORBIDDEN_EXTERNAL_TOKENS = (
    "start-process",
    "xdg-open",
    "open ",
    "webbrowser",
    "selenium",
    "playwright",
    "curl ",
    "wget ",
    "invoke-webrequest",
    "requests.",
    "git clean",
    "reset --hard",
)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    reason: str
    details: list[str]


Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def detect_repo_root() -> Path:
    candidate = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("unable to resolve repository root with git rev-parse")
    return Path(result.stdout.strip()).resolve()


def safe_runner(command: Sequence[str], root: Path) -> subprocess.CompletedProcess[str]:
    text = " ".join(command).lower()
    if any(token in text for token in FORBIDDEN_EXTERNAL_TOKENS):
        raise RuntimeError(f"unsafe command rejected by synthetic harness: {' '.join(command)}")
    allowed = (
        command[:2] == ["git", "branch"],
        command[:2] == ["git", "rev-parse"],
        len(command) >= 2 and command[0] == sys.executable and command[1].endswith("validate_harness.py"),
        len(command) >= 3 and command[:3] == [sys.executable, "-m", "triage.gitignore_hygiene"],
    )
    if not any(allowed):
        raise RuntimeError(f"command is not in the offline allowlist: {' '.join(command)}")
    return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)


def preserve_existing_output(root: Path, target: Path) -> Path | None:
    """Copy an existing runtime receipt to a timestamped Outputs/backups path."""
    if not target.is_file():
        return None
    outputs = (root / "Outputs").resolve()
    resolved = target.resolve()
    try:
        relative = resolved.relative_to(outputs)
    except ValueError as exc:
        raise ValueError("receipt preservation is restricted to Outputs/") from exc
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = outputs / "backups" / "app-harness-validation" / stamp / relative
    backup.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(resolved, backup)
    return backup


def _result(name: str, ok: bool, reason: str, details: list[str] | None = None) -> Check:
    return Check(name, "PASS" if ok else "FAIL", reason, details or [])


def check_required_files(root: Path, runner: Runner) -> Check:
    missing = [path for path in REQUIRED_FILES if not (root / path).is_file()]
    if missing:
        return _result("required files", False, "missing_required_files", missing)
    nested_report = root / "Outputs" / "harness-completeness-report.json"
    try:
        backup = preserve_existing_output(root, nested_report)
    except ValueError as exc:
        return _result("required files", False, "nested_receipt_backup_failed", [str(exc)])
    command = [
        sys.executable,
        str(root / "scripts" / "validate_harness.py"),
        "--report",
        str(nested_report),
    ]
    result = runner(command, root)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return _result("required files", False, "required_harness_validator_failed", [detail][:1])
    details = [f"previous_receipt_backup={backup.relative_to(root).as_posix()}"] if backup else []
    return _result("required files", True, "required_harness_validator_passed", details)


def check_run_context(root: Path, runner: Runner, env: Mapping[str, str]) -> tuple[Check, str, str]:
    branch_result = runner(["git", "branch", "--show-current"], root)
    commit_result = runner(["git", "rev-parse", "HEAD"], root)
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    branch = branch or env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME") or "detached"
    commit = commit_result.stdout.strip() if commit_result.returncode == 0 else ""
    ok = branch_result.returncode == 0 and commit_result.returncode == 0 and bool(commit)
    return _result("run context", ok, "git_identity_resolved" if ok else "git_identity_unavailable", [f"branch={branch}", f"commit={commit or 'unknown'}"]), branch, commit or "unknown"


def check_artifact_registry(root: Path) -> Check:
    path = root / "harness" / "artifacts.v1.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        artifacts = payload.get("artifacts")
        ids = {item.get("id") for item in artifacts if isinstance(item, dict)} if isinstance(artifacts, list) else set()
        required = {
            "harness-control-plane",
            "operator-harness-state",
            "harness-completeness-report",
            "app-harness-validation-report",
        }
        ok = payload.get("schema_version") == "web-excel-artifacts/v1" and required <= ids
    except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        return _result("artifact registry", False, "artifact_registry_invalid", [str(exc)])
    return _result("artifact registry", ok, "artifact_registry_parseable" if ok else "artifact_registry_contract_missing")


def check_report_renderer(root: Path) -> Check:
    if not (root / "harness" / "reports" / "CURRENT_STATE.md").is_file():
        return _result("report renderer", False, "operator_report_missing")
    sample = render_matrix([Check("probe", "PASS", "ok", [])], "main", "0" * 40)
    ok = sample.startswith("APP HARNESS VALIDATION\n") and "[PASS] probe" in sample and "Result: 1 passed / 0 skipped / 0 failed" in sample
    return _result("report renderer", ok, "matrix_and_summary_renderer_ready" if ok else "matrix_renderer_broken")


def check_optional_mcp(root: Path, env: Mapping[str, str]) -> Check:
    if env.get("HARNESS_LSP_PROJECT_LOADED") != "1":
        return Check("optional MCP symbol smoke", "SKIP", "lsp_project_not_loaded", [])
    path = root / "mcp_server.py"
    if not path.is_file():
        return Check("optional MCP symbol smoke", "SKIP", "mcp_server_not_present", [])
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return _result("optional MCP symbol smoke", False, "mcp_module_not_parseable", [str(exc)])
    symbols = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    return _result("optional MCP symbol smoke", bool(symbols), "static_mcp_symbols_readable" if symbols else "mcp_symbols_missing", symbols[:5])


def check_hook_hygiene(root: Path, runner: Runner) -> Check:
    try:
        validators = json.loads((root / "harness" / "validators.v1.json").read_text(encoding="utf-8"))
        hooks = validators.get("hooks", {})
        hook_paths = [entry.get("path") for entry in hooks.values() if isinstance(entry, dict)] if isinstance(hooks, dict) else []
        missing = [path for path in hook_paths if not isinstance(path, str) or not (root / path).is_file()]
        if missing or len(hook_paths) < 2:
            return _result("hook hygiene", False, "registered_hooks_missing", [str(item) for item in missing])
    except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        return _result("hook hygiene", False, "validator_registry_invalid", [str(exc)])
    result = runner([sys.executable, "-m", "triage.gitignore_hygiene"], root)
    if result.returncode != 0:
        return _result("hook hygiene", False, "artifact_hygiene_failed", [(result.stderr or result.stdout).strip()][:1])
    return _result("hook hygiene", True, "registered_hooks_and_artifact_hygiene_passed")


def render_matrix(checks: Sequence[Check], branch: str, commit: str) -> str:
    passed = sum(item.status == "PASS" for item in checks)
    skipped = sum(item.status == "SKIP" for item in checks)
    failed = sum(item.status == "FAIL" for item in checks)
    lines = ["APP HARNESS VALIDATION", f"Branch: {branch}", f"Commit: {commit}"]
    for item in checks:
        suffix = f": {item.reason}" if item.status != "PASS" else ""
        lines.append(f"[{item.status}] {item.name}{suffix}")
    lines.append(f"Result: {passed} passed / {skipped} skipped / {failed} failed")
    lines.append(f"Proof ceiling: {PROOF_CEILING}")
    return "\n".join(lines)


def validate(root: Path, runner: Runner = safe_runner, env: Mapping[str, str] | None = None) -> dict[str, object]:
    environment = dict(os.environ if env is None else env)
    run_context, branch, commit = check_run_context(root, runner, environment)
    checks = [
        check_required_files(root, runner),
        run_context,
        check_artifact_registry(root),
        check_report_renderer(root),
        check_optional_mcp(root, environment),
        check_hook_hygiene(root, runner),
    ]
    return {
        "schema_version": "app-harness-validation/v1",
        "repository_root": str(root),
        "branch": branch,
        "commit": commit,
        "proof_ceiling": PROOF_CEILING,
        "checks": [asdict(item) for item in checks],
        "summary": {
            "passed": sum(item.status == "PASS" for item in checks),
            "skipped": sum(item.status == "SKIP" for item in checks),
            "failed": sum(item.status == "FAIL" for item in checks),
        },
    }


def output_path(root: Path, value: str) -> Path:
    path = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    outputs = (root / "Outputs").resolve()
    try:
        path.relative_to(outputs)
    except ValueError as exc:
        raise ValueError("JSON output must remain under Outputs/") from exc
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="Outputs/app-harness-validation.json")
    args = parser.parse_args()
    try:
        root = detect_repo_root()
        report = validate(root)
        target = output_path(root, args.output)
        backup = preserve_existing_output(root, target)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"APP HARNESS VALIDATION\n[FAIL] bootstrap: {exc}", file=sys.stderr)
        return 2
    if backup:
        report["previous_receipt_backup"] = backup.relative_to(root).as_posix()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    checks = [Check(**item) for item in report["checks"]]
    print(render_matrix(checks, str(report["branch"]), str(report["commit"])))
    if backup:
        print(f"Previous JSON: {backup}")
    print(f"JSON: {target}")
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
