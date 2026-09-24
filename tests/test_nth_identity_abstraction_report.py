from __future__ import annotations

import json
import unittest

from triage.nth_identity_abstraction_report import REPORT_SCHEMA, build_report


def policy() -> dict[str, object]:
    return {
        "schema": "fun-nth-identity-abstraction-policy/v1",
        "policy_id": "fixture-policy",
        "artifact_type": "fixture",
        "identity_tokens": [
            {"token": "Person Alpha", "aliases": ["P. Alpha"]},
            {"token": "Person Beta"},
        ],
        "allowed_named_ranges": [
            {"sheet": "NTH", "range": "C9:C20", "purpose": "ordinary technician column"}
        ],
        "forbidden_special_case_labels": ["Extended NTH Coverage"],
    }


def validation(status: str = "PASS") -> dict[str, object]:
    return {
        "schema": "fun-nth-identity-abstraction-result/v1",
        "status": status,
        "policy_id": "fixture-policy",
        "artifact": {
            "filename": "fixture.xlsx",
            "size": 1234,
            "sha256": "a" * 64,
            "artifact_type": "fixture",
        },
        "counts": {
            "identities_scanned": 2,
            "allowed_row_identity_occurrences": 3,
            "identity_violations": 0,
            "special_case_label_violations": 0,
            "package_identity_violations": 0,
        },
        "allowed_occurrences": [
            {"sheet": "NTH", "cell": "C9", "identity_index": 1}
        ],
        "violations": [],
        "errors": [],
        "proof_ceiling": "fixture proof",
    }


class AbstractDetailReportTests(unittest.TestCase):
    def test_passing_report_is_redacted_and_complete(self) -> None:
        bundle = build_report(validation(), policy())
        self.assertEqual("PASS", bundle.report["status"])
        self.assertEqual(REPORT_SCHEMA, bundle.report["schema"])
        self.assertEqual(3, bundle.report["counts"]["allowed_row_identity_occurrences"])
        combined = json.dumps(bundle.report) + bundle.markdown
        self.assertNotIn("Person Alpha", combined)
        self.assertNotIn("Person Beta", combined)
        self.assertIn("workstream-centered", bundle.markdown)

    def test_upstream_failure_fails_closed(self) -> None:
        value = validation("FAIL")
        value["counts"]["identity_violations"] = 1
        value["violations"] = [
            {
                "kind": "identity_outside_approved_range",
                "sheet": "Task Summary",
                "cell": "C4",
                "identity_index": 1,
            }
        ]
        bundle = build_report(value, policy())
        self.assertEqual("FAIL", bundle.report["status"])
        self.assertEqual(1, bundle.report["counts"]["identity_violations"])
        self.assertEqual("Task Summary", bundle.report["locations"][0]["sheet"])
        self.assertNotIn("Person Alpha", bundle.markdown)

    def test_policy_mismatch_fails(self) -> None:
        value = validation()
        value["policy_id"] = "different-policy"
        bundle = build_report(value, policy())
        self.assertEqual("FAIL", bundle.report["status"])
        self.assertTrue(any("identifiers do not match" in error for error in bundle.report["errors"]))

    def test_report_rejects_accidental_identity_echo(self) -> None:
        value = validation()
        value["errors"] = ["Person Alpha appeared in report text"]
        bundle = build_report(value, policy())
        self.assertEqual("FAIL", bundle.report["status"])
        self.assertTrue(any("echoed" in error for error in bundle.report["errors"]))


if __name__ == "__main__":
    unittest.main()
