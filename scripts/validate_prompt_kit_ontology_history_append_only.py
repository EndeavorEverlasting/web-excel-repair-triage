#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import stat
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HISTORY_LEDGER = ROOT / "docs" / "prompt-kit-ontology-history.v1.json"
HISTORY_REPO_PATH = HISTORY_LEDGER.relative_to(ROOT).as_posix()
HISTORY_SCHEMA = "prompt-kit-ontology-history/v1"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def git_text(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise ValueError(detail)
    return completed.stdout


def load_history_at_ref(ref: str) -> dict[str, Any]:
    ref = ref.strip()
    if not ref:
        raise ValueError("baseline ref is required")
    git_text("rev-parse", "--verify", f"{ref}^{{commit}}")
    raw = git_text("show", f"{ref}:{HISTORY_REPO_PATH}")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"{HISTORY_REPO_PATH} at {ref} must contain a JSON object")
    return payload


def validate_append_only_history(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    baseline_records = baseline.get("records")
    current_records = current.get("records")

    if baseline.get("schema_version") != HISTORY_SCHEMA:
        errors.append("baseline ontology history ledger schema mismatch")
    if current.get("schema_version") != HISTORY_SCHEMA:
        errors.append("current ontology history ledger schema mismatch")
    if baseline.get("append_only") is not True:
        errors.append("baseline ontology history ledger is not append-only")
    if current.get("append_only") is not True:
        errors.append("current ontology history ledger is not append-only")
    if not isinstance(baseline_records, list):
        errors.append("baseline ontology history records must be an array")
        return errors
    if not isinstance(current_records, list):
        errors.append("current ontology history records must be an array")
        return errors

    if len(current_records) < len(baseline_records):
        errors.append(
            "append-only violation: current ontology history dropped one or more prior records"
        )
        return errors

    for index, prior in enumerate(baseline_records):
        candidate = current_records[index]
        if candidate != prior:
            record_id = prior.get("record_id") if isinstance(prior, dict) else None
            suffix = f" ({record_id})" if isinstance(record_id, str) and record_id.strip() else ""
            errors.append(
                f"append-only violation: prior history record {index}{suffix} changed or moved"
            )
    return errors


def validate(baseline_ref: str) -> dict[str, Any]:
    baseline = load_history_at_ref(baseline_ref)
    current = load_json(HISTORY_LEDGER)
    errors = validate_append_only_history(baseline, current)
    return {
        "schema_version": "prompt-kit-ontology-history-append-only-validation/v1",
        "status": "PASS" if not errors else "FAIL",
        "baseline_ref": baseline_ref,
        "baseline_records": len(baseline.get("records") or []),
        "current_records": len(current.get("records") or []),
        "errors": errors,
        "proof_ceiling": (
            "Repository Git-history comparison only. This validator proves that every record present "
            "in the supplied baseline ledger remains byte-for-JSON-value identical at the same prefix "
            "position in the current ledger; it does not prove that any runtime event occurred."
        ),
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    existing_mode = stat.S_IMODE(path.stat().st_mode) if path.is_file() else None
    with TemporaryDirectory(dir=path.parent, prefix=f".{path.name}.") as temp_dir:
        temp_path = Path(temp_dir) / path.name
        temp_path.write_text(payload, encoding="utf-8")
        if existing_mode is not None:
            temp_path.chmod(existing_mode)
        temp_path.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate(args.baseline_ref)
        if args.output:
            write_report(args.output, report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Prompt Kit ontology append-only validation failed: {exc}", file=sys.stderr)
        return 2
    if args.summary or not args.output:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "baseline_ref": report["baseline_ref"],
                    "baseline_records": report["baseline_records"],
                    "current_records": report["current_records"],
                    "errors": report["errors"],
                },
                sort_keys=True,
            )
        )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
