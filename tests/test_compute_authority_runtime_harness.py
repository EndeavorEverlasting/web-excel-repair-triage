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
from grade_run import grade_run  # noqa: E402
from init_run import initialize_run, materialize_workspace_evidence  # noqa: E402


class ComputeAuthorityRuntimeHarnessTests(unittest.TestCase):
    def tearDown(self) -> None:
        prefixes = (
            "runtime-test-",
            "privacy-test-",
            "exit-test-",
            "launch-test-",
            "capture-test-",
            "scope-test-",
            "pair-test-",
            "rep-test-",
        )
        for prefix in prefixes:
            for path in (EVAL / "runs").glob(prefix + "*"):
                shutil.rmtree(path, ignore_errors=True)

    def test_frozen_conditions_match_prompt_identities(self) -> None:
        contract = conditions.validate_conditions()
        self.assertTrue(contract["frozen"])
        self.assertEqual(contract["pilot"]["expected_runs"], 16)
        self.assertEqual(set(contract["conditions"]), {"control", "treatment"})

    def test_gen2_conditions_preserve_control_and_advance_treatment(self) -> None:
        v1 = conditions.validate_conditions()
        v2 = conditions.validate_conditions("v2")
        self.assertTrue(v2["frozen"])
        self.assertEqual(v2["generation"], "v2")
        self.assertEqual(v2["pilot"]["expected_runs"], 16)
        self.assertEqual(
            v2["conditions"]["control"]["prompt_contract_sha"],
            v1["conditions"]["control"]["prompt_contract_sha"],
        )
        self.assertNotEqual(
            v2["conditions"]["treatment"]["prompt_contract_sha"],
            v1["conditions"]["treatment"]["prompt_contract_sha"],
        )

    def test_gen2_selector_binds_gen2_prompt_snapshots(self) -> None:
        run_dir = initialize_run(
            case_id="TC01",
            condition="treatment",
            run_id="runtime-test-gen2",
            generation="v2",
        )
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        condition = json.loads((run_dir / "condition.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["generation"], "v2")
        self.assertIn("prompts/gen2/", condition["prompt_path"])

    def test_gen2_pilot_plan_is_balanced_and_labeled(self) -> None:
        plan = pilot.build_plan(generation="v2")
        self.assertEqual(plan["generation"], "v2")
        self.assertEqual(plan["planned_runs"], 16)
        self.assertEqual(plan["control_first_pairs"], 4)
        self.assertEqual(plan["treatment_first_pairs"], 4)

    def test_pilot_order_is_deterministic_balanced_and_paired(self) -> None:
        first = pilot.build_plan()
        second = pilot.build_plan()
        self.assertEqual(first, second)
        self.assertEqual(first["planned_runs"], 16)
        self.assertEqual(first["control_first_pairs"], 4)
        self.assertEqual(first["treatment_first_pairs"], 4)
        self.assertEqual(
            {item["case"] for item in first["pair_orders"]},
            {f"TC{i:02d}" for i in range(1, 9)},
        )
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

    def test_run_id_must_be_safe_single_path_component(self) -> None:
        with self.assertRaises(ValueError):
            initialize_run(case_id="TC01", condition="control", run_id="../escape")
        with self.assertRaises(ValueError):
            initialize_run(case_id="TC01", condition="control", run_id="/absolute")

    def _fake_adapter(self, directory: Path, *, mode: str) -> dict:
        script = directory / "adapter.py"
        body = r'''
import json
import pathlib
import sys

result = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
prompt = pathlib.Path(sys.argv[3])

if mode == "exit":
    print("SECRET RAW OUTPUT")
    raise SystemExit(7)

if mode == "forbidden":
    target = pathlib.Path("src/neighbor_a.py")
    target.write_text(target.read_text(encoding="utf-8") + "\n# forbidden mutation\n", encoding="utf-8")

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
  "validations": [{"id": "V1", "status": "PASS", "return_code": 0}],
  "outcomes": {"seeded_defects_found": 0}
}

if mode == "privacy":
    payload["response"] = "must never persist"
elif mode == "schema_only":
    payload = {"schema_version": "compute-authority-provider-capture/v1"}
elif mode == "failed":
    payload["status"] = "failed"
elif mode == "duplicate_index":
    payload["events"][2]["action_index"] = 2
elif mode == "out_of_order":
    payload["events"][1]["action_index"] = 3
    payload["events"][2]["action_index"] = 2
elif mode == "missing_outcomes":
    payload.pop("outcomes")
elif mode == "identity_mismatch":
    payload["model"] = "control-model" if "control" in prompt.name else "treatment-model"

result.write_text(json.dumps(payload), encoding="utf-8")
print("SECRET RAW OUTPUT")
'''
        script.write_text(textwrap.dedent(body), encoding="utf-8")
        return {
            "schema_version": "compute-authority-agent-adapter/v1",
            "argv": [sys.executable, str(script), "{result}", mode, "{prompt}"],
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
        self.assertEqual(capture["status"], "complete")
        self.assertEqual(capture["outcomes"]["seeded_defects_found"], 0)
        self.assertEqual(metrics["parallel_lanes_used"], 2)
        self.assertEqual(metrics["useful_actions_after_first_green"], 1)
        persisted = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in run_dir.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("SECRET RAW OUTPUT", persisted)

    def test_schema_only_and_failed_captures_fail_closed(self) -> None:
        for mode in ("schema_only", "failed"):
            with self.subTest(mode=mode):
                run_dir = initialize_run(case_id="TC01", condition="control", run_id=f"capture-test-{mode}")
                with tempfile.TemporaryDirectory() as td:
                    result = runtime_adapter.invoke_or_mark_invalid(self._fake_adapter(Path(td), mode=mode), run_dir)
                self.assertFalse(result["valid"])
                self.assertEqual(result["invalid"]["code"], "EVIDENCE_INCOMPLETE")
                self.assertFalse((run_dir / "provider-capture.json").exists())

    def test_action_index_and_required_outcome_invariants_fail_closed(self) -> None:
        for mode in ("duplicate_index", "out_of_order", "missing_outcomes"):
            with self.subTest(mode=mode):
                run_dir = initialize_run(case_id="TC01", condition="control", run_id=f"capture-test-{mode}")
                with tempfile.TemporaryDirectory() as td:
                    result = runtime_adapter.invoke_or_mark_invalid(self._fake_adapter(Path(td), mode=mode), run_dir)
                self.assertFalse(result["valid"])
                self.assertEqual(result["invalid"]["code"], "EVIDENCE_INCOMPLETE")

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

    def test_missing_adapter_executable_becomes_invalid_receipt(self) -> None:
        run_dir = initialize_run(case_id="TC01", condition="control", run_id="launch-test-one")
        config = {
            "schema_version": "compute-authority-agent-adapter/v1",
            "argv": ["__compute_authority_missing_executable__", "{result}"],
            "timeout_seconds": 5,
            "env_allowlist": [],
        }
        result = runtime_adapter.invoke_or_mark_invalid(config, run_dir)
        self.assertFalse(result["valid"])
        self.assertEqual(result["invalid"]["code"], "ADAPTER_LAUNCH_ERROR")
        self.assertFalse(result["invalid"]["metadata"]["raw_output_persisted"])

    def test_workspace_snapshot_detects_forbidden_mutation_before_grading(self) -> None:
        run_dir = initialize_run(case_id="TC02", condition="treatment", run_id="scope-test-one")
        with tempfile.TemporaryDirectory() as td:
            result = runtime_adapter.invoke_or_mark_invalid(self._fake_adapter(Path(td), mode="forbidden"), run_dir)
        self.assertTrue(result["valid"])
        changed = materialize_workspace_evidence(run_dir)
        self.assertIn("src/neighbor_a.py", changed)
        grade = grade_run(run_dir)
        self.assertEqual(grade["scope"]["forbidden_mutations"], 1)
        self.assertIn("SCOPE_CREEP", grade["failure_codes"])
        self.assertEqual(grade["result"], "fail")

    def test_deterministic_seeded_defect_probe_wins_over_provider_count(self) -> None:
        run_dir = initialize_run(
            case_id="TC01",
            condition="control",
            run_id="scope-test-deterministic-defects",
        )
        (run_dir / "metrics.json").write_text(
            json.dumps({"seeded_defects_found": 999}) + "\n",
            encoding="utf-8",
        )
        materialize_workspace_evidence(run_dir)
        grade = grade_run(run_dir)
        self.assertNotIn(
            "provider structural defect count",
            " ".join(grade["defects"]["notes"]),
        )
        self.assertLessEqual(
            grade["defects"]["seeded_defects_found"],
            grade["defects"]["seeded_defects_reachable"],
        )

    def test_grader_preserves_repetition_identity(self) -> None:
        run_dir = initialize_run(case_id="TC01", condition="control", repetition=2, run_id="rep-test-one")
        materialize_workspace_evidence(run_dir)
        grade = grade_run(run_dir)
        self.assertEqual(grade["repetition"], 2)

    def test_pair_runtime_identity_mismatch_invalidates_both_runs(self) -> None:
        plan = pilot.build_plan(cases=["TC01"])
        with tempfile.TemporaryDirectory() as td:
            receipt = pilot.execute_pilot(
                plan,
                pilot_id="pair-test-identity",
                adapter_config=self._fake_adapter(Path(td), mode="identity_mismatch"),
            )
        self.assertEqual(receipt["valid_runs"], 0)
        self.assertEqual(receipt["invalid_runs"], 2)
        self.assertEqual(receipt["blocker"], "INVALID_RUNS")
        self.assertEqual({run["invalid_code"] for run in receipt["runs"]}, {"PAIR_IDENTITY_MISMATCH"})
        for run in receipt["runs"]:
            run_dir = EVAL / "runs" / run["run_id"]
            self.assertFalse((run_dir / "grader-result.json").exists())

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

    def test_v2_capture_rejects_evaluative_fields(self) -> None:
        run_dir = initialize_run(case_id="TC01", condition="control", run_id="capture-test-v2-evaluative")
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "adapter_v2_eval.py"
            body = r'''
import json
import pathlib
import sys

result = pathlib.Path(sys.argv[1])

payload = {
  "schema_version": "compute-authority-provider-capture/v2",
  "provider": "fake-v2",
  "agent": "test-agent",
  "model": "test-model",
  "status": "complete",
  "termination_reason": "completed",
  "usage": {"tool_calls": 3, "latency_ms": 15},
  "events": [
    {"id": "a1", "kind": "action", "action_index": 1, "useful": True},
    {"id": "a2", "kind": "action", "action_index": 2, "first_green": True}
  ],
  "validations": []
}

result.write_text(json.dumps(payload), encoding="utf-8")
'''
            script.write_text(textwrap.dedent(body), encoding="utf-8")
            config = {
                "schema_version": "compute-authority-agent-adapter/v1",
                "argv": [sys.executable, str(script), "{result}"],
                "timeout_seconds": 30,
                "env_allowlist": [],
            }
            result = runtime_adapter.invoke_or_mark_invalid(config, run_dir)
        self.assertFalse(result["valid"])
        invalid = json.loads((run_dir / "invalid-run.json").read_text(encoding="utf-8"))
        self.assertEqual(invalid["code"], "CAPTURE_EVALUATIVE_REJECTED")
        self.assertIn("useful", invalid["detail"])
        self.assertFalse((run_dir / "provider-capture.json").exists())

    def test_v2_capture_accepts_neutral_telemetry(self) -> None:
        run_dir = initialize_run(case_id="TC06", condition="treatment", run_id="capture-test-v2-neutral")
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "adapter_v2_neutral.py"
            body = r'''
import json
import pathlib
import sys

result = pathlib.Path(sys.argv[1])

payload = {
  "schema_version": "compute-authority-provider-capture/v2",
  "provider": "fake-v2-neutral",
  "agent": "test-agent",
  "model": "test-model",
  "status": "complete",
  "termination_reason": "completed",
  "usage": {"tool_calls": 5, "input_tokens": 1000, "output_tokens": 500, "latency_ms": 20},
  "events": [
    {"id": "a1", "kind": "action", "action_index": 1, "category": "read", "started_ns": 100, "ended_ns": 200},
    {"id": "a2", "kind": "action", "action_index": 2, "category": "write", "started_ns": 250, "ended_ns": 350},
    {"id": "a3", "kind": "action", "action_index": 3, "category": "execute", "started_ns": 400, "ended_ns": 500},
    {"id": "h1", "kind": "hypothesis_test", "hypothesis_id": "hyp-1", "result_code": "pass"},
    {"id": "c1", "kind": "child_lane", "child_lane_id": "lane-1", "started_ns": 600, "ended_ns": 1000},
    {"id": "c2", "kind": "child_lane", "child_lane_id": "lane-2", "started_ns": 650, "ended_ns": 950}
  ],
  "validations": [
    {"id": "v1", "command": "validate.py", "return_code": 0, "started_ns": 1100, "ended_ns": 1200}
  ]
}

result.write_text(json.dumps(payload), encoding="utf-8")
'''
            script.write_text(textwrap.dedent(body), encoding="utf-8")
            config = {
                "schema_version": "compute-authority-agent-adapter/v1",
                "argv": [sys.executable, str(script), "{result}"],
                "timeout_seconds": 30,
                "env_allowlist": [],
            }
            result = runtime_adapter.invoke_or_mark_invalid(config, run_dir)
        self.assertTrue(result["valid"])
        capture = json.loads((run_dir / "provider-capture.json").read_text(encoding="utf-8"))
        metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(capture["schema_version"], "compute-authority-provider-capture/v2")
        self.assertEqual(capture["provider"], "fake-v2-neutral")
        self.assertEqual(capture["status"], "complete")
        self.assertNotIn("outcomes", capture)
        self.assertNotIn("contracts", capture)
        self.assertEqual(len(capture["events"]), 6)
        self.assertEqual(metrics["total_substantive_actions"], 3)
        self.assertEqual(metrics["parallel_lanes_used"], 2)
        self.assertNotIn("useful_compute_actions", metrics)
        self.assertNotIn("seeded_defects_found", metrics)


if __name__ == "__main__":
    unittest.main()
