#!/usr/bin/env python3
"""Run the deterministic test-floor negative canary with causal proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "harness/contracts/deterministic-test-floor-canary.v1.json"
DEFAULT_REPORT = REPO_ROOT / "Outputs/deterministic-test-floor-canary-report.json"
DEFAULT_FLOOR_REPORT = REPO_ROOT / "Outputs/deterministic-test-floor-canary-floor-report.json"
DEFAULT_BASELINE_FLOOR_REPORT = (
    REPO_ROOT / "Outputs/deterministic-test-floor-canary-clean-floor-report.json"
)


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
    if not isinstance(mutation, dict):
        raise ContractError("mutation must be an object")
    mutation_mode = mutation.get("mode")
    if mutation_mode == "append_text":
        mutation_text = mutation.get("text")
        if not isinstance(mutation_text, str) or not mutation_text:
            raise ContractError("append_text mutation.text must be a non-empty string")
    elif mutation_mode == "replace_text":
        old_text = mutation.get("old_text")
        new_text = mutation.get("new_text")
        expected_occurrences = mutation.get("expected_occurrences", 1)
        if not isinstance(old_text, str) or not old_text:
            raise ContractError("replace_text mutation.old_text must be a non-empty string")
        if not isinstance(new_text, str) or not new_text:
            raise ContractError("replace_text mutation.new_text must be a non-empty string")
        if old_text == new_text:
            raise ContractError("replace_text mutation must change the target text")
        if (
            not isinstance(expected_occurrences, int)
            or isinstance(expected_occurrences, bool)
            or expected_occurrences < 1
        ):
            raise ContractError("replace_text expected_occurrences must be a positive integer")
    else:
        raise ContractError("mutation.mode must be append_text or replace_text")

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


def _apply_declared_mutation(original: bytes, mutation: dict[str, Any]) -> bytes:
    """Build the mutated bytes without writing the target."""
    mode = mutation["mode"]
    if mode == "append_text":
        marker = mutation["text"].encode("utf-8")
        if marker in original:
            raise ContractError("declared append_text mutation already exists in clean target")
        return original + marker

    if mode == "replace_text":
        try:
            source = original.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContractError("replace_text target must be UTF-8 text") from exc
        old_text = mutation["old_text"]
        new_text = mutation["new_text"]
        expected = mutation.get("expected_occurrences", 1)
        observed = source.count(old_text)
        if observed != expected:
            raise ContractError(
                "replace_text occurrence mismatch: "
                f"expected {expected}, observed {observed}"
            )
        return source.replace(old_text, new_text, expected).encode("utf-8")

    raise ContractError(f"unsupported mutation mode: {mode}")


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Replace one file atomically from a same-directory fully flushed temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode if path.exists() else None
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.canary-", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temp_path, mode)
        os.replace(temp_path, path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _prepare_fresh_report(path: Path) -> None:
    """Ensure a nested proof receipt cannot be inherited from an earlier run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if not path.is_file():
            raise ContractError(f"floor report path is not a regular file: {path}")
        path.unlink()


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


def evaluate_clean_floor_baseline(
    floor_process: dict[str, Any],
    floor_receipt: dict[str, Any] | None,
) -> list[str]:
    """Require the exact clean checkout/environment to pass before mutation."""
    errors: list[str] = []
    if floor_process.get("returncode") != 0:
        errors.append("CLEAN_FLOOR_BASELINE_PROCESS_FAILED")
    if not isinstance(floor_receipt, dict) or floor_receipt.get("status") != "PASS":
        errors.append("CLEAN_FLOOR_BASELINE_RECEIPT_NOT_PASS")
    return errors


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


def run(
    contract_path: Path,
    report_path: Path,
    floor_report_path: Path,
    baseline_floor_report_path: Path | None = None,
) -> int:
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
    baseline_floor_process: dict[str, Any] = {}
    baseline_floor_receipt: dict[str, Any] | None = None
    if baseline_floor_report_path is None:
        baseline_floor_report_path = floor_report_path.with_name(
            floor_report_path.stem + "-clean" + floor_report_path.suffix
        )

    try:
        contract = load_contract(contract_path)
        report["canary_id"] = contract["canary_id"]
        report["target_path"] = contract["target_path"]
        report["proof_ceiling"] = contract.get("proof_ceiling")
        target = _repo_path(contract["target_path"])
        original = target.read_bytes()
        before_digest = _digest(original)
        mutated_bytes = _apply_declared_mutation(original, contract["mutation"])

        witness_argv = command_argv(contract["witness"]["argv"])
        clean_witness = run_command(witness_argv)
        report["clean_witness"] = clean_witness
        if clean_witness["returncode"] != 0:
            report["state"] = "CLEAN_WITNESS_FAILED"
            report["proof_errors"] = ["CLEAN_WITNESS_FAILED"]
            return 1
        report["state"] = "CLEAN_WITNESS_PROVEN"

        runner = _repo_path(contract["full_floor"]["runner"])
        _prepare_fresh_report(baseline_floor_report_path)
        baseline_floor_process = run_command(
            [
                sys.executable,
                str(runner.relative_to(REPO_ROOT)),
                "--report",
                str(baseline_floor_report_path),
            ]
        )
        report["baseline_floor_process"] = baseline_floor_process
        if baseline_floor_report_path.is_file():
            baseline_floor_receipt = _read_json(baseline_floor_report_path)
            report["baseline_floor_receipt"] = {
                "schema_version": baseline_floor_receipt.get("schema_version"),
                "status": baseline_floor_receipt.get("status"),
                "failed_step": baseline_floor_receipt.get("failed_step"),
            }
        baseline_errors = evaluate_clean_floor_baseline(
            baseline_floor_process,
            baseline_floor_receipt,
        )
        if baseline_errors:
            report["state"] = baseline_errors[0]
            report["proof_errors"] = baseline_errors
            return 1
        report["state"] = "CLEAN_FLOOR_PROVEN"

        _atomic_write_bytes(target, mutated_bytes)
        report["state"] = "MUTATED"
        report["mutated_digest"] = _digest(target.read_bytes())

        mutated_witness = run_command(witness_argv)
        report["mutated_witness"] = mutated_witness
        report["state"] = "MUTATED_WITNESS_PROVEN"

        _prepare_fresh_report(floor_report_path)
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
        report["state"] = "FLOOR_PROCESS_OBSERVED"
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
                _atomic_write_bytes(target, original)
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
            report.get("state") == "FLOOR_PROCESS_OBSERVED"
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
        _atomic_write_bytes(report_path, (json.dumps(report, indent=2) + "\n").encode("utf-8"))

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
    parser.add_argument(
        "--baseline-floor-report",
        type=Path,
        default=DEFAULT_BASELINE_FLOOR_REPORT,
    )
    args = parser.parse_args(argv)
    contract = args.contract if args.contract.is_absolute() else REPO_ROOT / args.contract
    report = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    floor_report = args.floor_report if args.floor_report.is_absolute() else REPO_ROOT / args.floor_report
    baseline_floor_report = (
        args.baseline_floor_report
        if args.baseline_floor_report.is_absolute()
        else REPO_ROOT / args.baseline_floor_report
    )
    return run(
        contract.resolve(),
        report.resolve(),
        floor_report.resolve(),
        baseline_floor_report.resolve(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
