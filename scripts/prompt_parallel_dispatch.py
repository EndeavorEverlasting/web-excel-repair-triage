#!/usr/bin/env python3
"""Validate and execute machine-readable parallel dispatch manifests.

The CLI executes argv-addressable lanes in dependency waves. Runtime-tool lanes are
validated here but must be invoked by the active agent runtime, which can then emit
a receipt for `verify-receipt`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness/contracts/prompt-parallel-dispatch.v1.json"
DEFAULT_MANIFEST = ROOT / "Outputs/prompt-parallel-dispatch/manifest.json"
DEFAULT_RECEIPT = ROOT / "Outputs/prompt-parallel-dispatch/receipt.json"


class DispatchError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DispatchError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DispatchError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DispatchError(f"expected JSON object: {path}")
    return value


def _contract() -> dict[str, Any]:
    contract = _load_json(CONTRACT_PATH)
    if contract.get("schema_version") != "prompt-parallel-dispatch-contract/v1":
        raise DispatchError("unsupported parallel-dispatch contract")
    return contract


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DispatchError(f"{label} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise DispatchError(f"{label} must be an array of non-empty strings")
    if not allow_empty and not value:
        raise DispatchError(f"{label} must not be empty")
    return [item.strip() for item in value]


def _safe_repo_path(value: str, label: str) -> Path:
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise DispatchError(f"{label} escapes repository: {value}") from exc
    return candidate


def _topological_waves(lanes: dict[str, dict[str, Any]]) -> list[list[str]]:
    remaining = {lane_id: set(lane["dependencies"]) for lane_id, lane in lanes.items()}
    waves: list[list[str]] = []
    completed: set[str] = set()
    while remaining:
        ready = sorted(lane_id for lane_id, deps in remaining.items() if deps <= completed)
        if not ready:
            raise DispatchError("lane dependency graph contains a cycle")
        waves.append(ready)
        completed.update(ready)
        for lane_id in ready:
            remaining.pop(lane_id)
    return waves


def _depends_on(lanes: dict[str, dict[str, Any]], child: str, ancestor: str) -> bool:
    todo = list(lanes[child]["dependencies"])
    seen: set[str] = set()
    while todo:
        current = todo.pop()
        if current == ancestor:
            return True
        if current in seen:
            continue
        seen.add(current)
        todo.extend(lanes[current]["dependencies"])
    return False


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    contract = _contract()
    if manifest.get("schema_version") != contract["manifest_schema"]:
        raise DispatchError("unsupported parallel-dispatch manifest schema")
    for field in contract["required_manifest_fields"]:
        if field not in manifest:
            raise DispatchError(f"manifest missing field: {field}")
    _nonempty(manifest.get("run_id"), "run_id")
    declared_width = manifest.get("graph_width")
    if not isinstance(declared_width, int) or isinstance(declared_width, bool) or declared_width < 1:
        raise DispatchError("graph_width must be an integer >= 1")
    disposition = manifest.get("parallel_disposition")
    if disposition not in contract["parallel_dispositions"]:
        raise DispatchError(f"invalid parallel_disposition: {disposition!r}")
    autonomy_gap = manifest.get("autonomy_gap")
    if autonomy_gap is not None and (not isinstance(autonomy_gap, str) or not autonomy_gap.strip()):
        raise DispatchError("autonomy_gap must be null or a non-empty string")

    raw_lanes = manifest.get("lanes")
    if not isinstance(raw_lanes, list) or not raw_lanes:
        raise DispatchError("manifest lanes must be a non-empty array")
    allowed_adapters = {item["kind"]: item for item in contract["adapter_ladder"]}
    allowed_statuses = set(contract["lane_statuses"])
    lanes: dict[str, dict[str, Any]] = {}
    for index, lane in enumerate(raw_lanes):
        if not isinstance(lane, dict):
            raise DispatchError(f"lane {index} must be an object")
        for field in contract["required_lane_fields"]:
            if field not in lane:
                raise DispatchError(f"lane {index} missing field: {field}")
        lane_id = _nonempty(lane.get("lane_id"), f"lane {index} lane_id")
        if lane_id in lanes:
            raise DispatchError(f"duplicate lane_id: {lane_id}")
        _nonempty(lane.get("mission"), f"lane {lane_id} mission")
        dependencies = _string_list(lane.get("dependencies"), f"lane {lane_id} dependencies")
        if lane_id in dependencies:
            raise DispatchError(f"lane {lane_id} may not depend on itself")
        _string_list(lane.get("owned_mutation_surfaces"), f"lane {lane_id} owned_mutation_surfaces")
        _string_list(lane.get("forbidden_surfaces"), f"lane {lane_id} forbidden_surfaces")
        _string_list(lane.get("expected_artifacts"), f"lane {lane_id} expected_artifacts")
        _string_list(lane.get("validation"), f"lane {lane_id} validation", allow_empty=False)
        _nonempty(lane.get("convergence_owner"), f"lane {lane_id} convergence_owner")
        if lane.get("status") not in allowed_statuses:
            raise DispatchError(f"lane {lane_id} has invalid status: {lane.get('status')!r}")

        adapter = lane.get("adapter")
        if not isinstance(adapter, dict):
            raise DispatchError(f"lane {lane_id} adapter must be an object")
        kind = adapter.get("kind")
        if kind not in allowed_adapters:
            raise DispatchError(f"lane {lane_id} has unsupported adapter kind: {kind!r}")
        if adapter.get("rung") != allowed_adapters[kind]["rung"]:
            raise DispatchError(f"lane {lane_id} adapter rung does not match {kind}")

        launch = lane.get("launch")
        if not isinstance(launch, dict):
            raise DispatchError(f"lane {lane_id} launch must be an object")
        mode = launch.get("mode")
        if mode not in allowed_adapters[kind]["launch_modes"]:
            raise DispatchError(f"lane {lane_id} launch mode {mode!r} is invalid for {kind}")
        if mode == "argv":
            argv = launch.get("argv")
            if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
                raise DispatchError(f"lane {lane_id} argv must be a non-empty string array")
            cwd = launch.get("cwd", ".")
            _nonempty(cwd, f"lane {lane_id} cwd")
            _safe_repo_path(cwd, f"lane {lane_id} cwd")
            timeout = launch.get("timeout_seconds", 900)
            if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
                raise DispatchError(f"lane {lane_id} timeout_seconds must be an integer >= 1")
        elif mode == "runtime_tool":
            _nonempty(launch.get("tool"), f"lane {lane_id} runtime tool")
            _nonempty(launch.get("operation"), f"lane {lane_id} runtime operation")
            if not isinstance(launch.get("arguments"), dict):
                raise DispatchError(f"lane {lane_id} runtime arguments must be an object")
        lanes[lane_id] = {**lane, "dependencies": dependencies}

    known = set(lanes)
    for lane_id, lane in lanes.items():
        unknown = sorted(set(lane["dependencies"]) - known)
        if unknown:
            raise DispatchError(f"lane {lane_id} depends on unknown lanes: {unknown}")

    waves = _topological_waves(lanes)
    computed_width = max(len(wave) for wave in waves)
    if declared_width != computed_width:
        raise DispatchError(f"graph_width mismatch: declared={declared_width} computed={computed_width}")

    lane_ids = sorted(lanes)
    for index, left_id in enumerate(lane_ids):
        left = lanes[left_id]
        left_surfaces = set(left["owned_mutation_surfaces"])
        for right_id in lane_ids[index + 1 :]:
            overlap = left_surfaces & set(lanes[right_id]["owned_mutation_surfaces"])
            if not overlap:
                continue
            if not (_depends_on(lanes, left_id, right_id) or _depends_on(lanes, right_id, left_id)):
                raise DispatchError(
                    f"unordered lanes {left_id}/{right_id} share mutation surfaces: {sorted(overlap)}"
                )

    if computed_width == 1:
        if disposition != contract["policy"]["graph_width_one_disposition"]:
            raise DispatchError("graph width 1 must use NOT_APPLICABLE")
        if autonomy_gap is not None:
            raise DispatchError("NOT_APPLICABLE may not declare autonomy_gap")
    else:
        if disposition == "NOT_APPLICABLE":
            raise DispatchError("graph width >= 2 may not use NOT_APPLICABLE")
        if disposition == "DEGRADED" and (not isinstance(autonomy_gap, str) or not autonomy_gap.strip()):
            raise DispatchError("DEGRADED requires AUTONOMY_GAP")
        if disposition == "REQUIRED" and autonomy_gap is not None:
            raise DispatchError("REQUIRED may not predeclare autonomy_gap")

    return {
        "schema_version": manifest["schema_version"],
        "run_id": manifest["run_id"],
        "graph_width": computed_width,
        "parallel_disposition": disposition,
        "waves": waves,
        "lane_count": len(lanes),
        "lanes": lanes,
    }


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _run_argv_lane(lane: dict[str, Any]) -> dict[str, Any]:
    launch = lane["launch"]
    started_ns = time.time_ns()
    try:
        proc = subprocess.run(
            launch["argv"],
            cwd=_safe_repo_path(launch.get("cwd", "."), f"lane {lane['lane_id']} cwd"),
            text=True,
            capture_output=True,
            timeout=launch.get("timeout_seconds", 900),
            check=False,
        )
        ended_ns = time.time_ns()
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        return {
            "lane_id": lane["lane_id"],
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "adapter_kind": lane["adapter"]["kind"],
            "started_ns": started_ns,
            "ended_ns": ended_ns,
            "evidence": [{
                "type": "process",
                "exit_code": proc.returncode,
                "stdout_sha256": _sha256(stdout.encode("utf-8")),
                "stderr_sha256": _sha256(stderr.encode("utf-8")),
                "stdout_tail": stdout[-1000:],
                "stderr_tail": stderr[-1000:],
            }],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        ended_ns = time.time_ns()
        return {
            "lane_id": lane["lane_id"],
            "status": "FAIL",
            "adapter_kind": lane["adapter"]["kind"],
            "started_ns": started_ns,
            "ended_ns": ended_ns,
            "evidence": [{"type": "process_error", "error": str(exc)}],
        }


def dispatch_manifest(
    manifest: dict[str, Any],
    *,
    runner: Callable[[dict[str, Any]], dict[str, Any]] = _run_argv_lane,
    allow_degraded_serial: bool = False,
) -> dict[str, Any]:
    validated = validate_manifest(manifest)
    lanes = validated["lanes"]
    disposition = validated["parallel_disposition"]
    if any(lane["launch"]["mode"] != "argv" for lane in lanes.values()):
        raise DispatchError(
            "runtime_tool lanes require the active agent runtime to perform the declared tool/API calls; "
            "use this CLI to validate the manifest and verify the resulting receipt"
        )
    if disposition == "DEGRADED" and not allow_degraded_serial:
        raise DispatchError("DEGRADED execution requires --allow-degraded-serial and remains UNPROVEN parallelism")

    results: dict[str, dict[str, Any]] = {}
    observed_parallelism = False
    for wave in validated["waves"]:
        runnable = [lane_id for lane_id in wave if all(results.get(dep, {}).get("status") == "PASS" for dep in lanes[lane_id]["dependencies"])]
        blocked = sorted(set(wave) - set(runnable))
        for lane_id in blocked:
            results[lane_id] = {
                "lane_id": lane_id,
                "status": "BLOCKED",
                "adapter_kind": lanes[lane_id]["adapter"]["kind"],
                "evidence": [{"type": "dependency", "reason": "upstream lane did not pass"}],
            }
        if not runnable:
            continue
        if disposition == "REQUIRED" and len(runnable) > 1:
            observed_parallelism = True
            with ThreadPoolExecutor(max_workers=len(runnable)) as pool:
                futures = {pool.submit(runner, lanes[lane_id]): lane_id for lane_id in sorted(runnable)}
                for future in as_completed(futures):
                    result = future.result()
                    results[result["lane_id"]] = result
        else:
            for lane_id in sorted(runnable):
                results[lane_id] = runner(lanes[lane_id])

    ordered = [results[lane_id] for lane_id in sorted(results)]
    status = "PASS" if ordered and all(item["status"] == "PASS" for item in ordered) else "FAIL"
    if disposition == "REQUIRED" and validated["graph_width"] >= 2 and not observed_parallelism:
        status = "FAIL"
    return {
        "schema_version": "prompt-parallel-dispatch-receipt/v1",
        "run_id": validated["run_id"],
        "status": status,
        "parallel_disposition": disposition,
        "graph_width": validated["graph_width"],
        "observed_parallelism": observed_parallelism,
        "autonomy_gap": manifest.get("autonomy_gap"),
        "lanes": ordered,
    }


def validate_receipt(manifest: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    validated = validate_manifest(manifest)
    contract = _contract()
    if receipt.get("schema_version") != contract["receipt_schema"]:
        raise DispatchError("unsupported parallel-dispatch receipt schema")
    if receipt.get("run_id") != validated["run_id"]:
        raise DispatchError("receipt run_id does not match manifest")
    if receipt.get("graph_width") != validated["graph_width"]:
        raise DispatchError("receipt graph_width does not match manifest")
    if receipt.get("parallel_disposition") != validated["parallel_disposition"]:
        raise DispatchError("receipt disposition does not match manifest")
    raw = receipt.get("lanes")
    if not isinstance(raw, list):
        raise DispatchError("receipt lanes must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise DispatchError("receipt lane result must be an object")
        lane_id = _nonempty(item.get("lane_id"), "receipt lane_id")
        if lane_id in by_id:
            raise DispatchError(f"duplicate receipt lane: {lane_id}")
        if item.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
            raise DispatchError(f"invalid receipt status for {lane_id}")
        if not isinstance(item.get("evidence"), list) or not item["evidence"]:
            raise DispatchError(f"receipt lane {lane_id} requires evidence")
        by_id[lane_id] = item
    if set(by_id) != set(validated["lanes"]):
        raise DispatchError("receipt lane set does not match manifest")
    if validated["parallel_disposition"] == "REQUIRED" and validated["graph_width"] >= 2:
        if receipt.get("observed_parallelism") is not True:
            raise DispatchError("REQUIRED width >= 2 receipt must prove observed_parallelism=true")
    if validated["parallel_disposition"] == "DEGRADED":
        if receipt.get("observed_parallelism") is not False:
            raise DispatchError("DEGRADED receipt may not claim observed parallelism")
        if receipt.get("autonomy_gap") != manifest.get("autonomy_gap"):
            raise DispatchError("DEGRADED receipt must preserve manifest autonomy_gap")
    return {"status": receipt.get("status"), "lane_count": len(by_id), "observed_parallelism": receipt.get("observed_parallelism")}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    resolved = path if path.is_absolute() else ROOT / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to((ROOT / "Outputs").resolve())
    except ValueError as exc:
        raise DispatchError(f"receipt output must remain under Outputs/: {resolved}") from exc
    resolved.parent.mkdir(parents=True, exist_ok=True)
    tmp = resolved.with_name(f".{resolved.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(resolved)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    run = sub.add_parser("run")
    run.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    run.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    run.add_argument("--allow-degraded-serial", action="store_true")
    verify = sub.add_parser("verify-receipt")
    verify.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    verify.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args(argv)
    try:
        manifest = _load_json(args.manifest if args.manifest.is_absolute() else ROOT / args.manifest)
        if args.command == "validate":
            summary = validate_manifest(manifest)
            print(json.dumps({k: summary[k] for k in ("run_id", "graph_width", "parallel_disposition", "waves", "lane_count")}, indent=2))
            return 0
        if args.command == "run":
            receipt = dispatch_manifest(manifest, allow_degraded_serial=args.allow_degraded_serial)
            _write_json(args.receipt, receipt)
            print(json.dumps({"status": receipt["status"], "observed_parallelism": receipt["observed_parallelism"], "receipt": str(args.receipt)}, indent=2))
            return 0 if receipt["status"] == "PASS" else 1
        receipt = _load_json(args.receipt if args.receipt.is_absolute() else ROOT / args.receipt)
        print(json.dumps(validate_receipt(manifest, receipt), indent=2))
        return 0
    except DispatchError as exc:
        print(f"parallel-dispatch error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
