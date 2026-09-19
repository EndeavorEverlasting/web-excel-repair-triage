from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import validate_prompt_runtime_compliance_receipt as validator

ROOT = Path(__file__).resolve().parents[1]
POSITIVE = ROOT / "harness" / "evals" / "runtime-compliance" / "contract-fixtures" / "receipt.positive.v1.json"
NEGATIVE_PENDING = ROOT / "harness" / "evals" / "runtime-compliance" / "contract-fixtures" / "receipt.negative.pending-publication.v1.json"
NEGATIVE_READBACK = ROOT / "harness" / "evals" / "runtime-compliance" / "contract-fixtures" / "receipt.negative.ambiguous-no-readback.v1.json"


def load_positive() -> dict:
    return json.loads(POSITIVE.read_text(encoding="utf-8"))


def finding(result: dict, rule_id: str) -> dict:
    return next(row for row in result["findings"] if row["rule_id"] == rule_id)


def pilot_receipt() -> dict:
    return {
        "schema_version": "prompt-runtime-compliance-pilot-receipt/v1",
        "pilot_id": "fixture-pilot",
        "runtime_state": "UNPROVEN_RUNTIME",
        "planned_runs": 5,
        "valid_runs": 0,
        "invalid_runs": 0,
        "observed_runs": 0,
        "blocker": "RUNTIME_UNAVAILABLE",
        "runs": [],
        "proof_ceiling": "Repository harness evidence only; target runtime remains unobserved.",
    }


class PromptRuntimeComplianceValidatorTests(unittest.TestCase):
    def test_pilot_receipt_schema_is_supported_by_registered_artifact_validator(self) -> None:
        artifacts = json.loads((ROOT / "harness" / "artifacts.v1.json").read_text(encoding="utf-8"))
        artifact = next(
            item for item in artifacts["artifacts"]
            if item["id"] == "prompt-runtime-compliance-evidence"
        )
        self.assertIn(artifact["schema"], validator.SUPPORTED_SCHEMA_VERSIONS)
        result = validator.validate_pilot_receipt(pilot_receipt())
        self.assertEqual(result["overall_result"], "PASS")
        self.assertEqual(result["receipt_schema"], artifact["schema"])

    def test_pilot_receipt_count_mismatch_fails_closed(self) -> None:
        receipt = pilot_receipt()
        receipt["valid_runs"] = 1
        result = validator.validate_pilot_receipt(receipt)
        self.assertEqual(result["overall_result"], "FAIL")
        self.assertNotEqual(validator.exit_code(result), 0)

    def test_validate_path_dispatches_pilot_receipt_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pilot-receipt.json"
            path.write_text(json.dumps(pilot_receipt()), encoding="utf-8")
            result = validator.validate_path(path)
        self.assertEqual(result["schema_version"], "prompt-runtime-compliance-pilot-validation/v1")
        self.assertEqual(result["overall_result"], "PASS")

    def test_positive_contract_fixture_passes_and_covers_every_rule(self) -> None:
        result = validator.validate_receipt(load_positive())
        self.assertEqual(result["overall_result"], "PASS")
        self.assertEqual(
            {row["rule_id"] for row in result["findings"]},
            {row["rule_id"] for row in validator.CONTRACT["rules"]},
        )
        self.assertEqual(result["counts"]["FAIL"], 0)
        self.assertEqual(result["counts"]["UNKNOWN"], 0)

    def test_durable_negative_fixtures_fail_their_expected_rules(self) -> None:
        cases = (
            (NEGATIVE_PENDING, "PRCR.BOUNDARY.MATERIAL_PUBLICATION"),
            (NEGATIVE_READBACK, "PRCR.ACTION.PARTIAL_READBACK"),
        )
        for path, rule_id in cases:
            with self.subTest(path=path.name):
                receipt = json.loads(path.read_text(encoding="utf-8"))
                result = validator.validate_receipt(receipt)
                self.assertEqual(result["overall_result"], "FAIL")
                self.assertEqual(finding(result, rule_id)["result"], "FAIL")

    def test_duplicate_trace_identity_is_rejected(self) -> None:
        receipt = load_positive()
        receipt["actions"][0]["action_id"] = receipt["boundary_events"][0]["boundary_event_id"]
        receipt["boundary_events"][0]["recovery_sprint"]["first_executable_action_id"] = receipt["actions"][0]["action_id"]
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.ID.UNIQUE")["result"], "FAIL")
        self.assertEqual(result["overall_result"], "FAIL")

    def test_unknown_canonical_boundary_class_is_rejected(self) -> None:
        receipt = load_positive()
        receipt["boundary_events"][0]["class_id"] = "PS_NOT_A_REAL_CLASS"
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.BOUNDARY.CANONICAL_CLASS")["result"], "FAIL")

    def test_material_boundary_publication_cannot_remain_pending(self) -> None:
        receipt = load_positive()
        receipt["boundary_events"][0]["publication_ack"] = "PENDING"
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.BOUNDARY.MATERIAL_PUBLICATION")["result"], "FAIL")

    def test_required_recovery_sprint_must_open(self) -> None:
        receipt = load_positive()
        sprint = receipt["boundary_events"][0]["recovery_sprint"]
        sprint["opened"] = False
        for key in (
            "sprint_id", "scope", "outcome", "first_executable_action_id",
            "completion_gate", "return_condition", "preserves_parent_outcome",
        ):
            sprint[key] = None
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.BOUNDARY.RECOVERY_OPENED")["result"], "FAIL")

    def test_recovery_first_action_must_be_progress_bearing(self) -> None:
        receipt = load_positive()
        receipt["actions"][0]["progress_bearing"] = False
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.BOUNDARY.FIRST_ACTION_PROGRESS")["result"], "FAIL")

    def test_partial_mutation_requires_readback_before_retry(self) -> None:
        receipt = load_positive()
        first = receipt["actions"][0]
        first["side_effect_state"] = "UNKNOWN"
        first["target_identity"] = "fixture:target"
        first["pre_state_fingerprint"] = "state-v1"
        retry = copy.deepcopy(first)
        retry["action_id"] = "A-002"
        retry["sequence"] = 2
        retry["started_at"] = "2026-09-18T12:03:35Z"
        retry["completed_at"] = "2026-09-18T12:03:40Z"
        retry["side_effect_state"] = "NONE"
        retry["retry_of_action_id"] = "A-001"
        retry["proof_before"] = "VALIDATED"
        retry["proof_after"] = "VALIDATED"
        receipt["actions"].append(retry)
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.ACTION.PARTIAL_READBACK")["result"], "FAIL")

    def test_partial_mutation_passes_when_readback_precedes_retry(self) -> None:
        receipt = load_positive()
        first = receipt["actions"][0]
        first["side_effect_state"] = "UNKNOWN"
        first["target_identity"] = "fixture:target"
        first["pre_state_fingerprint"] = "state-v1"
        readback = copy.deepcopy(first)
        readback["action_id"] = "A-002"
        readback["sequence"] = 2
        readback["started_at"] = "2026-09-18T12:03:35Z"
        readback["completed_at"] = "2026-09-18T12:03:40Z"
        readback["side_effect_state"] = "NONE"
        readback["readback_of_action_id"] = "A-001"
        readback["proof_before"] = "VALIDATED"
        readback["proof_after"] = "VALIDATED"
        retry = copy.deepcopy(readback)
        retry["action_id"] = "A-003"
        retry["sequence"] = 3
        retry["started_at"] = "2026-09-18T12:03:45Z"
        retry["completed_at"] = "2026-09-18T12:03:50Z"
        retry["readback_of_action_id"] = None
        retry["retry_of_action_id"] = "A-001"
        receipt["actions"].extend([readback, retry])
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.ACTION.PARTIAL_READBACK")["result"], "PASS")

    def test_false_proof_promotion_without_evidence_is_rejected(self) -> None:
        receipt = load_positive()
        receipt["actions"][0]["evidence_refs"] = []
        receipt["proof"]["checks"][0]["status"] = "UNKNOWN"
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.ACTION.NO_FALSE_PROOF_PROMOTION")["result"], "FAIL")

    def test_blocked_terminal_requires_resume_and_next_transition(self) -> None:
        receipt = load_positive()
        receipt["terminal"]["next_transition"] = None
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.TERMINAL.BLOCKED_GATE")["result"], "FAIL")

    def test_observed_state_requires_direct_runtime_evidence(self) -> None:
        receipt = load_positive()
        receipt["proof"]["strongest_state"] = "OBSERVED"
        receipt["proof"]["runtime_observed"] = False
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.PROOF.OBSERVED_RUNTIME")["result"], "FAIL")

    def test_privacy_block_absence_makes_pass_inconclusive(self) -> None:
        receipt = load_positive()
        receipt["privacy"] = None
        result = validator.validate_receipt(receipt)
        self.assertEqual(finding(result, "PRCR.PRIVACY.NO_RAW_TRANSCRIPT")["result"], "UNKNOWN")
        self.assertEqual(result["overall_result"], "FAIL")

    def test_structural_schema_failure_is_fail_closed(self) -> None:
        receipt = load_positive()
        receipt["raw_prompt"] = "forbidden"
        result = validator.validate_receipt(receipt)
        self.assertEqual(result["overall_result"], "INCONCLUSIVE")
        self.assertNotEqual(validator.exit_code(result), 0)

    def test_cli_exit_codes_and_json_result(self) -> None:
        positive = subprocess.run(
            [sys.executable, "scripts/validate_prompt_runtime_compliance_receipt.py", str(POSITIVE), "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(positive.returncode, 0, positive.stderr or positive.stdout)
        payload = json.loads(positive.stdout)
        self.assertEqual(payload["schema_version"], "prompt-runtime-compliance-validation/v1")
        self.assertEqual(payload["overall_result"], "PASS")

        negative_receipt = load_positive()
        negative_receipt["boundary_events"][0]["publication_ack"] = "PENDING"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "negative.json"
            path.write_text(json.dumps(negative_receipt), encoding="utf-8")
            negative = subprocess.run(
                [sys.executable, "scripts/validate_prompt_runtime_compliance_receipt.py", str(path), "--summary"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(negative.returncode, 0)
        self.assertIn("PROMPT RUNTIME COMPLIANCE: FAIL", negative.stdout)


if __name__ == "__main__":
    unittest.main()
