from __future__ import annotations

import unittest

from triage.july_nth_public_disclosure_report import build_report


def _policy() -> dict:
    return {
        "schema": "fun-july-nth-public-disclosure-policy/v1",
        "policy_id": "july-2026-admin-public-disclosure",
        "forbidden_rules": [
            {"id": "cutoff", "pattern": r"\bJuly\s+24\b", "reason": "protected"},
            {"id": "analysis", "pattern": r"PM\s*/\s*data[- ]analysis", "reason": "protected"},
        ],
    }


def _validation() -> dict:
    return {
        "schema": "fun-july-nth-public-disclosure-result/v1",
        "status": "PASS",
        "policy_id": "july-2026-admin-public-disclosure",
        "artifact": {
            "filename": "ADMIN_SHARE_NTH_July_2026_MTD_SLEEK_FINAL.xlsx",
            "size": 18000,
            "sha256": "a" * 64,
        },
        "counts": {
            "rules_scanned": 2,
            "cell_disclosure_violations": 0,
            "package_disclosure_violations": 0,
            "math_lock_violations": 0,
            "scope_violations": 0,
        },
        "violations": [],
        "errors": [],
    }


class JulyDisclosureReportTests(unittest.TestCase):
    def test_passing_fun_result_produces_pass(self) -> None:
        bundle = build_report(_validation(), _policy())
        self.assertEqual(bundle.report["status"], "PASS")
        self.assertIn("confirmed math", bundle.markdown.lower())

    def test_upstream_disclosure_violation_fails(self) -> None:
        validation = _validation()
        validation["status"] = "FAIL"
        validation["counts"]["cell_disclosure_violations"] = 1
        validation["violations"] = [
            {
                "kind": "forbidden_public_disclosure",
                "rule_id": "cutoff",
                "surface": "cell",
                "sheet": "Task Summary",
                "cell": "D24",
            }
        ]
        bundle = build_report(validation, _policy())
        self.assertEqual(bundle.report["status"], "FAIL")
        self.assertNotIn("July 24", bundle.markdown)
        self.assertIn("cell=D24", bundle.markdown)

    def test_math_lock_violation_fails(self) -> None:
        validation = _validation()
        validation["status"] = "FAIL"
        validation["counts"]["math_lock_violations"] = 1
        validation["violations"] = [
            {
                "kind": "locked_numeric_cell_changed",
                "sheet": "Task Summary",
                "cell": "B10",
            }
        ]
        bundle = build_report(validation, _policy())
        self.assertEqual(bundle.report["status"], "FAIL")
        self.assertEqual(bundle.report["counts"]["math_lock_violations"], 1)

    def test_policy_mismatch_fails(self) -> None:
        policy = _policy()
        policy["policy_id"] = "different"
        bundle = build_report(_validation(), policy)
        self.assertEqual(bundle.report["status"], "FAIL")
        self.assertTrue(any("identifiers" in item for item in bundle.report["errors"]))


if __name__ == "__main__":
    unittest.main()
