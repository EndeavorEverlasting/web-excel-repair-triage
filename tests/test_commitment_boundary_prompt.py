from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts import validate_commitment_boundary as commitment_boundary


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "commitment-boundary.v1.json"
AGENTS = ROOT / "AGENTS.md"
TEST_FLOOR = ROOT / "harness" / "test-floor.v1.json"
VALIDATORS = ROOT / "harness" / "validators.v1.json"


class CommitmentBoundaryPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)

    def test_contract_is_valid_portable_json_schema(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(self.schema["$id"], "commitment-boundary/v1")
        self.assertEqual(self.schema["schema_version"], "commitment-boundary/v1")
        governance = self.schema["x-governance"]
        self.assertEqual(governance["principle_id"], "commitment-boundary")
        self.assertTrue(governance["portable"])
        self.assertEqual(governance["propagation_owner"], "P00")
        self.assertEqual(
            governance["semantic_validator"],
            "scripts/validate_commitment_boundary.py",
        )
        self.assertIn("does not prove", governance["proof_ceiling"])

    def test_invalid_contract_schema_uses_typed_failure(self) -> None:
        invalid = copy.deepcopy(self.schema)
        invalid["type"] = 7
        with self.assertRaisesRegex(
            commitment_boundary.CommitmentBoundaryError,
            "invalid contract schema",
        ):
            commitment_boundary.validate_contract_schema(invalid)

    def test_canonical_buffer_case_preserves_external_window_without_promoting_target(self) -> None:
        packet = commitment_boundary.canonical_packet()
        result = commitment_boundary.validate_packet(packet, self.schema)
        self.assertEqual(result["status"], "PASS")
        canonical = self.schema["x-governance"]["canonical_case"]
        self.assertEqual(
            canonical["valid_external_wording"],
            "Our technicians will assemble on-site during delivery.",
        )

    def test_internal_target_cannot_be_promoted_to_external_commitment(self) -> None:
        packet = commitment_boundary.canonical_packet()
        packet["claims"] = [
            {
                "claim_id": "promoted-arrival-promise",
                "source_ref": "internal-arrival-target",
                "asserted_kind": "EXTERNAL_COMMITMENT",
                "text": "Our technicians will be on-site by 11:00 AM.",
            }
        ]
        with self.assertRaisesRegex(
            commitment_boundary.CommitmentBoundaryError,
            "promotes INTERNAL_TARGET to EXTERNAL_COMMITMENT",
        ):
            commitment_boundary.validate_packet(packet, self.schema)
        self.assertEqual(
            self.schema["x-governance"]["canonical_case"]["invalid_external_wording"],
            "Our technicians will be on-site by 11:00 AM.",
        )

    def test_estimate_and_external_constraint_cannot_be_promoted_to_commitment(self) -> None:
        cases = (
            {
                "kind": "ESTIMATE",
                "authority_class": "ESTIMATE_EVIDENCE",
                "evidence_ref": "estimate-evidence:working-arrival",
            },
            {
                "kind": "EXTERNAL_CONSTRAINT",
                "authority_class": "RECIPIENT_CONFIRMED",
                "evidence_ref": "recipient-confirmation:access-window",
            },
        )
        for case in cases:
            with self.subTest(kind=case["kind"]):
                packet = {
                    "schema_version": "commitment-boundary/v1",
                    "communication_scope": "EXTERNAL",
                    "facts": [
                        {
                            "fact_id": "source",
                            "kind": case["kind"],
                            "value": "working timing",
                            "authority_class": case["authority_class"],
                            "evidence_ref": case["evidence_ref"],
                            "externally_material": True,
                        }
                    ],
                    "claims": [
                        {
                            "claim_id": "promotion",
                            "source_ref": "source",
                            "asserted_kind": "EXTERNAL_COMMITMENT",
                            "text": "This is guaranteed.",
                        }
                    ],
                }
                with self.assertRaisesRegex(
                    commitment_boundary.CommitmentBoundaryError,
                    f"promotes {case['kind']} to EXTERNAL_COMMITMENT",
                ):
                    commitment_boundary.validate_packet(packet, self.schema)

    def test_claim_source_must_resolve_uniquely(self) -> None:
        missing = commitment_boundary.canonical_packet()
        missing["claims"][0]["source_ref"] = "does-not-exist"
        with self.assertRaisesRegex(
            commitment_boundary.CommitmentBoundaryError,
            "references missing fact",
        ):
            commitment_boundary.validate_packet(missing, self.schema)

        duplicate = commitment_boundary.canonical_packet()
        duplicate["facts"].append(copy.deepcopy(duplicate["facts"][0]))
        with self.assertRaisesRegex(
            commitment_boundary.CommitmentBoundaryError,
            "duplicate fact_id",
        ):
            commitment_boundary.validate_packet(duplicate, self.schema)

    def test_claim_cannot_supply_a_fake_source_kind(self) -> None:
        packet = commitment_boundary.canonical_packet()
        packet["claims"][0]["source_kind"] = "EXTERNAL_COMMITMENT"
        errors = list(self.validator.iter_errors(packet))
        self.assertTrue(errors)
        self.assertTrue(
            any("Additional properties are not allowed" in error.message for error in errors)
        )

    def test_external_commitment_requires_typed_external_authority_and_evidence_ref(self) -> None:
        packet = commitment_boundary.canonical_packet()
        source = packet["facts"][1]
        source["authority_class"] = "INTERNAL_PLANNING"
        source["evidence_ref"] = "internal-plan:fabricated-promise"
        with self.assertRaisesRegex(
            commitment_boundary.CommitmentBoundaryError,
            "schema validation failed",
        ):
            commitment_boundary.validate_packet(packet, self.schema)

    def test_non_material_internal_target_is_not_exposed_in_external_packet(self) -> None:
        packet = commitment_boundary.canonical_packet()
        packet["claims"] = [
            {
                "claim_id": "exposed-buffer",
                "source_ref": "internal-arrival-target",
                "asserted_kind": "INTERNAL_TARGET",
                "text": "Our internal target is 11:00 AM.",
            }
        ]
        with self.assertRaisesRegex(
            commitment_boundary.CommitmentBoundaryError,
            "exposes a non-material internal target externally",
        ):
            commitment_boundary.validate_packet(packet, self.schema)

    def test_root_governance_binds_commitment_boundary_and_p00_ownership(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")
        for phrase in (
            "**Commitment boundary:**",
            "internal targets, buffers, estimates, working dates, and planning assumptions are not external commitments",
            "never promote them into promises",
            "P00 owns propagation",
            "harness/contracts/commitment-boundary.v1.json",
        ):
            self.assertIn(phrase, agents)

    def test_regression_and_validator_are_registered(self) -> None:
        floor = json.loads(TEST_FLOOR.read_text(encoding="utf-8"))
        self.assertIn(
            "tests/test_commitment_boundary_prompt.py",
            floor["self_tests"],
        )

        validators = json.loads(VALIDATORS.read_text(encoding="utf-8"))
        by_id = {row["id"]: row for row in validators["validators"]}
        self.assertEqual(
            by_id["commitment-boundary-audit"]["command"],
            "python3 scripts/validate_commitment_boundary.py --summary",
        )
        self.assertEqual(
            by_id["commitment-boundary-tests"]["command"],
            "python3 -m unittest tests.test_commitment_boundary_prompt -v",
        )
        self.assertIn(
            "commitment-boundary-audit",
            validators["profiles"]["required_checks"],
        )
        self.assertIn(
            "commitment-boundary-tests",
            validators["profiles"]["required_checks"],
        )


if __name__ == "__main__":
    unittest.main()
