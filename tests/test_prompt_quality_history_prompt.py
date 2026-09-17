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

    def test_current_canonical_body_sources_match_accepted_history(self) -> None:
        contract = quality._load_contract()
        migrations = quality._load_migrations(contract)
        self.assertEqual(quality.audit_source_history(contract, migrations), [])

    def test_effective_prompt_variants_preserve_canonical_identity_except_owned_regression(self) -> None:
        contract = quality._load_contract()
        self.assertEqual(quality.audit_effective_identity(contract), [])

    def test_p07_exception_is_explicitly_owned_by_concurrent_repair(self) -> None:
        contract = quality._load_contract()
        exceptions = contract["effective_identity"]["temporary_exceptions"]
        self.assertEqual(
            [(item["prompt_id"], item["owner_pr"]) for item in exceptions],
            [("P07", 533)],
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
                "affected_prompt_ids": ["P00"],
                "change_kind": "strengthening",
                "rationale": "test only",
                "focused_tests": ["tests/test_prompt_quality_history_prompt.py"],
            }
        ]
        _, errors = quality._accepted_source_heads(contract, bad)
        self.assertTrue(errors)
        self.assertIn("accepted head", errors[0])


if __name__ == "__main__":
    unittest.main()
