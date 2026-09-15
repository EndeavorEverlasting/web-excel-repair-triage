from __future__ import annotations

import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "harness" / "evals" / "compute-authority"
SCRIPTS = EVAL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import conditions  # noqa: E402
import pilot  # noqa: E402
import runtime_adapter  # noqa: E402
from init_run import initialize_run  # noqa: E402


class ComputeAuthorityRuntimeHarnessTests(unittest.TestCase):
    def tearDown(self) -> None:
        for prefix in ("runtime-test-", "privacy-test-", "exit-test-"):
            for path in (EVAL / "runs").glob(prefix + "*"):
                shutil.rmtree(path, ignore_errors=True)

    def test_frozen_conditions_match_prompt_identities(self) -> None:
        contract = conditions.validate_conditions()
        self.assertTrue(contract["frozen"])
        self.assertEqual(contract["pilot"]["expected_runs"], 16)
        self.assertEqual(set(contract["conditions"]), {"control", "treatment"})

    def test_pilot_order_is_deterministic_balanced_and_paired(self) -> None:
        first = pilot.build_plan()
        second = pilot.build_plan()
        self.assertEqual(first, second)
        self.assertEqual(first["planned_runs"], 16)
        self.assertEqual(first["control_first_pairs"], 4)
        self.assertEqual(first["treatment_first_pairs"], 4)
        self.assertEqual({item["case"] for item in first["pair_orders"]}, {f"TC{i:02d}" for i in range(1, 9)})
        for pair in first["pair_orders"]:
            self.assertEqual(set(pair["order"]), {"control", "treatment"})

    def test_isolated_runs_bind_same_fixture_to_distinct_conditions(self) -> None:
        control = initialize_run(case_id="TC01", condition="control", run_id="runtime-test-control")
        treatment = initialize_run(case_id="TC01", condition="treatment", run_id="runtime-test-treatment")
        c_start = json.loads((control / "starting-state.json").read_text(encoding="utf-8"))
        t_start = json.loads((treatment / "starting-state.json").read_text(encoding="utf-8"))
        self.assertEqual(c_start["fixture_sha"], t_start["fixture_sha"])
        self.assertNotEqual(c_start["condition_sha"], t_start["condition_sha"])
        self.assertNotEqual(control / "workspace", treatment / "workspace")
        self.assertFalse((control / "workspace" / "evaluator.manifest.yaml").exists())
        self.assertFalse((treatment / "workspace" / "evaluator.manifest.yaml").exists())

    def _fake_adapter(self, directory: Path, *, mode: str) -> dict:
        script = directory / "adapter.py"
        body = """
import json, pathlib, sys
result = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
if mode == "exit":
    print("SECRET RAW OUTPUT")
    raise SystemExit(7)
payload = {
  "schema_version": "compute-authority-provider-capture/v1",
  "provider": "fake",
  "agent": "fixture-agent",
  "model": "fixture-model",
  "status": "complete",
  "termination_reason": "fixed_point",
  "usage": {"tool_calls": 4, "latency_ms": 10},
  "events": [
    {"id": "a1", "kind": "action", "action_index": 1, "useful": True},
    {"id": "a2", "kind": "action", "action_index": 2, "useful": True, "first_green": True},
    {"id": "a3", "kind": "action", "action_index": 3, "useful": True},
    {"id": "p1", "kind": "parallel_lane", "started_ns": 10, "ended_ns": 30},
    {"id": "p2", "kind": "parallel_lane", "started_ns": 20, "ended_ns": 40}
  ],
  "contracts": [{"id": "C1", "status": "PROVEN", "correct": True}],
  "validations": [{"id": "V1", "status": "PASS", "return_code": 0}]
}
if mode == "privacy":
    payload["response"] = "must never persist"
result.write_text(json.dumps(payload), encoding="utf-8")
print("SECRET RAW OUTPUT")
"""
        script.write_text(textwrap.dedent(body), encoding="utf-8")
        return {
            "schema_version": "compute-authority-agent-adapter/v1",
            "argv": [sys.executable, str(script), "{result}", mode],
            "timeout_seconds": 30,
            "env_allowlist": [],
        }

    def test_fake_adapter_persists_only_sanitized_structural_capture(self) -> None:
        run_dir = initialize_run(case_id="TC06", condition="treatment", run_id="runtime-test-fake")
        with tempfile.TemporaryDirectory() as td:
            result = runtime_adapter.invoke_or_mark_invalid(self._fake_adapter(Path(td), mode="ok"), run_dir)
        self.assertTrue(result["valid"])
        capture = json.loads((run_dir / "provider-capture.json").read_text(encoding="utf-8"))
        metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(capture["provider"], "fake")
        self.assertEqual(metrics["parallel_lanes_used"], 2)
        self.assertEqual(metrics["useful_actions_after_first_green"], 1)
        persisted = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in run_dir.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("SECRET RAW OUTPUT", persisted)

    def test_privacy_forbidden_provider_field_fails_closed(self) -> None:
        run_dir = initialize_run(case_id="TC01", condition="control", run_id="privacy-test-one")
        with tempfile.TemporaryDirectory() as td:
            result = runtime_adapter.invoke_or_mark_invalid(self._fake_adapter(Path(td), mode="privacy"), run_dir)
        self.assertFalse(result["valid"])
        invalid = json.loads((run_dir / "invalid-run.json").read_text(encoding="utf-8"))
        self.assertEqual(invalid["code"], "CAPTURE_PRIVACY_REJECTED")
        self.assertFalse((run_dir / "provider-capture.json").exists())

    def test_nonzero_adapter_exit_becomes_invalid_without_raw_output(self) -> None:
        run_dir = initialize_run(case_id="TC01", condition="control", run_id="exit-test-one")
        with tempfile.TemporaryDirectory() as td:
            result = runtime_adapter.invoke_or_mark_invalid(self._fake_adapter(Path(td), mode="exit"), run_dir)
        self.assertFalse(result["valid"])
        invalid = json.loads((run_dir / "invalid-run.json").read_text(encoding="utf-8"))
        self.assertEqual(invalid["code"], "ADAPTER_EXIT_NONZERO")
        persisted = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in run_dir.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("SECRET RAW OUTPUT", persisted)

    def test_plan_only_marks_runtime_unproven_not_passed(self) -> None:
        plan = pilot.build_plan(cases=["TC01"])
        self.assertEqual(plan["planned_runs"], 2)
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            rc = pilot.main([
                "--case", "TC01",
                "--pilot-id", "ci-no-runtime",
                "--plan-only",
                "--plan-output", str(out / "plan.json"),
                "--receipt-output", str(out / "receipt.json"),
            ])
            self.assertEqual(rc, 0)
            receipt = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["runtime_state"], "UNPROVEN_RUNTIME")
        self.assertEqual(receipt["planned_runs"], 2)
        self.assertEqual(receipt["valid_runs"], 0)
        self.assertEqual(receipt["invalid_runs"], 0)
        self.assertEqual(receipt["blocker"], "RUNTIME_UNAVAILABLE")
        self.assertFalse(receipt["effectiveness_promoted"])


if __name__ == "__main__":
    unittest.main()
