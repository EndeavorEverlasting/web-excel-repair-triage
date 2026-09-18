from __future__ import annotations

import importlib.util
import json
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prompt_parallel_dispatch",
    ROOT / "scripts/prompt_parallel_dispatch.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def lane(lane_id: str, *, deps: list[str] | None = None, surfaces: list[str] | None = None) -> dict:
    return {
        "lane_id": lane_id,
        "mission": f"execute {lane_id}",
        "dependencies": deps or [],
        "owned_mutation_surfaces": surfaces or [f"owned/{lane_id}"],
        "forbidden_surfaces": ["secrets/**"],
        "adapter": {"kind": "local_process", "rung": 5},
        "launch": {
            "mode": "argv",
            "argv": ["python", "-c", f"print('{lane_id}')"],
            "cwd": ".",
            "timeout_seconds": 30,
        },
        "expected_artifacts": [f"Outputs/{lane_id}.json"],
        "validation": [f"validate {lane_id}"],
        "convergence_owner": "coordinator",
        "status": "PLANNED",
    }


def manifest(*lanes: dict, width: int = 2, disposition: str = "REQUIRED", autonomy_gap=None) -> dict:
    return {
        "schema_version": "prompt-parallel-dispatch/v1",
        "run_id": "test-run",
        "graph_width": width,
        "parallel_disposition": disposition,
        "autonomy_gap": autonomy_gap,
        "lanes": list(lanes),
    }


class PromptParallelDispatchTests(unittest.TestCase):
    def test_validator_computes_deterministic_ready_wave_and_tiebreak(self) -> None:
        payload = manifest(lane("lane-b"), lane("lane-a"))
        summary = MOD.validate_manifest(payload)
        self.assertEqual(summary["graph_width"], 2)
        self.assertEqual(summary["waves"], [["lane-a", "lane-b"]])

    def test_validator_rejects_width_claim_that_does_not_match_dependencies(self) -> None:
        payload = manifest(lane("lane-a"), lane("lane-b", deps=["lane-a"]), width=2)
        with self.assertRaisesRegex(MOD.DispatchError, "graph_width mismatch"):
            MOD.validate_manifest(payload)

    def test_unordered_shared_mutation_surface_fails_closed(self) -> None:
        payload = manifest(
            lane("lane-a", surfaces=["docs/prompts.json"]),
            lane("lane-b", surfaces=["docs/prompts.json"]),
        )
        with self.assertRaisesRegex(MOD.DispatchError, "share mutation surfaces"):
            MOD.validate_manifest(payload)

    def test_shared_mutation_surface_is_valid_only_when_dependency_serializes_it(self) -> None:
        payload = manifest(
            lane("lane-a", surfaces=["docs/prompts.json"]),
            lane("lane-b", deps=["lane-a"], surfaces=["docs/prompts.json"]),
            width=1,
            disposition="NOT_APPLICABLE",
        )
        summary = MOD.validate_manifest(payload)
        self.assertEqual(summary["waves"], [["lane-a"], ["lane-b"]])

    def test_width_one_must_be_not_applicable(self) -> None:
        payload = manifest(lane("lane-a"), width=1, disposition="REQUIRED")
        with self.assertRaisesRegex(MOD.DispatchError, "width 1 must use NOT_APPLICABLE"):
            MOD.validate_manifest(payload)

    def test_degraded_parallelism_requires_an_autonomy_gap(self) -> None:
        payload = manifest(lane("lane-a"), lane("lane-b"), disposition="DEGRADED")
        with self.assertRaisesRegex(MOD.DispatchError, "DEGRADED requires AUTONOMY_GAP"):
            MOD.validate_manifest(payload)

    def test_required_width_two_actually_launches_two_lanes_concurrently(self) -> None:
        payload = manifest(lane("lane-b"), lane("lane-a"))
        barrier = threading.Barrier(2)
        lock = threading.Lock()
        active = 0
        max_active = 0

        def fake_runner(item: dict) -> dict:
            nonlocal active, max_active
            started_ns = time.time_ns()
            with lock:
                active += 1
                max_active = max(max_active, active)
            barrier.wait(timeout=2)
            # Hold the concurrent window long enough for wall-clock overlap proof.
            time.sleep(0.05)
            with lock:
                active -= 1
            return {
                "lane_id": item["lane_id"],
                "status": "PASS",
                "adapter_kind": item["adapter"]["kind"],
                "started_ns": started_ns,
                "ended_ns": time.time_ns(),
                "evidence": [{"type": "test", "proof": "barrier-reached"}],
            }

        receipt = MOD.dispatch_manifest(payload, runner=fake_runner)
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["observed_parallelism"])
        self.assertGreaterEqual(max_active, 2)
        self.assertEqual([item["lane_id"] for item in receipt["lanes"]], ["lane-a", "lane-b"])

    def test_required_parallelism_requires_overlapping_lane_intervals(self) -> None:
        payload = manifest(lane("lane-a"), lane("lane-b"))
        gate = threading.Lock()

        def serial_runner(item: dict) -> dict:
            with gate:
                started_ns = time.time_ns()
                time.sleep(0.02)
                ended_ns = time.time_ns()
            return {
                "lane_id": item["lane_id"],
                "status": "PASS",
                "adapter_kind": item["adapter"]["kind"],
                "started_ns": started_ns,
                "ended_ns": ended_ns,
                "evidence": [{"type": "test", "proof": "non-overlapping"}],
            }

        receipt = MOD.dispatch_manifest(payload, runner=serial_runner)
        self.assertFalse(receipt["observed_parallelism"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_unexpected_runner_exceptions_become_lane_failures(self) -> None:
        payload = manifest(lane("lane-a"), lane("lane-b"))

        def exploding_runner(item: dict) -> dict:
            raise RuntimeError(f"boom-{item['lane_id']}")

        receipt = MOD.dispatch_manifest(payload, runner=exploding_runner)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["observed_parallelism"])
        self.assertEqual({item["lane_id"] for item in receipt["lanes"]}, {"lane-a", "lane-b"})
        for item in receipt["lanes"]:
            self.assertEqual(item["status"], "FAIL")
            self.assertEqual(item["evidence"][0]["type"], "runner_error")
            self.assertIn("boom-", item["evidence"][0]["error"])

    def test_degraded_serial_execution_requires_explicit_opt_in_and_stays_unproven(self) -> None:
        payload = manifest(
            lane("lane-a"),
            lane("lane-b"),
            disposition="DEGRADED",
            autonomy_gap="bootstrap a safe command-addressable agent runner",
        )
        with self.assertRaisesRegex(MOD.DispatchError, "requires --allow-degraded-serial"):
            MOD.dispatch_manifest(payload, runner=lambda item: {})

        def passing_runner(item: dict) -> dict:
            return {
                "lane_id": item["lane_id"],
                "status": "PASS",
                "adapter_kind": item["adapter"]["kind"],
                "evidence": [{"type": "test", "proof": "serial"}],
            }

        receipt = MOD.dispatch_manifest(payload, runner=passing_runner, allow_degraded_serial=True)
        self.assertEqual(receipt["status"], "PASS")
        self.assertFalse(receipt["observed_parallelism"])
        self.assertEqual(receipt["autonomy_gap"], payload["autonomy_gap"])

    def test_declared_blocked_lane_is_never_launched_even_with_degraded_serial_opt_in(self) -> None:
        blocked_a = lane("lane-a")
        blocked_b = lane("lane-b")
        blocked_a["status"] = "BLOCKED"
        blocked_b["status"] = "BLOCKED"
        payload = manifest(
            blocked_a,
            blocked_b,
            disposition="DEGRADED",
            autonomy_gap="no autonomous repository runner is available",
        )
        calls: list[str] = []

        def forbidden_runner(item: dict) -> dict:
            calls.append(item["lane_id"])
            raise AssertionError("BLOCKED lane must not execute")

        receipt = MOD.dispatch_manifest(
            payload,
            runner=forbidden_runner,
            allow_degraded_serial=True,
        )
        self.assertEqual(calls, [])
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["observed_parallelism"])
        self.assertEqual(
            {item["status"] for item in receipt["lanes"]},
            {"BLOCKED"},
        )
        for item in receipt["lanes"]:
            self.assertEqual(item["evidence"][0]["type"], "manifest_status")

    def test_terminal_manifest_lane_state_requires_refresh_before_run(self) -> None:
        completed = lane("lane-a")
        completed["status"] = "PASS"
        payload = manifest(completed, width=1, disposition="NOT_APPLICABLE")
        with self.assertRaisesRegex(MOD.DispatchError, "is not executable"):
            MOD.dispatch_manifest(payload)

    def test_tracked_primary_manifest_validates_through_dispatch_owner(self) -> None:
        tracked = json.loads(
            (ROOT / "Outputs/prompt-parallel-dispatch/manifest.json").read_text(encoding="utf-8")
        )
        summary = MOD.validate_manifest(tracked)
        self.assertEqual(summary["run_id"], tracked["run_id"])
        self.assertEqual(summary["graph_width"], tracked["graph_width"])

    def test_runtime_tool_lane_is_machine_validated_but_cli_refuses_to_impersonate_runtime(self) -> None:
        external = lane("lane-a")
        external["adapter"] = {"kind": "native_agent", "rung": 1}
        external["launch"] = {
            "mode": "runtime_tool",
            "tool": "native_subagent",
            "operation": "spawn",
            "arguments": {"task": "bounded lane"},
        }
        payload = manifest(external, width=1, disposition="NOT_APPLICABLE")
        MOD.validate_manifest(payload)
        with self.assertRaisesRegex(MOD.DispatchError, "active agent runtime"):
            MOD.dispatch_manifest(payload)

    def test_receipt_cannot_claim_required_parallelism_without_observed_dispatch(self) -> None:
        payload = manifest(lane("lane-a"), lane("lane-b"))
        receipt = {
            "schema_version": "prompt-parallel-dispatch-receipt/v1",
            "run_id": "test-run",
            "status": "PASS",
            "parallel_disposition": "REQUIRED",
            "graph_width": 2,
            "observed_parallelism": False,
            "autonomy_gap": None,
            "lanes": [
                {"lane_id": "lane-a", "status": "PASS", "evidence": [{"type": "test"}]},
                {"lane_id": "lane-b", "status": "PASS", "evidence": [{"type": "test"}]},
            ],
        }
        with self.assertRaisesRegex(MOD.DispatchError, "observed_parallelism=true"):
            MOD.validate_receipt(payload, receipt)


if __name__ == "__main__":
    unittest.main()
