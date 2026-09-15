#!/usr/bin/env python3
"""Provider-neutral, privacy-bounded adapter/capture seam for compute-authority runs."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_CONFIG = "compute-authority-agent-adapter/v1"
SCHEMA_CAPTURE = "compute-authority-provider-capture/v1"
INVALID_CODES = {
    "RUNTIME_UNAVAILABLE",
    "ADAPTER_CONFIG_INVALID",
    "ADAPTER_EXIT_NONZERO",
    "ADAPTER_RESULT_MISSING",
    "ADAPTER_RESULT_INVALID",
    "CAPTURE_PRIVACY_REJECTED",
    "ADAPTER_TIMEOUT",
    "EVIDENCE_INCOMPLETE",
}
TOP_LEVEL_ALLOWED = {
    "schema_version", "provider", "agent", "model", "status", "termination_reason",
    "usage", "events", "contracts", "validations",
}
USAGE_ALLOWED = {
    "tool_calls", "retries", "input_tokens", "output_tokens", "total_tokens",
    "cost_microusd", "latency_ms",
}
EVENT_ALLOWED = {
    "id", "kind", "useful", "action_index", "first_green", "after_fixed_point",
    "started_ns", "ended_ns", "hypothesis_id", "validation_id", "result_code",
}
EVENT_KINDS = {"action", "hypothesis", "validation", "parallel_lane", "fixed_point"}
CONTRACT_ALLOWED = {"id", "status", "correct"}
VALIDATION_ALLOWED = {"id", "status", "return_code"}
FORBIDDEN_KEY_TOKENS = {
    "prompt", "response", "clipboard", "transcript", "content", "text", "query",
    "user_id", "session_id", "identity",
}
BASE_ENV_KEYS = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "HOME", "TMP", "TEMP", "LANG", "LC_ALL"}


class AdapterError(RuntimeError):
    def __init__(self, code: str, detail: str):
        if code not in INVALID_CODES:
            raise ValueError(f"unknown invalid-run code: {code}")
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _reject_extra_keys(payload: dict[str, Any], allowed: set[str], label: str) -> None:
    extra = set(payload) - allowed
    if extra:
        raise AdapterError("CAPTURE_PRIVACY_REJECTED", f"{label} contains unsupported keys: {sorted(extra)}")
    for key in payload:
        lowered = key.lower()
        if any(token in lowered for token in FORBIDDEN_KEY_TOKENS):
            raise AdapterError("CAPTURE_PRIVACY_REJECTED", f"{label} contains privacy-forbidden key: {key}")


def _identifier(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if value is None and allow_empty:
        return ""
    if not isinstance(value, str):
        raise AdapterError("ADAPTER_RESULT_INVALID", f"{label} must be a string")
    value = value.strip()
    if not value and not allow_empty:
        raise AdapterError("ADAPTER_RESULT_INVALID", f"{label} must not be empty")
    if len(value) > 256:
        raise AdapterError("ADAPTER_RESULT_INVALID", f"{label} exceeds 256 chars")
    if value and (any(ch in value for ch in "\r\n\t") or not re.fullmatch(r"[A-Za-z0-9_.:/+@-]+", value)):
        raise AdapterError("CAPTURE_PRIVACY_REJECTED", f"{label} must be a structural identifier/code, not free text")
    return value


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {"schema_version", "argv", "timeout_seconds", "env_allowlist"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "adapter config contains unsupported fields")
    if config.get("schema_version") != SCHEMA_CONFIG:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "adapter config schema_version mismatch")
    argv = config.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        raise AdapterError("ADAPTER_CONFIG_INVALID", "argv must be a non-empty list of strings")
    timeout = config.get("timeout_seconds", 900)
    if not isinstance(timeout, int) or not 1 <= timeout <= 7200:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "timeout_seconds must be 1..7200")
    env_allowlist = config.get("env_allowlist", [])
    if not isinstance(env_allowlist, list) or not all(isinstance(item, str) and item for item in env_allowlist):
        raise AdapterError("ADAPTER_CONFIG_INVALID", "env_allowlist must be a list of names")
    return {
        "schema_version": SCHEMA_CONFIG,
        "argv": list(argv),
        "timeout_seconds": timeout,
        "env_allowlist": sorted(set(env_allowlist)),
    }


def _sanitize_usage(payload: Any) -> dict[str, int | float]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise AdapterError("ADAPTER_RESULT_INVALID", "usage must be an object")
    _reject_extra_keys(payload, USAGE_ALLOWED, "usage")
    result: dict[str, int | float] = {}
    for key, value in payload.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"usage.{key} must be a non-negative number")
        result[key] = value
    return result


def _sanitize_events(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise AdapterError("ADAPTER_RESULT_INVALID", "events must be an array")
    events: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{index}] must be an object")
        _reject_extra_keys(item, EVENT_ALLOWED, f"event[{index}]")
        kind = _identifier(item.get("kind"), f"event[{index}].kind")
        if kind not in EVENT_KINDS:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{index}].kind unsupported: {kind}")
        event: dict[str, Any] = {"kind": kind}
        for key in ("id", "hypothesis_id", "validation_id", "result_code"):
            if key in item:
                event[key] = _identifier(item[key], f"event[{index}].{key}")
        for key in ("useful", "first_green", "after_fixed_point"):
            if key in item:
                if not isinstance(item[key], bool):
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{index}].{key} must be boolean")
                event[key] = item[key]
        for key in ("action_index", "started_ns", "ended_ns"):
            if key in item:
                value = item[key]
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{index}].{key} must be non-negative integer")
                event[key] = value
        if ("started_ns" in event) ^ ("ended_ns" in event):
            raise AdapterError("EVIDENCE_INCOMPLETE", f"event[{index}] interval must have both endpoints")
        if "started_ns" in event and event["ended_ns"] < event["started_ns"]:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{index}] interval ends before it starts")
        events.append(event)
    return events


def _sanitize_records(payload: Any, allowed: set[str], label: str) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise AdapterError("ADAPTER_RESULT_INVALID", f"{label} must be an array")
    out: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise AdapterError("ADAPTER_RESULT_INVALID", f"{label}[{index}] must be an object")
        _reject_extra_keys(item, allowed, f"{label}[{index}]")
        clean: dict[str, Any] = {}
        for key, value in item.items():
            if key == "correct":
                if not isinstance(value, bool):
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"{label}[{index}].correct must be boolean")
                clean[key] = value
            elif key == "return_code":
                if isinstance(value, bool) or not isinstance(value, int):
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"{label}[{index}].return_code must be integer")
                clean[key] = value
            else:
                clean[key] = _identifier(value, f"{label}[{index}].{key}")
        out.append(clean)
    return out


def sanitize_capture(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AdapterError("ADAPTER_RESULT_INVALID", "provider result must be an object")
    _reject_extra_keys(payload, TOP_LEVEL_ALLOWED, "capture")
    if payload.get("schema_version") != SCHEMA_CAPTURE:
        raise AdapterError("ADAPTER_RESULT_INVALID", "provider capture schema_version mismatch")
    result: dict[str, Any] = {"schema_version": SCHEMA_CAPTURE}
    for key in ("provider", "agent", "model", "status", "termination_reason"):
        if key in payload:
            result[key] = _identifier(payload[key], key, allow_empty=key in {"agent", "model", "termination_reason"})
    result["usage"] = _sanitize_usage(payload.get("usage"))
    result["events"] = _sanitize_events(payload.get("events"))
    result["contracts"] = _sanitize_records(payload.get("contracts"), CONTRACT_ALLOWED, "contracts")
    result["validations"] = _sanitize_records(payload.get("validations"), VALIDATION_ALLOWED, "validations")
    return result


def _overlap_peak(events: list[dict[str, Any]]) -> int:
    points: list[tuple[int, int]] = []
    for event in events:
        if event.get("kind") != "parallel_lane" or "started_ns" not in event:
            continue
        points.append((event["started_ns"], 1))
        points.append((event["ended_ns"], -1))
    active = peak = 0
    for _, delta in sorted(points, key=lambda item: (item[0], item[1])):
        active += delta
        peak = max(peak, active)
    return peak


def derive_metrics(capture: dict[str, Any]) -> dict[str, Any]:
    events = capture.get("events") or []
    actions = [event for event in events if event.get("kind") == "action"]
    total = len(actions)
    useful = sum(1 for event in actions if event.get("useful") is True)
    green_indexes = [event.get("action_index") for event in actions if event.get("first_green") is True]
    first_green = min((value for value in green_indexes if isinstance(value, int)), default=None)
    useful_after = 0
    if first_green is not None:
        useful_after = sum(
            1 for event in actions
            if event.get("useful") is True
            and isinstance(event.get("action_index"), int)
            and event["action_index"] > first_green
        )
    hypotheses = [event for event in events if event.get("kind") == "hypothesis"]
    fixed_point_indexes = [
        event.get("action_index") for event in events
        if event.get("kind") == "fixed_point" and isinstance(event.get("action_index"), int)
    ]
    fixed_point = min(fixed_point_indexes, default=None)
    unnecessary = sum(
        1 for event in actions
        if fixed_point is not None
        and isinstance(event.get("action_index"), int)
        and event["action_index"] > fixed_point
        and event.get("after_fixed_point") is True
    )
    return {
        "total_substantive_actions": total,
        "useful_compute_actions": useful,
        "useful_compute_ratio": (useful / total) if total else 0.0,
        "first_green_action_index": first_green,
        "useful_actions_after_first_green": useful_after,
        "hypotheses_considered": len({event.get("hypothesis_id") for event in hypotheses if event.get("hypothesis_id")}),
        "hypotheses_tested": sum(1 for event in hypotheses if event.get("result_code")),
        "parallel_lanes_used": _overlap_peak(events),
        "unnecessary_actions_after_fixed_point": unnecessary,
    }


def _minimal_env(allowlist: list[str]) -> dict[str, str]:
    allowed = {name.upper() for name in BASE_ENV_KEYS | set(allowlist)}
    return {key: value for key, value in os.environ.items() if key.upper() in allowed}


def _render_argv(argv: list[str], *, workspace: Path, task: Path, prompt: Path, result: Path) -> list[str]:
    mapping = {
        "{workspace}": str(workspace),
        "{task}": str(task),
        "{prompt}": str(prompt),
        "{result}": str(result),
    }
    rendered: list[str] = []
    for raw in argv:
        item = raw
        for token, value in mapping.items():
            item = item.replace(token, value)
        rendered.append(item)
    return rendered


def mark_invalid(run_dir: Path, code: str, detail: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if code not in INVALID_CODES:
        raise ValueError(f"invalid run code: {code}")
    receipt = {
        "schema_version": "compute-authority-invalid-run/v1",
        "code": code,
        "detail": detail,
        "metadata": metadata or {},
    }
    (run_dir / "invalid-run.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_path = run_dir / "run.json"
    run_meta = json.loads(run_path.read_text(encoding="utf-8"))
    run_meta["result"] = "invalid"
    run_meta["invalid_code"] = code
    run_path.write_text(json.dumps(run_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def invoke_adapter(config: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    validated = validate_config(config)
    workspace = run_dir / "workspace"
    task = run_dir / "task.txt"
    prompt_files = list(run_dir.glob("prompt-*.txt"))
    if not workspace.is_dir() or not task.is_file() or len(prompt_files) != 1:
        raise AdapterError("EVIDENCE_INCOMPLETE", "run directory lacks isolated workspace/task/prompt snapshot")
    tmp_parent = Path(tempfile.mkdtemp(prefix="compute-authority-adapter-"))
    result_path = tmp_parent / "result.json"
    try:
        argv = _render_argv(validated["argv"], workspace=workspace, task=task, prompt=prompt_files[0], result=result_path)
        try:
            proc = subprocess.run(
                argv,
                cwd=workspace,
                env=_minimal_env(validated["env_allowlist"]),
                capture_output=True,
                text=False,
                check=False,
                timeout=validated["timeout_seconds"],
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdapterError("ADAPTER_TIMEOUT", f"adapter exceeded {validated['timeout_seconds']} seconds") from exc
        if proc.returncode != 0:
            raise AdapterError("ADAPTER_EXIT_NONZERO", f"adapter exited {proc.returncode}")
        if not result_path.is_file():
            raise AdapterError("ADAPTER_RESULT_MISSING", "adapter did not write result JSON")
        try:
            raw = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"adapter result JSON invalid: {type(exc).__name__}") from exc
        capture = sanitize_capture(raw)
        metrics = derive_metrics(capture)
        (run_dir / "provider-capture.json").write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (run_dir / "tool-events.jsonl").write_text(
            "".join(json.dumps(event, sort_keys=True) + "\n" for event in capture["events"]), encoding="utf-8"
        )
        (run_dir / "contracts.json").write_text(
            json.dumps({"contracts": capture["contracts"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (run_dir / "validation-results.json").write_text(
            json.dumps({"validations": capture["validations"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        run_path = run_dir / "run.json"
        run_meta = json.loads(run_path.read_text(encoding="utf-8"))
        run_meta.update({
            "provider": capture.get("provider", ""),
            "agent": capture.get("agent", run_meta.get("agent", "")),
            "model": capture.get("model", run_meta.get("model", "")),
            "termination_reason": capture.get("termination_reason", ""),
            "result": "captured",
        })
        run_path.write_text(json.dumps(run_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"capture": capture, "metrics": metrics}
    finally:
        try:
            for child in tmp_parent.iterdir():
                child.unlink(missing_ok=True)
            tmp_parent.rmdir()
        except OSError:
            pass


def invoke_or_mark_invalid(config: dict[str, Any] | None, run_dir: Path) -> dict[str, Any]:
    if config is None:
        return {"valid": False, "invalid": mark_invalid(run_dir, "RUNTIME_UNAVAILABLE", "no external runtime adapter configured")}
    try:
        result = invoke_adapter(config, run_dir)
        return {"valid": True, **result}
    except AdapterError as exc:
        metadata: dict[str, Any] = {}
        if exc.code == "ADAPTER_EXIT_NONZERO":
            metadata["raw_output_persisted"] = False
        return {"valid": False, "invalid": mark_invalid(run_dir, exc.code, exc.detail, metadata)}
