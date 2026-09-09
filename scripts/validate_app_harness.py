#!/usr/bin/env python3
"""Aggregate safe offline harness checks into an honest PASS/SKIP/FAIL matrix."""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

SCHEMA_VERSION = "app-harness-validation/v2"
PROOF_LEVEL = "offline_synthetic"
CANONICAL_COMMAND = "python scripts/validate_app_harness.py --output Outputs/app-harness-validation.json"
PROOF_CEILING = (
    "Offline/synthetic repository harness validation only; no live runtime, browser, launcher, "
    "network, target, save/account, provider-runtime, deployment, or production proof."
)
P11_ID = "P11"
P11_NAME = "End-to-End Harness Validator"
P11_PURPOSE = "Aggregate safe repository harness proof into one exact-head offline/synthetic PASS/SKIP/FAIL gate."
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
VALID_REQUIREMENTS = {"REQUIRED", "OPTIONAL", "ENVIRONMENT_BLOCKED", "INAPPLICABLE"}
VALID_STATUSES = {"PASS", "SKIP", "FAIL"}


@dataclass(frozen=True)
class Check:
    id: str
    name: str
    requirement: str
    status: str
    reason: str
    details: list[str]

    def __post_init__(self) -> None:
        if self.requirement not in VALID_REQUIREMENTS:
            raise ValueError(f"invalid requirement: {self.requirement}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status: {self.status}")


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
    command = tuple(command)
    allowed = (
        command == ("git", "branch", "--show-current"),
        command == ("git", "rev-parse", "HEAD"),
        command == (
            sys.executable,
            str(root / "scripts" / "validate_harness.py"),
            "--report",
            str(root / "Outputs" / "harness-completeness-report.json"),
        ),
        command == (sys.executable, "-m", "triage.gitignore_hygiene"),
    )
    if not any(allowed):
        raise RuntimeError(f"command is not in the offline allowlist: {' '.join(command)}")
    return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)


def result(check_id: str, name: str, ok: bool, reason: str, details: list[str] | None = None) -> Check:
    return Check(check_id, name, "REQUIRED", "PASS" if ok else "FAIL", reason, details or [])


def check_required_files(root: Path, runner: Runner) -> Check:
    missing = [path for path in REQUIRED_FILES if not (root / path).is_file()]
    if missing:
        return result("required_files", "required files", False, "missing_required_files", missing)
    nested_report = root / "Outputs" / "harness-completeness-report.json"
    nested_report.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(root / "scripts" / "validate_harness.py"), "--report", str(nested_report)]
    completed = runner(command, root)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        return result("required_files", "required files", False, "required_harness_validator_failed", [detail][:1])
    return result("required_files", "required files", True, "required_harness_validator_passed")


def check_run_context(root: Path, runner: Runner, env: Mapping[str, str]) -> tuple[Check, str, str]:
    branch_result = runner(["git", "branch", "--show-current"], root)
    commit_result = runner(["git", "rev-parse", "HEAD"], root)
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    branch = branch or env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME") or "detached"
    commit = commit_result.stdout.strip() if commit_result.returncode == 0 else ""
    ok = branch_result.returncode == 0 and commit_result.returncode == 0 and len(commit) == 40
    return (
        result(
            "run_context",
            "run context",
            ok,
            "git_identity_resolved" if ok else "git_identity_unavailable",
            [f"branch={branch}", f"head_sha={commit or 'unknown'}"],
        ),
        branch,
        commit or "unknown",
    )


def check_artifact_registry(root: Path) -> Check:
    path = root / "harness" / "artifacts.v1.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        artifacts = payload.get("artifacts", [])
        ids = {item.get("id") for item in artifacts if isinstance(item, dict)}
        required = {"harness-control-plane", "operator-harness-state", "harness-completeness-report", "app-harness-validation-report"}
        ok = payload.get("schema_version") == "web-excel-artifacts/v1" and required <= ids
    except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        return result("artifact_registry", "artifact registry", False, "artifact_registry_invalid", [str(exc)])
    return result(
        "artifact_registry",
        "artifact registry",
        ok,
        "artifact_registry_parseable" if ok else "artifact_registry_contract_missing",
    )


def prompt_identity(root: Path) -> dict[str, str]:
    path = root / "docs" / "prompts.json"
    try:
        prompts = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"prompt registry unavailable: {exc}") from exc
    record = next((item for item in prompts if isinstance(item, dict) and item.get("id") == P11_ID), None)
    if not record:
        raise RuntimeError("P11 missing from canonical prompt registry")
    if record.get("name") != P11_NAME:
        raise RuntimeError(f"P11 canonical name drifted: {record.get('name')!r}")
    purpose = str(record.get("sprintRole", "")).strip()
    if not purpose:
        raise RuntimeError("P11 canonical purpose/sprintRole is empty")
    return {"id": P11_ID, "name": P11_NAME, "purpose": purpose}


def check_report_renderer(root: Path) -> Check:
    if not (root / "harness" / "reports" / "CURRENT_STATE.md").is_file():
        return result("report_renderer", "report renderer", False, "operator_report_missing")
    try:
        identity = prompt_identity(root)
    except RuntimeError as exc:
        return result("report_renderer", "report renderer", False, "prompt_identity_contract_failed", [str(exc)])
    sample = render_matrix([Check("probe", "probe", "REQUIRED", "PASS", "ok", [])], "main", "0" * 40)
    ok = (
        sample.startswith("APP HARNESS VALIDATION\n")
        and "[PASS] probe" in sample
        and "Result: 1 passed / 0 skipped / 0 failed" in sample
        and identity == {"id": P11_ID, "name": P11_NAME, "purpose": identity["purpose"]}
    )
    return result(
        "report_renderer",
        "report renderer",
        ok,
        "matrix_prompt_identity_and_summary_ready" if ok else "matrix_renderer_broken",
        [f"prompt={identity['id']} · {identity['name']} — {identity['purpose']}"] if ok else [],
    )


def check_optional_mcp(root: Path, env: Mapping[str, str]) -> Check:
    if env.get("HARNESS_LSP_PROJECT_LOADED") != "1":
        return Check("optional_mcp_symbol_smoke", "optional MCP symbol smoke", "OPTIONAL", "SKIP", "lsp_project_not_loaded", [])
    path = root / "mcp_server.py"
    if not path.is_file():
        return Check("optional_mcp_symbol_smoke", "optional MCP symbol smoke", "OPTIONAL", "SKIP", "mcp_server_not_present", [])
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return Check("optional_mcp_symbol_smoke", "optional MCP symbol smoke", "OPTIONAL", "FAIL", "mcp_module_not_parseable", [str(exc)])
    symbols = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    return Check(
        "optional_mcp_symbol_smoke",
        "optional MCP symbol smoke",
        "OPTIONAL",
        "PASS" if symbols else "FAIL",
        "static_mcp_symbols_readable" if symbols else "mcp_symbols_missing",
        symbols[:5],
    )


def check_hook_hygiene(root: Path, runner: Runner) -> Check:
    try:
        validators = json.loads((root / "harness" / "validators.v1.json").read_text(encoding="utf-8"))
        hooks = validators.get("hooks", {})
        paths = [entry.get("path") for entry in hooks.values() if isinstance(entry, dict)] if isinstance(hooks, dict) else []
        missing = [path for path in paths if not isinstance(path, str) or not (root / path).is_file()]
        if missing or len(paths) < 2:
            return result("hook_hygiene", "hook hygiene", False, "registered_hooks_missing", [str(item) for item in missing])
    except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        return result("hook_hygiene", "hook hygiene", False, "validator_registry_invalid", [str(exc)])
    completed = runner([sys.executable, "-m", "triage.gitignore_hygiene"], root)
    if completed.returncode:
        return result("hook_hygiene", "hook hygiene", False, "artifact_hygiene_failed", [(completed.stderr or completed.stdout).strip()][:1])
    return result("hook_hygiene", "hook hygiene", True, "registered_hooks_and_artifact_hygiene_passed")


def final_status(checks: Sequence[Check]) -> str:
    if any(item.status == "FAIL" for item in checks):
        return "FAIL"
    if any(item.requirement == "REQUIRED" and item.status != "PASS" for item in checks):
        return "FAIL"
    return "PASS"


def render_matrix(checks: Sequence[Check], branch: str, commit: str) -> str:
    passed = sum(item.status == "PASS" for item in checks)
    skipped = sum(item.status == "SKIP" for item in checks)
    failed = sum(item.status == "FAIL" for item in checks)
    lines = ["APP HARNESS VALIDATION", f"Branch: {branch}", f"Commit: {commit}"]
    for item in checks:
        suffix = f": {item.reason}" if item.status != "PASS" else ""
        lines.append(f"[{item.status}] {item.name}{suffix}")
    lines.append(f"Result: {passed} passed / {skipped} skipped / {failed} failed")
    lines.append(f"Gate: {final_status(checks)}")
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
    identity = prompt_identity(root)
    gate = final_status(checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "proof_level": PROOF_LEVEL,
        "runtime_proof": False,
        "repository_root": ".",
        "branch": branch,
        "head_sha": commit,
        "canonical_command": CANONICAL_COMMAND,
        "prompt_owner": identity,
        "proof_ceiling": PROOF_CEILING,
        "validator_set": [item.id for item in checks],
        "checks": [asdict(item) for item in checks],
        "required_checks": [item.id for item in checks if item.requirement == "REQUIRED"],
        "skipped_checks": [
            {"id": item.id, "requirement": item.requirement, "reason": item.reason}
            for item in checks
            if item.status == "SKIP"
        ],
        "summary": {
            "passed": sum(item.status == "PASS" for item in checks),
            "skipped": sum(item.status == "SKIP" for item in checks),
            "failed": sum(item.status == "FAIL" for item in checks),
        },
        "final_status": gate,
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
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"APP HARNESS VALIDATION\n[FAIL] bootstrap: {exc}", file=sys.stderr)
        return 2
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    checks = [Check(**item) for item in report["checks"]]
    print(render_matrix(checks, str(report["branch"]), str(report["head_sha"])))
    print(f"Prompt owner: {report['prompt_owner']['id']} · {report['prompt_owner']['name']} — {report['prompt_owner']['purpose']}")
    print(f"JSON: {target.relative_to(root).as_posix()}")
    return 0 if report["final_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
