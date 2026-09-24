#!/usr/bin/env python3
"""Provider-neutral, privacy-bounded adapter seam for runtime-compliance runs."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[4]
EVAL = ROOT / "harness" / "evals" / "runtime-compliance"
SCHEMA_PATH = EVAL / "runtime" / "capture-schema.v1.json"
CONTRACT_PATH = EVAL / "runtime" / "adapter-contract.v1.json"

SCHEMA_CONFIG = "prompt-runtime-compliance-agent-adapter/v1"
SCHEMA_CAPTURE = "prompt-runtime-compliance-capture/v1"
INVALID_CODES = {
    "RUNTIME_UNAVAILABLE",
    "ADAPTER_CONFIG_INVALID",
    "ADAPTER_EXIT_NONZERO",
    "ADAPTER_LAUNCH_ERROR",
    "ADAPTER_RESULT_MISSING",
    "ADAPTER_RESULT_INVALID",
    "CAPTURE_PRIVACY_REJECTED",
    "ADAPTER_TIMEOUT",
    "EVIDENCE_INCOMPLETE",
}
FORBIDDEN_KEYS = {
    "raw_prompt",
    "raw_response",
    "transcript",
    "chain_of_thought",
    "hidden_reasoning",
    "api_key",
    "credential",
    "secret",
    "token",
}
BASE_ENV = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "HOME",
    "TMP",
    "TEMP",
    "LANG",
    "LC_ALL",
}


class AdapterError(RuntimeError):
    def __init__(self, code: str, detail: str):
        if code not in INVALID_CODES:
            raise ValueError(f"unknown invalid-run code: {code}")
        super().__init__(detail)
        self.code = code
        self.detail = detail


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


CAPTURE_SCHEMA = load_json(SCHEMA_PATH)
ADAPTER_CONTRACT = load_json(CONTRACT_PATH)
CAPTURE_VALIDATOR = Draft202012Validator(CAPTURE_SCHEMA, format_checker=FormatChecker())


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {"schema_version", "argv", "timeout_seconds", "env_allowlist"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "adapter config contains unsupported fields")
    if config.get("schema_version") != SCHEMA_CONFIG:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "adapter config schema_version mismatch")
    argv = config.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        raise AdapterError("ADAPTER_CONFIG_INVALID", "argv must be a non-empty list of strings")
    timeout = config.get("timeout_seconds", ADAPTER_CONTRACT["execution"]["default_timeout_seconds"])
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= ADAPTER_CONTRACT["execution"]["max_timeout_seconds"]:
        raise AdapterError("ADAPTER_CONFIG_INVALID", "timeout_seconds is outside the governed range")
    allow = config.get("env_allowlist", [])
    if not isinstance(allow, list) or not all(isinstance(item, str) and item for item in allow):
        raise AdapterError("ADAPTER_CONFIG_INVALID", "env_allowlist must be a list of environment names")
    return {
        "schema_version": SCHEMA_CONFIG,
        "argv": list(argv),
        "timeout_seconds": timeout,
        "env_allowlist": sorted(set(allow)),
    }


def _scan_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise AdapterError("CAPTURE_PRIVACY_REJECTED", f"privacy-forbidden key at {path}.{key}")
            _scan_forbidden_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden_keys(item, f"{path}[{index}]")


def sanitize_capture(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AdapterError("ADAPTER_RESULT_INVALID", "provider result must be an object")
    _scan_forbidden_keys(payload)
    errors = sorted(CAPTURE_VALIDATOR.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        detail = "; ".join(error.message for error in errors[:6])
        raise AdapterError("ADAPTER_RESULT_INVALID", f"capture schema rejected payload: {detail}")
    privacy = payload["privacy"]
    if any(
        privacy[field] is not False
        for field in (
            "raw_transcript_persisted",
            "secrets_persisted",
            "hidden_reasoning_persisted",
        )
    ):
        raise AdapterError("CAPTURE_PRIVACY_REJECTED", "capture privacy flags must prove non-persistence")
    if payload["observed_runtime"] and not payload["proof"]["runtime_observed"]:
        raise AdapterError("EVIDENCE_INCOMPLETE", "observed_runtime requires proof.runtime_observed")
    if not payload["observed_runtime"] and payload["proof"]["runtime_observed"]:
        raise AdapterError("EVIDENCE_INCOMPLETE", "fake/non-observed capture cannot claim runtime observation")
    return json.loads(json.dumps(payload))


def _minimal_env(allow: list[str]) -> dict[str, str]:
    names = {name.upper() for name in BASE_ENV | set(allow)}
    return {key: value for key, value in os.environ.items() if key.upper() in names}


def _argv(argv: list[str], *, run_dir: Path, scenario: Path, result: Path) -> list[str]:
    replacements = {
        "{run_dir}": str(run_dir),
        "{scenario}": str(scenario),
        "{result}": str(result),
    }
    expanded: list[str] = []
    for item in argv:
        value = item
        for token, replacement in replacements.items():
            value = value.replace(token, replacement)
        expanded.append(value)
    return expanded


def mark_invalid(run_dir: Path, code: str, detail: str) -> dict[str, Any]:
    if code not in INVALID_CODES:
        raise ValueError(f"unknown invalid-run code: {code}")
    receipt = {
        "schema_version": "prompt-runtime-compliance-invalid-run/v1",
        "code": code,
        "detail": detail,
        "raw_output_persisted": False,
    }
    (run_dir / "invalid-run.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def invoke_adapter(config: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    config = validate_config(config)
    scenario = run_dir / "scenario.json"
    if not scenario.is_file():
        raise AdapterError("EVIDENCE_INCOMPLETE", "run directory lacks scenario.json")
    temp_dir = Path(tempfile.mkdtemp(prefix="prompt-runtime-compliance-"))
    result_path = temp_dir / "result.json"
    try:
        try:
            proc = subprocess.run(
                _argv(config["argv"], run_dir=run_dir, scenario=scenario, result=result_path),
                cwd=run_dir,
                env=_minimal_env(config["env_allowlist"]),
                capture_output=True,
                text=False,
                check=False,
                timeout=config["timeout_seconds"],
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdapterError("ADAPTER_TIMEOUT", f"adapter exceeded {config['timeout_seconds']} seconds") from exc
        except OSError as exc:
            raise AdapterError("ADAPTER_LAUNCH_ERROR", f"adapter launch failed: {type(exc).__name__}") from exc
        if proc.returncode != 0:
            raise AdapterError("ADAPTER_EXIT_NONZERO", f"adapter exited with {proc.returncode}")
        if not result_path.is_file():
            raise AdapterError("ADAPTER_RESULT_MISSING", "adapter did not create the temporary result file")
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AdapterError("ADAPTER_RESULT_INVALID", "adapter result is not valid JSON") from exc
        capture = sanitize_capture(payload)
        (run_dir / "capture.json").write_text(
            json.dumps(capture, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return capture
    finally:
        try:
            if result_path.exists():
                result_path.unlink()
            temp_dir.rmdir()
        except OSError:
            pass


def invoke_or_mark_invalid(config: dict[str, Any] | None, run_dir: Path) -> dict[str, Any]:
    if config is None:
        return {
            "valid": False,
            "invalid": mark_invalid(run_dir, "RUNTIME_UNAVAILABLE", "no runtime adapter configuration supplied"),
        }
    try:
        capture = invoke_adapter(config, run_dir)
    except AdapterError as exc:
        return {"valid": False, "invalid": mark_invalid(run_dir, exc.code, exc.detail)}
    return {"valid": True, "capture": capture}
