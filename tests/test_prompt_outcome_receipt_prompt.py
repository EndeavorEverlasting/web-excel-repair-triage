from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import validate_prompt_outcome_receipts as outcomes


class PromptOutcomeReceiptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.schema = json.loads(
            (cls.root / "harness/contracts/prompt-outcome-receipt.schema.v1.json").read_text(encoding="utf-8")
        )
        cls.contract = json.loads(
            (cls.root / "harness/contracts/prompt-outcome-classification.v1.json").read_text(encoding="utf-8")
        )
        cls.fixture = json.loads(
            (cls.root / "harness/evals/fixtures/prompt-outcome-classification-cases.v1.json").read_text(encoding="utf-8")
        )

    def case(self, case_id: str) -> dict:
        return next(case for case in self.fixture["cases"] if case["id"] == case_id)

    def receipt(self, case_id: str) -> dict:
        case = self.case(case_id)
        decision = outcomes.classify_signals(case["signals"], self.contract)
        return outcomes.receipt_from_case(case, decision)

    def test_contract_and_fixture_validator_pass(self) -> None:
        outcomes.validate_contract_files()
        counts = outcomes.validate_fixtures()
        self.assertEqual(set(counts), set(outcomes.FAILURE_CLASSES))
        self.assertTrue(all(counts[name] >= 1 for name in outcomes.FAILURE_CLASSES))

    def test_schema_exposes_symptom_cause_episode_and_intervention_taxonomies(self) -> None:
        self.assertEqual(tuple(self.schema["$defs"]["failure_class"]["enum"]), outcomes.FAILURE_CLASSES)
        self.assertEqual(tuple(self.schema["$defs"]["cause_family"]["enum"]), outcomes.CAUSE_FAMILIES)
        self.assertEqual(tuple(self.schema["$defs"]["intervention"]["enum"]), outcomes.INTERVENTIONS)
        self.assertEqual(self.contract["grounding_episode_policy"]["unit"], "grounding_episode")
        self.assertTrue(self.contract["grounding_recovery_protocol"]["fresh_session_is_last_resort"])

    def test_ordinary_prompt_usage_never_adds_correction_burden(self) -> None:
        metrics = outcomes.derive_interaction_metrics(
            "episode/clean-sprint",
            0.9,
            [],
            [
                {"type": "prompt_invoked"},
                {"type": "prompt_invoked"},
                {"type": "prompt_invoked"},
                {"type": "durable_state_advance"},
            ],
            "unknown",
            self.contract,
        )
        self.assertEqual(metrics["correction_burden"], 0.0)
        self.assertEqual(metrics["interaction_yield"], 0.9)
        self.assertEqual(metrics["divergence_pressure"], 0.1)
        self.assertEqual(metrics["intervention"], "CONTINUE")

    def test_distinct_sprints_do_not_share_correction_burden(self) -> None:
        with self.assertRaisesRegex(outcomes.ContractError, "not grounding episode"):
            outcomes.derive_interaction_metrics(
                "episode/sprint-a",
                0.7,
                [{
                    "event_id": "corr/sprint-b/1",
                    "grounding_episode_id": "episode/sprint-b",
                    "kind": "explicit_correction",
                    "corrective": True,
                }],
                [],
                "unknown",
                self.contract,
            )

    def test_correction_events_have_no_occurrence_count_field(self) -> None:
        schema = self.schema["$defs"]["correction_event"]
        self.assertNotIn("count", schema["properties"])
        self.assertTrue(
            self.contract["interaction_divergence_policy"]["correction_event_contract"]["event_count_field_forbidden"]
        )

    def test_same_correction_kind_uses_distinct_events_not_prompt_usage_count(self) -> None:
        metrics = outcomes.derive_interaction_metrics(
            "episode/repeat-correction",
            0.7,
            [
                {"event_id": "corr/repeat/1", "grounding_episode_id": "episode/repeat-correction", "kind": "corrective_repeat_request", "corrective": True},
                {"event_id": "corr/repeat/2", "grounding_episode_id": "episode/repeat-correction", "kind": "corrective_repeat_request", "corrective": True},
            ],
            [{"type": "prompt_invoked"}] * 20,
            "unknown",
            self.contract,
        )
        self.assertEqual(metrics["correction_burden"], 0.4)
        self.assertEqual(len(metrics["correction_events"]), 2)

    def test_non_corrective_operator_event_is_rejected(self) -> None:
        with self.assertRaisesRegex(outcomes.ContractError, "corrective must be true"):
            outcomes.derive_interaction_metrics(
                "episode/not-correction",
                0.8,
                [{"event_id": "operator/ordinary-use/1", "grounding_episode_id": "episode/not-correction", "kind": "corrective_repeat_request", "corrective": False}],
                [],
                "unknown",
                self.contract,
            )

    def test_fractional_occurrence_counts_are_rejected_not_truncated(self) -> None:
        with self.assertRaisesRegex(outcomes.ContractError, "must be an integer"):
            outcomes.classify_signals([{"type": "same_prompt_same_mission_repeat", "occurrence_count": 3.9}], self.contract)
        with self.assertRaisesRegex(outcomes.ContractError, "must be an integer"):
            outcomes.classify_signals([{"type": "manual_context_transfer", "occurrence_count": 2.1}], self.contract)

    def test_manual_context_transfer_matches_durability_contract_tuple(self) -> None:
        decision = outcomes.classify_signals([{"type": "manual_context_transfer", "occurrence_count": 2}], self.contract)
        self.assertEqual(
            (decision["result"], decision["confidence"], decision["attribution"], decision["actionability"]),
            ("FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR"),
        )

    def test_healthy_repeat_with_evidence_advance_remains_unknown(self) -> None:
        decision = outcomes.classify_signals(
            [{"type": "same_prompt_same_mission_repeat", "occurrence_count": 8}, {"type": "durable_state_advance"}],
            self.contract,
        )
        self.assertEqual(decision["primary"], "unknown")
        self.assertEqual(decision["result"], "UNKNOWN")

    def test_interaction_math_is_episode_scoped_and_deterministic(self) -> None:
        interaction = self.receipt("interaction-wrong-footing")["interaction"]
        self.assertEqual(interaction["grounding_episode_id"], "episode/wrong-footing")
        self.assertEqual(interaction["correction_burden"], 0.8)
        self.assertEqual(interaction["interaction_yield"], 0.305556)
        self.assertEqual(interaction["divergence_pressure"], 0.694444)
        self.assertEqual(interaction["intervention"], "REGROUND")
        self.assertIn("grounding", interaction["cause_candidates"])

    def test_restart_action_forces_rebootstrap(self) -> None:
        receipt = self.receipt("interaction-restart-forces-rebootstrap")
        self.assertEqual(receipt["interaction"]["intervention"], "REBOOTSTRAP")
        self.assertIn("recovery", receipt["interaction"]["cause_candidates"])

    def test_false_unavailable_claim_maps_to_action_space_candidate(self) -> None:
        receipt = self.receipt("interaction-action-space")
        self.assertEqual(receipt["classification"]["primary"], "execution")
        self.assertIn("action-space", receipt["interaction"]["cause_candidates"])

    def test_receipt_validation_applies_nested_schema_and_rejects_extra_fields(self) -> None:
        receipt = self.receipt("routing-review-proves-wrong-owner")
        receipt["evidence"][0]["raw_prompt"] = "should never fit"
        with self.assertRaisesRegex(outcomes.ContractError, "unsupported fields"):
            outcomes.validate_receipt(receipt)

    def test_receipt_validation_bounds_evidence_text(self) -> None:
        receipt = self.receipt("routing-review-proves-wrong-owner")
        receipt["evidence"][0]["ref"] = "x" * 241
        with self.assertRaisesRegex(outcomes.ContractError, "maxLength"):
            outcomes.validate_receipt(receipt)
        receipt = self.receipt("routing-review-proves-wrong-owner")
        receipt["evidence"][0]["supports"] = "line one\nline two"
        with self.assertRaisesRegex(outcomes.ContractError, "pattern"):
            outcomes.validate_receipt(receipt)

    def test_receipt_validation_enforces_primary_decision_tuple(self) -> None:
        receipt = self.receipt("execution-deterministic-action-failure")
        receipt["result"] = "BLOCKED"
        with self.assertRaisesRegex(outcomes.ContractError, "classification tuple mismatch"):
            outcomes.validate_receipt(receipt)

    def test_receipt_validation_rejects_tampered_interaction_metrics(self) -> None:
        receipt = self.receipt("interaction-dumb-zone")
        receipt["interaction"]["divergence_pressure"] = 0.01
        with self.assertRaisesRegex(outcomes.ContractError, "interaction metric mismatch"):
            outcomes.validate_receipt(receipt)

    def test_success_receipt_has_no_failure_class_and_requires_evidence(self) -> None:
        receipt = {
            "schema_version": "prompt-outcome-receipt/v1",
            "receipt_id": "success/1",
            "invocation": {"invocation_id": "invocation/success-1", "prompt_id": "P07", "prompt_revision": "abc1234", "surface_id": "agent"},
            "observer": {"observer_id": "validator-1", "kind": "validator", "surface_id": "repository"},
            "observation": {"type": "repository", "summary": "Owning validator and exact integration proof satisfy the invocation contract."},
            "result": "SUCCESS",
            "classification": {"primary": None, "secondary": [], "confidence": "HIGH", "attribution": "PROVEN", "actionability": "INFORMATION_ONLY", "rationale": "The declared acceptance gate is proven by bounded durable evidence."},
            "evidence": [{"kind": "validator", "ref": "workflow:123", "supports": "exact-head owning validation passed"}],
            "occurred_at": "2026-09-13T04:30:00Z",
        }
        outcomes.validate_receipt(receipt)
        missing = copy.deepcopy(receipt)
        missing["evidence"] = []
        with self.assertRaisesRegex(outcomes.ContractError, "SUCCESS receipt requires at least one evidence"):
            outcomes.validate_receipt(missing)

    def test_every_declared_class_has_fixture_coverage(self) -> None:
        observed = {case["expected"]["primary"] for case in self.fixture["cases"]}
        self.assertEqual(observed, set(outcomes.FAILURE_CLASSES))


if __name__ == "__main__":
    unittest.main()
