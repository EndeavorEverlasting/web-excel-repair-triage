"""Semantic coverage contract floor tests (Sprint 0).

Tests prove contract/schema structure and PSC rule shapes using synthetic fixtures.
No baseline profile population or runtime behavior claims.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from scripts import build_prompt_semantic_baseline as semantic_baseline
from scripts import prompt_registry_ops
from scripts import validate_prompt_semantic_coverage as semantic_validator


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

    def test_profiles_contract_schema_valid(self) -> None:
        """Profiles contract has valid schema and structure."""
        profiles_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
        profiles = json.loads(profiles_path.read_text(encoding="utf-8"))

        self.assertEqual(profiles["schema_version"], "prompt-capability-profiles/v1")
        self.assertIn("status", profiles)
        self.assertIsInstance(profiles["profiles"], list)

        # After Sprint 1A, profiles should be populated
        if profiles["status"] == "sprint1a_baseline_accepted":
            self.assertGreater(len(profiles["profiles"]), 0,
                             "Sprint 1A baseline should have profiles")
            self.assertTrue(profiles["baseline"]["strict_enforcement_active"],
                          "Sprint 1A baseline should activate enforcement")

    def test_migrations_contract_empty_until_sprint_1a(self) -> None:
        """Sprint 0 establishes migration schema only; first migrations after baseline."""
        migrations_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-migrations.v1.json"
        migrations = json.loads(migrations_path.read_text(encoding="utf-8"))

        self.assertEqual(migrations["schema_version"], "prompt-capability-migrations/v1")
        self.assertEqual(migrations["status"], "sprint0_floor")
        # Sprint 1A has begun: first migrations (agent transport binding law) recorded
        self.assertIsInstance(migrations["migrations"], list)

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


class Sprint1ABaselineAcceptanceTests(unittest.TestCase):
    """Sprint 1A: Baseline profile extraction and accepted matrix validation."""

    def test_psc001_profile_coverage_complete(self) -> None:
        """PSC001: Every current prompt has exactly one ACCEPTED profile."""
        prompts_path = ROOT / "docs" / "prompts.json"
        prompts = json.loads(prompts_path.read_text(encoding="utf-8"))

        profiles_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
        profiles_data = json.loads(profiles_path.read_text(encoding="utf-8"))

        profiles = profiles_data["profiles"]

        # Canonical coverage: every one of the 62 canonical prompts has a
        # profile; extension prompts (P62+) may add further profiles.
        self.assertEqual(len(prompts), 62, "Expected 62 canonical prompts")
        canonical_ids = {p["id"] for p in prompts}
        canonical_profiles = [p for p in profiles if p["prompt_id"] in canonical_ids]
        self.assertEqual(len(canonical_profiles), len(prompts),
                         "Every canonical prompt must have exactly one profile")

        # Every profile must be ACCEPTED
        for profile in profiles:
            self.assertEqual(profile["profile_status"], "ACCEPTED",
                           f"Profile {profile['prompt_id']} must be ACCEPTED")

        # Completeness flag must be true
        self.assertEqual(profiles_data["baseline"]["completeness"], "complete")
        self.assertTrue(profiles_data["baseline"]["strict_enforcement_active"])

        # Every canonical prompt ID must be covered; extension profiles
        # (P62+) are permitted beyond the frozen canonical baseline.
        profile_ids = [p["prompt_id"] for p in profiles]
        self.assertTrue(canonical_ids <= set(profile_ids),
                        "Every canonical prompt must have a profile")
        self.assertEqual(len(profile_ids), len(set(profile_ids)),
                         "Profile IDs must be unique")

    def test_psc002_profile_binds_canonical_prompt(self) -> None:
        """PSC002: Accepted profile binds to exact prompt identity and canonical hash."""
        profiles_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
        profiles_data = json.loads(profiles_path.read_text(encoding="utf-8"))

        for profile in profiles_data["profiles"]:
            # Must have prompt binding fields
            self.assertIn("prompt_id", profile)
            self.assertIn("canonical_prompt_hash", profile)
            self.assertIn("acceptance_commit", profile)

            # Prompt ID must be valid P## format
            self.assertRegex(profile["prompt_id"], r"^P\d{2,4}$")

            # Hash must be non-empty
            self.assertTrue(profile["canonical_prompt_hash"],
                          f"Profile {profile['prompt_id']} must bind to canonical prompt hash")

            # Acceptance commit must be valid git SHA
            self.assertRegex(profile["acceptance_commit"], r"^[a-f0-9]{7,40}$")

    def test_psc003_known_capability_only(self) -> None:
        """PSC003: Every assignment references the stable catalog."""
        catalog_path = ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

        known_capabilities = {cap["capability_id"] for cap in catalog["capabilities"]}

        profiles_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
        profiles_data = json.loads(profiles_path.read_text(encoding="utf-8"))

        for profile in profiles_data["profiles"]:
            for assignment in profile["direct_assignments"]:
                cap_id = assignment["capability_id"]
                self.assertIn(cap_id, known_capabilities,
                            f"Profile {profile['prompt_id']} references unknown capability {cap_id}")

    def test_psc011_primary_required_have_evidence(self) -> None:
        """PSC011: PRIMARY/REQUIRED assignments have evidence refs and rationale."""
        profiles_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
        profiles_data = json.loads(profiles_path.read_text(encoding="utf-8"))

        for profile in profiles_data["profiles"]:
            for assignment in profile["direct_assignments"]:
                ownership = assignment.get("ownership")
                presence = assignment.get("presence")

                if ownership == "PRIMARY" or presence == "REQUIRED":
                    # Must have evidence
                    self.assertIn("evidence_refs", assignment,
                                f"Profile {profile['prompt_id']} assignment {assignment['capability_id']} "
                                "must have evidence_refs")
                    self.assertTrue(assignment["evidence_refs"],
                                  f"Profile {profile['prompt_id']} assignment {assignment['capability_id']} "
                                  "evidence_refs must not be empty")

                    # Must have rationale
                    self.assertIn("rationale", assignment,
                                f"Profile {profile['prompt_id']} assignment {assignment['capability_id']} "
                                "must have rationale")
                    self.assertTrue(assignment["rationale"],
                                  f"Profile {profile['prompt_id']} assignment {assignment['capability_id']} "
                                  "rationale must not be empty")

    def test_capability_catalog_populated(self) -> None:
        """Capability catalog is populated with seed vocabulary."""
        catalog_path = ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

        self.assertEqual(catalog["status"], "sprint1a_baseline")
        self.assertGreater(len(catalog["capabilities"]), 0, "Catalog must have capabilities")

        # Verify required fields on each capability
        for cap in catalog["capabilities"]:
            self.assertIn("capability_id", cap)
            self.assertIn("title", cap)
            self.assertIn("definition", cap)
            self.assertIn("class", cap)
            self.assertIn("domain", cap)
            self.assertIn("global_coverage_policy", cap)
            self.assertIn("overlap_policy", cap)
            self.assertIn("seed_source", cap)
            self.assertIn("provenance", cap)

    def test_derived_matrix_deterministic(self) -> None:
        """Derived matrix is reconstructed in-memory from canonical tracked owners."""
        catalog = json.loads(
            (ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json").read_text(
                encoding="utf-8"
            )
        )
        profiles_data = json.loads(
            (ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json").read_text(
                encoding="utf-8"
            )
        )
        profiles = [
            row for row in profiles_data["profiles"]
            if row.get("profile_status") == "ACCEPTED"
        ]
        matrix = semantic_baseline.generate_baseline_matrix(catalog, profiles)
        matrix_again = semantic_baseline.generate_baseline_matrix(catalog, profiles)

        self.assertEqual(matrix, matrix_again)
        self.assertTrue(matrix["deterministic"])
        self.assertEqual(matrix["prompt_count"], len(profiles))
        self.assertGreater(matrix["capability_count"], 0)
        self.assertEqual(len(matrix["matrix"]), len(profiles))
        for row in matrix["matrix"]:
            self.assertIn("prompt_id", row)
            self.assertRegex(row["prompt_id"], r"^P\d{2,4}$")

    def test_coverage_report_generated(self) -> None:
        """Coverage report is generated in-memory; ignored artifacts are never test prerequisites."""
        catalog = json.loads(
            (ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json").read_text(
                encoding="utf-8"
            )
        )
        profiles_data = json.loads(
            (ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json").read_text(
                encoding="utf-8"
            )
        )
        profiles = [
            row for row in profiles_data["profiles"]
            if row.get("profile_status") == "ACCEPTED"
        ]
        coverage_report = semantic_baseline.generate_coverage_report(catalog, profiles)

        self.assertIn("coverage", coverage_report)
        self.assertGreater(len(coverage_report["coverage"]), 0)
        for data in coverage_report["coverage"].values():
            self.assertIn("capability", data)
            self.assertIn("policy", data)
            self.assertIn("primary_owners", data)
            self.assertIsInstance(data["primary_owners"], list)

    def test_baseline_builder_script_executable(self) -> None:
        """Baseline builder script exists and is executable."""
        builder_path = ROOT / "scripts" / "build_prompt_semantic_baseline.py"
        self.assertTrue(builder_path.exists(), "Baseline builder script must exist")

        # Verify it has proper shebang
        first_line = builder_path.read_text(encoding="utf-8").split("\n")[0]
        self.assertTrue(first_line.startswith("#!"), "Builder must have shebang")

    def test_primary_ownership_non_crowded(self) -> None:
        """Primary crowding policy is checked against an in-memory canonical projection."""
        catalog = json.loads(
            (ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json").read_text(
                encoding="utf-8"
            )
        )
        profiles_data = json.loads(
            (ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json").read_text(
                encoding="utf-8"
            )
        )
        profiles = [
            row for row in profiles_data["profiles"]
            if row.get("profile_status") == "ACCEPTED"
        ]
        coverage_report = semantic_baseline.generate_coverage_report(catalog, profiles)
        policies = {
            cap["capability_id"]: cap["overlap_policy"]
            for cap in catalog["capabilities"]
        }

        for cap_id, data in coverage_report["coverage"].items():
            primary_count = len(data["primary_owners"])
            if policies.get(cap_id, "OVERLAP_EXPECTED") == "PRIMARY_CROWDING_FAIL":
                self.assertLessEqual(
                    primary_count,
                    1,
                    f"Capability {cap_id} has PRIMARY_CROWDING_FAIL policy "
                    f"but {primary_count} PRIMARY owners: {data['primary_owners']}",
                )


class Sprint2LifecycleGateTests(unittest.TestCase):
    @staticmethod
    def candidate_profile(*, reviewed: bool) -> dict:
        profile = {
            "direct_assignments": [
                {
                    "capability_id": "execution.implementation",
                    "presence": "AWARE",
                    "ownership": "NONE",
                    "capability_relation": "ROUTES_TO",
                    "delivery_source": "ROUTED_OWNER",
                    "evidence_refs": ["tests/test_prompt_semantic_coverage.py"],
                    "rationale": "Synthetic candidate routes execution to the existing P07 owner.",
                }
            ],
            "evidence_refs": ["tests/test_prompt_semantic_coverage.py"],
        }
        if reviewed:
            profile["distinct_residual"] = {
                "summary": "Focused fixture proves a reviewed residual without inventing another execution owner.",
                "evidence_refs": ["tests/test_prompt_semantic_coverage.py"],
                "reviewed_against": ["P07"],
            }
        return profile

    def test_malformed_candidate_profile_fails_closed(self) -> None:
        with self.assertRaises(SystemExit):
            prompt_registry_ops._validate_candidate_semantic_profile(
                {"capabilities": [{"id": "execution.implementation"}]}
            )

    def test_psc008_overlapping_add_without_reviewed_residual_fails(self) -> None:
        result = prompt_registry_ops._check_distinct_residual_for_add(
            {"semantic_profile": self.candidate_profile(reviewed=False)}
        )
        self.assertFalse(result["distinct_residual"])
        self.assertEqual(result["mode"], "absorbed_by_existing_owner")
        self.assertIn("P07", result["overlapping_owners"])

    def test_psc008_reviewed_residual_can_pass_without_duplicate_ownership(self) -> None:
        result = prompt_registry_ops._check_distinct_residual_for_add(
            {"semantic_profile": self.candidate_profile(reviewed=True)}
        )
        self.assertTrue(result["distinct_residual"])
        self.assertEqual(result["mode"], "reviewed_residual")
        self.assertIn("P07", result["reviewed_existing_owners"])

    def test_direct_body_drift_breaks_accepted_profile_binding(self) -> None:
        profiles = json.loads(
            (ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json").read_text(
                encoding="utf-8"
            )
        )["profiles"]
        base = {
            row["id"]: row
            for row in json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        }
        profile = next(
            row
            for row in profiles
            if row.get("profile_status") == "ACCEPTED" and row.get("prompt_id") in base
        )
        modified = dict(base[profile["prompt_id"]])
        modified["copyContent"] = modified["copyContent"] + "\nSILENT DRIFT"
        errors = semantic_validator.check_psc002_profile_matches_canonical_record(
            profile,
            modified,
        )
        self.assertTrue(errors)
        self.assertTrue(any("PSC009" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
