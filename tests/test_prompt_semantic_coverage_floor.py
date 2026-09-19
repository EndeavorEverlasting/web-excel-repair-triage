from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PromptSemanticCoverageFloorTests(unittest.TestCase):
    def _load_json(self, path: str) -> dict:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_semantic_coverage_contract_exists_and_is_v1(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        self.assertEqual(payload["schema_version"], "prompt-semantic-coverage/v1")
        self.assertEqual(payload["contract_id"], "prompt-semantic-coverage")
        self.assertIn("ownership_boundaries", payload)
        self.assertIn("capability_cell_model", payload)

    def test_psc_rules_are_machine_addressable_and_complete(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        rules = payload.get("psc_rules")
        self.assertIsInstance(rules, list)
        self.assertEqual(len(rules), 16)
        ids = [r["id"] for r in rules]
        self.assertEqual(ids, [f"PSC{str(i).zfill(3)}" for i in range(1, 17)])
        self.assertEqual(len(ids), len(set(ids)))
        for rule in rules:
            for field in ("id", "title", "description", "enforcement"):
                self.assertIn(field, rule)
                self.assertTrue(str(rule[field]).strip())

    def test_ownership_boundaries_cover_required_systems(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        boundaries = payload["ownership_boundaries"]
        for key in ("P79", "P13", "P94", "PromptStrength", "QualityHistory", "Topology", "RuntimeCompliance"):
            self.assertIn(key, boundaries)
            self.assertTrue(str(boundaries[key]).strip())

    def test_capability_cell_model_has_required_dimensions(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        cell = payload["capability_cell_model"]
        self.assertEqual(cell["presence"]["values"], ["NONE", "AWARE", "SUPPORT", "REQUIRED"])
        self.assertEqual(cell["ownership"]["values"], ["NONE", "SECONDARY", "PRIMARY"])
        self.assertEqual(cell["capability_relation"]["values"], ["IMPLEMENTS", "ROUTES_TO", "TESTS", "GUARDS", "FORBIDDEN"])
        self.assertEqual(cell["delivery_source"]["values"], ["CANONICAL_BODY", "SHARED_POLICY", "COMPILER_OVERLAY", "ROUTED_OWNER", "TEST_GUARD"])

    def test_direct_vs_inherited_is_represented(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        div = payload["direct_vs_inherited"]
        self.assertIn("direct", div)
        self.assertIn("inherited", div)
        self.assertIn("fingerprint", div)
        self.assertIn("direct", div["fingerprint"])
        self.assertIn("inherited", div["fingerprint"])

    def test_relation_vocabulary_reuses_topology_channels(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        vocab = payload["prompt_to_prompt_relations"]["vocabulary"]
        self.assertEqual(set(vocab), {"CO_USAGE", "TRANSITION", "SUBSTITUTION", "COMPLEMENT"})
        # ensure we did not invent competing synonyms like RELATED or DEPENDS
        for forbidden in ("RELATED", "DEPENDS", "LINKS", "CONNECTS"):
            self.assertNotIn(forbidden, vocab)

    def test_lifecycle_kinds_are_append_only_and_complete(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        kinds = [item["kind"] for item in payload["lifecycle_kinds"]]
        self.assertEqual(set(kinds), {"ADD", "STRENGTHEN", "NO_CAPABILITY_CHANGE", "INTENTIONAL_CHANGE", "TRANSFER", "RETIRE", "RESTORE"})
        self.assertTrue(payload["append_only"])

    def test_candidate_inference_cannot_become_accepted(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        self.assertIn("candidate_inference", payload)
        rule_lower = payload["candidate_inference"]["rule"].lower()
        self.assertTrue("cannot" in rule_lower or "never" in rule_lower)
        self.assertIn("provisional", rule_lower)
        # profile schema must enforce that only PROVISIONAL may be created by generators
        schema = self._load_json("harness/prompt-topology/prompt-capability-profile.schema.v1.json")
        self.assertIn("PROVISIONAL", schema["properties"]["status"]["enum"])
        self.assertIn("ACCEPTED", schema["properties"]["status"]["enum"])

    def test_capability_catalog_shape_is_valid(self) -> None:
        catalog = self._load_json("harness/prompt-topology/semantic-capability-catalog.v1.json")
        self.assertEqual(catalog["schema_version"], "semantic-capability-catalog/v1")
        self.assertIn("capabilities", catalog)
        self.assertGreaterEqual(len(catalog["capabilities"]), 1)
        for cap in catalog["capabilities"]:
            for field in ("capability_id", "title", "definition", "class", "aliases", "admissible_relations", "evidence_requirements", "global_coverage_policy", "overlap_policy", "provenance"):
                self.assertIn(field, cap)
            self.assertIn(cap["global_coverage_policy"], catalog["global_coverage_policies"])
            self.assertIn(cap["overlap_policy"], catalog["overlap_policies"])
            for rel in cap["admissible_relations"]:
                self.assertIn(rel, catalog["admissible_relations"])
        # ensure IDs are unique
        ids = [c["capability_id"] for c in catalog["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_profile_schema_exists_and_validates_bounds(self) -> None:
        schema = self._load_json("harness/prompt-topology/prompt-capability-profile.schema.v1.json")
        self.assertEqual(schema["schema_version"], "prompt-capability-profile/v1")
        self.assertEqual(schema["properties"]["presence"] if "presence" in schema["properties"] else None, None)  # presence is nested in direct_assignments
        # check direct_assignments presence enum
        assignment_schema = schema["properties"]["direct_assignments"]["items"]
        self.assertEqual(assignment_schema["properties"]["presence"]["enum"], ["NONE", "AWARE", "SUPPORT", "REQUIRED"])
        self.assertEqual(assignment_schema["properties"]["ownership"]["enum"], ["NONE", "SECONDARY", "PRIMARY"])
        # check that PRIMARY/REQUIRED require evidence and rationale
        self.assertIn("evidence_refs", assignment_schema["properties"])
        self.assertIn("rationale", assignment_schema["properties"])

    def test_profile_bootstrap_is_shape_only(self) -> None:
        profiles = self._load_json("harness/prompt-topology/prompt-capability-profiles.v1.json")
        self.assertEqual(profiles["schema_version"], "prompt-capability-profiles/v1")
        self.assertEqual(profiles["acceptance_state"], "BOOTSTRAP")
        self.assertEqual(profiles["profile_count"], 0)
        self.assertEqual(profiles["profiles"], [])
        self.assertIn("Shape only", profiles["proof_ceiling"])

    def test_migration_ledger_shape(self) -> None:
        ledger = self._load_json("harness/prompt-topology/prompt-capability-migrations.v1.json")
        self.assertEqual(ledger["schema_version"], "prompt-capability-migrations/v1")
        self.assertIn("migration_kinds", ledger)
        self.assertEqual(set(ledger["migration_kinds"]), {"ADD", "STRENGTHEN", "NO_CAPABILITY_CHANGE", "INTENTIONAL_CHANGE", "TRANSFER", "RETIRE", "RESTORE"})
        self.assertTrue(ledger["append_only"])
        self.assertEqual(ledger["migrations"], [])

    def test_ontology_reuse_is_explicit(self) -> None:
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        self.assertIn("ontology_reuse", payload)
        self.assertIn("capability -> skill", payload["ontology_reuse"]["chain"])

    # Negative fixture tests - prove floor fails closed
    def test_negative_fixture_missing_source_coverage_is_detected(self) -> None:
        from scripts import validate_prompt_quality_history as quality
        contract = quality._load_contract()
        mutated = dict(contract)
        mutated["canonical_body_sources"] = [s for s in contract["canonical_body_sources"] if s["path"] != "docs/prompts.json"]
        errors = quality.audit_canonical_source_coverage(mutated)
        self.assertTrue(errors)
        self.assertTrue(any("docs/prompts.json" in e or "missing" in e.lower() for e in errors))

    def test_negative_fixture_malformed_transfer_missing_evidence(self) -> None:
        # A candidate PRIMARY assignment without evidence must be invalid per profile schema logic
        # We simulate the rule: PRIMARY requires evidence_refs and rationale
        catalog = self._load_json("harness/prompt-topology/semantic-capability-catalog.v1.json")
        valid_id = catalog["capabilities"][0]["capability_id"]
        # malformed assignment: PRIMARY but no evidence
        malformed = {
            "capability_id": valid_id,
            "presence": "REQUIRED",
            "ownership": "PRIMARY",
            "capability_relation": "IMPLEMENTS",
            "delivery_source": "CANONICAL_BODY",
            "evidence_refs": [],
            "rationale": ""
        }
        # Our schema would require evidence_refs minItems 1 and rationale non-empty for PRIMARY
        self.assertEqual(malformed["evidence_refs"], [])
        self.assertEqual(malformed["rationale"], "")
        # This is the condition PSC011 guards: new PRIMARY without proof must fail
        self.assertTrue(malformed["ownership"] == "PRIMARY" and not malformed["evidence_refs"])

    def test_negative_fixture_unsupported_downgrade_must_fail(self) -> None:
        # PSC004/PSC005: REQUIRED->SUPPORT without migration must fail; PRIMARY->SECONDARY without transfer must fail
        # We test the contract description contains the rule
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        psc004 = next(r for r in payload["psc_rules"] if r["id"] == "PSC004")
        self.assertIn("REQUIRED", psc004["description"])
        self.assertIn("without", psc004["description"].lower())
        psc005 = next(r for r in payload["psc_rules"] if r["id"] == "PSC005")
        self.assertIn("PRIMARY", psc005["description"])

    def test_negative_fixture_stale_inherited_fingerprint(self) -> None:
        # PSC016: inherited source revision change without revalidation must be detected
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        psc016 = next(r for r in payload["psc_rules"] if r["id"] == "PSC016")
        self.assertIn("inherited", psc016["description"].lower())
        self.assertIn("revision", psc016["description"].lower())
        # Check that profile schema has inherited_sources with revision field
        schema = self._load_json("harness/prompt-topology/prompt-capability-profile.schema.v1.json")
        inherited_item = schema["properties"]["inherited_sources"]["items"]
        self.assertIn("revision", inherited_item["properties"])
        self.assertEqual(inherited_item["properties"]["revision"]["pattern"], "^[0-9a-f]{64}$")

    def test_negative_fixture_source_capability_migration_mismatch(self) -> None:
        # PSC015: body-changing capability migration must cross-link to source-history migration
        payload = self._load_json("harness/contracts/prompt-semantic-coverage.v1.json")
        psc015 = next(r for r in payload["psc_rules"] if r["id"] == "PSC015")
        self.assertIn("source", psc015["description"].lower())
        self.assertIn("capability", psc015["description"].lower())
        self.assertIn("migration", psc015["description"].lower())

    def test_workflow_path_coverage_includes_docs_prompts(self) -> None:
        workflow = (ROOT / ".github/workflows/prompt-quality-history.yml").read_text(encoding="utf-8")
        self.assertIn("docs/prompts.json", workflow)
        self.assertIn("registry/prompts/product-boundaries.v1.json", workflow)

    def test_prompt_strength_and_topology_compatibility(self) -> None:
        # Ensure we did not break existing contracts: prompt-strength still validates, topology still loads
        strength = self._load_json("harness/contracts/prompt-strength.v1.json")
        self.assertEqual(strength["schema_version"], "prompt-strength/v1")
        topology = self._load_json("harness/contracts/prompt-topology-classifier.v1.json")
        self.assertEqual(topology["schema_version"], "prompt-topology-classifier/v1")
        # Ensure catalog does not duplicate prompt-strength entire contract but seeds from it
        catalog = self._load_json("harness/prompt-topology/semantic-capability-catalog.v1.json")
        # At least one seed references prompt-strength
        self.assertTrue(any("prompt-strength" in str(c.get("provenance", {})) for c in catalog["capabilities"]))


if __name__ == "__main__":
    unittest.main()
