from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import evidence_spine_runtime as runtime

ROOT = Path(__file__).resolve().parents[1]


class EvidenceSpineRuntimeTests(unittest.TestCase):
    def test_continuation_recovery_supersedes_completion_candidate(self) -> None:
        result = runtime.resolve_continuation(
            {
                "open_recovery": True,
                "agent_completion_candidate": True,
                "required_work_remaining": False,
                "outcome_receipts": [{"receipt_id": "r1"}],
            }
        )
        self.assertEqual(result["disposition"], "recover")
        self.assertFalse(result["completion_candidate_honored"])

    def test_continuation_complete_when_gates_clear(self) -> None:
        result = runtime.resolve_continuation(
            {
                "open_recovery": False,
                "required_work_remaining": False,
                "agent_completion_candidate": True,
            }
        )
        self.assertEqual(result["disposition"], "complete")
        self.assertTrue(result["completion_candidate_honored"])

    def test_inferred_destination_not_authoritative(self) -> None:
        routed = runtime.classify_route_destination(
            destination="cursor-agent",
            provenance="inferred",
        )
        self.assertFalse(routed["authoritative"])
        self.assertEqual(routed["effective_destination"], "unknown")

    def test_unknown_destination_allowed_for_clipboard_path(self) -> None:
        routed = runtime.classify_route_destination(destination=None, provenance="unknown")
        self.assertEqual(routed["effective_destination"], "unknown")

    def test_observation_rejects_raw_clipboard(self) -> None:
        result = runtime.accept_observation_event(
            {"kind": "copy", "prompt_id": "P07", "clipboard": "SECRET"}
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "privacy_rejected")

    def test_ordinary_observation_is_not_failure(self) -> None:
        result = runtime.accept_observation_event(
            {"kind": "copy", "prompt_id": "P07", "provenance": "observed"}
        )
        self.assertTrue(result["accepted"])
        self.assertFalse(result["is_failure"])

    def test_recurrence_thresholds_and_dedupe(self) -> None:
        occ = [
            {"contract_failure_id": "cf-1", "failure_kind": "generic", "receipt_id": "a"},
            {"contract_failure_id": "cf-1", "failure_kind": "generic", "receipt_id": "b"},
            {"contract_failure_id": "cf-1", "failure_kind": "generic", "receipt_id": "c"},
            {"contract_failure_id": "cf-2", "failure_kind": "deterministic_contradiction", "receipt_id": "d"},
        ]
        findings = {f["contract_failure_id"]: f for f in runtime.aggregate_recurrence(occ)["findings"]}
        self.assertEqual(findings["cf-1"]["state"], "confirmed_recurrence")
        self.assertEqual(findings["cf-1"]["count"], 3)
        self.assertEqual(findings["cf-2"]["state"], "confirmed_recurrence")
        self.assertEqual(findings["cf-2"]["threshold"], 1)

    def test_post_fix_recurrence_reopens_monitoring(self) -> None:
        occ = [
            {"contract_failure_id": "cf-3", "failure_kind": "generic", "receipt_id": "a"},
            {"contract_failure_id": "cf-3", "failure_kind": "generic", "receipt_id": "b"},
            {
                "contract_failure_id": "cf-3",
                "failure_kind": "generic",
                "receipt_id": "c",
                "post_fix": True,
            },
        ]
        finding = runtime.aggregate_recurrence(occ)["findings"][0]
        self.assertEqual(finding["state"], "monitoring_reopened")

    def test_work_request_requires_bounded_inputs(self) -> None:
        finding = {
            "state": "confirmed_recurrence",
            "contract_failure_id": "cf-1",
            "receipt_ids": ["a", "b", "c"],
        }
        self.assertEqual(runtime.compile_work_request(finding)["compiled"], False)
        finding.update(
            {
                "remediation_owner": "P07",
                "observed_behavior": "agent stops at PR",
                "expected_behavior": "merge when green",
                "acceptance_criteria": "contained on main",
                "proof_requirements": "merge-base ancestor check",
            }
        )
        compiled = runtime.compile_work_request(finding)
        self.assertTrue(compiled["compiled"])
        self.assertEqual(compiled["remediation_owner"], "P07")

    def test_cli_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            path.write_text(
                json.dumps({"required_work_remaining": True}),
                encoding="utf-8",
            )
            self.assertEqual(runtime.main(["resolve", "--evidence", str(path)]), 0)

    def test_contract_file_present(self) -> None:
        contract = json.loads(
            (ROOT / "harness/contracts/evidence-spine-continuation.v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            contract["schema_version"], "evidence-spine-continuation-disposition/v1"
        )


if __name__ == "__main__":
    unittest.main()
