from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "harness" / "evals" / "runtime-compliance" / "fixtures"
INDEX = FIXTURE_DIR / "index.v1.json"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-runtime-compliance.v1.json"
TAXONOMY = ROOT / "harness" / "contracts" / "execution-boundary-taxonomy.v1.json"

EXPECTED_IDS = {"RTC01", "RTC02", "RTC03", "RTC04", "RTC05"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class RuntimeComplianceScenarioFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = load(INDEX)
        cls.contract = load(CONTRACT)
        cls.taxonomy = load(TAXONOMY)
        cls.rules = {row["rule_id"] for row in cls.contract["rules"]}
        cls.classes = {
            (family["id"], klass["id"])
            for family in cls.taxonomy["families"]
            for klass in family["classes"]
        }
        cls.fixtures = {
            row["scenario_id"]: load(ROOT / row["path"])
            for row in cls.index["scenarios"]
        }

    def test_exact_five_scenario_identities(self) -> None:
        ids = [row["scenario_id"] for row in self.index["scenarios"]]
        self.assertEqual(set(ids), EXPECTED_IDS)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(self.fixtures), EXPECTED_IDS)

    def test_each_fixture_has_required_oracle_surfaces(self) -> None:
        required = {
            "schema_version", "scenario_id", "title", "starting_state",
            "injected_boundary", "expected_continuation",
            "forbidden_terminal_behaviors", "protected_rule_ids",
            "expected_rule_outcomes", "proof_ceiling",
        }
        for scenario_id, fixture in self.fixtures.items():
            self.assertEqual(fixture["schema_version"], "prompt-runtime-compliance-scenario/v1")
            self.assertEqual(fixture["scenario_id"], scenario_id)
            self.assertTrue(required.issubset(fixture))
            for key in (
                "starting_state", "expected_continuation",
                "forbidden_terminal_behaviors", "protected_rule_ids",
            ):
                self.assertTrue(fixture[key], (scenario_id, key))
            self.assertTrue(fixture["expected_rule_outcomes"], scenario_id)
            self.assertTrue(fixture["proof_ceiling"])

    def test_boundary_classes_resolve_to_canonical_taxonomy(self) -> None:
        for scenario_id, fixture in self.fixtures.items():
            boundary = fixture["injected_boundary"]
            self.assertEqual(boundary["classification_status"], "CANONICAL")
            self.assertIn(
                (boundary["family_id"], boundary["class_id"]),
                self.classes,
                scenario_id,
            )
            self.assertIn(boundary["materiality"], {"MATERIAL", "CRITICAL"})

    def test_protected_and_expected_rules_resolve(self) -> None:
        for scenario_id, fixture in self.fixtures.items():
            self.assertTrue(set(fixture["protected_rule_ids"]).issubset(self.rules), scenario_id)
            self.assertTrue(set(fixture["expected_rule_outcomes"]).issubset(self.rules), scenario_id)
            self.assertTrue(
                set(fixture["expected_rule_outcomes"]).issubset(
                    set(fixture["protected_rule_ids"])
                ),
                scenario_id,
            )
            self.assertTrue(
                set(fixture["expected_rule_outcomes"].values()).issubset(
                    {"PASS", "FAIL", "NOT_APPLICABLE", "UNKNOWN"}
                ),
                scenario_id,
            )

    def test_rtc04_has_readback_before_retry_oracle(self) -> None:
        fixture = self.fixtures["RTC04"]
        protocol = fixture["mutation_protocol"]
        self.assertTrue(protocol["retry_may_follow_readback_only"])
        self.assertTrue(protocol["duplicate_effect_is_failure"])
        self.assertNotEqual(
            protocol["ambiguous_action_id"],
            protocol["required_readback_action_id"],
        )
        self.assertEqual(
            fixture["expected_rule_outcomes"]["PRCR.ACTION.PARTIAL_READBACK"],
            "PASS",
        )

    def test_rtc05_has_parallel_adapter_ladder_oracle(self) -> None:
        fixture = self.fixtures["RTC05"]
        protocol = fixture["parallel_protocol"]
        self.assertGreaterEqual(protocol["graph_width"], 2)
        self.assertFalse(protocol["preferred_adapter_available"])
        self.assertTrue(protocol["require_first_safe_available_rung"])
        self.assertTrue(protocol["degraded_only_after_ladder_exhaustion"])
        self.assertTrue(protocol["operator_scheduler_is_forbidden_while_autonomous_rung_exists"])

    def test_no_fixture_claims_runtime_observation(self) -> None:
        for scenario_id, fixture in self.fixtures.items():
            self.assertIn("Deterministic", fixture["proof_ceiling"], scenario_id)
            self.assertIn("no ", fixture["proof_ceiling"].lower(), scenario_id)


if __name__ == "__main__":
    unittest.main()
