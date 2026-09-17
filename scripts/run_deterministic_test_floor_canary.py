#!/usr/bin/env python3
"""Run the deterministic test-floor negative canary with causal proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "harness/contracts/deterministic-test-floor-canary.v1.json"
DEFAULT_REPORT = REPO_ROOT / "Outputs/deterministic-test-floor-canary-report.json"
DEFAULT_FLOOR_REPORT = REPO_ROOT / "Outputs/deterministic-test-floor-canary-floor-report.json"


class ContractError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return payload


def _repo_path(value: str, *, must_exist: bool = True) -> Path:
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise ContractError(f"path must be repository-relative without traversal: {value!r}")
    resolved = (REPO_ROOT / rel).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ContractError(f"path escapes repository root: {value!r}") from exc
    if must_exist and not resolved.exists():
        raise ContractError(f"required canary path is missing: {value}")
    return resolved


def command_argv(values: list[str]) -> list[str]:
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise ContractError("witness argv must be a non-empty list of non-empty strings")
    argv = list(values)
    if argv[0].lower() in {"python", "python3", "py"}:
        argv[0] = sys.executable
    return argv


def load_contract(path: Path) -> dict[str, Any]:
    contract = _read_json(path)
    if contract.get("schema_version") != "deterministic-test-floor-canary/v1":
        raise ContractError("unsupported deterministic test-floor canary schema")
    if not str(contract.get("canary_id", "")).strip():
        raise ContractError("canary_id is required")

    target = str(contract.get("target_path", "")).strip()
    _repo_path(target)

    mutation = contract.get("mutation")
    if not isinstance(mutation, dict) or mutation.get("mode") != "append_text":
        raise ContractError("mutation.mode must be append_text")
    mutation_text = mutation.get("text")
    if not isinstance(mutation_text, str) or not mutation_text:
        raise ContractError("mutation.text must be a non-empty string")

    witness = contract.get("witness")
    if not isinstance(witness, dict):
        raise ContractError("witness must be an object")
    command_argv(witness.get("argv"))
    signatures = witness.get("required_failure_signatures")
    if not isinstance(signatures, list) or not signatures or any(
        not isinstance(item, str) or not item for item in signatures
    ):
        raise ContractError("witness.required_failure_signatures must be a non-empty string list")

    floor = contract.get("full_floor")
    if not isinstance(floor, dict):
        raise ContractError("full_floor must be an object")
    runner = str(floor.get("runner", "")).strip()
    runner_path = _repo_path(runner)
    if runner_path.suffix != ".py":
        raise ContractError("full_floor.runner must be a Python repository path")
    if not str(floor.get("expected_failed_step", "")).strip():
        raise ContractError("full_floor.expected_failed_step is required")
    return contract


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_command(argv: list[str]) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }


def evaluate_proof(
    contract: dict[str, Any],
    clean_witness: dict[str, Any],
    mutated_witness: dict[str, Any],
    floor_process: dict[str, Any],
    floor_receipt: dict[str, Any] | None,
    before_digest: str,
    after_digest: str,
) -> list[str]:
    errors: list[str] = []
    if clean_witness.get("returncode") != 0:
        errors.append("CLEAN_WITNESS_FAILED")
    if mutated_witness.get("returncode") == 0:
        errors.append("MUTATED_WITNESS_UNEXPECTEDLY_PASSED")

    witness_output = (mutated_witness.get("stdout_tail") or "") + "\n" + (
        mutated_witness.get("stderr_tail") or ""
    )
    missing = [
        signature
        for signature in contract["witness"]["required_failure_signatures"]
        if signature not in witness_output
    ]
    if missing:
        errors.append("WRONG_FAILURE_SIGNATURE:" + ",".join(missing))

    if floor_process.get("returncode") == 0:
        errors.append("FULL_FLOOR_UNEXPECTEDLY_PASSED")
    expected_step = contract["full_floor"]["expected_failed_step"]
    if not isinstance(floor_receipt, dict) or floor_receipt.get("status") != "FAIL":
        errors.append("FULL_FLOOR_RECEIPT_NOT_FAIL")
    elif floor_receipt.get("failed_step") != expected_step:
        errors.append(
            f"WRONG_FULL_FLOOR_GATE:{floor_receipt.get('failed_step')}!={expected_step}"
        )

    if before_digest != after_digest:
        errors.append("RESTORE_MISMATCH")
    return errors


def run(contract_path: Path, report_path: Path, floor_report_path: Path) -> int:
    report: dict[str, Any] = {
        "schema_version": "deterministic-test-floor-canary-report/v1",
        "status": "FAIL",
        "canary_id": None,
        "state": "READY_CLEAN",
        "proof_errors": [],
    }
    original: bytes | None = None
    target: Path | None = None
    before_digest: str | None = None
    clean_witness: dict[str, Any] = {}
    mutated_witness: dict[str, Any] = {}
    floor_process: dict[str, Any] = {}
    floor_receipt: dict[str, Any] | None = None

    try:
        contract = load_contract(contract_path)
        report["canary_id"] = contract["canary_id"]
        report["target_path"] = contract["target_path"]
        report["proof_ceiling"] = contract.get("proof_ceiling")
        target = _repo_path(contract["target_path"])
        original = target.read_bytes()
        before_digest = _digest(original)
        mutation_bytes = contract["mutation"]["text"].encode("utf-8")
        if mutation_bytes in original:
            raise ContractError("declared mutation marker already exists in clean target")

        witness_argv = command_argv(contract["witness"]["argv"])
        clean_witness = run_command(witness_argv)
        report["clean_witness"] = clean_witness
        if clean_witness["returncode"] != 0:
            report["state"] = "CLEAN_WITNESS_FAILED"
            report["proof_errors"] = ["CLEAN_WITNESS_FAILED"]
            return 1
        report["state"] = "CLEAN_WITNESS_PROVEN"

        target.write_bytes(original + mutation_bytes)
        report["state"] = "MUTATED"
        report["mutated_digest"] = _digest(target.read_bytes())

        mutated_witness = run_command(witness_argv)
        report["mutated_witness"] = mutated_witness
        report["state"] = "MUTATED_WITNESS_PROVEN"

        runner = _repo_path(contract["full_floor"]["runner"])
        floor_report_path.parent.mkdir(parents=True, exist_ok=True)
        floor_process = run_command(
            [sys.executable, str(runner.relative_to(REPO_ROOT)), "--report", str(floor_report_path)]
        )
        report["floor_process"] = floor_process
        if floor_report_path.is_file():
            floor_receipt = _read_json(floor_report_path)
            report["floor_receipt"] = {
                "schema_version": floor_receipt.get("schema_version"),
                "status": floor_receipt.get("status"),
                "failed_step": floor_receipt.get("failed_step"),
            }
        report["state"] = "FLOOR_FAILURE_PROVEN"
    except ContractError as exc:
        report["state"] = "CONTRACT_INVALID"
        report["proof_errors"] = [f"CONTRACT_INVALID:{exc}"]
        return_code = 2
    except Exception as exc:  # fail closed while preserving restoration
        report["state"] = "PROBE_ERROR"
        report["proof_errors"] = [f"PROBE_ERROR:{type(exc).__name__}:{exc}"]
        return_code = 3
    else:
        return_code = 1
    finally:
        if target is not None and original is not None:
            try:
                target.write_bytes(original)
                after_digest = _digest(target.read_bytes())
                report["before_digest"] = before_digest
                report["after_digest"] = after_digest
                report["restored"] = before_digest == after_digest
            except Exception as exc:
                report["restored"] = False
                report.setdefault("proof_errors", []).append(
                    f"RESTORE_ERROR:{type(exc).__name__}:{exc}"
                )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        if (
            report.get("state") == "FLOOR_FAILURE_PROVEN"
            and before_digest is not None
            and report.get("after_digest") is not None
        ):
            proof_errors = evaluate_proof(
                contract,
                clean_witness,
                mutated_witness,
                floor_process,
                floor_receipt,
                before_digest,
                report["after_digest"],
            )
            report["proof_errors"] = proof_errors
            if not proof_errors:
                report["status"] = "PASS"
                report["state"] = "PROVEN"
                return_code = 0
            elif report.get("state") != "CONTRACT_INVALID":
                report["state"] = proof_errors[0].split(":", 1)[0]
        if report.get("restored") is False and "RESTORE_MISMATCH" not in report.get("proof_errors", []):
            report.setdefault("proof_errors", []).append("RESTORE_MISMATCH")
            report["status"] = "FAIL"
            report["state"] = "RESTORE_MISMATCH"
            return_code = 4
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"DETERMINISTIC TEST-FLOOR CANARY: {report['status']} "
        f"canary={report.get('canary_id')} state={report.get('state')}"
    )
    print(f"Receipt: {report_path}")
    return return_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run failure-specific deterministic test-floor canary")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--floor-report", type=Path, default=DEFAULT_FLOOR_REPORT)
    args = parser.parse_args(argv)
    contract = args.contract if args.contract.is_absolute() else REPO_ROOT / args.contract
    report = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    floor_report = args.floor_report if args.floor_report.is_absolute() else REPO_ROOT / args.floor_report
    return run(contract.resolve(), report.resolve(), floor_report.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
