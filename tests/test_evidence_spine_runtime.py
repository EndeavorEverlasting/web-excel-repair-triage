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

    def test_route_receipt_observed_destination_is_authoritative_and_stable(self) -> None:
        route = {
            "prompt_id": "P07",
            "prompt_revision": "sha256:abc123",
            "destination": "cursor-agent",
            "provenance": "observed",
            "surface_id": "prompt-kit",
            "invocation_id": "inv-42",
            "run_id": "run-7",
        }
        first = runtime.build_route_receipt(route)
        second = runtime.build_route_receipt(dict(reversed(list(route.items()))))
        self.assertEqual(first["schema_version"], "evidence-spine-route-receipt/v1")
        self.assertTrue(first["authoritative"])
        self.assertEqual(first["destination_confidence"], "authoritative")
        self.assertEqual(first["effective_destination"], "cursor-agent")
        self.assertEqual(first["route_id"], second["route_id"])
        self.assertEqual(first["semantic_sha256"], second["semantic_sha256"])

    def test_route_receipt_inferred_destination_never_becomes_effective(self) -> None:
        receipt = runtime.build_route_receipt(
            {
                "prompt_id": "P115",
                "prompt_revision": "rev-1",
                "destination": "opencode",
                "provenance": "inferred",
                "surface_id": "agent-runtime",
            }
        )
        self.assertFalse(receipt["authoritative"])
        self.assertEqual(receipt["destination_confidence"], "inferred")
        self.assertEqual(receipt["destination"], "opencode")
        self.assertEqual(receipt["effective_destination"], "unknown")

    def test_route_receipt_unknown_supports_zero_metadata_destination(self) -> None:
        receipt = runtime.build_route_receipt(
            {
                "prompt_id": "P07",
                "prompt_revision": "rev-clipboard",
                "destination": None,
                "provenance": "unknown",
                "surface_id": "clipboard",
            }
        )
        self.assertFalse(receipt["authoritative"])
        self.assertEqual(receipt["destination_confidence"], "unknown")
        self.assertEqual(receipt["effective_destination"], "unknown")

    def test_route_receipt_declared_destination_is_non_authoritative(self) -> None:
        receipt = runtime.build_route_receipt(
            {
                "prompt_id": "P07",
                "prompt_revision": "rev-declared",
                "destination": "cursor-agent",
                "provenance": "declared",
                "surface_id": "manual-launch",
            }
        )
        self.assertFalse(receipt["authoritative"])
        self.assertEqual(receipt["destination_confidence"], "declared")
        self.assertEqual(receipt["destination"], "cursor-agent")
        self.assertEqual(receipt["effective_destination"], "unknown")

    def test_route_receipt_rejects_actor_identity_and_caller_fingerprint(self) -> None:
        base = {
            "prompt_id": "P07",
            "prompt_revision": "rev-1",
            "destination": "cursor-agent",
            "provenance": "observed",
            "surface_id": "prompt-kit",
        }
        for key, value in (
            ("user_id", "person-1"),
            ("session_id", "session-1"),
            ("request_fingerprint", "caller-controlled"),
            ("idempotency_key", "caller-controlled"),
            ("raw_prompt", "private text"),
        ):
            with self.subTest(key=key), self.assertRaises(runtime.ContinuationError):
                runtime.build_route_receipt({**base, key: value})

    def test_route_receipt_fail_closed_shape_and_identity(self) -> None:
        valid = {
            "prompt_id": "P07",
            "prompt_revision": "rev-1",
            "destination": "cursor-agent",
            "provenance": "observed",
            "surface_id": "prompt-kit",
        }
        invalid_cases = [
            {**valid, "prompt_id": "P9999"},
            {**valid, "prompt_revision": ""},
            {**valid, "surface_id": ""},
            {**valid, "provenance": "guessed"},
            {**valid, "destination": None},
            {**valid, "provenance": "unknown"},
            {**valid, "invocation_id": ""},
        ]
        for payload in invalid_cases:
            with self.subTest(payload=payload), self.assertRaises(runtime.ContinuationError):
                runtime.build_route_receipt(payload)

        changed = runtime.build_route_receipt({**valid, "destination": "opencode"})
        original = runtime.build_route_receipt(valid)
        self.assertNotEqual(original["route_id"], changed["route_id"])

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
