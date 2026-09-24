from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_SCHEMA = ROOT / "harness/contracts/prompt-runtime-compliance-receipt.schema.v1.json"
CONTRACT = ROOT / "harness/contracts/prompt-runtime-compliance.v1.json"
CAPTURE_MAPPING = ROOT / "harness/evals/runtime-compliance/runtime/capture-mapping.v1.json"
TAXONOMY = ROOT / "harness/contracts/execution-boundary-taxonomy.v1.json"
POSITIVE = ROOT / "harness/evals/runtime-compliance/contract-fixtures/receipt.positive.v1.json"

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
FORBIDDEN_PROPERTY_NAMES = {
    "raw_prompt", "raw_response", "transcript", "prompt_text", "response_text",
    "chain_of_thought", "hidden_reasoning", "secret", "api_key", "token", "credential",
}
REQUIRED_PILOT_RULES = {
    "PRCR.BOUNDARY.RECOVERY_REQUIRED", "PRCR.BOUNDARY.RECOVERY_OPENED",
    "PRCR.BOUNDARY.FIRST_ACTION_PROGRESS", "PRCR.ACTION.PARTIAL_READBACK",
    "PRCR.TERMINAL.COMPLETE_GATE", "PRCR.ACTION.NO_FALSE_PROOF_PROMOTION",
    "PRCR.PROOF.NO_PROMOTION_FROM_BLOCKED", "PRCR.PROOF.FINGERPRINT.REQUIRED",
    "PRCR.COMPLIANCE.PASS", "PRCR.COMPLIANCE.FAIL",
}
REQUIRED_MAPPING_TARGETS = {
    "model_config", "run + scenario", "boundary_events[]", "actions[]", "terminal",
    "proof.checks[]", "evidence[]", "violations[]", "regression_linkage",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def property_names(node) -> set:
    names: set = set()
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            names.update(props)
        for value in node.values():
            names |= property_names(value)
    elif isinstance(node, list):
        for item in node:
            names |= property_names(item)
    return names


def object_schemas(node):
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            yield node
        for value in node.values():
            yield from object_schemas(value)
    elif isinstance(node, list):
        for item in node:
            yield from object_schemas(item)


class RuntimeComplianceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load(RECEIPT_SCHEMA)
        cls.contract = load(CONTRACT)
        cls.mapping = load(CAPTURE_MAPPING)
        cls.taxonomy = load(TAXONOMY)
        cls.positive = load(POSITIVE)

    def test_receipt_schema_identity_and_strictness(self) -> None:
        self.assertEqual(self.schema["$schema"], DRAFT_2020_12)
        self.assertEqual(self.schema["$id"], "prompt-runtime-compliance-receipt/v1")
        self.assertEqual(self.schema["schema_version"], "prompt-runtime-compliance-receipt/v1")
        self.assertEqual(self.schema["boundary_taxonomy"], "execution-boundary-taxonomy/v1")
        Draft202012Validator.check_schema(self.schema)
        self.assertFalse(self.schema["additionalProperties"])
        for node in object_schemas(self.schema):
            self.assertIs(node.get("additionalProperties"), False, node.get("required"))

    def test_receipt_schema_forbids_raw_payload_fields(self) -> None:
        names = property_names(self.schema)
        self.assertEqual(names & FORBIDDEN_PROPERTY_NAMES, set())
        privacy = self.schema["$defs"]["privacy"]["properties"]
        for field in ("raw_transcript_persisted", "secrets_persisted", "hidden_reasoning_persisted"):
            self.assertEqual(privacy[field]["const"], False)

    def test_semantic_contract_identity_and_rule_table(self) -> None:
        self.assertEqual(self.contract["schema_version"], "prompt-runtime-compliance/v1")
        self.assertEqual(self.contract["receipt_schema"], "prompt-runtime-compliance-receipt/v1")
        self.assertEqual(self.contract["validation_result_schema"], "prompt-runtime-compliance-validation/v1")
        self.assertEqual(self.contract["capture_mapping_schema"], "prompt-runtime-compliance-capture-mapping/v1")
        rules = self.contract["rules"]
        ids = [r["rule_id"] for r in rules]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(r["rule_id"].startswith("PRCR.") for r in rules))
        self.assertTrue(all(r["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"} for r in rules))
        self.assertTrue(all(r["trigger"] and r["required"] for r in rules))
        pilot = self.contract["pilot_priority_rules"]
        self.assertTrue(set(pilot).issubset(set(ids)))
        self.assertTrue(REQUIRED_PILOT_RULES.issubset(set(pilot)))
        self.assertTrue(self.contract["nonzero_exit_conditions"])
        owners = {link["owner"] for link in self.contract["composition"]["links"]}
        self.assertIn("prompt-outcome-receipt/v1", owners)
        self.assertIn("observed-behavior-proof/v1", owners)

    def test_embedded_validation_result_schema_identity(self) -> None:
        vs = self.contract["validation_result_schema_definition"]
        self.assertEqual(vs["$schema"], DRAFT_2020_12)
        self.assertEqual(vs["$id"], "prompt-runtime-compliance-validation/v1")
        self.assertEqual(vs["schema_version"], "prompt-runtime-compliance-validation/v1")
        Draft202012Validator.check_schema(vs)
        self.assertIs(vs["additionalProperties"], False)
        finding = vs["properties"]["findings"]["items"]["properties"]
        for field in ("rule_id", "severity", "result", "subject", "message", "evidence_refs"):
            self.assertIn(field, finding)

    def test_capture_mapping_identity_and_completeness(self) -> None:
        self.assertEqual(self.mapping["schema_version"], "prompt-runtime-compliance-capture-mapping/v1")
        self.assertEqual(self.mapping["receipt_schema"], "prompt-runtime-compliance-receipt/v1")
        targets_text = " ".join(m["compliance_receipt"] for m in self.mapping["mappings"])
        missing = {token for token in REQUIRED_MAPPING_TARGETS if token not in targets_text}
        self.assertEqual(missing, set(), missing)
        self.assertTrue(all(m["required"] for m in self.mapping["mappings"]))
        invariants = " ".join(self.mapping["mapping_invariants"]).lower()
        self.assertIn("fail-closed", invariants)
        self.assertIn("compute-authority capture schema is not modified", invariants)

    def test_positive_fixture_validates_against_receipt_schema(self) -> None:
        errors = list(Draft202012Validator(self.schema).iter_errors(self.positive))
        self.assertEqual(errors, [], [e.message for e in errors])

    def test_positive_fixture_boundary_class_resolves_in_pinned_taxonomy(self) -> None:
        classes = {
            klass["id"]
            for family in self.taxonomy["families"]
            for klass in family["classes"]
        }
        for event in self.positive["boundary_events"]:
            if event["classification_status"] == "CANONICAL":
                self.assertIn(event["class_id"], classes)

    def test_additional_property_smuggling_is_rejected(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["raw_prompt"] = "should never be persisted"
        errors = [e.validator for e in Draft202012Validator(self.schema).iter_errors(bad)]
        self.assertIn("additionalProperties", errors)

    def test_missing_required_field_is_rejected(self) -> None:
        bad = copy.deepcopy(self.positive)
        del bad["proof"]
        errors = [e.validator for e in Draft202012Validator(self.schema).iter_errors(bad)]
        self.assertIn("required", errors)

    def test_malformed_identity_pattern_is_rejected(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["receipt_id"] = "bad id with spaces!"
        self.assertFalse(Draft202012Validator(self.schema).is_valid(bad))

    def test_privacy_block_pins_non_persistence(self) -> None:
        bad = copy.deepcopy(self.positive)
        bad["privacy"]["raw_transcript_persisted"] = True
        self.assertFalse(Draft202012Validator(self.schema).is_valid(bad))


if __name__ == "__main__":
    unittest.main()
