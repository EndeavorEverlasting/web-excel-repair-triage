#!/usr/bin/env python3
"""Deterministically score P123 full-source / tail coverage receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "p123_source_coverage"
    / "drive_7UyhyhxdFsQ_20260910.v1.json"
)
DEFAULT_CONTRACT = ROOT / "harness" / "contracts" / "p123-source-coverage-proof.v1.json"
DEFAULT_OUTPUT = ROOT / "Outputs" / "p123-source-coverage-report.json"

FAILURE_CLASSES = {
    "SOURCE_EXTENT_MISMATCH",
    "MISSING_END_COVERAGE_RECEIPT",
    "UNACCOUNTED_TAIL_UNRECEIPTED",
    "COMPLETE_WITHOUT_FULL_ACCOUNTING",
    "FABRICATED_UNREPRESENTED_TAIL_FACTS",
    "COVERAGE_LEDGER_INCOMPLETE",
}

REQUIRED_RECEIPT_FIELDS = (
    "source_extent_seconds",
    "last_inspected_position_seconds",
    "full_source_coverage",
    "unaccounted_spans",
    "coverage_ledger",
    "explicit_end_coverage_receipt",
    "claims_specific_unrepresented_tail_facts",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_output_path(path: Path) -> None:
    outputs = (ROOT / "Outputs").resolve()
    try:
        path.resolve().relative_to(outputs)
    except ValueError as exc:
        raise SystemExit(f"P123 coverage eval report must remain under {outputs}") from exc


def _write_report_atomic(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _require_output_path(path)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name).resolve()
        _require_output_path(tmp_path)
        _require_output_path(path)
        os.replace(tmp_path, path)
        tmp_path = None
        _require_output_path(path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


def _require_nonneg_int(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"P123 coverage field {field} must be a non-negative integer")
    return value


def _validate_span(span: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(span, dict):
        raise ValueError(f"{field} entries must be objects")
    start = span.get("start_seconds")
    end = span.get("end_seconds")
    if type(start) is not int or type(end) is not int or start < 0 or end < 0:
        raise ValueError(f"{field} requires non-negative integer start_seconds/end_seconds")
    if end < start:
        raise ValueError(f"{field} end_seconds must be >= start_seconds")
    return span


def _validate_ledger_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ValueError("coverage_ledger entries must be objects")
    for key in ("span", "evidence", "disposition"):
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"coverage_ledger.{key} must be a non-empty string")
    finding_ids = entry.get("finding_ids", [])
    if not isinstance(finding_ids, list) or any(not isinstance(item, str) for item in finding_ids):
        raise ValueError("coverage_ledger.finding_ids must be a list of strings")
    return entry


def validate_coverage_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ValueError("coverage receipt must be an object")
    for key in REQUIRED_RECEIPT_FIELDS:
        if key not in receipt:
            raise ValueError(f"coverage receipt missing required field {key}")
    _require_nonneg_int(receipt["source_extent_seconds"], "source_extent_seconds")
    _require_nonneg_int(receipt["last_inspected_position_seconds"], "last_inspected_position_seconds")
    coverage = receipt["full_source_coverage"]
    if coverage not in {"PARTIAL", "COMPLETE"}:
        raise ValueError("full_source_coverage must be PARTIAL or COMPLETE")
    spans = receipt["unaccounted_spans"]
    if not isinstance(spans, list):
        raise ValueError("unaccounted_spans must be a list")
    for index, span in enumerate(spans):
        _validate_span(span, field=f"unaccounted_spans[{index}]")
    ledger = receipt["coverage_ledger"]
    if not isinstance(ledger, list):
        raise ValueError("coverage_ledger must be a list")
    for entry in ledger:
        _validate_ledger_entry(entry)
    if type(receipt["explicit_end_coverage_receipt"]) is not bool:
        raise ValueError("explicit_end_coverage_receipt must be boolean")
    if type(receipt["claims_specific_unrepresented_tail_facts"]) is not bool:
        raise ValueError("claims_specific_unrepresented_tail_facts must be boolean")
    return receipt


def load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "p123-source-coverage/v1":
        raise ValueError(f"unsupported P123 coverage fixture schema: {payload.get('schema_version')!r}")
    if payload.get("owner") != "P123" or payload.get("eval_owner") != "P67":
        raise ValueError("P123 coverage fixture must declare owner=P123 and eval_owner=P67")
    source = payload.get("source")
    if not isinstance(source, dict):
        raise ValueError("P123 coverage fixture source must be an object")
    for key in ("kind", "identity"):
        value = source.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"P123 source field {key} must be a non-empty string")
    _require_nonneg_int(source.get("duration_seconds"), "source.duration_seconds")
    validate_coverage_receipt(payload.get("baseline_coverage_receipt"))
    validate_coverage_receipt(payload.get("candidate_coverage_receipt"))
    expected = payload.get("expected")
    if not isinstance(expected, dict):
        raise ValueError("expected block must be an object")
    return payload


def load_contract(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "p123-source-coverage-proof/v1":
        raise ValueError(f"unsupported coverage contract schema: {payload.get('schema_version')!r}")
    classes = set(payload.get("failure_classes") or [])
    if classes != FAILURE_CLASSES:
        raise ValueError("coverage contract failure_classes drifted from scorer FAILURE_CLASSES")
    return payload


def _tail_unaccounted(receipt: dict[str, Any]) -> bool:
    extent = receipt["source_extent_seconds"]
    last = receipt["last_inspected_position_seconds"]
    if last >= extent:
        return False
    for span in receipt["unaccounted_spans"]:
        if span["start_seconds"] <= last and span["end_seconds"] >= extent:
            return False
    return True


def _ledger_covers_extent(receipt: dict[str, Any]) -> bool:
    extent = receipt["source_extent_seconds"]
    if not receipt["coverage_ledger"]:
        return False
    covered_to = 0
    for entry in receipt["coverage_ledger"]:
        span = entry["span"].strip()
        if "-" not in span:
            return False
        left, right = span.split("-", 1)
        try:
            start = int(left)
            end = int(right)
        except ValueError:
            return False
        if start > covered_to:
            return False
        covered_to = max(covered_to, end)
    return covered_to >= extent


def score_coverage_receipt(
    fixture: dict[str, Any],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    receipt = validate_coverage_receipt(receipt)
    source_duration = fixture["source"]["duration_seconds"]
    criteria: list[dict[str, Any]] = []

    def add(name: str, ok: bool, failure_class: str | None, detail: str, rule: str) -> None:
        criteria.append(
            {
                "id": name,
                "status": "PASS" if ok else "FAIL",
                "failure_class": None if ok else failure_class,
                "detail": detail,
                "rule": rule,
            }
        )

    extent_ok = receipt["source_extent_seconds"] == source_duration
    add(
        "source_extent_matches_fixture",
        extent_ok,
        "SOURCE_EXTENT_MISMATCH",
        (
            f"receipt extent {receipt['source_extent_seconds']} matches source duration {source_duration}"
            if extent_ok
            else f"receipt extent {receipt['source_extent_seconds']} != source duration {source_duration}"
        ),
        "Coverage receipt source_extent_seconds must equal the fixture source duration_seconds.",
    )

    end_receipt = receipt["explicit_end_coverage_receipt"] is True
    add(
        "explicit_end_coverage_receipt",
        end_receipt,
        "MISSING_END_COVERAGE_RECEIPT",
        "explicit end-coverage receipt present" if end_receipt else "explicit end-coverage receipt missing",
        "A coverage proof requires an explicit end-of-source / tail-check receipt flag.",
    )

    tail_gap = _tail_unaccounted(receipt)
    add(
        "unaccounted_tail_receipted",
        not tail_gap,
        "UNACCOUNTED_TAIL_UNRECEIPTED",
        (
            "no unreceipted tail gap"
            if not tail_gap
            else (
                f"tail after last_inspected={receipt['last_inspected_position_seconds']} "
                f"through extent={receipt['source_extent_seconds']} lacks an unaccounted span"
            )
        ),
        "When last_inspected_position_seconds is before source extent, unaccounted_spans must cover that tail.",
    )

    complete = receipt["full_source_coverage"] == "COMPLETE"
    complete_ok = (not complete) or (
        end_receipt
        and receipt["last_inspected_position_seconds"] >= receipt["source_extent_seconds"]
        and not receipt["unaccounted_spans"]
        and not tail_gap
    )
    add(
        "complete_requires_full_accounting",
        complete_ok,
        "COMPLETE_WITHOUT_FULL_ACCOUNTING",
        "COMPLETE accounting is coherent" if complete_ok else "COMPLETE claimed without full accounting",
        "COMPLETE is allowed only with end receipt, last_inspected >= extent, and empty unaccounted_spans.",
    )

    fabricated = receipt["claims_specific_unrepresented_tail_facts"] is True
    add(
        "no_fabricated_unrepresented_tail_facts",
        not fabricated,
        "FABRICATED_UNREPRESENTED_TAIL_FACTS",
        "no fabricated unrepresented-tail facts" if not fabricated else "fabricated unrepresented-tail facts claimed",
        "Absence of coverage evidence must not be replaced by invented facts about unrepresented source time.",
    )

    ledger_ok = _ledger_covers_extent(receipt)
    add(
        "coverage_ledger_covers_extent",
        ledger_ok,
        "COVERAGE_LEDGER_INCOMPLETE",
        "coverage_ledger covers source extent" if ledger_ok else "coverage_ledger does not cover source extent",
        "coverage_ledger spans must contiguously cover 0 through source_extent_seconds.",
    )

    failures = [item for item in criteria if item["status"] == "FAIL"]
    failure_classes = [item["failure_class"] for item in failures if item["failure_class"]]
    unknown = [item for item in failure_classes if item not in FAILURE_CLASSES]
    if unknown:
        raise AssertionError(f"unregistered failure classes: {unknown}")

    status = "FAIL" if failures else "PASS"
    return {
        "schema_version": "p123-source-coverage-result/v1",
        "case_id": fixture["case_id"],
        "status": status,
        "owner": "P123",
        "eval_owner": "P67",
        "failure_classes": failure_classes,
        "criteria": criteria,
        "receipt_sha256": _sha256_text(json.dumps(receipt, sort_keys=True, ensure_ascii=False)),
        "synthetic": bool(receipt.get("synthetic")),
        "proof_ceiling": (
            "Deterministic scoring proves only the encoded coverage-receipt criteria. "
            "A synthetic or repository-local PASS does not prove provider-observed full-source coverage."
        ),
    }


def compare_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    baseline = score_coverage_receipt(fixture, fixture["baseline_coverage_receipt"])
    candidate = score_coverage_receipt(fixture, fixture["candidate_coverage_receipt"])
    expected = fixture["expected"]
    errors: list[str] = []

    if baseline["status"] != expected["baseline_status"]:
        errors.append(f"baseline status expected {expected['baseline_status']}, got {baseline['status']}")
    if set(baseline["failure_classes"]) != set(expected["baseline_failure_classes"]):
        errors.append(
            "baseline failure classes expected "
            + ",".join(sorted(expected["baseline_failure_classes"]))
            + ", got "
            + ",".join(sorted(baseline["failure_classes"]))
        )
    if candidate["status"] != expected["candidate_status"]:
        errors.append(f"candidate status expected {expected['candidate_status']}, got {candidate['status']}")
    if set(candidate["failure_classes"]) != set(expected.get("candidate_failure_classes", [])):
        errors.append(
            "candidate failure classes expected "
            + ",".join(sorted(expected.get("candidate_failure_classes", [])))
            + ", got "
            + ",".join(sorted(candidate["failure_classes"]))
        )
    if candidate["status"] == "PASS" and not candidate["synthetic"]:
        errors.append("candidate PASS must remain explicitly synthetic until provider field proof exists")

    return {
        "schema_version": "p123-source-coverage-comparison/v1",
        "case_id": fixture["case_id"],
        "status": "PASS" if not errors else "FAIL",
        "baseline": baseline,
        "candidate": candidate,
        "errors": errors,
        "proof_ceiling": fixture.get("proof_ceiling"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate P123 full-source / tail coverage receipts.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--receipt", type=Path, help="Optional JSON coverage receipt to score alone")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    fixture_path = args.fixture.resolve()
    output_candidate = args.output.expanduser()
    if not output_candidate.is_absolute():
        output_candidate = ROOT / output_candidate
    output_path = output_candidate.resolve()
    if output_path == fixture_path:
        raise SystemExit("refusing to write P123 coverage report over input fixture")
    if args.receipt is not None and output_path == args.receipt.resolve():
        raise SystemExit("refusing to write P123 coverage report over receipt input")
    _require_output_path(output_path)

    load_contract(args.contract)
    fixture = load_fixture(args.fixture)
    if args.receipt:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        report = score_coverage_receipt(fixture, receipt)
    else:
        report = compare_fixture(fixture)

    _write_report_atomic(output_path, report)
    if args.summary:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
