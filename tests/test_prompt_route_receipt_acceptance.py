from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "operant_prompt_route.py"
SPEC = importlib.util.spec_from_file_location("operant_prompt_route", MODULE_PATH)
assert SPEC and SPEC.loader
router = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = router
SPEC.loader.exec_module(router)

SHA_A = "a" * 40
SHA256_A = "sha256:" + "a" * 64
SHA256_B = "sha256:" + "b" * 64


def base_receipt(
    *,
    receipt_id: str = "route_test_001",
    actor_type: str = "workflow",
    authority_class: str = "deterministic-workflow",
    authority_rank: int = 800,
    source_prompt: str = "P07",
    target_prompt: str = "P08",
    state_version: int = 41,
    idempotency_key: str = "run-1:P07->P08",
    fingerprint: str = SHA256_B,
    priority: int = 500,
) -> dict:
    return {
        "schema_version": "prompt-route-receipt/v1",
        "receipt_id": receipt_id,
        "created_at": "2026-09-12T23:30:00Z",
        "repository": {
            "repository_id": "EndeavorEverlasting/web-excel-repair-triage",
            "revision": SHA_A,
            "registry_version": "prompt-registry/v1",
            "registry_digest": SHA256_A,
        },
        "request": {
            "route_id": f"request:{receipt_id}",
            "idempotency_key": idempotency_key,
            "request_fingerprint": fingerprint,
            "attempt": 1,
            "caused_by_receipt_id": None,
        },
        "actor": {
            "type": actor_type,
            "actor_id": f"{actor_type}-test",
            "run_id": "run-1",
            "session_id": "session-1" if actor_type == "human" else None,
            "authority_class": authority_class,
            "human_present": actor_type == "human",
        },
        "source": {
            "prompt_id": source_prompt,
            "state_version": state_version,
            "surface": "acceptance-test",
            "intent": "advance_owner",
        },
        "target": {
            "requested_prompt_id": target_prompt,
            "resolved_prompt_id": target_prompt,
            "canonical": True,
            "active": True,
            "resolution": "exact_id",
            "prompt_digest": SHA256_B,
        },
        "decision": {
            "reason_code": "TEST_TRANSITION",
            "reason": "Deterministic acceptance-test transition.",
            "decision_source": "human" if actor_type == "human" else "workflow-contract",
            "priority": priority,
            "confidence": None,
            "classifier": None,
        },
        "precedence": {
            "policy_id": "prompt-routing-precedence/v1",
            "authority_rank": authority_rank,
            "expected_state_version": state_version,
            "observed_state_version": state_version,
            "compare_and_set": "MATCH",
            "supersedes_receipt_id": None,
            "superseded_by_receipt_id": None,
        },
        "gates": {"aggregate": "PASS", "mutation_allowed": True, "results": []},
        "route": {
            "requested_transition": f"{source_prompt}->{target_prompt}",
            "status": "ROUTED",
            "route_version_before": state_version,
            "route_version_after": state_version + 1,
            "changed": True,
        },
        "presentation": {
            "requested_mode": "none",
            "applied_mode": "none",
            "surface": "headless",
            "device_class": "headless",
            "navigator_state_ref": None,
            "prompt_visible": False,
            "prompt_opened": False,
            "prompt_snapped": False,
            "focus_applied": False,
            "return_token": None,
            "failure_code": None,
        },
        "idempotency": {
            "scope": "run",
            "duplicate": False,
            "original_receipt_id": None,
            "replay_result": None,
        },
        "autonomy": {
            "status": "PASS",
            "human_dependency": False,
            "failure_class": None,
            "remediation_prompt_id": None,
        },
        "evidence": {
            "candidate_eval_eligible": True,
            "gold_eval_authority": False,
            "health_signal_eligible": True,
            "privacy_class": "sanitized-routing-metadata",
            "raw_user_content_stored": False,
        },
        "outcome": {
            "code": "ROUTED",
            "message": "Route applied.",
            "blocking": False,
            "next_action": None,
        },
    }


class PromptRouteReceiptAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = router.load_policy()
        self.state = router.RouteState(current_prompt_id="P07", version=41)
        self.ledger = router.RouteLedger()

    def assert_valid_final(self, receipt: dict) -> None:
        router.validate_receipt(receipt, self.policy, final=True)

    def assert_no_mutation(self, before, after) -> None:
        self.assertEqual(after.current_prompt_id, before.current_prompt_id)
        self.assertEqual(after.version, before.version)

    def test_higher_precedence_route_wins_conflict(self) -> None:
        human_navigation = base_receipt(
            receipt_id="route_human",
            actor_type="human",
            authority_class="interactive-navigation",
            authority_rank=100,
            target_prompt="P40",
            idempotency_key="human:P07->P40",
            fingerprint="sha256:" + "2" * 64,
        )
        workflow_route = base_receipt(
            receipt_id="route_workflow",
            target_prompt="P08",
            idempotency_key="workflow:P07->P08",
            fingerprint="sha256:" + "3" * 64,
        )
        results, new_state = router.resolve_competing_routes(
            [human_navigation, workflow_route], state=self.state, ledger=self.ledger
        )
        by_id = {item["receipt_id"]: item for item in results}
        self.assertEqual(by_id["route_workflow"]["route"]["status"], "ROUTED")
        self.assertEqual(by_id["route_human"]["route"]["status"], "PRECEDENCE_REJECTED")
        self.assertEqual(by_id["route_human"]["precedence"]["superseded_by_receipt_id"], "route_workflow")
        self.assertEqual(new_state, router.RouteState("P08", 42))
        for receipt in results:
            self.assert_valid_final(receipt)

    def test_precedence_is_independent_of_arrival_order(self) -> None:
        low = base_receipt(
            receipt_id="route_low",
            actor_type="agent",
            authority_class="authorized-agent",
            authority_rank=600,
            target_prompt="P32",
            idempotency_key="agent:P07->P32",
            fingerprint="sha256:" + "4" * 64,
        )
        high = base_receipt(
            receipt_id="route_high",
            authority_class="policy-safety-recovery",
            authority_rank=1000,
            target_prompt="P43",
            idempotency_key="recovery:P07->P43",
            fingerprint="sha256:" + "5" * 64,
        )
        forward, state_forward = router.resolve_competing_routes(
            [low, high], state=self.state, ledger=router.RouteLedger()
        )
        reverse, state_reverse = router.resolve_competing_routes(
            [high, low], state=self.state, ledger=router.RouteLedger()
        )
        self.assertEqual(state_forward, state_reverse)
        self.assertEqual(state_forward, router.RouteState("P43", 42))
        self.assertEqual(
            {r["receipt_id"]: r["route"]["status"] for r in forward},
            {r["receipt_id"]: r["route"]["status"] for r in reverse},
        )

    def test_equal_precedence_uses_deterministic_tiebreak_not_arrival_order(self) -> None:
        lexical_winner = base_receipt(
            receipt_id="route_z",
            target_prompt="P32",
            idempotency_key="tie:P07->P32",
            fingerprint="sha256:" + "1" * 64,
            priority=700,
        )
        lexical_loser = base_receipt(
            receipt_id="route_a",
            target_prompt="P40",
            idempotency_key="tie:P07->P40",
            fingerprint="sha256:" + "9" * 64,
            priority=700,
        )
        first, first_state = router.resolve_competing_routes(
            [lexical_loser, lexical_winner], state=self.state, ledger=router.RouteLedger()
        )
        second, second_state = router.resolve_competing_routes(
            [lexical_winner, lexical_loser], state=self.state, ledger=router.RouteLedger()
        )
        self.assertEqual(first_state, router.RouteState("P32", 42))
        self.assertEqual(first_state, second_state)
        for results in (first, second):
            statuses = {r["receipt_id"]: r["route"]["status"] for r in results}
            self.assertEqual(statuses["route_z"], "ROUTED")
            self.assertEqual(statuses["route_a"], "PRECEDENCE_REJECTED")

    def test_stale_compare_and_set_cannot_mutate(self) -> None:
        receipt = base_receipt(receipt_id="route_stale", target_prompt="P32")
        actual = router.RouteState(current_prompt_id="P28", version=42)
        result, after = router.evaluate_route(receipt, state=actual, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "STALE_REJECTED")
        self.assertEqual(result["precedence"]["compare_and_set"], "STALE")
        self.assertFalse(result["route"]["changed"])
        self.assert_no_mutation(actual, after)
        self.assert_valid_final(result)

    def test_matching_compare_and_set_mutates_exactly_once(self) -> None:
        receipt = base_receipt()
        result, after = router.evaluate_route(receipt, state=self.state, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "ROUTED")
        self.assertEqual(result["route"]["route_version_before"], 41)
        self.assertEqual(result["route"]["route_version_after"], 42)
        self.assertEqual(after, router.RouteState("P08", 42))
        self.assert_valid_final(result)

    def test_duplicate_idempotency_key_same_fingerprint_is_noop(self) -> None:
        original = base_receipt(receipt_id="route_original", idempotency_key="run-1:once")
        first, after_first = router.evaluate_route(original, state=self.state, ledger=self.ledger)
        replay = copy.deepcopy(original)
        replay["receipt_id"] = "route_replay"
        replay["request"]["attempt"] = 2
        second, after_second = router.evaluate_route(replay, state=after_first, ledger=self.ledger)
        self.assertEqual(first["route"]["status"], "ROUTED")
        self.assertEqual(second["route"]["status"], "IDEMPOTENT_NOOP")
        self.assertTrue(second["idempotency"]["duplicate"])
        self.assertEqual(second["idempotency"]["original_receipt_id"], "route_original")
        self.assertEqual(second["idempotency"]["replay_result"], "NOOP_ALREADY_APPLIED")
        self.assertEqual(after_first, after_second)
        self.assert_valid_final(second)

    def test_duplicate_idempotency_key_different_fingerprint_fails_closed(self) -> None:
        original = base_receipt(
            receipt_id="route_original",
            idempotency_key="run-1:shared",
            fingerprint="sha256:" + "6" * 64,
        )
        _, after_first = router.evaluate_route(original, state=self.state, ledger=self.ledger)
        conflict = base_receipt(
            receipt_id="route_conflict",
            source_prompt="P08",
            target_prompt="P32",
            state_version=42,
            idempotency_key="run-1:shared",
            fingerprint="sha256:" + "7" * 64,
        )
        result, after = router.evaluate_route(conflict, state=after_first, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "POLICY_REJECTED")
        self.assertEqual(result["decision"]["reason_code"], "IDEMPOTENCY_KEY_REUSE_MISMATCH")
        self.assert_no_mutation(after_first, after)
        self.assert_valid_final(result)

    def test_human_required_gate_becomes_autonomy_gap_and_routes_prototype(self) -> None:
        receipt = base_receipt(receipt_id="route_autonomy_gap", target_prompt="P08")
        receipt["gates"] = {
            "aggregate": "HUMAN_REQUIRED",
            "mutation_allowed": False,
            "results": [{
                "gate_id": "repair-decision",
                "classification": "REQUIRED",
                "outcome": "HUMAN_REQUIRED",
                "dependency_class": "UNIMPLEMENTED_AUTOMATION",
                "remediation_prompt_id": "P32",
                "evidence_ref": "validator://failure/report",
            }],
        }
        result, after = router.evaluate_route(receipt, state=self.state, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "AUTONOMY_GAP")
        self.assertEqual(result["autonomy"]["status"], "FAIL")
        self.assertTrue(result["autonomy"]["human_dependency"])
        self.assertEqual(result["autonomy"]["remediation_prompt_id"], "P32")
        self.assertEqual(result["outcome"]["next_action"], "AUTOMATE_OR_PROTOTYPE_GATE:repair-decision:P32")
        self.assert_no_mutation(self.state, after)
        self.assert_valid_final(result)

    def test_human_presence_does_not_satisfy_human_required_gate(self) -> None:
        receipt = base_receipt(
            receipt_id="route_human_present",
            actor_type="human",
            authority_class="operator-override",
            authority_rank=900,
            target_prompt="P08",
        )
        receipt["decision"]["decision_source"] = "manual-override"
        receipt["gates"] = {
            "aggregate": "HUMAN_REQUIRED",
            "mutation_allowed": False,
            "results": [{
                "gate_id": "missing-automation",
                "classification": "REQUIRED",
                "outcome": "HUMAN_REQUIRED",
                "dependency_class": "UNIMPLEMENTED_AUTOMATION",
                "remediation_prompt_id": "P07",
                "evidence_ref": "contract://missing-automation",
            }],
        }
        result, after = router.evaluate_route(receipt, state=self.state, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "AUTONOMY_GAP")
        self.assertEqual(result["autonomy"]["status"], "FAIL")
        self.assert_no_mutation(self.state, after)

    def test_irreducible_external_authority_is_still_autonomy_failure(self) -> None:
        receipt = base_receipt(receipt_id="route_external_authority")
        receipt["gates"] = {
            "aggregate": "HUMAN_REQUIRED",
            "mutation_allowed": False,
            "results": [{
                "gate_id": "external-legal-authority",
                "classification": "REQUIRED",
                "outcome": "HUMAN_REQUIRED",
                "dependency_class": "IRREDUCIBLE_EXTERNAL_AUTHORITY",
                "remediation_prompt_id": "P07",
                "evidence_ref": "policy://external-authority",
            }],
        }
        result, after = router.evaluate_route(receipt, state=self.state, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "HUMAN_GATE_REQUIRED")
        self.assertEqual(result["autonomy"]["status"], "FAIL")
        self.assertTrue(result["autonomy"]["human_dependency"])
        self.assert_no_mutation(self.state, after)

    def test_validation_failure_routes_remediation_instead_of_human_diagnosis(self) -> None:
        receipt = base_receipt(receipt_id="route_validation_failure")
        receipt["gates"] = {
            "aggregate": "BLOCKED",
            "mutation_allowed": False,
            "results": [{
                "gate_id": "repository-validation",
                "classification": "REQUIRED",
                "outcome": "FAIL",
                "dependency_class": "AUTOMATABLE_REPAIR",
                "remediation_prompt_id": "P32",
                "evidence_ref": "artifact://validation/failure.json",
            }],
        }
        result, after = router.evaluate_route(receipt, state=self.state, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "BLOCKED")
        self.assertEqual(result["outcome"]["next_action"], "ROUTE_REMEDIATION:P32")
        self.assertEqual(result["autonomy"]["status"], "DEGRADED")
        self.assertFalse(result["autonomy"]["human_dependency"])
        self.assert_no_mutation(self.state, after)

    def test_classifier_recommendation_cannot_mutate_until_auto_route_authorized(self) -> None:
        receipt = base_receipt(
            receipt_id="route_classifier_recommendation",
            actor_type="classifier",
            authority_class="classifier-recommendation",
            authority_rank=400,
            target_prompt="P32",
        )
        receipt["decision"].update({
            "decision_source": "classifier",
            "confidence": 0.92,
            "classifier": {
                "classifier_id": "prompt-finder-classifier",
                "classifier_version": "v1",
                "input_digest": SHA256_A,
                "rank": 1,
                "candidate_prompt_ids": ["P32", "P40", "P28"],
                "auto_route_authorized": False,
            },
        })
        result, after = router.evaluate_route(receipt, state=self.state, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "POLICY_REJECTED")
        self.assertEqual(result["decision"]["reason_code"], "AUTHORITY_NOT_MUTATING")
        self.assert_no_mutation(self.state, after)

    def test_headless_workflow_route_does_not_require_presentation_or_dom(self) -> None:
        receipt = base_receipt(receipt_id="route_headless")
        result, after = router.evaluate_route(receipt, state=self.state, ledger=self.ledger)
        self.assertEqual(result["route"]["status"], "ROUTED")
        self.assertEqual(result["presentation"]["applied_mode"], "none")
        self.assertFalse(result["presentation"]["prompt_visible"])
        self.assertEqual(after.current_prompt_id, "P08")

    def test_canonical_registry_resolver_binds_exact_prompt_without_guessing(self) -> None:
        if not (ROOT / "scripts/build_prompt_kit_registry.py").is_file():
            self.skipTest("isolated staging tree has no canonical registry builder")
        target, registry_digest = router.resolve_canonical_target("P32")
        self.assertEqual(target["resolved_prompt_id"], "P32")
        self.assertTrue(target["canonical"])
        self.assertTrue(target["active"])
        self.assertEqual(target["resolution"], "exact_id")
        self.assertTrue(target["prompt_digest"].startswith("sha256:"))
        self.assertTrue(registry_digest.startswith("sha256:"))
        missing, _ = router.resolve_canonical_target("P999999")
        self.assertIsNone(missing["resolved_prompt_id"] )
        self.assertEqual(missing["resolution"], "unresolved")

    def test_contract_and_json_schema_keep_autonomy_and_tiebreak_invariants(self) -> None:
        schema = json.loads((ROOT / "harness/schemas/prompt-route-receipt.v1.schema.json").read_text(encoding="utf-8"))
        contract = json.loads((ROOT / "harness/contracts/operant-prompt-routing.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "prompt-route-receipt/v1")
        self.assertIn("AUTONOMY_GAP", schema["$defs"]["route"]["properties"]["status"]["enum"])
        self.assertIn("autonomy", schema["required"])
        self.assertFalse(contract["precedence"]["arrival_order_authority"])
        self.assertEqual(
            contract["precedence"]["order"],
            ["authority_rank_desc", "decision_priority_desc", "request_fingerprint_asc", "receipt_id_asc"],
        )
        self.assertFalse(contract["autonomy_policy"]["human_required_is_success"])
        self.assertTrue(contract["autonomy_policy"]["prototype_before_handoff"])


if __name__ == "__main__":
    unittest.main()
