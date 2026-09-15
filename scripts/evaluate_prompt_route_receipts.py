#!/usr/bin/env python3
"""Evaluate the deterministic prompt-route-receipt/v1 control plane."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_OUTPUT = ROOT / "Outputs/repository-ai-evals/prompt-route-receipts.json"
CASES = ROOT / "harness/evals/fixtures/prompt-route-receipt-cases.v1.json"
TEST_MODULE = "tests.test_prompt_route_receipt_acceptance"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class CapturingResult(unittest.TextTestResult):
    def startTest(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        super().startTest(test)
        self._current_id = test.id()


def run_eval() -> dict[str, Any]:
    fixture = json.loads(CASES.read_text(encoding="utf-8"))
    if fixture.get("schema_version") != "prompt-route-receipt-cases/v1":
        raise RuntimeError("unsupported prompt route eval fixture schema")
    declared = fixture.get("cases")
    if not isinstance(declared, list) or not declared:
        raise RuntimeError("prompt route eval fixture must declare cases")

    suite = unittest.defaultTestLoader.loadTestsFromName(TEST_MODULE)
    test_ids = [test.id() for test in _flatten(suite)]
    stream = open(os.devnull, "w", encoding="utf-8")
    try:
        runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=CapturingResult)
        result = runner.run(suite)
    finally:
        stream.close()

    failures = {test.id(): text for test, text in result.failures}
    errors = {test.id(): text for test, text in result.errors}
    skipped = {test.id(): reason for test, reason in result.skipped}
    tests: list[dict[str, Any]] = []
    for test_id in test_ids:
        if test_id in failures:
            status, detail = "FAIL", failures[test_id]
        elif test_id in errors:
            status, detail = "ERROR", errors[test_id]
        elif test_id in skipped:
            status, detail = "SKIP", skipped[test_id]
        else:
            status, detail = "PASS", None
        tests.append({"id": test_id, "status": status, "detail": detail})

    status = "PASS" if result.wasSuccessful() else "FAIL"
    return {
        "schema_version": "prompt-route-receipt-eval-result/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "surface": fixture.get("surface"),
        "declared_case_count": len(declared),
        "failure_classes": sorted({str(case.get("failure_class")) for case in declared}),
        "tests_total": result.testsRun,
        "tests_passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        "tests_failed": len(result.failures) + len(result.errors),
        "tests_skipped": len(result.skipped),
        "tests": tests,
        "proof": {
            "precedence_arrival_order_independent": status == "PASS",
            "deterministic_tiebreak_exercised": status == "PASS",
            "compare_and_set_staleness_exercised": status == "PASS",
            "idempotency_replay_exercised": status == "PASS",
            "human_dependency_is_autonomy_failure": status == "PASS"
        }
    }


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    try:
        payload = run_eval()
        _atomic_json(output, payload)
    except Exception as exc:
        print(f"prompt route eval error: {exc}", file=sys.stderr)
        return 2
    if args.summary:
        print(
            "prompt_route_receipt_eval "
            f"status={payload['status']} tests={payload['tests_passed']}/{payload['tests_total']} "
            f"failure_classes={len(payload['failure_classes'])}"
        )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
