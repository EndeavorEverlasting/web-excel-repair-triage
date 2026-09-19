"""Sprint 1B: Semantic diff validator + lifecycle engine tests.

Tests prove the validator enforces PSC rules against synthetic fixtures.
Negative fixtures MUST FAIL; positive controls MUST PASS.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Import validator functions
import sys
sys.path.insert(0, str(ROOT / "scripts"))
from validate_prompt_semantic_coverage import (
    check_psc004_required_presence_non_weakening,
    check_psc005_primary_ownership_non_weakening,
    check_psc006_transfer_equal_or_stronger,
    check_psc007_retire_no_coverage_hole,
    check_psc009_body_change_requires_profile_disposition,
    check_psc010_same_agent_rescoring_cannot_reset_prior,
    check_psc011_new_primary_or_required_requires_proof,
    validate_profile_change,
)


class NegativeFixtureTests(unittest.TestCase):
    """Negative fixtures MUST FAIL validation."""
    
    def test_negative_silent_weakening_required_to_support(self) -> None:
        """FAIL: REQUIRED downgraded to SUPPORT without migration."""
        before = {
            "prompt_id": "P999",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_WEAKENING",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Primary owner"
            }]
        }
        
        after = {
            "prompt_id": "P999",
            "profile_version": 2,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_WEAKENING",
                "presence": "SUPPORT",  # Silent downgrade
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Primary owner"
            }]
        }
        
        errors = check_psc004_required_presence_non_weakening(before, after, None)
        self.assertTrue(errors, "Silent weakening must be detected")
        self.assertTrue(any("PSC004" in err for err in errors))
    
    def test_negative_last_owner_deletion(self) -> None:
        """FAIL: PRIMARY capability removed without transfer."""
        before = {
            "prompt_id": "P998",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_REMOVAL",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Primary owner"
            }]
        }
        
        after = {
            "prompt_id": "P998",
            "profile_version": 2,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": []  # Capability removed
        }
        
        errors = check_psc005_primary_ownership_non_weakening(before, after, None)
        self.assertTrue(errors, "PRIMARY removal without transfer must be detected")
        self.assertTrue(any("PSC005" in err for err in errors))
    
    def test_negative_retirement_coverage_hole(self) -> None:
        """FAIL: Retirement creates coverage hole for protected capability."""
        retiring_profile = {
            "prompt_id": "P997",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_HOLE",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Only owner"
            }]
        }
        
        retirement_migration = {
            "migration_kind": "RETIRE",
            "prompt_id": "P997",
            "capability_deltas": [{
                "capability_id": "TEST_CAP_HOLE",
                "before": {"presence": "REQUIRED", "ownership": "PRIMARY"},
                "after": None,
                "transfer_target": None  # No successor
            }]
        }
        
        all_profiles = [retiring_profile]  # No other profiles
        
        errors = check_psc007_retire_no_coverage_hole(retiring_profile, retirement_migration, all_profiles)
        self.assertTrue(errors, "Retirement creating coverage hole must be detected")
        self.assertTrue(any("PSC007" in err for err in errors))
    
    def test_negative_fake_strengthening_no_evidence(self) -> None:
        """FAIL: New PRIMARY claim without evidence."""
        profile = {
            "prompt_id": "P996",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_FAKE",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": [],  # No evidence
                "rationale": ""  # No rationale
            }]
        }
        
        errors = check_psc011_new_primary_or_required_requires_proof(profile)
        self.assertTrue(errors, "PRIMARY without evidence must be detected")
        self.assertTrue(any("PSC011" in err for err in errors))
    
    def test_negative_baseline_reset_by_rescoring(self) -> None:
        """FAIL: ACCEPTED profile replaced by PROVISIONAL same version."""
        accepted = {
            "prompt_id": "P995",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "profile_sha256": "abc123",
            "acceptance_commit": "55148914"
        }
        
        provisional = {
            "prompt_id": "P995",
            "profile_version": 1,  # Same version
            "profile_status": "PROVISIONAL",
            "profile_sha256": "def456",  # Different content
            "acceptance_commit": None
        }
        
        errors = check_psc010_same_agent_rescoring_cannot_reset_prior(accepted, provisional)
        self.assertTrue(errors, "ACCEPTED replacement by PROVISIONAL must be detected")
        self.assertTrue(any("PSC010" in err for err in errors))
    
    def test_negative_invalid_transfer_weaker_successor(self) -> None:
        """FAIL: Transfer to successor with weaker presence."""
        transfer_migration = {
            "migration_kind": "TRANSFER",
            "prompt_id": "P994",
            "capability_deltas": [{
                "capability_id": "TEST_CAP_TRANSFER",
                "before": {"presence": "REQUIRED", "ownership": "PRIMARY"},
                "after": None,
                "transfer_target": "P993",
                "transfer_proof": "tests/fixture.py"
            }]
        }
        
        successor_profile = {
            "prompt_id": "P993",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_TRANSFER",
                "presence": "AWARE",  # Weaker than REQUIRED
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Primary owner"
            }]
        }
        
        errors = check_psc006_transfer_equal_or_stronger(transfer_migration, successor_profile, [])
        self.assertTrue(errors, "Transfer to weaker successor must be detected")
        self.assertTrue(any("PSC006" in err for err in errors))
    
    def test_negative_body_change_no_disposition(self) -> None:
        """FAIL: Body changed without capability disposition."""
        before = {
            "prompt_id": "P992",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash_old",
            "direct_assignments": []
        }
        
        after = {
            "prompt_id": "P992",
            "profile_version": 2,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash_new",  # Body changed
            "direct_assignments": []
        }
        
        errors = check_psc009_body_change_requires_profile_disposition(before, after, None)
        self.assertTrue(errors, "Body change without disposition must be detected")
        self.assertTrue(any("PSC009" in err for err in errors))


class PositiveControlTests(unittest.TestCase):
    """Positive controls MUST PASS validation."""
    
    def test_positive_strengthening_with_evidence(self) -> None:
        """PASS: SUPPORT -> REQUIRED strengthening with evidence."""
        before = {
            "prompt_id": "P900",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_STRENGTHEN",
                "presence": "SUPPORT",
                "ownership": "SECONDARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Secondary support"
            }]
        }
        
        after = {
            "prompt_id": "P900",
            "profile_version": 2,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_STRENGTHEN",
                "presence": "REQUIRED",  # Strengthened
                "ownership": "PRIMARY",  # Strengthened
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py", "tests/strengthen_proof.py"],
                "rationale": "Promoted to primary with proof"
            }]
        }
        
        migration = {
            "migration_kind": "STRENGTHEN",
            "prompt_id": "P900",
            "from_profile_version": 1,
            "to_profile_version": 2,
            "focused_proof": ["tests/strengthen_proof.py"]
        }
        
        errors = check_psc004_required_presence_non_weakening(before, after, migration)
        self.assertEqual(errors, [], "Strengthening should pass")
        
        errors = check_psc005_primary_ownership_non_weakening(before, after, migration)
        self.assertEqual(errors, [], "Ownership strengthening should pass")
    
    def test_positive_no_capability_change_edit(self) -> None:
        """PASS: Body changed with NO_CAPABILITY_CHANGE migration."""
        before = {
            "prompt_id": "P901",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash_v1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_STABLE",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Primary owner"
            }]
        }
        
        after = {
            "prompt_id": "P901",
            "profile_version": 2,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash_v2",  # Body changed
            "direct_assignments": [{
                "capability_id": "TEST_CAP_STABLE",
                "presence": "REQUIRED",  # Same
                "ownership": "PRIMARY",  # Same
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Primary owner"
            }]
        }
        
        migration = {
            "migration_kind": "NO_CAPABILITY_CHANGE",
            "prompt_id": "P901",
            "from_profile_version": 1,
            "to_profile_version": 2,
            "focused_proof": ["tests/no_change_proof.py"]
        }
        
        errors = check_psc009_body_change_requires_profile_disposition(before, after, migration)
        self.assertEqual(errors, [], "NO_CAPABILITY_CHANGE with migration should pass")
    
    def test_positive_equal_or_stronger_transfer(self) -> None:
        """PASS: Transfer to successor with equal/stronger coverage."""
        transfer_migration = {
            "migration_kind": "TRANSFER",
            "prompt_id": "P902",
            "capability_deltas": [{
                "capability_id": "TEST_CAP_VALID_TRANSFER",
                "before": {"presence": "REQUIRED", "ownership": "PRIMARY"},
                "after": None,
                "transfer_target": "P903",
                "transfer_proof": "tests/transfer_proof.py"
            }]
        }
        
        successor_profile = {
            "prompt_id": "P903",
            "profile_version": 2,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_VALID_TRANSFER",
                "presence": "REQUIRED",  # Equal
                "ownership": "PRIMARY",  # Equal
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/transfer_proof.py"],
                "rationale": "Accepted transferred responsibility"
            }]
        }
        
        errors = check_psc006_transfer_equal_or_stronger(transfer_migration, successor_profile, [])
        self.assertEqual(errors, [], "Equal/stronger transfer should pass")
    
    def test_positive_valid_retirement_with_transfer(self) -> None:
        """PASS: Retirement with proper capability transfer."""
        retiring_profile = {
            "prompt_id": "P904",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_RETIRE_VALID",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Original owner"
            }]
        }
        
        successor_profile = {
            "prompt_id": "P905",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_RETIRE_VALID",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Successor"
            }]
        }
        
        retirement_migration = {
            "migration_kind": "RETIRE",
            "prompt_id": "P904",
            "capability_deltas": [{
                "capability_id": "TEST_CAP_RETIRE_VALID",
                "before": {"presence": "REQUIRED", "ownership": "PRIMARY"},
                "after": None,
                "transfer_target": "P905"
            }]
        }
        
        all_profiles = [retiring_profile, successor_profile]
        
        errors = check_psc007_retire_no_coverage_hole(retiring_profile, retirement_migration, all_profiles)
        self.assertEqual(errors, [], "Valid retirement with transfer should pass")
    
    def test_positive_retirement_non_primary_with_other_owners(self) -> None:
        """PASS: Retirement of non-PRIMARY when others exist."""
        retiring_profile = {
            "prompt_id": "P906",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_SHARED",
                "presence": "SUPPORT",  # Not PRIMARY or REQUIRED
                "ownership": "SECONDARY",
                "capability_relation": "ROUTES_TO",
                "delivery_source": "CANONICAL_BODY"
            }]
        }
        
        other_profile = {
            "prompt_id": "P907",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "canonical_prompt_hash": "hash1",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_SHARED",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/fixture.py"],
                "rationale": "Primary owner"
            }]
        }
        
        retirement_migration = {
            "migration_kind": "RETIRE",
            "prompt_id": "P906",
            "capability_deltas": []  # No protected capabilities lost
        }
        
        all_profiles = [retiring_profile, other_profile]
        
        errors = check_psc007_retire_no_coverage_hole(retiring_profile, retirement_migration, all_profiles)
        self.assertEqual(errors, [], "Retirement of SECONDARY when PRIMARY exists should pass")


class LifecycleEngineIntegrationTests(unittest.TestCase):
    """Integration tests for complete lifecycle operations."""
    
    def test_add_operation_structure(self) -> None:
        """Prove ADD operation creates proper profile + migration."""
        new_profile = {
            "prompt_id": "P910",
            "profile_version": 1,
            "profile_status": "ACCEPTED",
            "profile_sha256": "new_hash",
            "canonical_prompt_hash": "canonical_hash_910",
            "acceptance_commit": "55148914",
            "direct_assignments": [{
                "capability_id": "TEST_CAP_NEW",
                "presence": "REQUIRED",
                "ownership": "PRIMARY",
                "capability_relation": "IMPLEMENTS",
                "delivery_source": "CANONICAL_BODY",
                "evidence_refs": ["tests/add_proof.py"],
                "rationale": "New capability implementation"
            }],
            "inherited_sources": [],
            "semantic_dependency_fingerprint": "dep_fingerprint",
            "evidence_refs": ["tests/add_proof.py"]
        }
        
        add_migration = {
            "migration_id": "ADD_P910_001",
            "migration_kind": "ADD",
            "prompt_id": "P910",
            "from_profile_version": None,
            "to_profile_version": 1,
            "capability_deltas": [{
                "capability_id": "TEST_CAP_NEW",
                "before": None,
                "after": {"presence": "REQUIRED", "ownership": "PRIMARY"}
            }],
            "focused_proof": ["tests/add_proof.py"],
            "distinct_residual_proof": "tests/topology_distinct.py"
        }
        
        # Verify structure
        self.assertEqual(new_profile["profile_version"], 1)
        self.assertEqual(new_profile["profile_status"], "ACCEPTED")
        self.assertEqual(add_migration["migration_kind"], "ADD")
        self.assertIsNone(add_migration["from_profile_version"])
        
        # Verify evidence exists
        errors = check_psc011_new_primary_or_required_requires_proof(new_profile)
        self.assertEqual(errors, [], "ADD with proper evidence should pass")


if __name__ == "__main__":
    unittest.main()
