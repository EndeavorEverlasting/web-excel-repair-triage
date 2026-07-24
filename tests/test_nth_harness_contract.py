from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_nth_harness


class NeuronTrackHoursHarnessContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(
            (ROOT / "harness" / "nth" / "monthly-rule-packs.v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.july = next(
            item for item in cls.registry["rule_packs"] if item["id"] == "july-2026"
        )

    def test_full_nth_harness_validator_passes(self) -> None:
        self.assertEqual(validate_nth_harness.main(), 0)

    def test_july_guardrail_is_60_40_reasonableness_not_quota(self) -> None:
        guardrail = self.july["aggregate_guardrail"]
        self.assertEqual(guardrail["configurations"], 0.6)
        self.assertEqual(guardrail["other_work"], 0.4)
        self.assertAlmostEqual(
            guardrail["configurations"] + guardrail["other_work"], 1.0
        )
        self.assertEqual(guardrail["mode"], "reasonableness_not_quota")
        self.assertEqual(self.july["effective_start"], "2026-06-26")

    def test_attendance_and_primary_workstream_contracts_are_explicit(self) -> None:
        self.assertEqual(self.july["hours_source_of_truth"], "roster/attendance")
        primary = self.july["primary_workstream"]
        self.assertTrue(primary["one_dominant_per_paid_shift"])
        self.assertFalse(primary["complimentary_work_creates_hours"])
        semantics = self.july["task_semantics"]
        self.assertTrue(semantics["configuration_and_deployment_are_distinct"])
        self.assertTrue(semantics["pm_operational_control_is_not_catch_all"])
        self.assertTrue(semantics["role_specific_pm_client_ticket_work"])

    def test_rich_weekly_correspondence_cadence_is_preserved(self) -> None:
        cadence = self.july["role_cadence"]["Rich Perez"]
        self.assertEqual(cadence["full_client_correspondence_days_per_week"], 1)
        self.assertEqual(cadence["usual_day"], "Thursday")
        self.assertEqual(
            set(cadence["known_anchors"]), {"2026-07-02", "2026-07-23"}
        )

    def test_july_date_and_person_exceptions_are_preserved(self) -> None:
        exceptions = {
            (item["date"], item["person"]): item
            for item in self.july["date_person_exceptions"]
        }
        self.assertEqual(exceptions[("2026-07-03", "core team")]["project_hours"], 0)
        self.assertEqual(exceptions[("2026-07-03", "core team")]["type"], "holiday")
        self.assertEqual(
            exceptions[("2026-07-24", "Alejandro Perales")]["project_hours"], 0
        )
        self.assertEqual(
            exceptions[("2026-07-24", "Alejandro Perales")]["internal_status"],
            "A",
        )
        self.assertEqual(
            exceptions[("2026-07-10", "team")]["type"], "mixed_operational_day"
        )

    def test_client_and_internal_workbook_modes_cannot_drift(self) -> None:
        modes = self.july["delivery_modes"]
        internal = modes["internal"]
        client = modes["client"]
        self.assertTrue(internal["preserve_complete_supporting_workbook"])
        self.assertEqual(client["derived_from"], "validated internal workbook")
        self.assertEqual(client["tabs"], ["Executive Summary", "July 2026"])
        self.assertTrue(client["omit_internal_only_sheets"])
        self.assertFalse(client["hidden_internal_sheets_allowed"])
        self.assertFalse(client["expose_internal_percentages"])
        self.assertTrue(client["preserve_attendance_totals"])
        self.assertTrue(client["preserve_primary_workstream_truth"])
        self.assertTrue(client["preserve_task_attribution"])

    def test_historical_review_does_not_imply_historical_mutation(self) -> None:
        history = self.july["historical_review_boundaries"]["2026-05-26_to_2026-05-29"]
        self.assertEqual(history["mode"], "review_not_correction")
        self.assertFalse(history["historical_workbook_mutation_authorized"])
        self.assertIn("review", history["preferred_terms"])
        self.assertIn("reconciliation", history["avoid_terms_without_actual_mutation"])

    def test_month_rules_do_not_silently_carry_forward(self) -> None:
        self.assertEqual(
            self.july["carry_forward_policy"],
            "forbidden_without_month_specific_confirmation",
        )

    def test_domain_trigger_registry_routes_both_delivery_modes(self) -> None:
        payload = json.loads(
            (ROOT / "harness" / "nth" / "triggers.v1.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in payload["triggers"]}
        self.assertEqual(set(by_id), validate_nth_harness.REQUIRED_TRIGGER_IDS)
        self.assertEqual(by_id["nth-internal-workbook-request"]["mode"], "internal")
        self.assertEqual(by_id["nth-client-send-copy-request"]["mode"], "client")
        for trigger in by_id.values():
            self.assertEqual(
                trigger["skill"],
                ".ai/skills/neuron-track-hours-monthly-artifact/SKILL.md",
            )


if __name__ == "__main__":
    unittest.main()
