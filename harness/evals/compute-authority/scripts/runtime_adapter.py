#!/usr/bin/env python3
"""Provider-neutral, privacy-bounded adapter/capture seam for compute-authority runs."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_CONFIG = "compute-authority-agent-adapter/v1"
SCHEMA_CAPTURE_V1 = "compute-authority-provider-capture/v1"
SCHEMA_CAPTURE_V2 = "compute-authority-provider-capture/v2"
INVALID_CODES = {
    "RUNTIME_UNAVAILABLE", "ADAPTER_CONFIG_INVALID", "ADAPTER_EXIT_NONZERO",
    "ADAPTER_LAUNCH_ERROR", "ADAPTER_RESULT_MISSING", "ADAPTER_RESULT_INVALID",
    "CAPTURE_PRIVACY_REJECTED", "CAPTURE_EVALUATIVE_REJECTED", "ADAPTER_TIMEOUT",
    "EVIDENCE_INCOMPLETE", "PAIR_IDENTITY_MISMATCH",
}
TOP_ALLOWED_V1 = {
    "schema_version", "provider", "agent", "model", "status",
    "termination_reason", "usage", "events", "contracts", "validations", "outcomes",
}
TOP_ALLOWED_V2 = {
    "schema_version", "provider", "agent", "model", "status",
    "termination_reason", "usage", "events", "validations",
}
USAGE_ALLOWED = {
    "tool_calls", "retries", "input_tokens", "output_tokens", "total_tokens",
    "cost_microusd", "latency_ms",
}
EVENT_ALLOWED_V1 = {
    "id", "kind", "useful", "action_index", "first_green", "after_fixed_point",
    "started_ns", "ended_ns", "hypothesis_id", "validation_id", "result_code",
}
EVENT_ALLOWED_V2 = {
    "id", "kind", "category", "action_index", "started_ns", "ended_ns",
    "hypothesis_id", "validation_id", "result_code", "child_lane_id",
}
EVENT_KINDS_V1 = {"action", "hypothesis", "validation", "parallel_lane", "fixed_point"}
EVENT_KINDS_V2 = {"action", "hypothesis_test", "validation_run", "child_lane", "termination"}
EVENT_CATEGORIES = {"read", "write", "execute", "search", "analysis", "test", "unknown"}
CONTRACT_ALLOWED = {"id", "status", "correct"}
VALIDATION_ALLOWED_V1 = {"id", "status", "return_code"}
VALIDATION_ALLOWED_V2 = {"id", "command", "return_code", "started_ns", "ended_ns"}
EVALUATIVE_FIELDS_V2 = {
    "useful", "first_green", "after_fixed_point", "correct",
    "seeded_defects_found", "contracts", "outcomes",
}
FORBIDDEN_TOKENS = {
    "prompt", "response", "clipboard", "transcript", "content", "text", "query",
    "user_id", "session_id", "identity",
}
BASE_ENV = {
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "HOME", "TMP", "TEMP", "LANG", "LC_ALL",
}


class AdapterError(RuntimeError):
    def __init__(self, code: str, detail: str):
        if code not in INVALID_CODES:
            raise ValueError(f"unknown invalid-run code: {code}")
        super().__init__(detail)
        self.code, self.detail = code, detail


def _extra(payload: dict[str, Any], allowed: set[str], label: str) -> None:
    extra = set(payload) - allowed
    if extra:
        raise AdapterError("CAPTURE_PRIVACY_REJECTED", f"{label} unsupported keys: {sorted(extra)}")
    for key in payload:
        if any(token in key.lower() for token in FORBIDDEN_TOKENS):
            raise AdapterError("CAPTURE_PRIVACY_REJECTED", f"{label} privacy-forbidden key: {key}")


def _ident(value: Any, label: str, *, empty: bool = False) -> str:
    if value is None and empty:
        return ""
    if not isinstance(value, str):
        raise AdapterError("ADAPTER_RESULT_INVALID", f"{label} must be a string")
    value = value.strip()
    if not value and not empty:
        raise AdapterError("EVIDENCE_INCOMPLETE", f"{label} must not be empty")
    if len(value) > 256:
        raise AdapterError("ADAPTER_RESULT_INVALID", f"{label} exceeds 256 chars")
    if value and (any(ch in value for ch in "\r\n\t") or not re.fullmatch(r"[A-Za-z0-9_.:/+@-]+", value)):
        raise AdapterError("CAPTURE_PRIVACY_REJECTED", f"{label} must be a structural identifier/code")
    return value


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {"schema_version", "argv", "timeout_seconds", "env_allowlist"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "adapter config contains unsupported fields")
    if config.get("schema_version") != SCHEMA_CONFIG:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "adapter config schema_version mismatch")
    argv = config.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
        raise AdapterError("ADAPTER_CONFIG_INVALID", "argv must be a non-empty list of strings")
    timeout = config.get("timeout_seconds", 900)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 7200:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "timeout_seconds must be 1..7200")
    allow = config.get("env_allowlist", [])
    if not isinstance(allow, list) or not all(isinstance(v, str) and v for v in allow):
        raise AdapterError("ADAPTER_CONFIG_INVALID", "env_allowlist must be a list of names")
    return {"schema_version": SCHEMA_CONFIG, "argv": list(argv), "timeout_seconds": timeout, "env_allowlist": sorted(set(allow))}


def _usage(value: Any) -> dict[str, int | float]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise AdapterError("ADAPTER_RESULT_INVALID", "usage must be an object")
    _extra(value, USAGE_ALLOWED, "usage")
    out: dict[str, int | float] = {}
    for key, item in value.items():
        if isinstance(item, bool) or not isinstance(item, (int, float)) or item < 0:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"usage.{key} must be non-negative")
        out[key] = item
    return out


def _events(value: Any, schema_version: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise AdapterError("EVIDENCE_INCOMPLETE", "events must be an array")
    is_v2 = schema_version == SCHEMA_CAPTURE_V2
    event_allowed = EVENT_ALLOWED_V2 if is_v2 else EVENT_ALLOWED_V1
    event_kinds = EVENT_KINDS_V2 if is_v2 else EVENT_KINDS_V1
    out: list[dict[str, Any]] = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{i}] must be an object")
        if is_v2:
            for forbidden in EVALUATIVE_FIELDS_V2:
                if forbidden in item:
                    raise AdapterError("CAPTURE_EVALUATIVE_REJECTED", f"event[{i}] contains evaluative field '{forbidden}' forbidden in v2")
        _extra(item, event_allowed, f"event[{i}]")
        event: dict[str, Any] = {"kind": _ident(item.get("kind"), f"event[{i}].kind")}
        if event["kind"] not in event_kinds:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{i}].kind unsupported")
        for key in ("id", "hypothesis_id", "validation_id", "result_code", "child_lane_id", "category"):
            if key in item:
                event[key] = _ident(item[key], f"event[{i}].{key}", empty=(key == "category"))
        if is_v2 and "category" in event and event["category"] and event["category"] not in EVENT_CATEGORIES:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{i}].category unsupported")
        if not is_v2:
            for key in ("useful", "first_green", "after_fixed_point"):
                if key in item:
                    if not isinstance(item[key], bool):
                        raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{i}].{key} must be boolean")
                    event[key] = item[key]
        for key in ("action_index", "started_ns", "ended_ns"):
            if key in item:
                n = item[key]
                if isinstance(n, bool) or not isinstance(n, int) or n < 0:
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{i}].{key} must be non-negative integer")
                event[key] = n
        if ("started_ns" in event) ^ ("ended_ns" in event):
            raise AdapterError("EVIDENCE_INCOMPLETE", f"event[{i}] interval requires both endpoints")
        if "started_ns" in event and event["ended_ns"] < event["started_ns"]:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"event[{i}] interval reversed")
        out.append(event)
    _event_invariants(out, schema_version)
    return out


def _event_invariants(events: list[dict[str, Any]], schema_version: str) -> None:
    is_v2 = schema_version == SCHEMA_CAPTURE_V2
    ids: set[str] = set()
    actions: list[int] = []
    green: list[int] = []
    fixed: list[int] = []
    for i, event in enumerate(events):
        event_id = event.get("id")
        if not event_id:
            raise AdapterError("EVIDENCE_INCOMPLETE", f"event[{i}] requires id")
        if event_id in ids:
            raise AdapterError("EVIDENCE_INCOMPLETE", f"duplicate event id: {event_id}")
        ids.add(event_id)
        idx = event.get("action_index")
        if event["kind"] == "action":
            if not isinstance(idx, int) or idx < 1:
                raise AdapterError("EVIDENCE_INCOMPLETE", f"action {event_id} requires positive action_index")
            actions.append(idx)
            if not is_v2 and event.get("first_green") is True:
                green.append(idx)
        elif not is_v2 and (event.get("first_green") is True or event.get("after_fixed_point") is True):
            raise AdapterError("EVIDENCE_INCOMPLETE", f"{event['kind']} cannot carry action markers")
        if not is_v2 and event["kind"] == "fixed_point":
            if not isinstance(idx, int) or idx < 1:
                raise AdapterError("EVIDENCE_INCOMPLETE", f"fixed_point {event_id} requires positive action_index")
            fixed.append(idx)
    if not actions:
        raise AdapterError("EVIDENCE_INCOMPLETE", "capture requires at least one action event")
    if len(set(actions)) != len(actions):
        raise AdapterError("EVIDENCE_INCOMPLETE", "action_index values must be unique")
    if actions != sorted(actions):
        raise AdapterError("EVIDENCE_INCOMPLETE", "action_index values must increase in event order")
    if not is_v2:
        if len(green) > 1 or len(fixed) > 1:
            raise AdapterError("EVIDENCE_INCOMPLETE", "first_green/fixed_point markers must be singular")
        fixed_idx = fixed[0] if fixed else None
        for event in events:
            if event.get("kind") == "action" and event.get("after_fixed_point") is True:
                if fixed_idx is None or event["action_index"] <= fixed_idx:
                    raise AdapterError("EVIDENCE_INCOMPLETE", "after_fixed_point contradicts fixed-point ordering")


def _records(value: Any, allowed: set[str], label: str, schema_version: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AdapterError("ADAPTER_RESULT_INVALID", f"{label} must be an array")
    is_v2 = schema_version == SCHEMA_CAPTURE_V2
    out: list[dict[str, Any]] = []
    ids: set[str] = set()
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise AdapterError("ADAPTER_RESULT_INVALID", f"{label}[{i}] must be an object")
        if is_v2 and label == "validations":
            for forbidden in EVALUATIVE_FIELDS_V2:
                if forbidden in item:
                    raise AdapterError("CAPTURE_EVALUATIVE_REJECTED", f"{label}[{i}] contains evaluative field '{forbidden}' forbidden in v2")
        _extra(item, allowed, f"{label}[{i}]")
        clean: dict[str, Any] = {}
        for key, raw in item.items():
            if key == "correct":
                if not isinstance(raw, bool):
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"{label}[{i}].correct must be boolean")
                clean[key] = raw
            elif key == "return_code":
                if isinstance(raw, bool) or not isinstance(raw, int):
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"{label}[{i}].return_code must be integer")
                clean[key] = raw
            elif key in ("started_ns", "ended_ns"):
                if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
                    raise AdapterError("ADAPTER_RESULT_INVALID", f"{label}[{i}].{key} must be non-negative integer")
                clean[key] = raw
            else:
                clean[key] = _ident(raw, f"{label}[{i}].{key}")
        rid = clean.get("id")
        if not rid or rid in ids:
            raise AdapterError("EVIDENCE_INCOMPLETE", f"{label}[{i}] id missing or duplicate")
        ids.add(rid)
        out.append(clean)
    return out


def sanitize_capture(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AdapterError("ADAPTER_RESULT_INVALID", "provider result must be an object")
    schema_version = payload.get("schema_version")
    if schema_version not in {SCHEMA_CAPTURE_V1, SCHEMA_CAPTURE_V2}:
        raise AdapterError("ADAPTER_RESULT_INVALID", f"provider capture schema_version unsupported or missing: {schema_version!r}")
    is_v2 = schema_version == SCHEMA_CAPTURE_V2
    top_allowed = TOP_ALLOWED_V2 if is_v2 else TOP_ALLOWED_V1
    validation_allowed = VALIDATION_ALLOWED_V2 if is_v2 else VALIDATION_ALLOWED_V1
    if is_v2:
        for forbidden in EVALUATIVE_FIELDS_V2:
            if forbidden in payload:
                raise AdapterError("CAPTURE_EVALUATIVE_REJECTED", f"capture top-level contains evaluative field '{forbidden}' forbidden in v2")
    _extra(payload, top_allowed, "capture")
    required_base = {"provider", "status", "termination_reason", "events"}
    required = required_base | ({"outcomes"} if not is_v2 else set())
    missing = sorted(required - set(payload))
    if missing:
        raise AdapterError("EVIDENCE_INCOMPLETE", f"provider capture missing required fields: {missing}")
    status = _ident(payload["status"], "status")
    if status != "complete":
        raise AdapterError("EVIDENCE_INCOMPLETE", f"capture status must be complete, got {status!r}")
    result: dict[str, Any] = {
        "schema_version": schema_version,
        "provider": _ident(payload["provider"], "provider"),
        "agent": _ident(payload.get("agent"), "agent", empty=True),
        "model": _ident(payload.get("model"), "model", empty=True),
        "status": status,
        "termination_reason": _ident(payload["termination_reason"], "termination_reason"),
        "usage": _usage(payload.get("usage")),
        "events": _events(payload["events"], schema_version),
        "validations": _records(payload.get("validations"), validation_allowed, "validations", schema_version),
    }
    if not is_v2:
        outcomes = payload["outcomes"]
        if not isinstance(outcomes, dict):
            raise AdapterError("EVIDENCE_INCOMPLETE", "outcomes must be an object")
        _extra(outcomes, {"seeded_defects_found"}, "outcomes")
        defects = outcomes.get("seeded_defects_found")
        if isinstance(defects, bool) or not isinstance(defects, int) or defects < 0:
            raise AdapterError("EVIDENCE_INCOMPLETE", "outcomes.seeded_defects_found must be a non-negative integer")
        result["contracts"] = _records(payload.get("contracts"), CONTRACT_ALLOWED, "contracts", schema_version)
        result["outcomes"] = {"seeded_defects_found": defects}
    return result


def _overlap(events: list[dict[str, Any]]) -> int:
    points: list[tuple[int, int]] = []
    for event in events:
        if event.get("kind") in {"parallel_lane", "child_lane"} and "started_ns" in event:
            points += [(event["started_ns"], 1), (event["ended_ns"], -1)]
    active = peak = 0
    for _, delta in sorted(points, key=lambda p: (p[0], p[1])):
        active += delta
        peak = max(peak, active)
    return peak


def derive_metrics(capture: dict[str, Any]) -> dict[str, Any]:
    schema_version = capture.get("schema_version")
    is_v2 = schema_version == SCHEMA_CAPTURE_V2
    events = capture["events"]
    actions = [e for e in events if e["kind"] == "action"]
    if is_v2:
        hypotheses = [e for e in events if e["kind"] == "hypothesis_test"]
        return {
            "total_substantive_actions": len(actions),
            "hypotheses_considered": len({e.get("hypothesis_id") for e in hypotheses if e.get("hypothesis_id")}),
            "hypotheses_tested": sum(bool(e.get("result_code")) for e in hypotheses),
            "parallel_lanes_used": _overlap(events),
        }
    useful = sum(e.get("useful") is True for e in actions)
    green = [e["action_index"] for e in actions if e.get("first_green") is True]
    first_green = green[0] if green else None
    hypotheses = [e for e in events if e["kind"] == "hypothesis"]
    fixed = [e["action_index"] for e in events if e["kind"] == "fixed_point"]
    fixed_idx = fixed[0] if fixed else None
    return {
        "total_substantive_actions": len(actions),
        "useful_compute_actions": useful,
        "useful_compute_ratio": useful / len(actions) if actions else 0.0,
        "first_green_action_index": first_green,
        "useful_actions_after_first_green": sum(
            e.get("useful") is True and first_green is not None and e["action_index"] > first_green
            for e in actions
        ),
        "hypotheses_considered": len({e.get("hypothesis_id") for e in hypotheses if e.get("hypothesis_id")}),
        "hypotheses_tested": sum(bool(e.get("result_code")) for e in hypotheses),
        "parallel_lanes_used": _overlap(events),
        "unnecessary_actions_after_fixed_point": sum(
            fixed_idx is not None and e["action_index"] > fixed_idx and e.get("after_fixed_point") is True
            for e in actions
        ),
        "seeded_defects_found": capture["outcomes"]["seeded_defects_found"],
    }


def _env(allow: list[str]) -> dict[str, str]:
    names = {v.upper() for v in BASE_ENV | set(allow)}
    return {k: v for k, v in os.environ.items() if k.upper() in names}


def _argv(argv: list[str], workspace: Path, task: Path, prompt: Path, result: Path) -> list[str]:
    values = {"{workspace}": str(workspace), "{task}": str(task), "{prompt}": str(prompt), "{result}": str(result)}
    out = []
    for raw in argv:
        for token, value in values.items():
            raw = raw.replace(token, value)
        out.append(raw)
    return out


def mark_invalid(run_dir: Path, code: str, detail: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if code not in INVALID_CODES:
        raise ValueError(f"invalid run code: {code}")
    receipt = {"schema_version": "compute-authority-invalid-run/v1", "code": code, "detail": detail, "metadata": metadata or {}}
    (run_dir / "invalid-run.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path = run_dir / "run.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta.update({"result": "invalid", "invalid_code": code, "completed_at": datetime.now(timezone.utc).isoformat()})
    path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def invoke_adapter(config: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    config = validate_config(config)
    workspace, task = run_dir / "workspace", run_dir / "task.txt"
    prompts = list(run_dir.glob("prompt-*.txt"))
    if not workspace.is_dir() or not task.is_file() or len(prompts) != 1:
        raise AdapterError("EVIDENCE_INCOMPLETE", "run directory lacks isolated workspace/task/prompt snapshot")
    temp = Path(tempfile.mkdtemp(prefix="compute-authority-adapter-"))
    result = temp / "result.json"
    try:
        try:
            proc = subprocess.run(
                _argv(config["argv"], workspace, task, prompts[0], result),
                cwd=workspace, env=_env(config["env_allowlist"]), capture_output=True,
                text=False, check=False, timeout=config["timeout_seconds"], shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdapterError("ADAPTER_TIMEOUT", f"adapter exceeded {config['timeout_seconds']} seconds") from exc
        except OSError as exc:
            raise AdapterError("ADAPTER_LAUNCH_ERROR", f"adapter process could not launch: {type(exc).__name__}") from exc
        if proc.returncode:
            raise AdapterError("ADAPTER_EXIT_NONZERO", f"adapter exited {proc.returncode}")
        if not result.is_file():
            raise AdapterError("ADAPTER_RESULT_MISSING", "adapter did not write result JSON")
        try:
            raw = json.loads(result.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AdapterError("ADAPTER_RESULT_INVALID", f"adapter result JSON invalid: {type(exc).__name__}") from exc
        capture = sanitize_capture(raw)
        metrics = derive_metrics(capture)
        is_v2 = capture.get("schema_version") == SCHEMA_CAPTURE_V2
        (run_dir / "provider-capture.json").write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (run_dir / "tool-events.jsonl").write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in capture["events"]), encoding="utf-8")
        if not is_v2:
            (run_dir / "contracts.json").write_text(json.dumps({"contracts": capture["contracts"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (run_dir / "validation-results.json").write_text(json.dumps({"validations": capture["validations"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        run_path = run_dir / "run.json"
        meta = json.loads(run_path.read_text(encoding="utf-8"))
        meta.update({
            "provider": capture["provider"], "agent": capture["agent"] or meta.get("agent", ""),
            "model": capture["model"] or meta.get("model", ""),
            "termination_reason": capture["termination_reason"],
            "completed_at": datetime.now(timezone.utc).isoformat(), "result": "captured",
        })
        run_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"capture": capture, "metrics": metrics}
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def invoke_or_mark_invalid(config: dict[str, Any] | None, run_dir: Path) -> dict[str, Any]:
    if config is None:
        return {"valid": False, "invalid": mark_invalid(run_dir, "RUNTIME_UNAVAILABLE", "no external runtime adapter configured")}
    try:
        return {"valid": True, **invoke_adapter(config, run_dir)}
    except AdapterError as exc:
        metadata = {"raw_output_persisted": False} if exc.code in {"ADAPTER_EXIT_NONZERO", "ADAPTER_LAUNCH_ERROR"} else {}
        return {"valid": False, "invalid": mark_invalid(run_dir, exc.code, exc.detail, metadata)}
