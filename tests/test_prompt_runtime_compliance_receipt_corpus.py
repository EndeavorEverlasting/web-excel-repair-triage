from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "harness" / "evals" / "runtime-compliance" / "fixtures"
CORPUS = FIXTURES / "receipt-corpus.v1.json"
CANONICAL_INDEX = FIXTURES / "index.v1.json"
RECEIPT_SCHEMA = ROOT / "harness" / "contracts" / "prompt-runtime-compliance-receipt.schema.v1.json"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-runtime-compliance.v1.json"
TAXONOMY = ROOT / "harness" / "contracts" / "execution-boundary-taxonomy.v1.json"

EXPECTED_IDS = ["RTC01", "RTC02", "RTC03", "RTC04", "RTC05"]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class RuntimeComplianceReceiptCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = load(CORPUS)
        cls.index = load(CANONICAL_INDEX)
        cls.schema = load(RECEIPT_SCHEMA)
        cls.contract = load(CONTRACT)
        cls.taxonomy = load(TAXONOMY)
        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )
        cls.rules = {row["rule_id"] for row in cls.contract["rules"]}
        cls.canonical = {
            row["scenario_id"]: row
            for row in cls.index["scenarios"]
        }
        cls.family_classes = {
            family["id"]: {klass["id"] for klass in family["classes"]}
            for family in cls.taxonomy["families"]
        }

    def scenarios(self) -> list[dict]:
        return self.corpus["scenarios"]

    def test_corpus_is_subordinate_to_single_canonical_scenario_index(self) -> None:
        self.assertEqual(
            self.corpus["manifest_version"],
            "runtime-compliance-receipt-corpus/v1",
        )
        self.assertEqual(
            self.corpus["canonical_scenario_index"],
            "harness/evals/runtime-compliance/fixtures/index.v1.json",
        )
        self.assertEqual(
            [row["scenario_id"] for row in self.scenarios()],
            EXPECTED_IDS,
        )
        self.assertEqual(set(self.canonical), set(EXPECTED_IDS))
        self.assertFalse((FIXTURES / "scenario-index.v1.json").exists())

    def test_definitions_bind_exactly_to_canonical_rule_ownership(self) -> None:
        for row in self.scenarios():
            sid = row["scenario_id"]
            with self.subTest(scenario=sid):
                definition = load(ROOT / row["definition"])
                self.assertEqual(definition["scenario_id"], sid)
                self.assertEqual(
                    definition["canonical_scenario_index"],
                    self.corpus["canonical_scenario_index"],
                )
                canonical_rules = self.canonical[sid]["protected_rule_ids"]
                self.assertEqual(
                    definition["primary_protected_rules"],
                    canonical_rules,
                )
                self.assertTrue(set(canonical_rules).issubset(self.rules))
                boundary = definition["injected_boundary"]
                self.assertIn(boundary["family_id"], self.family_classes)
                self.assertIn(
                    boundary["class_id"],
                    self.family_classes[boundary["family_id"]],
                )

    def test_receipts_validate_with_format_checker_and_bind_to_definition(self) -> None:
        seen: set[str] = set()
        for row in self.scenarios():
            sid = row["scenario_id"]
            definition = load(ROOT / row["definition"])
            canonical_rules = self.canonical[sid]["protected_rule_ids"]
            for role in ("positive_receipt", "negative_receipt"):
                path = ROOT / row[role]
                with self.subTest(scenario=sid, role=role):
                    receipt = load(path)
                    errors = sorted(
                        self.validator.iter_errors(receipt),
                        key=lambda error: list(error.absolute_path),
                    )
                    self.assertEqual(errors, [], [error.message for error in errors])
                    self.assertEqual(receipt["scenario"]["scenario_id"], sid)
                    self.assertEqual(
                        receipt["scenario"]["protected_invariants"],
                        canonical_rules,
                    )
                    self.assertEqual(
                        (ROOT / receipt["scenario"]["fixture_path"]).resolve(),
                        path.resolve(),
                    )
                    self.assertNotIn(receipt["receipt_id"], seen)
                    seen.add(receipt["receipt_id"])

                    canonical_events = [
                        event
                        for event in receipt["boundary_events"]
                        if event["classification_status"] == "CANONICAL"
                    ]
                    self.assertTrue(canonical_events)
                    injected = definition["injected_boundary"]
                    self.assertTrue(
                        any(
                            event["family_id"] == injected["family_id"]
                            and event["class_id"] == injected["class_id"]
                            for event in canonical_events
                        )
                    )

    def test_negative_receipts_are_declared_pass_traps_not_fake_failures(self) -> None:
        for row in self.scenarios():
            sid = row["scenario_id"]
            definition = load(ROOT / row["definition"])
            positive = load(ROOT / row["positive_receipt"])
            negative = load(ROOT / row["negative_receipt"])
            with self.subTest(scenario=sid):
                self.assertEqual(positive["compliance_result"], "PASS")
                self.assertEqual(
                    positive["compliance_result"],
                    definition["positive"]["expected_compliance_result"],
                )
                self.assertEqual(negative["compliance_result"], "PASS")
                self.assertEqual(
                    negative["compliance_result"],
                    definition["negative"]["declared_receipt_result"],
                )
                self.assertEqual(
                    definition["negative"]["expected_compliance_result"],
                    "FAIL",
                )
                failing = definition["negative"]["expected_failing_rules"]
                self.assertTrue(failing)
                self.assertIn("PRCR.COMPLIANCE.PASS", failing)
                self.assertIn(
                    definition["negative"]["primary_failing_rule"],
                    failing,
                )

    def test_positive_proof_promotions_are_action_addressed(self) -> None:
        ranks = {
            "PLANNED_DESIGNED": 0,
            "TRACKED": 1,
            "IMPLEMENTED": 2,
            "WIRED_REACHABLE": 3,
            "VALIDATED": 4,
            "INTEGRATED": 5,
            "DEPLOYED": 6,
            "OBSERVED": 7,
        }
        for row in self.scenarios():
            receipt = load(ROOT / row["positive_receipt"])
            passing = [
                check
                for check in receipt["proof"]["checks"]
                if check["status"] == "PASS"
            ]
            for action in receipt["actions"]:
                before = action["proof_before"]
                after = action["proof_after"]
                if before is None or after is None or ranks[after] <= ranks[before]:
                    continue
                with self.subTest(
                    scenario=row["scenario_id"],
                    action=action["action_id"],
                ):
                    action_refs = set(action["evidence_refs"])
                    matches = [
                        check
                        for check in passing
                        if check["name"].startswith(
                            f"action:{action['action_id']}:"
                        )
                        and action_refs.intersection(check["evidence_refs"])
                    ]
                    self.assertTrue(matches)

    def test_rtc04_oracle_proves_absence_before_retry_machine_readably(self) -> None:
        row = next(
            item for item in self.scenarios()
            if item["scenario_id"] == "RTC04"
        )
        definition = load(ROOT / row["definition"])
        receipt = load(ROOT / row["positive_receipt"])
        protocol = definition["readback_oracle"]
        by_id = {action["action_id"]: action for action in receipt["actions"]}
        ambiguous = by_id[protocol["ambiguous_action_id"]]
        readback = by_id[protocol["authoritative_readback_action_id"]]
        retry = by_id[protocol["retry_action_id"]]

        self.assertEqual(
            readback["readback_of_action_id"],
            ambiguous["action_id"],
        )
        self.assertEqual(
            readback["target_identity"],
            ambiguous["target_identity"],
        )
        self.assertEqual(
            readback["pre_state_fingerprint"],
            ambiguous["pre_state_fingerprint"],
        )
        self.assertEqual(
            readback["side_effect_state"],
            protocol["readback_absence_side_effect_state"],
        )
        self.assertLess(readback["sequence"], retry["sequence"])
        self.assertEqual(retry["retry_of_action_id"], ambiguous["action_id"])
        self.assertEqual(
            retry["idempotency_key"],
            ambiguous["idempotency_key"],
        )

        evidence = {
            item["evidence_id"]: item
            for item in receipt["evidence"]
        }
        readback_evidence = [
            evidence[ref]
            for ref in readback["evidence_refs"]
        ]
        self.assertTrue(
            any(
                item["ref"].endswith(":mutation-absent")
                for item in readback_evidence
            )
        )

    def test_rtc05_oracle_proves_graph_width_rung_and_concurrent_group(self) -> None:
        row = next(
            item for item in self.scenarios()
            if item["scenario_id"] == "RTC05"
        )
        definition = load(ROOT / row["definition"])
        receipt = load(ROOT / row["positive_receipt"])
        protocol = definition["parallel_oracle"]
        actions = receipt["actions"]

        self.assertGreaterEqual(protocol["graph_width"], 2)
        self.assertFalse(protocol["preferred_adapter_available"])
        self.assertEqual(len(actions), protocol["graph_width"])
        self.assertEqual(
            {action["started_at"] for action in actions},
            {actions[0]["started_at"]},
        )
        for action in actions:
            self.assertIn(
                f"group:{protocol['concurrent_group_id']}",
                action["target_identity"],
            )
            self.assertIn(
                f"rung:{protocol['first_safe_rung']}",
                action["target_identity"],
            )
            self.assertIn("EV-DISPATCH", action["evidence_refs"])

        dispatch = next(
            item
            for item in receipt["evidence"]
            if item["evidence_id"] == "EV-DISPATCH"
        )
        self.assertEqual(
            dispatch["ref"],
            definition["positive"]["machine_checkable_oracle"][
                "shared_dispatch_evidence_ref"
            ],
        )
        self.assertIn(
            f"graph-width:{protocol['graph_width']}",
            dispatch["ref"],
        )


if __name__ == "__main__":
    unittest.main()
