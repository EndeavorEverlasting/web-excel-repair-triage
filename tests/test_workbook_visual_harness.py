from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_workbook_visual_harness as harness
import validate_workbook_visual_integrity as visual


class WorkbookVisualHarnessTests(unittest.TestCase):
    def test_complete_harness_passes(self) -> None:
        report = harness.validate()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["profile_count"], 3)
        self.assertEqual(report["canonical_role_count"], 8)

    def test_profile_audit_passes_and_colors_are_unique(self) -> None:
        report = visual.audit_profiles()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["profile_count"], 3)
        policy = json.loads((ROOT / "configs" / "workbook_visual_integrity_v1.json").read_text(encoding="utf-8"))
        fills = [item["fill"] for item in policy["semantic_roles"].values()]
        self.assertEqual(len(fills), len(set(fills)))

    def test_may_date_striping_is_bounded_exception_only(self) -> None:
        profile = json.loads((ROOT / "harness" / "workbook-visual-integrity" / "profiles" / "nth-admin-may-26-29.v1.json").read_text(encoding="utf-8"))
        exceptions = [item for item in profile["exceptions"] if item["type"] == "legacy_date_band"]
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0]["bounded_rows"], [9, 20])
        july = json.loads((ROOT / "harness" / "workbook-visual-integrity" / "profiles" / "nth-admin-july.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(july["exceptions"], [])
        self.assertTrue(any(rule["type"] == "forbid_unbounded_striping" for rule in july["rules"]))

    def test_fun_and_triage_have_distinct_connected_authority(self) -> None:
        contract = json.loads((ROOT / "harness" / "workbook-visual-integrity" / "fun-triage-contract.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["producer"]["repository"], "EndeavorEverlasting/web-excel-repair-triage")
        self.assertEqual(contract["acceptor"]["repository"], "EndeavorEverlasting/FUN")
        self.assertEqual(contract["receipt_contract"]["required_status"], "PASS")
        self.assertIn("artifact.sha256", contract["receipt_contract"]["required_match_fields"])

    def test_generator_bindings_require_visual_receipt_and_operator_gate(self) -> None:
        bindings = json.loads((ROOT / "harness" / "workbook-visual-integrity" / "generator-bindings.v1.json").read_text(encoding="utf-8"))
        self.assertIn("visual_validation_result", bindings["required_manifest_fields"])
        self.assertIn("operator_excel_for_web_status", bindings["required_manifest_fields"])
        for item in bindings["bindings"][:2]:
            self.assertEqual(item["status"], "contract_ready_product_wiring_pending")
            self.assertIn("visual_gate", item["required_sequence"])


if __name__ == "__main__":
    unittest.main()
