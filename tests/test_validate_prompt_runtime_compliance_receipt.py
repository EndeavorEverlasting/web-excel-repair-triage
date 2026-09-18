from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts import validate_prompt_runtime_compliance_receipt as validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/prompt-runtime-compliance.v1.json"
POSITIVE = ROOT / "harness/evals/runtime-compliance/validator-fixtures/receipt.pass.v1.json"
NEGATIVE = ROOT / "harness/evals/runtime-compliance/validator-fixtures/receipt.fail.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def finding(result: dict, rule_id: str) -> dict:
    return next(f for f in result["findings"] if f["rule_id"] == rule_id)


class RuntimeComplianceValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load(CONTRACT)
        cls.validation_schema = cls.contract["validation_result_schema_definition"]
        cls.positive = load(POSITIVE)
        cls.negative = load(NEGATIVE)

    # -- controls ------------------------------------------------------------
    def test_positive_control_passes(self) -> None:
        result, code = validator.validate_receipt(self.positive)
        self.assertEqual(result["overall_result"], "PASS")
        self.assertEqual(code, 0)
        self.assertEqual(result["counts"]["FAIL"], 0)
        self.assertEqual(result["counts"]["UNKNOWN"], 0)

    def test_negative_control_fails_with_nonzero_exit(self) -> None:
        result, code = validator.validate_receipt(self.negative)
        self.assertEqual(result["overall_result"], "FAIL")
        self.assertEqual(code, 1)
        failed = {f["rule_id"] for f in result["findings"] if f["result"] == "FAIL"}
        self.assertIn("PRCR.TERMINAL.COMPLETE_GATE", failed)
        self.assertIn("PRCR.ACTION.NO_FALSE_PROOF_PROMOTION", failed)
        self.assertIn("PRCR.COMPLIANCE.PASS", failed)

    # -- result-shape / completeness ----------------------------------------
    def test_validation_result_conforms_to_embedded_schema(self) -> None:
        for receipt in (self.positive, self.negative):
            result, _ = validator.validate_receipt(receipt)
            errors = list(Draft202012Validator(self.validation_schema).iter_errors(result))
            self.assertEqual(errors, [], [e.message for e in errors])

    def test_every_contract_rule_emits_exactly_one_finding(self) -> None:
        result, _ = validator.validate_receipt(self.positive)
        rule_ids = [rule["rule_id"] for rule in self.contract["rules"]]
        finding_ids = [f["rule_id"] for f in result["findings"]]
        self.assertEqual(finding_ids, rule_ids)
        self.assertEqual(len(finding_ids), len(set(finding_ids)))

    def test_finding_severity_matches_contract(self) -> None:
        severity = {rule["rule_id"]: rule["severity"] for rule in self.contract["rules"]}
        result, _ = validator.validate_receipt(self.positive)
        for f in result["findings"]:
            self.assertEqual(f["severity"], severity[f["rule_id"]], f["rule_id"])

    def test_structural_schema_failure_short_circuits(self) -> None:
        bad = copy.deepcopy(self.positive)
        del bad["proof"]
        result, code = validator.validate_receipt(bad)
        self.assertEqual(code, 1)
        self.assertEqual(result["overall_result"], "INCONCLUSIVE")
        self.assertEqual([f["rule_id"] for f in result["findings"]], ["PRCR.SCHEMA.STRUCTURE"])

    # -- per-rule negative coverage -----------------------------------------
    def _assert_rule_fails(self, receipt: dict, rule_id: str) -> None:
        result, code = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, rule_id)["result"], "FAIL", rule_id)
        self.assertEqual(code, 1, rule_id)

    def test_recovery_required_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["boundary_events"][0]["recovery_sprint"]["required"] = False
        self._assert_rule_fails(bad, "PRCR.BOUNDARY.RECOVERY_REQUIRED")

    def test_recovery_opened_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["boundary_events"][0]["recovery_sprint"]["opened"] = False
        self._assert_rule_fails(bad, "PRCR.BOUNDARY.RECOVERY_OPENED")

    def test_first_action_progress_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["actions"][0]["progress_bearing"] = False
        self._assert_rule_fails(bad, "PRCR.BOUNDARY.FIRST_ACTION_PROGRESS")

    def test_partial_readback_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["actions"][0]["side_effect_state"] = "PARTIAL"
        bad["actions"][0]["target_identity"] = "pr:558"
        retry = copy.deepcopy(bad["actions"][0])
        retry.update({
            "action_id": "A-002", "sequence": 2, "started_at": "2026-09-18T12:03:31Z",
            "completed_at": "2026-09-18T12:03:45Z", "side_effect_state": "CONFIRMED",
            "retry_of_action_id": "A-001", "summary": "Blind retry of the partial mutation without readback.",
        })
        bad["actions"].append(retry)
        self._assert_rule_fails(bad, "PRCR.ACTION.PARTIAL_READBACK")

    def test_complete_gate_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["terminal"]["state"] = "COMPLETE"
        self._assert_rule_fails(bad, "PRCR.TERMINAL.COMPLETE_GATE")

    def test_no_false_proof_promotion_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["actions"][0]["proof_after"] = "DEPLOYED"
        bad["actions"][0]["evidence_refs"] = []
        self._assert_rule_fails(bad, "PRCR.ACTION.NO_FALSE_PROOF_PROMOTION")

    def test_no_promotion_from_blocked_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["proof"]["strongest_state"] = "OBSERVED"
        self._assert_rule_fails(bad, "PRCR.PROOF.NO_PROMOTION_FROM_BLOCKED")

    def test_pass_with_open_critical_violation_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["violations"].append({
            "violation_id": "V-001", "rule_id": "PRCR.BOUNDARY.RECOVERY_OPENED",
            "severity": "CRITICAL", "result": "FAIL", "family": "RUNTIME_BEHAVIOR",
            "status": "OPEN", "subject": "boundary_events",
            "message": "Recovery was required but never opened.", "regression_required": False,
            "regression_link_id": None, "evidence_refs": ["EV-001"],
        })
        self._assert_rule_fails(bad, "PRCR.VIOLATION.PASS_CRITICAL")

    def test_unresolved_reference_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["actions"][0]["boundary_event_id"] = "BE-999"
        self._assert_rule_fails(bad, "PRCR.REF.RESOLVES")

    def test_duplicate_identifier_fail(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["evidence"].append(copy.deepcopy(bad["evidence"][0]))
        self._assert_rule_fails(bad, "PRCR.ID.UNIQUE")

    def test_main_returns_nonzero_for_negative_control(self) -> None:
        self.assertEqual(validator.main([str(NEGATIVE), "--summary"]), 1)

    def test_main_returns_zero_for_positive_control(self) -> None:
        self.assertEqual(validator.main([str(POSITIVE), "--summary"]), 0)


if __name__ == "__main__":
    unittest.main()
