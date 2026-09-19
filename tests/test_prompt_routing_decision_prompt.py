from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts import evidence_spine_runtime
from scripts import prompt_routing_decision as routing

ROOT = Path(__file__).resolve().parents[1]


class PromptRoutingDecisionTests(unittest.TestCase):
    @staticmethod
    def request(**overrides):
        payload = {
            "schema": "prompt-kit.routing-request/v1",
            "eventId": "evt_route_req_rrb03_0001",
            "correlationId": "corr_rrb03_route_decision_0001",
            "causationId": "evt_obs_rrb03_source_0001",
            "createdAt": "2026-09-19T21:00:00Z",
            "producer": {
                "system": "agentswitchboard",
                "component": "prompt-router-client",
                "version": "1.0.0",
            },
            "observationEventId": "evt_obs_rrb03_source_0001",
            "task": {
                "firstMateTaskId": "rrb03-task",
                "repository": {
                    "fullName": "EndeavorEverlasting/web-excel-repair-triage",
                    "branch": "feat/example",
                    "headSha": "a" * 40,
                    "worktreeId": "wt-rrb03",
                },
            },
            "mission": {
                "groundingEpisodeId": "ge_rrb03_grounding_0001",
                "summary": "Continue from current registry-bound routing evidence.",
            },
            "executionSurface": "regular_ai_prompt",
            "currentPrompt": None,
            "evidenceState": {
                "observed": "VALIDATED",
                "claimed": "INTEGRATED",
            },
            "signals": ["evidence-promotion"],
            "correctionEvents": [],
            "constraints": {
                "forbiddenScopes": ["main"],
                "evidenceRefs": [],
                "rawTranscriptIncluded": False,
            },
            "routingPolicy": {
                "maxCandidates": 3,
                "crossSurfaceFallbackAllowed": False,
                "requireCurrentRegistry": True,
            },
            "idempotency": {
                "key": "idem_" + "1" * 64,
                "semanticSha256": "2" * 64,
            },
        }
        payload.update(overrides)
        semantic = {
            key: value
            for key, value in payload.items()
            if key not in {"eventId", "createdAt", "idempotency"}
        }
        semantic_sha = hashlib.sha256(
            json.dumps(
                semantic,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        payload["idempotency"] = {
            "key": "idem_"
            + hashlib.sha256(
                "|".join(
                    [
                        "prompt-kit.routing-request/v1",
                        payload["observationEventId"],
                        payload["mission"]["groundingEpisodeId"],
                        payload["executionSurface"],
                    ]
                ).encode("utf-8")
            ).hexdigest(),
            "semanticSha256": semantic_sha,
        }
        return payload

    @classmethod
    def setUpClass(cls) -> None:
        prompts, by_id, registry_sha, kit_version = routing._load_registry()
        cls.prompts = prompts
        cls.by_id = by_id
        cls.registry_sha = registry_sha
        cls.kit_version = kit_version
        cls.prompt_id = "P07"
        cls.prompt_record = by_id[cls.prompt_id]
        cls.prompt_ref = routing._prompt_ref(
            cls.prompt_record,
            registry_sha256=registry_sha,
            kit_version=kit_version,
        )

    def route_receipt(self, **overrides):
        payload = {
            "prompt_id": self.prompt_id,
            "prompt_revision": self.prompt_ref["promptSha256"],
            "destination": "firstmate",
            "provenance": "observed",
            "surface_id": "fm-asb",
            "invocation_id": None,
            "run_id": "rrb03-run",
        }
        payload.update(overrides)
        return evidence_spine_runtime.build_route_receipt(payload)

    def test_switch_decision_binds_current_registry_and_prompt_owner_text(self) -> None:
        request = self.request()
        receipt = self.route_receipt()
        decision = routing.build_routing_decision(request, receipt)

        self.assertEqual(decision["schema"], "prompt-kit.routing-decision/v1")
        self.assertEqual(decision["routingRequestEventId"], request["eventId"])
        self.assertEqual(decision["correlationId"], request["correlationId"])
        self.assertEqual(decision["causationId"], request["eventId"])
        self.assertEqual(decision["registry"]["kitVersion"], self.kit_version)
        self.assertEqual(decision["registry"]["registrySha256"], self.registry_sha)
        self.assertEqual(decision["decision"]["routeAction"], "SWITCH_PROMPT")
        self.assertEqual(decision["decision"]["primaryPrompt"], self.prompt_ref)
        self.assertEqual(decision["decision"]["intervention"], "REGROUND")
        self.assertEqual(decision["classification"]["outcomeClass"], "evidence-promotion")
        self.assertEqual(decision["proofGate"], self.prompt_record["proofGate"])
        self.assertEqual(decision["nextStep"], self.prompt_record["nextStep"])
        self.assertEqual(decision["requiredVariables"], [])
        self.assertEqual(decision["confidence"], "MEDIUM")

        semantic = {
            key: value
            for key, value in decision.items()
            if key not in {"eventId", "createdAt", "idempotency"}
        }
        expected_semantic = hashlib.sha256(
            json.dumps(
                semantic,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(decision["idempotency"]["semanticSha256"], expected_semantic)
        expected_idem = routing._idem_key(
            "prompt-kit.routing-decision/v1",
            request["eventId"],
            self.registry_sha,
        )
        self.assertEqual(decision["idempotency"]["key"], expected_idem)

    def test_exact_current_prompt_ref_keeps_prompt(self) -> None:
        decision = routing.build_routing_decision(
            self.request(currentPrompt=copy.deepcopy(self.prompt_ref)),
            self.route_receipt(),
        )
        self.assertEqual(decision["decision"]["routeAction"], "KEEP_CURRENT_PROMPT")
        self.assertIn("current-prompt-kept", decision["decision"]["reasonCodes"])

    def test_stale_same_id_current_prompt_switches_to_current_ref(self) -> None:
        stale = copy.deepcopy(self.prompt_ref)
        stale["promptSha256"] = "0" * 64
        decision = routing.build_routing_decision(
            self.request(currentPrompt=stale),
            self.route_receipt(),
        )
        self.assertEqual(decision["decision"]["routeAction"], "SWITCH_PROMPT")
        self.assertEqual(decision["decision"]["primaryPrompt"], self.prompt_ref)

    def test_frozen_asb_prompt_ref_rejects_four_digit_ids(self) -> None:
        invalid = {
            "id": "P1000",
            "kitVersion": self.kit_version,
            "registrySha256": self.registry_sha,
            "promptSha256": "0" * 64,
            "executionSurface": "regular_ai_prompt",
        }
        with self.assertRaisesRegex(
            routing.RoutingDecisionError,
            "frozen ASB promptRef protocol",
        ):
            routing._validate_prompt_ref(invalid, "fixture")

    def test_route_receipt_must_bind_current_prompt_revision(self) -> None:
        stale = self.route_receipt(prompt_revision="0" * 64)
        with self.assertRaisesRegex(routing.RoutingDecisionError, "prompt revision is stale"):
            routing.build_routing_decision(self.request(), stale)

    def test_retired_or_unknown_prompt_id_fails_closed(self) -> None:
        self.assertNotIn("P83", self.by_id)
        receipt = evidence_spine_runtime.build_route_receipt(
            {
                "prompt_id": "P83",
                "prompt_revision": "0" * 64,
                "destination": "firstmate",
                "provenance": "observed",
                "surface_id": "fm-asb",
            }
        )
        with self.assertRaisesRegex(routing.RoutingDecisionError, "not in the current registry"):
            routing.build_routing_decision(self.request(), receipt)

    def test_non_authoritative_route_receipts_cannot_select_a_prompt(self) -> None:
        for provenance, destination in (
            ("declared", "firstmate"),
            ("inferred", "firstmate"),
            ("unknown", None),
        ):
            with self.subTest(provenance=provenance):
                receipt = evidence_spine_runtime.build_route_receipt(
                    {
                        "prompt_id": self.prompt_id,
                        "prompt_revision": self.prompt_ref["promptSha256"],
                        "destination": destination,
                        "provenance": provenance,
                        "surface_id": "fm-asb",
                    }
                )
                with self.assertRaisesRegex(
                    routing.RoutingDecisionError,
                    "observed authoritative route receipt",
                ):
                    routing.build_routing_decision(self.request(), receipt)

    def test_tampered_route_receipt_fails_identity_verification(self) -> None:
        receipt = self.route_receipt()
        receipt["destination"] = "cursor-agent"
        with self.assertRaisesRegex(routing.RoutingDecisionError, "do not verify"):
            routing.build_routing_decision(self.request(), receipt)

    def test_routing_request_tamper_seal_rejects_post_builder_mutation(self) -> None:
        request = self.request()
        request["signals"] = ["routing"]
        with self.assertRaisesRegex(
            routing.RoutingDecisionError,
            "semanticSha256 does not verify",
        ):
            routing.build_routing_decision(request, self.route_receipt())

    def test_routing_request_idempotency_key_must_verify(self) -> None:
        request = self.request()
        request["idempotency"]["key"] = "idem_" + "0" * 64
        with self.assertRaisesRegex(
            routing.RoutingDecisionError,
            "idempotency key does not verify",
        ):
            routing.build_routing_decision(request, self.route_receipt())

    def test_request_must_require_current_registry_and_no_cross_surface_fallback(self) -> None:
        for policy in (
            {
                "maxCandidates": 3,
                "crossSurfaceFallbackAllowed": False,
                "requireCurrentRegistry": False,
            },
            {
                "maxCandidates": 3,
                "crossSurfaceFallbackAllowed": True,
                "requireCurrentRegistry": True,
            },
        ):
            with self.subTest(policy=policy), self.assertRaises(routing.RoutingDecisionError):
                routing.build_routing_decision(
                    self.request(routingPolicy=policy),
                    self.route_receipt(),
                )

    def test_cross_surface_request_fails_closed_instead_of_falling_back(self) -> None:
        request = self.request(executionSurface="gnhf_launch_artifact")
        with self.assertRaisesRegex(
            routing.RoutingDecisionError,
            "cross-surface fallback is forbidden",
        ):
            routing.build_routing_decision(request, self.route_receipt())

    def test_invalid_execution_surface_fails_closed(self) -> None:
        request = self.request(executionSurface="shell")
        with self.assertRaisesRegex(routing.RoutingDecisionError, "executionSurface is invalid"):
            routing.build_routing_decision(request, self.route_receipt())

    def test_correction_without_recovery_signal_routes_to_critique(self) -> None:
        request = self.request(
            signals=["routing"],
            correctionEvents=[{"kind": "explicit_correction", "corrective": True}],
        )
        decision = routing.build_routing_decision(request, self.route_receipt())
        self.assertEqual(decision["decision"]["intervention"], "CRITIQUE")
        self.assertEqual(decision["classification"]["outcomeClass"], "routing")

    def test_cli_failure_removes_stale_output_and_returns_bounded_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "request.json"
            receipt_path = root / "receipt.json"
            output_path = root / "decision.json"
            request_path.write_text("{not-json", encoding="utf-8")
            receipt_path.write_text(json.dumps(self.route_receipt()), encoding="utf-8")
            output_path.write_text('{"stale": true}\n', encoding="utf-8")
            self.assertEqual(
                routing.main(
                    [
                        "--request",
                        str(request_path),
                        "--route-receipt",
                        str(receipt_path),
                        "--output",
                        str(output_path),
                    ]
                ),
                2,
            )
            self.assertFalse(output_path.exists())

    def test_cli_refuses_to_overwrite_an_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "request.json"
            receipt_path = root / "receipt.json"
            original = json.dumps(self.request())
            request_path.write_text(original, encoding="utf-8")
            receipt_path.write_text(json.dumps(self.route_receipt()), encoding="utf-8")
            self.assertEqual(
                routing.main(
                    [
                        "--request",
                        str(request_path),
                        "--route-receipt",
                        str(receipt_path),
                        "--output",
                        str(request_path),
                    ]
                ),
                2,
            )
            self.assertEqual(request_path.read_text(encoding="utf-8"), original)

    def test_cli_emits_same_current_registry_bound_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "request.json"
            receipt_path = root / "receipt.json"
            output_path = root / "decision.json"
            request_path.write_text(json.dumps(self.request()), encoding="utf-8")
            receipt_path.write_text(json.dumps(self.route_receipt()), encoding="utf-8")
            self.assertEqual(
                routing.main(
                    [
                        "--request",
                        str(request_path),
                        "--route-receipt",
                        str(receipt_path),
                        "--output",
                        str(output_path),
                    ]
                ),
                0,
            )
            decision = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(decision["decision"]["primaryPrompt"], self.prompt_ref)
            self.assertEqual(decision["registry"]["registrySha256"], self.registry_sha)


if __name__ == "__main__":
    unittest.main()
