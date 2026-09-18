from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "harness/evals/runtime-compliance/fixtures"
INDEX = FIXTURES / "scenario-index.v1.json"
RECEIPT_SCHEMA = ROOT / "harness/contracts/prompt-runtime-compliance-receipt.schema.v1.json"
CONTRACT = ROOT / "harness/contracts/prompt-runtime-compliance.v1.json"
TAXONOMY = ROOT / "harness/contracts/execution-boundary-taxonomy.v1.json"

EXPECTED_SCENARIO_IDS = ["RTC01", "RTC02", "RTC03", "RTC04", "RTC05"]
SCENARIO_FIXTURE_VERSION = "runtime-compliance-scenario/v1"
INDEX_MANIFEST_VERSION = "runtime-compliance-scenario-index/v1"
RECEIPT_SCHEMA_ID = "prompt-runtime-compliance-receipt/v1"
SEMANTIC_CONTRACT_ID = "prompt-runtime-compliance/v1"
BOUNDARY_TAXONOMY_ID = "execution-boundary-taxonomy/v1"
MATERIALITY_LEVELS = {"INFO", "MATERIAL", "CRITICAL"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class RuntimeComplianceFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = load(INDEX)
        cls.schema = load(RECEIPT_SCHEMA)
        cls.contract = load(CONTRACT)
        cls.taxonomy = load(TAXONOMY)
        cls.validator = Draft202012Validator(cls.schema)
        cls.rule_ids = {rule["rule_id"] for rule in cls.contract["rules"]}
        cls.family_classes = {
            family["id"]: {klass["id"] for klass in family["classes"]}
            for family in cls.taxonomy["families"]
        }
        cls.all_classes = {klass for classes in cls.family_classes.values() for klass in classes}

    def scenarios(self):
        return self.index["scenarios"]

    def scenario_dir(self, scenario: dict) -> Path:
        return ROOT / scenario["directory"]

    def test_scenario_index_identity_and_completeness(self) -> None:
        self.assertEqual(self.index["manifest_version"], INDEX_MANIFEST_VERSION)
        self.assertEqual(self.index["receipt_schema"], RECEIPT_SCHEMA_ID)
        self.assertEqual(self.index["semantic_contract"], SEMANTIC_CONTRACT_ID)
        self.assertEqual(self.index["boundary_taxonomy"], BOUNDARY_TAXONOMY_ID)
        self.assertTrue((ROOT / self.index["receipt_schema_path"]).is_file())
        self.assertTrue((ROOT / self.index["semantic_contract_path"]).is_file())
        ids = [scenario["scenario_id"] for scenario in self.scenarios()]
        self.assertEqual(ids, EXPECTED_SCENARIO_IDS)
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in self.scenarios():
            for key in ("directory", "definition", "positive_receipt", "negative_receipt"):
                self.assertTrue((ROOT / scenario[key]).exists(), scenario[key])

    def test_every_scenario_definition_is_wellformed(self) -> None:
        for scenario in self.scenarios():
            sid = scenario["scenario_id"]
            with self.subTest(scenario=sid):
                definition = load(ROOT / scenario["definition"])
                self.assertEqual(definition["fixture_version"], SCENARIO_FIXTURE_VERSION)
                self.assertEqual(definition["scenario_id"], sid)
                self.assertEqual(self.scenario_dir(scenario).name.upper(), sid)

                boundary = definition["injected_boundary"]
                self.assertIn(boundary["family_id"], self.family_classes)
                self.assertIn(boundary["class_id"], self.family_classes[boundary["family_id"]])
                self.assertIn(boundary["materiality"], MATERIALITY_LEVELS)

                for key in ("required_behavior", "forbidden_terminal_behaviors", "protected_invariants"):
                    self.assertTrue(definition[key], key)

                protected = definition["primary_protected_rules"]
                self.assertTrue(protected)
                self.assertTrue(set(protected).issubset(self.rule_ids), set(protected) - self.rule_ids)

                positive = definition["positive"]
                self.assertEqual(positive["receipt"], "receipt.pass.v1.json")
                self.assertEqual(positive["expected_compliance_result"], "PASS")

                negative = definition["negative"]
                self.assertEqual(negative["receipt"], "receipt.fail.v1.json")
                self.assertEqual(negative["declared_receipt_result"], "PASS")
                self.assertEqual(negative["expected_compliance_result"], "FAIL")
                self.assertTrue(isinstance(negative["forbidden_signature"], str) and negative["forbidden_signature"])
                failing = negative["expected_failing_rules"]
                self.assertTrue(failing)
                self.assertTrue(set(failing).issubset(self.rule_ids), set(failing) - self.rule_ids)
                self.assertIn("PRCR.COMPLIANCE.PASS", failing)
                self.assertIn(negative["primary_failing_rule"], failing)
                self.assertIn(negative["primary_failing_rule"], self.rule_ids)

    def test_all_receipts_validate_against_receipt_schema(self) -> None:
        for scenario in self.scenarios():
            for role in ("positive_receipt", "negative_receipt"):
                path = ROOT / scenario[role]
                with self.subTest(scenario=scenario["scenario_id"], role=role):
                    receipt = load(path)
                    self.assertEqual(receipt["schema_version"], RECEIPT_SCHEMA_ID)
                    errors = sorted(self.validator.iter_errors(receipt), key=lambda e: e.path)
                    self.assertEqual(errors, [], [e.message for e in errors])

    def test_receipts_bind_to_scenario_and_pinned_taxonomy(self) -> None:
        for scenario in self.scenarios():
            sid = scenario["scenario_id"]
            definition = load(ROOT / scenario["definition"])
            injected = definition["injected_boundary"]
            for role, rel in (("positive_receipt", "receipt.pass.v1.json"),
                              ("negative_receipt", "receipt.fail.v1.json")):
                path = ROOT / scenario[role]
                with self.subTest(scenario=sid, role=role):
                    self.assertEqual(path.name, rel)
                    self.assertEqual(path.parent, self.scenario_dir(scenario))
                    receipt = load(path)
                    self.assertEqual(receipt["scenario"]["scenario_id"], sid)
                    self.assertEqual((ROOT / receipt["scenario"]["fixture_path"]).resolve(), path.resolve())

                    canonical = [
                        event for event in receipt["boundary_events"]
                        if event["classification_status"] == "CANONICAL"
                    ]
                    self.assertTrue(canonical)
                    for event in canonical:
                        self.assertIn(event["family_id"], self.family_classes)
                        self.assertIn(event["class_id"], self.all_classes)
                        self.assertIn(event["class_id"], self.family_classes[event["family_id"]])
                    injected_events = [
                        event for event in canonical
                        if event["family_id"] == injected["family_id"]
                        and event["class_id"] == injected["class_id"]
                    ]
                    self.assertTrue(injected_events, f"{sid} {role} missing injected boundary")

    def test_negative_oracle_is_a_genuine_declared_pass_trap(self) -> None:
        seen_ids: set[str] = set()
        for scenario in self.scenarios():
            sid = scenario["scenario_id"]
            definition = load(ROOT / scenario["definition"])
            positive = load(ROOT / scenario["positive_receipt"])
            negative = load(ROOT / scenario["negative_receipt"])
            with self.subTest(scenario=sid):
                self.assertEqual(positive["compliance_result"], "PASS")
                self.assertEqual(
                    positive["compliance_result"],
                    definition["positive"]["expected_compliance_result"],
                )
                self.assertEqual(
                    negative["compliance_result"],
                    definition["negative"]["declared_receipt_result"],
                )
                self.assertEqual(negative["compliance_result"], "PASS")
                self.assertEqual(definition["negative"]["expected_compliance_result"], "FAIL")
                self.assertNotEqual(
                    definition["negative"]["expected_compliance_result"],
                    definition["negative"]["declared_receipt_result"],
                )
                self.assertEqual(negative["violations"], [])
                for receipt in (positive, negative):
                    self.assertNotIn(receipt["receipt_id"], seen_ids)
                    seen_ids.add(receipt["receipt_id"])
                self.assertNotEqual(positive["receipt_id"], negative["receipt_id"])


if __name__ == "__main__":
    unittest.main()
