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
        cls.schema = json.loads((cls.root / "harness/contracts/prompt-outcome-receipt.schema.v1.json").read_text(encoding="utf-8"))
        cls.contract = json.loads((cls.root / "harness/contracts/prompt-outcome-classification.v1.json").read_text(encoding="utf-8"))
        cls.fixture = json.loads((cls.root / "harness/evals/fixtures/prompt-outcome-classification-cases.v1.json").read_text(encoding="utf-8"))

    def test_contract_and_fixture_validator_pass(self) -> None:
        outcomes.validate_contract_files()
        counts = outcomes.validate_fixtures()
        self.assertEqual(set(counts), set(outcomes.FAILURE_CLASSES))
        self.assertTrue(all(counts[name] >= 1 for name in outcomes.FAILURE_CLASSES))

    def test_schema_exposes_exact_failure_taxonomy_and_evidence_states(self) -> None:
        self.assertEqual(tuple(self.schema["$defs"]["failure_class"]["enum"]), outcomes.FAILURE_CLASSES)
        self.assertEqual(self.contract["evidence_state_order"], ["PLANNED_DESIGNED", "TRACKED", "IMPLEMENTED", "WIRED_REACHABLE", "VALIDATED", "INTEGRATED", "DEPLOYED", "OBSERVED"])

    def test_raw_usage_and_single_dislike_remain_unknown(self) -> None:
        for signals in ([{"type":"prompt_opened"}], [{"type":"prompt_copied"}], [{"type":"prompt_invoked"}], [{"type":"prompt_favorited"}], [{"type":"prompt_dislike"}]):
            with self.subTest(signals=signals):
                decision = outcomes.classify_signals(signals, self.contract)
                self.assertEqual(decision["primary"], "unknown")
                self.assertEqual(decision["result"], "UNKNOWN")
                self.assertEqual(decision["actionability"], "INFORMATION_ONLY")

    def test_repetition_requires_threshold_and_no_progress(self) -> None:
        below = outcomes.classify_signals([{"type":"same_prompt_same_mission_repeat","occurrence_count":2}], self.contract)
        self.assertEqual(below["primary"], "unknown")
        stalled = outcomes.classify_signals([{"type":"same_prompt_same_mission_repeat","occurrence_count":3}], self.contract)
        self.assertEqual(stalled["primary"], "progression")
        progressing = outcomes.classify_signals([{"type":"same_prompt_same_mission_repeat","occurrence_count":5},{"type":"durable_state_advance"}], self.contract)
        self.assertEqual(progressing["primary"], "unknown")

    def test_evidence_promotion_outranks_environment_without_erasing_it(self) -> None:
        decision = outcomes.classify_signals([{"type":"environment_failure","cause":"provider outage"},{"type":"success_claim_with_unresolved_blocker"}], self.contract)
        self.assertEqual(decision["primary"], "evidence-promotion")
        self.assertEqual(decision["secondary"], ["environment"])
        self.assertEqual(decision["result"], "FAILURE")

    def test_environment_cause_does_not_become_execution_failure(self) -> None:
        decision = outcomes.classify_signals([{"type":"deterministic_action_failure"},{"type":"environment_failure","cause":"credential denied"}], self.contract)
        self.assertEqual(decision["primary"], "environment")
        self.assertEqual(decision["result"], "BLOCKED")

    def test_receipt_validation_rejects_actionable_unknown(self) -> None:
        case = next(c for c in self.fixture["cases"] if c["id"] == "unknown-single-ordinary-invocation")
        receipt = outcomes.receipt_from_case(case, outcomes.classify_signals(case["signals"], self.contract))
        receipt["classification"]["actionability"] = "ACTIONABLE_REPAIR"
        with self.assertRaisesRegex(outcomes.ContractError, "unknown classification cannot be actionable repair"):
            outcomes.validate_receipt(receipt)

    def test_receipt_validation_requires_evidence_for_proven_failure(self) -> None:
        case = next(c for c in self.fixture["cases"] if c["id"] == "durability-required-plan-absent")
        receipt = outcomes.receipt_from_case(case, outcomes.classify_signals(case["signals"], self.contract))
        receipt["evidence"] = []
        with self.assertRaisesRegex(outcomes.ContractError, "requires at least one evidence reference"):
            outcomes.validate_receipt(receipt)

    def test_success_receipt_has_no_failure_class_and_requires_evidence(self) -> None:
        receipt = {
            "schema_version":"prompt-outcome-receipt/v1", "receipt_id":"success/1",
            "invocation":{"invocation_id":"invocation/success-1","prompt_id":"P07","prompt_revision":"abc1234","surface_id":"agent"},
            "observer":{"observer_id":"validator-1","kind":"validator","surface_id":"repository"},
            "observation":{"type":"repository","summary":"Owning validator and exact integration proof satisfy the invocation contract."},
            "result":"SUCCESS",
            "classification":{"primary":None,"secondary":[],"confidence":"HIGH","attribution":"PROVEN","actionability":"INFORMATION_ONLY","rationale":"The declared acceptance gate is proven by bounded durable evidence."},
            "evidence":[{"kind":"validator","ref":"workflow:123","supports":"exact-head owning validation passed"}],
            "occurred_at":"2026-09-13T04:30:00Z"
        }
        outcomes.validate_receipt(receipt)
        missing = copy.deepcopy(receipt); missing["evidence"] = []
        with self.assertRaisesRegex(outcomes.ContractError, "SUCCESS receipt requires at least one evidence"):
            outcomes.validate_receipt(missing)

    def test_multiple_receipts_for_one_invocation_are_allowed_without_overwrite(self) -> None:
        base = next(c for c in self.fixture["cases"] if c["id"] == "unknown-external-runtime-unobserved")
        first = outcomes.receipt_from_case(base, outcomes.classify_signals(base["signals"], self.contract))
        later = copy.deepcopy(next(c for c in self.fixture["cases"] if c["id"] == "premature-terminal-safe-successor-remains")); later["id"] = "later-observer"
        second = outcomes.receipt_from_case(later, outcomes.classify_signals(later["signals"], self.contract))
        second["invocation"]["invocation_id"] = first["invocation"]["invocation_id"]
        second["related_receipt_ids"] = [first["receipt_id"]]; second["retrospective"] = True
        outcomes.validate_receipt(first); outcomes.validate_receipt(second)
        self.assertNotEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(first["invocation"]["invocation_id"], second["invocation"]["invocation_id"])
        self.assertEqual(first["classification"]["primary"], "unknown")
        self.assertEqual(second["classification"]["primary"], "premature-terminal")

    def test_every_declared_class_has_a_fixture(self) -> None:
        observed = {case["expected"]["primary"] for case in self.fixture["cases"]}
        self.assertEqual(observed, set(outcomes.FAILURE_CLASSES))


if __name__ == "__main__":
    unittest.main()
