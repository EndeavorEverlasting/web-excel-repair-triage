#!/usr/bin/env python3
"""Run the repository-wide AI eval registry and emit one attributable report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "harness/evals/repository-ai-evals.v1.json"
DEFAULT_OUTPUT = ROOT / "Outputs/repository-ai-eval-report.json"
OUTPUTS = (ROOT / "Outputs").resolve()
ALLOWED_LAYERS = {"deterministic", "synthetic", "model_runtime", "human_review"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class EvalFrameworkError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvalFrameworkError(f"missing required eval file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvalFrameworkError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvalFrameworkError(f"expected JSON object: {path}")
    return value


def resolve_repo_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise EvalFrameworkError(f"path escapes repository: {value}") from exc
    return path


def resolve_output(path: Path) -> Path:
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve()
    try:
        rel = resolved.relative_to(OUTPUTS)
    except ValueError as exc:
        raise EvalFrameworkError(f"eval report must remain under Outputs/: {resolved}") from exc
    if rel == Path("."):
        raise EvalFrameworkError("eval output must name a file below Outputs/")
    return resolved


def git_head() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
            capture_output=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = proc.stdout.strip()
    return value if proc.returncode == 0 and SHA_RE.fullmatch(value) else None


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_command(command: Any, suite_id: str, field: str) -> list[str]:
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise EvalFrameworkError(f"suite {suite_id} {field} must be a non-empty argv array")
    if command[0] not in {"python", "node"}:
        raise EvalFrameworkError(f"suite {suite_id} {field} executable is not allowed: {command[0]}")
    return command


def validate_registry(registry: dict[str, Any]) -> list[dict[str, Any]]:
    if registry.get("schema_version") != "repository-ai-evals/v1":
        raise EvalFrameworkError("unsupported repository AI eval registry schema")
    layers = registry.get("layers")
    if not isinstance(layers, list) or set(layers) != ALLOWED_LAYERS:
        raise EvalFrameworkError("repository AI eval layers must declare the full deterministic/synthetic/model_runtime/human_review pyramid")
    suites = registry.get("suites")
    if not isinstance(suites, list) or not suites:
        raise EvalFrameworkError("repository AI eval registry must contain suites")

    seen: set[str] = set()
    for suite in suites:
        if not isinstance(suite, dict):
            raise EvalFrameworkError("every eval suite must be an object")
        suite_id = suite.get("id")
        if not isinstance(suite_id, str) or not suite_id.strip() or suite_id in seen:
            raise EvalFrameworkError(f"invalid or duplicate suite id: {suite_id!r}")
        seen.add(suite_id)
        layer = suite.get("layer")
        if layer not in ALLOWED_LAYERS:
            raise EvalFrameworkError(f"suite {suite_id} has invalid layer: {layer!r}")
        if not isinstance(suite.get("surface"), str) or not suite["surface"].strip():
            raise EvalFrameworkError(f"suite {suite_id} must name its evaluated surface")
        if not isinstance(suite.get("proof_ceiling"), str) or not suite["proof_ceiling"].strip():
            raise EvalFrameworkError(f"suite {suite_id} must declare a proof ceiling")
        case_source = suite.get("case_source")
        if case_source:
            path = resolve_repo_path(case_source)
            if not path.is_file():
                raise EvalFrameworkError(f"suite {suite_id} case source missing: {case_source}")
        contract = suite.get("contract")
        if contract and not resolve_repo_path(contract).is_file():
            raise EvalFrameworkError(f"suite {suite_id} contract missing: {contract}")
        if layer in {"deterministic", "synthetic"}:
            validate_command(suite.get("command"), suite_id, "command")
            artifact = suite.get("artifact")
            if not isinstance(artifact, str) or not artifact.startswith("Outputs/"):
                raise EvalFrameworkError(f"suite {suite_id} must write its artifact under Outputs/")
        elif layer == "model_runtime":
            validate_command(suite.get("contract_command"), suite_id, "contract_command")
            validate_command(suite.get("runtime_command"), suite_id, "runtime_command")
            pair = suite.get("required_pair")
            if not isinstance(pair, dict):
                raise EvalFrameworkError(f"suite {suite_id} must declare required_pair")
            missing = pair.get("missing_context") or {}
            present = pair.get("present_but_ignored") or {}
            if missing.get("classification") != "FACTUALITY_CONTEXT_MISSING" or missing.get("remediation") != "TARGETED_GROUNDING":
                raise EvalFrameworkError(f"suite {suite_id} missing-context pair must require targeted grounding")
            if present.get("classification") != "FAITHFULNESS_CONTEXT_IGNORED" or present.get("remediation") != "REANCHOR_EXISTING_CONTEXT":
                raise EvalFrameworkError(f"suite {suite_id} present-context pair must require re-anchoring")

    candidate = registry.get("candidate_corpus")
    if not isinstance(candidate, dict) or candidate.get("authority") != "candidate_only":
        raise EvalFrameworkError("observed candidate corpus must remain candidate_only")
    required_flags = candidate.get("required_flags") or {}
    if required_flags != {"candidate_only": True, "gold_eval_authority": False}:
        raise EvalFrameworkError("observed candidate authority flags drifted")
    return suites


def recursive_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key).lower())
            keys.update(recursive_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(recursive_keys(child))
    return keys


def validate_observed_candidates(path: Path, registry: dict[str, Any]) -> dict[str, Any]:
    payload = load_json(path)
    policy = registry["candidate_corpus"]
    if payload.get("schema_version") != policy["schema_version"]:
        raise EvalFrameworkError("observed candidate report schema does not match repository policy")
    if payload.get("gold_eval_authority") is not False or payload.get("mutation_authority") is not False:
        raise EvalFrameworkError("observed candidate report attempted to claim gold or mutation authority")
    field = policy["field"]
    candidates = payload.get(field)
    if not isinstance(candidates, list):
        raise EvalFrameworkError(f"observed candidate report missing list field: {field}")
    forbidden = {str(item).lower() for item in policy.get("forbidden_fields", [])}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise EvalFrameworkError("every observed eval candidate must be an object")
        for flag, expected in policy["required_flags"].items():
            if candidate.get(flag) is not expected:
                raise EvalFrameworkError(f"observed eval candidate must keep {flag}={expected!r}")
        bad = sorted(recursive_keys(candidate) & forbidden)
        if bad:
            raise EvalFrameworkError(f"observed eval candidate contains forbidden fields: {bad}")
        if candidate.get("surface") != "prompt_finder" or candidate.get("measurement") != "selection_intent":
            raise EvalFrameworkError("unsupported observed candidate surface/measurement")
        recommendations = candidate.get("recommendations")
        actions = candidate.get("observed_actions")
        if not isinstance(recommendations, list) or not recommendations:
            raise EvalFrameworkError("observed eval candidate must preserve recommendation IDs")
        if not isinstance(actions, list) or not actions:
            raise EvalFrameworkError("observed eval candidate must preserve at least one selection-intent action")
    return {
        "path": str(path.resolve().relative_to(ROOT.resolve())),
        "candidate_count": len(candidates),
        "authority": "candidate_only",
        "gold_eval_authority": False,
        "mutation_authority": False,
    }


def run_command(command: list[str], timeout_seconds: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True,
            timeout=timeout_seconds, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": None,
            "timed_out": True,
            "stdout_sha256": sha256_text(exc.stdout or ""),
            "stderr_sha256": sha256_text(exc.stderr or ""),
            "stdout_tail": (exc.stdout or "")[-2000:],
            "stderr_tail": (exc.stderr or "")[-2000:],
        }
    except OSError as exc:
        return {
            "exit_code": None,
            "timed_out": False,
            "error": str(exc),
            "stdout_sha256": sha256_text(""),
            "stderr_sha256": sha256_text(str(exc)),
            "stdout_tail": "",
            "stderr_tail": str(exc)[-2000:],
        }
    return {
        "exit_code": proc.returncode,
        "timed_out": False,
        "stdout_sha256": sha256_text(proc.stdout or ""),
        "stderr_sha256": sha256_text(proc.stderr or ""),
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }


def artifact_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False}
    payload = load_json(path)
    return {
        "exists": True,
        "path": str(path.resolve().relative_to(ROOT.resolve())),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "schema_version": payload.get("schema_version"),
        "status": payload.get("status"),
        "ready": payload.get("ready"),
    }


def run_suite(suite: dict[str, Any], *, include_model_runtime: bool, timeout_seconds: int) -> dict[str, Any]:
    layer = suite["layer"]
    result: dict[str, Any] = {
        "id": suite["id"],
        "owner": suite.get("owner"),
        "surface": suite["surface"],
        "layer": layer,
        "blocking": bool(suite.get("blocking")),
        "proof_ceiling": suite["proof_ceiling"],
    }
    if layer in {"deterministic", "synthetic"}:
        execution = run_command(suite["command"], timeout_seconds)
        artifact = resolve_repo_path(suite["artifact"])
        summary = artifact_summary(artifact)
        passed = execution.get("exit_code") == 0 and summary.get("exists") is True
        result.update({
            "status": "PASS" if passed else "FAIL",
            "command": suite["command"],
            "execution": execution,
            "artifact": summary,
        })
        return result

    if layer == "model_runtime":
        contract = run_command(suite["contract_command"], timeout_seconds)
        contract_pass = contract.get("exit_code") == 0
        result["contract"] = {"status": "PASS" if contract_pass else "FAIL", "command": suite["contract_command"], "execution": contract}
        if not contract_pass:
            result["status"] = "FAIL"
            result["blocking"] = bool(suite.get("contract_blocking", True))
            return result
        if not include_model_runtime:
            result["status"] = "UNPROVEN_RUNTIME"
            result["blocking"] = False
            result["runtime_command"] = suite["runtime_command"]
            return result
        runtime = run_command(suite["runtime_command"], timeout_seconds)
        artifact_arg = suite["runtime_command"][suite["runtime_command"].index("--output") + 1]
        summary = artifact_summary(resolve_repo_path(artifact_arg))
        runtime_status = summary.get("status")
        if runtime.get("exit_code") == 0 and runtime_status == "PASS":
            status = "PASS"
        elif runtime_status == "UNPROVEN" or runtime.get("exit_code") == 2:
            status = "UNPROVEN_RUNTIME"
        else:
            status = "FAIL"
        result.update({"status": status, "runtime_command": suite["runtime_command"], "runtime": runtime, "artifact": summary})
        result["blocking"] = False if status == "UNPROVEN_RUNTIME" else bool(suite.get("blocking"))
        return result

    result["status"] = "UNPROVEN_HUMAN_REVIEW"
    result["blocking"] = False
    return result


def baseline_delta(results: list[dict[str, Any]], baseline_path: Path | None) -> dict[str, Any] | None:
    if baseline_path is None:
        return None
    baseline = load_json(baseline_path)
    if baseline.get("schema_version") != "repository-ai-eval-report/v1":
        raise EvalFrameworkError("baseline report has unsupported schema")
    before = {item.get("id"): item.get("status") for item in baseline.get("suites", []) if isinstance(item, dict)}
    after = {item["id"]: item["status"] for item in results}
    changed = [
        {"id": suite_id, "baseline": before.get(suite_id), "candidate": status}
        for suite_id, status in sorted(after.items())
        if before.get(suite_id) != status
    ]
    regressions = [item for item in changed if item["baseline"] == "PASS" and item["candidate"] == "FAIL"]
    return {"baseline_path": str(baseline_path), "changed": changed, "regressions": regressions}


def build_report(
    registry: dict[str, Any],
    results: list[dict[str, Any]],
    observed: dict[str, Any] | None,
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    blocking_failures = [item["id"] for item in results if item.get("blocking") and item.get("status") != "PASS"]
    return {
        "schema_version": "repository-ai-eval-report/v1",
        "registry_schema_version": registry["schema_version"],
        "owner": registry["owner"],
        "commit_sha": git_head(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not blocking_failures else "FAIL",
        "blocking_failures": blocking_failures,
        "summary": {
            "suite_count": len(results),
            "pass_count": sum(item["status"] == "PASS" for item in results),
            "fail_count": sum(item["status"] == "FAIL" for item in results),
            "runtime_unproven_count": sum(item["status"] == "UNPROVEN_RUNTIME" for item in results),
            "observed_candidate_count": 0 if observed is None else observed["candidate_count"],
        },
        "candidate_corpus": observed,
        "baseline_comparison": baseline,
        "suites": results,
        "proof_ceiling": "Aggregated deterministic/synthetic exact-head eval evidence plus registered runtime-eval contract status. Candidate-only usage samples never become gold labels automatically; model/runtime and human quality remain explicit when unobserved."
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--observed-candidates", type=Path)
    parser.add_argument("--baseline-report", type=Path)
    parser.add_argument("--include-model-runtime", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        registry = load_json(args.registry)
        suites = validate_registry(registry)
        observed = validate_observed_candidates(args.observed_candidates, registry) if args.observed_candidates else None
        if args.validate_only:
            if args.summary:
                print(f"repository_ai_evals registry=PASS suites={len(suites)} observed_candidates={0 if observed is None else observed['candidate_count']}")
            return 0
        results = [run_suite(item, include_model_runtime=args.include_model_runtime, timeout_seconds=args.timeout_seconds) for item in suites]
        baseline = baseline_delta(results, args.baseline_report)
        report = build_report(registry, results, observed, baseline)
        output = resolve_output(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.summary:
            print(
                "repository_ai_evals "
                f"status={report['status']} suites={report['summary']['suite_count']} "
                f"pass={report['summary']['pass_count']} fail={report['summary']['fail_count']} "
                f"runtime_unproven={report['summary']['runtime_unproven_count']} "
                f"observed_candidates={report['summary']['observed_candidate_count']}"
            )
            for item in results:
                print(f"suite={item['id']} layer={item['layer']} status={item['status']} blocking={item['blocking']}")
        return 0 if report["status"] == "PASS" else 1
    except EvalFrameworkError as exc:
        print(f"repository AI eval framework error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
