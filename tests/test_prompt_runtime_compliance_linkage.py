from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "harness" / "evals" / "runtime-compliance"
LINKAGE_SCRIPTS = RUNTIME / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(LINKAGE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(LINKAGE_SCRIPTS))

import linkage  # noqa: E402
from scripts import validate_prompt_runtime_compliance_receipt as compliance_validator  # noqa: E402

POSITIVE = RUNTIME / "contract-fixtures" / "receipt.positive.v1.json"
NEGATIVE_PENDING = (
    RUNTIME
    / "contract-fixtures"
    / "receipt.negative.pending-publication.v1.json"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def make_regression_receipt(
    receipt_id: str,
    *,
    evidence_id: str,
    evidence_ref: str,
) -> dict:
    receipt = load(NEGATIVE_PENDING)
    receipt["receipt_id"] = receipt_id
    violation = receipt["violations"][0]
    violation["regression_required"] = True
    violation["regression_link_id"] = f"RL-{receipt_id.split('/')[-1]}"
    violation["evidence_refs"] = [evidence_id]
    receipt["evidence"].append(
        {
            "evidence_id": evidence_id,
            "kind": "artifact",
            "ref": evidence_ref,
            "supports": "Independent synthetic incident evidence for regression routing.",
        }
    )
    receipt["regression_linkage"] = {
        "status": "CANDIDATE",
        "incident_source": "validator_finding",
        "systemic_threshold_met": False,
        "canonical_owner": None,
        "occurrences": [
            {
                "occurrence_id": f"OCC-{receipt_id.split('/')[-1]}",
                "evidence_ref": evidence_ref,
            }
        ],
        "regression_link_ids": [violation["regression_link_id"]],
    }
    return receipt


class RuntimeComplianceLinkageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.p99_schema = load(
            ROOT / "harness" / "contracts" / "prompt-outcome-receipt.schema.v1.json"
        )

    def test_contract_matches_current_p99_and_regression_authority(self) -> None:
        linkage.validate_contract()
        self.assertEqual(
            linkage.CONTRACT["regression"]["systemic_threshold"],
            linkage.REGRESSION_CONTRACT["recurrence"]["systemic_threshold"],
        )
        self.assertEqual(
            linkage.CONTRACT["regression"]["recurring_process_owner"],
            "P13",
        )
        self.assertEqual(
            linkage.CONTRACT["regression"]["regression_design_owner"],
            "P94",
        )
        self.assertFalse(linkage.CONTRACT["p99"]["authoritative_classification"])

    def test_pass_maps_to_p99_validator_evidence_without_regression_route(self) -> None:
        receipt = load(POSITIVE)
        validation = compliance_validator.validate_receipt(receipt)
        self.assertEqual(validation["overall_result"], "PASS")
        record = linkage.build_linkage_record(receipt, validation)
        self.assertEqual(record["validation_result"], "PASS")
        self.assertEqual(record["p99_result_candidate"], "SUCCESS")
        self.assertEqual(record["p99_evidence_candidate"]["kind"], "validator")
        self.assertEqual(record["failure_class_hints"], [])
        self.assertEqual(record["regression"]["status"], "NONE")
        p99_evidence_schema = {
            "$schema": self.p99_schema["$schema"],
            "$defs": self.p99_schema["$defs"],
            "$ref": "#/$defs/evidence",
        }
        self.assertTrue(
            Draft202012Validator(p99_evidence_schema).is_valid(
                record["p99_evidence_candidate"]
            )
        )

    def test_failure_maps_high_severity_rule_to_bounded_p99_hint(self) -> None:
        receipt = load(NEGATIVE_PENDING)
        validation = compliance_validator.validate_receipt(receipt)
        self.assertEqual(validation["overall_result"], "FAIL")
        record = linkage.build_linkage_record(receipt, validation)
        self.assertEqual(record["p99_result_candidate"], "FAILURE")
        self.assertIn("PRCR.BOUNDARY.MATERIAL_PUBLICATION", record["rule_ids"])
        self.assertIn("progression", record["failure_class_hints"])
        self.assertIn("V-001", record["source_violation_ids"])

    def test_one_independent_regression_occurrence_remains_candidate(self) -> None:
        receipt = make_regression_receipt(
            "prcr/regression/one",
            evidence_id="EV-R1",
            evidence_ref="artifact:regression-one",
        )
        validation = compliance_validator.validate_receipt(receipt)
        self.assertEqual(validation["overall_result"], "FAIL")
        record = linkage.build_linkage_record(receipt, validation)
        self.assertEqual(record["regression"]["status"], "CANDIDATE")
        self.assertEqual(record["regression"]["family"], "RUNTIME_BEHAVIOR")
        aggregate = linkage.aggregate_regressions([record])
        self.assertEqual(len(aggregate), 1)
        self.assertEqual(aggregate[0]["status"], "CANDIDATE")
        self.assertEqual(aggregate[0]["independent_occurrences"], 1)

    def test_regression_required_routing_survives_repaired_or_not_applicable_result(self) -> None:
        cases = (
            ("PASS", "REPAIRED"),
            ("NOT_APPLICABLE", "WAIVED_NOT_APPLICABLE"),
        )
        for result_value, status_value in cases:
            with self.subTest(result=result_value, status=status_value):
                receipt = make_regression_receipt(
                    f"prcr/regression/{result_value.lower()}",
                    evidence_id=f"EV-{result_value}",
                    evidence_ref=f"artifact:regression-{result_value.lower()}",
                )
                violation = receipt["violations"][0]
                violation["result"] = result_value
                violation["status"] = status_value
                validation = compliance_validator.validate_receipt(receipt)
                record = linkage.build_linkage_record(receipt, validation)
                self.assertEqual(record["regression"]["status"], "CANDIDATE")
                self.assertEqual(
                    record["regression"]["occurrences"][0]["compliance_receipt_id"],
                    receipt["receipt_id"],
                )

    def test_duplicate_incident_cannot_manufacture_systemic_status(self) -> None:
        receipt = make_regression_receipt(
            "prcr/regression/duplicate",
            evidence_id="EV-RD",
            evidence_ref="artifact:regression-duplicate",
        )
        validation = compliance_validator.validate_receipt(receipt)
        record = linkage.build_linkage_record(receipt, validation)
        aggregate = linkage.aggregate_regressions(
            [record, copy.deepcopy(record), copy.deepcopy(record)]
        )
        self.assertEqual(aggregate[0]["status"], "CANDIDATE")
        self.assertEqual(aggregate[0]["independent_occurrences"], 1)

    def test_two_independent_same_family_occurrences_become_systemic(self) -> None:
        first = make_regression_receipt(
            "prcr/regression/first",
            evidence_id="EV-FIRST",
            evidence_ref="artifact:regression-first",
        )
        second = make_regression_receipt(
            "prcr/regression/second",
            evidence_id="EV-SECOND",
            evidence_ref="artifact:regression-second",
        )
        first_record = linkage.build_linkage_record(
            first,
            compliance_validator.validate_receipt(first),
        )
        second_record = linkage.build_linkage_record(
            second,
            compliance_validator.validate_receipt(second),
        )
        aggregate = linkage.aggregate_regressions([first_record, second_record])
        self.assertEqual(aggregate[0]["status"], "SYSTEMIC")
        self.assertEqual(aggregate[0]["independent_occurrences"], 2)
        self.assertEqual(aggregate[0]["recurring_process_owner"], "P13")
        self.assertEqual(aggregate[0]["regression_design_owner"], "P94")

    def test_linkage_record_does_not_copy_violation_message_or_raw_payload(self) -> None:
        receipt = make_regression_receipt(
            "prcr/regression/privacy",
            evidence_id="EV-PRIVACY",
            evidence_ref="artifact:regression-privacy",
        )
        receipt["violations"][0]["message"] = "PRIVATE-INCIDENT-MESSAGE-DO-NOT-COPY"
        validation = compliance_validator.validate_receipt(receipt)
        record = linkage.build_linkage_record(receipt, validation)
        serialized = json.dumps(record, sort_keys=True)
        self.assertNotIn("PRIVATE-INCIDENT-MESSAGE-DO-NOT-COPY", serialized)
        self.assertFalse(record["privacy"]["raw_payload_copied"])
        self.assertFalse(record["privacy"]["violation_messages_copied"])
        self.assertFalse(record["privacy"]["secret_material_copied"])

    def test_validation_receipt_identity_mismatch_fails_closed(self) -> None:
        receipt = load(POSITIVE)
        validation = compliance_validator.validate_receipt(receipt)
        validation["receipt_id"] = "prcr/different/receipt"
        with self.assertRaisesRegex(linkage.LinkageError, "does not belong"):
            linkage.build_linkage_record(receipt, validation)


if __name__ == "__main__":
    unittest.main()
