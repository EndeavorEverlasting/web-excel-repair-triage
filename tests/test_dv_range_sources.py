from __future__ import annotations

import unittest

from triage.dv_range_sources import make_range_list_validation, normalize_range_formula


class RangeBackedValidationTests(unittest.TestCase):
    def test_google_style_range_is_normalized_for_ooxml(self) -> None:
        self.assertEqual(
            normalize_range_formula("='Review Rules'!$J$2:$J$100"),
            "'Review Rules'!$J$2:$J$100",
        )

    def test_range_rule_reuses_dv_engine_primitive(self) -> None:
        rule = make_range_list_validation(
            "xl/worksheets/sheet3.xml",
            "D11:D1000",
            "='Review Rules'!$J$2:$J$100",
            "Activity & Ad Hoc Ledger",
        )
        self.assertEqual(rule.category, "list")
        self.assertEqual(rule.dv_type, "list")
        self.assertEqual(rule.formula1, "'Review Rules'!$J$2:$J$100")
        self.assertEqual(rule.sqref, "D11:D1000")
        xml = rule.to_xml()
        self.assertIn("<formula1>'Review Rules'!$J$2:$J$100</formula1>", xml)
        self.assertNotIn('"Assignment,', xml)

    def test_inline_list_is_rejected_by_range_helper(self) -> None:
        with self.assertRaises(ValueError):
            normalize_range_formula('"Assignment,Other"')

    def test_non_range_formula_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_range_formula("Review Rules")


if __name__ == "__main__":
    unittest.main()
