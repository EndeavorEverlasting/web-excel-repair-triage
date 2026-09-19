"""Semantic coverage contract floor tests (Sprint 0).

Tests prove contract/schema structure and PSC rule shapes using synthetic fixtures.
No baseline profile population or runtime behavior claims.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SemanticCoverageContractTests(unittest.TestCase):
    """Test semantic coverage contract schema and structure."""

    def test_main_contract_declares_psc_rules(self) -> None:
        """Main contract establishes all PSC invariants."""
        contract_path = ROOT / "harness" / "contracts" / "prompt-semantic-coverage.v1.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        
        self.assertEqual(contract["schema_version"], "prompt-semantic-coverage/v1")
        self.assertEqual(contract["contract_id"], "prompt-semantic-coverage")
        
        invariants = contract["invariants"]
        self.assertIsInstance(invariants, list)
        self.assertGreaterEqual(len(invariants), 16)
        
        psc_ids = {item["id"] for item in invariants}
        required_rules = {
            "PSC001",  # PROFILE_COVERAGE_COMPLETE
            "PSC002",  # PROFILE_BINDS_CANONICAL_PROMPT
            "PSC003",  # KNOWN_CAPABILITY_ONLY
            "PSC004",  # REQUIRED_PRESENCE_NON_WEAKENING
            "PSC005",  # PRIMARY_OWNERSHIP_NON_WEAKENING
            "PSC006",  # TRANSFER_EQUAL_OR_STRONGER
            "PSC007",  # RETIRE_NO_COVERAGE_HOLE
            "PSC008",  # ADD_REQUIRES_DISTINCT_RESIDUAL
            "PSC009",  # BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION
            "PSC010",  # SAME_AGENT_RESCORING_CANNOT_RESET_PRIOR
            "PSC011",  # NEW_PRIMARY_OR_REQUIRED_REQUIRES_PROOF
            "PSC013",  # SOURCE_HISTORY_COMPLETE
            "PSC014",  # LIFECYCLE_TRANSITION_ATOMIC
            "PSC015",  # SOURCE_AND_CAPABILITY_MIGRATION_LINK
        }
        self.assertTrue(required_rules.issubset(psc_ids))

    def test_capability_catalog_schema_parses(self) -> None:
        """Capability catalog contract is valid JSON with expected structure."""
        catalog_path = ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        
        self.assertEqual(catalog["schema_version"], "semantic-capability-catalog/v1")
        self.assertEqual(catalog["catalog_id"], "prompt-semantic-capability-catalog")
        self.assertIsInstance(catalog["capabilities"], list)
        self.assertIn("seed_sources", catalog)

    def test_profile_schema_is_valid_json_schema(self) -> None:
        """Profile schema defines required fields and enums correctly."""
        schema_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profile.schema.v1.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["type"], "object")
        
        required = schema["required"]
        self.assertIn("prompt_id", required)
        self.assertIn("profile_version", required)
        self.assertIn("profile_status", required)
        self.assertIn("direct_assignments", required)
        self.assertIn("inherited_sources", required)
        
        properties = schema["properties"]
        self.assertEqual(
            properties["profile_status"]["enum"],
            ["PROVISIONAL", "REVIEW_READY", "ACCEPTED", "RETIRED"]
        )

    def test_profiles_contract_empty_until_sprint_1a(self) -> None:
        """Sprint 0 establishes schema only; profile population is Sprint 1A."""
        profiles_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
        profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
        
        self.assertEqual(profiles["schema_version"], "prompt-capability-profiles/v1")
        self.assertEqual(profiles["status"], "sprint0_floor")
        self.assertEqual(profiles["profiles"], [])
        self.assertFalse(profiles["baseline"]["strict_enforcement_active"])

    def test_migrations_contract_empty_until_sprint_1a(self) -> None:
        """Sprint 0 establishes migration schema only; first migrations after baseline."""
        migrations_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-migrations.v1.json"
        migrations = json.loads(migrations_path.read_text(encoding="utf-8"))
        
        self.assertEqual(migrations["schema_version"], "prompt-capability-migrations/v1")
        self.assertEqual(migrations["status"], "sprint0_floor")
        self.assertEqual(migrations["migrations"], [])
        
        kinds = migrations["migration_kinds"]
        self.assertIn("ADD", kinds)
        self.assertIn("STRENGTHEN", kinds)
        self.assertIn("TRANSFER", kinds)
        self.assertIn("RETIRE", kinds)
        self.assertIn("NO_CAPABILITY_CHANGE", kinds)


class SemanticCoverageRuleShapeTests(unittest.TestCase):
    """Prove PSC rule shapes using synthetic fixtures (Sprint 0 proof ceiling)."""

    def test_psc004_required_presence_weakening_shape(self) -> None:
        """Synthetic fixture shows REQUIRED->SUPPORT downgrade structure."""
        # This proves the rule shape, not enforcement (Sprint 1B)
        before = {
            "prompt_id": "P999",
            "profile_version": 1,
            "direct_assignments": [
                {
                    "capability_id": "TEST_CAP_001",
                    "presence": "REQUIRED",
                    "ownership": "PRIMARY",
                    "capability_relation": "IMPLEMENTS",
                    "delivery_source": "CANONICAL_BODY"
                }
            ]
        }
        
        after_weakened = {
            "prompt_id": "P999",
            "profile_version": 2,
            "direct_assignments": [
                {
                    "capability_id": "TEST_CAP_001",
                    "presence": "SUPPORT",  # Downgrade without migration
                    "ownership": "PRIMARY",
                    "capability_relation": "IMPLEMENTS",
                    "delivery_source": "CANONICAL_BODY"
                }
            ]
        }
        
        # Prove structure represents detectable weakening
        before_presence = before["direct_assignments"][0]["presence"]
        after_presence = after_weakened["direct_assignments"][0]["presence"]
        presence_order = ["NONE", "AWARE", "SUPPORT", "REQUIRED"]
        
        self.assertGreater(
            presence_order.index(before_presence),
            presence_order.index(after_presence),
            "Fixture represents detectable REQUIRED->SUPPORT downgrade"
        )

    def test_psc005_primary_ownership_weakening_shape(self) -> None:
        """Synthetic fixture shows PRIMARY->NONE removal without transfer."""
        before = {
            "prompt_id": "P998",
            "profile_version": 1,
            "direct_assignments": [
                {
                    "capability_id": "TEST_CAP_002",
                    "presence": "REQUIRED",
                    "ownership": "PRIMARY",
                    "capability_relation": "IMPLEMENTS",
                    "delivery_source": "CANONICAL_BODY"
                }
            ]
        }
        
        after_removed = {
            "prompt_id": "P998",
            "profile_version": 2,
            "direct_assignments": []  # Primary capability removed without transfer
        }
        
        before_caps = {a["capability_id"] for a in before["direct_assignments"]}
        after_caps = {a["capability_id"] for a in after_removed["direct_assignments"]}
        lost_caps = before_caps - after_caps
        
        self.assertTrue(lost_caps, "Fixture represents capability removal")
        self.assertIn("TEST_CAP_002", lost_caps)

    def test_psc006_transfer_equal_or_stronger_shape(self) -> None:
        """Synthetic fixture shows valid transfer structure."""
        retirement = {
            "migration_id": "TEST_RETIRE_001",
            "migration_kind": "RETIRE",
            "prompt_id": "P997",
            "old_profile_version": 1,
            "new_profile_version": None,
            "capability_deltas": [
                {
                    "capability_id": "TEST_CAP_003",
                    "before": {"presence": "REQUIRED", "ownership": "PRIMARY"},
                    "after": None,
                    "transfer_target": "P996",
                    "transfer_proof": "tests/test_prompt_semantic_coverage.py"
                }
            ]
        }
        
        successor = {
            "prompt_id": "P996",
            "profile_version": 2,
            "direct_assignments": [
                {
                    "capability_id": "TEST_CAP_003",
                    "presence": "REQUIRED",  # Equal strength
                    "ownership": "PRIMARY",
                    "capability_relation": "IMPLEMENTS",
                    "delivery_source": "CANONICAL_BODY"
                }
            ]
        }
        
        delta = retirement["capability_deltas"][0]
        self.assertIsNotNone(delta["transfer_target"])
        self.assertEqual(delta["transfer_target"], successor["prompt_id"])
        
        successor_assignment = successor["direct_assignments"][0]
        self.assertEqual(successor_assignment["presence"], "REQUIRED")
        self.assertEqual(successor_assignment["ownership"], "PRIMARY")

    def test_psc007_retire_coverage_hole_shape(self) -> None:
        """Synthetic fixture shows retirement without successor creating hole."""
        retirement_without_successor = {
            "migration_id": "TEST_RETIRE_002",
            "migration_kind": "RETIRE",
            "prompt_id": "P995",
            "capability_deltas": [
                {
                    "capability_id": "TEST_CAP_004",
                    "before": {"presence": "REQUIRED", "ownership": "PRIMARY"},
                    "after": None,
                    "transfer_target": None  # No successor
                }
            ]
        }
        
        global_coverage_before = {"TEST_CAP_004": ["P995"]}
        global_coverage_after = {"TEST_CAP_004": []}  # Coverage hole
        
        cap_id = "TEST_CAP_004"
        self.assertIn(cap_id, global_coverage_before)
        self.assertTrue(global_coverage_before[cap_id])
        self.assertFalse(global_coverage_after[cap_id], "Retirement creates coverage hole")

    def test_psc009_body_change_requires_disposition_shape(self) -> None:
        """Synthetic fixture shows body change needing capability disposition."""
        body_change_without_disposition = {
            "prompt_id": "P994",
            "old_canonical_hash": "aaa111",
            "new_canonical_hash": "bbb222",
            "capability_migration": None  # Missing required disposition
        }
        
        body_change_with_disposition = {
            "prompt_id": "P994",
            "old_canonical_hash": "aaa111",
            "new_canonical_hash": "bbb222",
            "capability_migration": {
                "migration_kind": "NO_CAPABILITY_CHANGE",
                "focused_proof": ["tests/test_prompt_semantic_coverage.py"]
            }
        }
        
        self.assertNotEqual(
            body_change_without_disposition["old_canonical_hash"],
            body_change_without_disposition["new_canonical_hash"]
        )
        self.assertIsNone(body_change_without_disposition["capability_migration"])
        self.assertIsNotNone(body_change_with_disposition["capability_migration"])

    def test_psc010_rescoring_cannot_reset_prior_shape(self) -> None:
        """Synthetic fixture shows ACCEPTED profile cannot be replaced by generated inference."""
        accepted_prior = {
            "prompt_id": "P993",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "profile_sha256": "abc123...",
            "acceptance_commit": "25a2b6b6"
        }
        
        generated_candidate = {
            "prompt_id": "P993",
            "profile_version": 1,  # Same version - attempting replacement
            "profile_status": "PROVISIONAL",
            "profile_sha256": "def456...",  # Different hash
            "acceptance_commit": None
        }
        
        self.assertEqual(accepted_prior["profile_status"], "ACCEPTED")
        self.assertEqual(generated_candidate["profile_status"], "PROVISIONAL")
        self.assertIsNotNone(accepted_prior["acceptance_commit"])
        
        # Attempting to replace ACCEPTED with same version is detectable
        self.assertEqual(accepted_prior["profile_version"], generated_candidate["profile_version"])
        self.assertNotEqual(accepted_prior["profile_sha256"], generated_candidate["profile_sha256"])

    def test_psc013_enforced_by_quality_history_validator(self) -> None:
        """PSC013 SOURCE_HISTORY_COMPLETE is enforced by updated quality history validator."""
        from scripts import validate_prompt_quality_history as quality
        
        contract = quality._load_contract()
        errors = quality.audit_source_set_parity(contract)
        
        # Should pass with docs/prompts.json now included
        self.assertEqual(errors, [])
        
        # Protected sources must include base registry
        protected = {item["path"] for item in contract["canonical_body_sources"]}
        self.assertIn("docs/prompts.json", protected)


if __name__ == "__main__":
    unittest.main()
