from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_prompt_quality_history as quality

ROOT = Path(__file__).resolve().parents[1]


class PromptQualityHistoryTests(unittest.TestCase):
    def test_contract_pins_pre_compiler_known_good_floor(self) -> None:
        contract = json.loads(
            (ROOT / "harness" / "contracts" / "prompt-quality-history.v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["schema_version"], "prompt-quality-history/v1")
        self.assertEqual(
            contract["baseline"]["commit"],
            "93a8886d77e043023eeecca05f5e2e8e13b89f06",
        )
        self.assertGreaterEqual(len(contract["canonical_body_sources"]), 8)
        self.assertIn("fail", contract["effective_identity"]["temporary_exception_policy"].lower())

    def test_current_canonical_body_sources_match_accepted_history(self) -> None:
        contract = quality._load_contract()
        migrations = quality._load_migrations(contract)
        self.assertEqual(quality.audit_source_history(contract, migrations), [])

    def test_effective_prompt_variants_preserve_canonical_identity_except_active_owned_regression(self) -> None:
        contract = quality._load_contract()
        migrations = quality._load_migrations(contract)
        self.assertEqual(quality.audit_effective_identity(contract, migrations), [])

    def test_p07_exception_is_explicitly_owned_by_concurrent_repair(self) -> None:
        contract = quality._load_contract()
        exceptions = contract["effective_identity"]["temporary_exceptions"]
        self.assertEqual(
            [(item["prompt_id"], item["owner_pr"]) for item in exceptions],
            [("P07", 533)],
        )
        self.assertIn("Canonical containment is restored", exceptions[0]["remove_when"])

    def test_replacement_authority_requires_explicit_migration_intent(self) -> None:
        migrations = [
            {
                "migration_id": "TEST-REPLACEMENT",
                "path": "registry/prompts/prompt-overrides.v1.json",
                "from_git_blob_sha1": "0" * 40,
                "to_git_blob_sha1": "1" * 40,
                "affected_prompt_ids": ["P07", "P13"],
                "change_kind": "intentional_semantic_change",
                "effective_identity_change": "replacement_authorized",
                "rationale": "test only",
                "focused_tests": ["tests/test_prompt_quality_history.py"],
            },
            {
                "migration_id": "TEST-PRESERVE",
                "path": "registry/prompts/prompt-overrides.v1.json",
                "from_git_blob_sha1": "1" * 40,
                "to_git_blob_sha1": "2" * 40,
                "affected_prompt_ids": ["P03"],
                "change_kind": "strengthening",
                "effective_identity_change": "preserve_canonical",
                "rationale": "test only",
                "focused_tests": ["tests/test_prompt_quality_history.py"],
            },
        ]
        self.assertEqual(
            quality._replacement_authorized_prompt_ids(migrations),
            {"P07", "P13"},
        )

    def test_migration_chain_rejects_silent_baseline_reset(self) -> None:
        contract = quality._load_contract()
        first = contract["canonical_body_sources"][0]
        bad = [
            {
                "migration_id": "TEST-INVALID-CHAIN",
                "path": first["path"],
                "from_git_blob_sha1": "0" * 40,
                "to_git_blob_sha1": "1" * 40,
                "affected_prompt_ids": ["P03"],
                "change_kind": "strengthening",
                "effective_identity_change": "preserve_canonical",
                "rationale": "test only",
                "focused_tests": ["tests/test_prompt_quality_history.py"],
            }
        ]
        _, errors = quality._accepted_source_heads(contract, bad)
        self.assertTrue(errors)
        self.assertIn("accepted head", errors[0])

    def test_temporary_exception_becomes_stale_after_restoration(self) -> None:
        contract = quality._load_contract()
        original = quality.builder.load_prompt_kit_registry
        canonical = {p["id"]: p for p in quality.builder.load_prompt_registry()}
        repaired = [dict(prompt) for prompt in original()]
        for prompt in repaired:
            if prompt["id"] == "P07":
                base = canonical["P07"]["copyContent"]
                prompt["compiledEffectivePrompts"] = {
                    "exhaustive": base + "\n\nEXECUTION PROFILE OVERLAY",
                    "efficient": base + "\n\nEXECUTION PROFILE OVERLAY",
                }
        quality.builder.load_prompt_kit_registry = lambda: repaired
        try:
            errors = quality.audit_effective_identity(contract, [])
        finally:
            quality.builder.load_prompt_kit_registry = original
        self.assertTrue(any("temporary exceptions are no longer needed" in item for item in errors))

    def test_source_set_parity_rejects_missing_canonical_source(self) -> None:
        """PSC013: removing a canonical source from history fails validation."""
        contract = quality._load_contract()
        incomplete_contract = dict(contract)
        incomplete_contract["canonical_body_sources"] = [
            item for item in contract["canonical_body_sources"]
            if item["path"] != "docs/prompts.json"
        ]
        errors = quality.audit_source_set_parity(incomplete_contract)
        self.assertTrue(errors)
        self.assertTrue(
            any("docs/prompts.json" in error and "missing from history protection" in error 
                for error in errors)
        )

    def test_base_registry_is_history_protected(self) -> None:
        """Defect D1: docs/prompts.json must be present in canonical_body_sources."""
        contract = quality._load_contract()
        protected_paths = {item["path"] for item in contract["canonical_body_sources"]}
        self.assertIn("docs/prompts.json", protected_paths)


if __name__ == "__main__":
    unittest.main()
