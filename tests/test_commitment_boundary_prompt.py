from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "commitment-boundary.v1.json"
AGENTS = ROOT / "AGENTS.md"
TEST_FLOOR = ROOT / "harness" / "test-floor.v1.json"


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

    def test_canonical_buffer_case_preserves_external_window_without_promoting_target(self) -> None:
        packet = {
            "schema_version": "commitment-boundary/v1",
            "communication_scope": "EXTERNAL",
            "facts": [
                {
                    "fact_id": "internal-arrival-target",
                    "kind": "INTERNAL_TARGET",
                    "value": "11:00 AM",
                    "source": "internal scheduling buffer",
                },
                {
                    "fact_id": "delivery-window",
                    "kind": "EXTERNAL_COMMITMENT",
                    "value": "11:30 AM-12:00 PM",
                    "source": "confirmed recipient-facing delivery window",
                    "externally_material": True,
                },
            ],
            "claims": [
                {
                    "claim_id": "assembly-during-delivery",
                    "source_ref": "delivery-window",
                    "source_kind": "EXTERNAL_COMMITMENT",
                    "asserted_kind": "EXTERNAL_COMMITMENT",
                    "text": "Our technicians will assemble on-site during delivery.",
                }
            ],
        }
        self.validator.validate(packet)
        canonical = self.schema["x-governance"]["canonical_case"]
        self.assertEqual(
            canonical["valid_external_wording"],
            "Our technicians will assemble on-site during delivery.",
        )

    def test_internal_target_cannot_be_promoted_to_external_commitment(self) -> None:
        packet = {
            "schema_version": "commitment-boundary/v1",
            "communication_scope": "EXTERNAL",
            "facts": [
                {
                    "fact_id": "internal-arrival-target",
                    "kind": "INTERNAL_TARGET",
                    "value": "11:00 AM",
                    "source": "internal scheduling buffer",
                }
            ],
            "claims": [
                {
                    "claim_id": "promoted-arrival-promise",
                    "source_ref": "internal-arrival-target",
                    "source_kind": "INTERNAL_TARGET",
                    "asserted_kind": "EXTERNAL_COMMITMENT",
                    "text": "Our technicians will be on-site by 11:00 AM.",
                }
            ],
        }
        errors = list(self.validator.iter_errors(packet))
        self.assertTrue(errors)
        self.assertEqual(
            self.schema["x-governance"]["canonical_case"]["invalid_external_wording"],
            "Our technicians will be on-site by 11:00 AM.",
        )

    def test_estimate_and_external_constraint_cannot_be_promoted_to_commitment(self) -> None:
        for source_kind in ("ESTIMATE", "EXTERNAL_CONSTRAINT"):
            with self.subTest(source_kind=source_kind):
                packet = {
                    "schema_version": "commitment-boundary/v1",
                    "communication_scope": "EXTERNAL",
                    "facts": [
                        {
                            "fact_id": "source",
                            "kind": source_kind,
                            "value": "working timing",
                            "source": "planning evidence",
                        }
                    ],
                    "claims": [
                        {
                            "claim_id": "promotion",
                            "source_ref": "source",
                            "source_kind": source_kind,
                            "asserted_kind": "EXTERNAL_COMMITMENT",
                            "text": "This is guaranteed.",
                        }
                    ],
                }
                self.assertTrue(list(self.validator.iter_errors(packet)))

    def test_root_governance_binds_commitment_boundary_and_cross_repo_p00_propagation(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")
        for phrase in (
            "Commitment Boundary Principle",
            "Internal targets, buffers, estimates, working dates, and planning assumptions are not external commitments",
            "Never promote them into promises",
            "harness/contracts/commitment-boundary.v1.json",
            "Any P00 governance installation or repair in another repository must carry this boundary forward",
            "Our technicians will assemble on-site during delivery.",
            "Our technicians will be on-site by 11:00 AM.",
        ):
            self.assertIn(phrase, agents)

    def test_regression_is_registered_in_deterministic_floor(self) -> None:
        floor = json.loads(TEST_FLOOR.read_text(encoding="utf-8"))
        self.assertIn(
            "tests/test_commitment_boundary_prompt.py",
            floor["self_tests"],
        )


if __name__ == "__main__":
    unittest.main()
