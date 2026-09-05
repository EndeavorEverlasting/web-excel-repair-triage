from __future__ import annotations

import unittest

from scripts import validate_prompt_kit_ontology_history_append_only as append_only_validator


class PromptKitOntologyHistoryAppendOnlyTests(unittest.TestCase):
    def _ledger(self, records: list[dict[str, object]]) -> dict[str, object]:
        return {
            "schema_version": "prompt-kit-ontology-history/v1",
            "append_only": True,
            "records": records,
        }

    def test_accepts_exact_prior_prefix_with_new_records_appended(self) -> None:
        prior = [{"record_id": "obs-1", "record_kind": "invocation"}]
        current = prior + [{"record_id": "obs-2", "record_kind": "run_result"}]
        self.assertEqual(
            append_only_validator.validate_append_only_history(
                self._ledger(prior),
                self._ledger(current),
            ),
            [],
        )

    def test_rejects_dropped_prior_record(self) -> None:
        prior = [
            {"record_id": "obs-1", "record_kind": "invocation"},
            {"record_id": "obs-2", "record_kind": "failure"},
        ]
        errors = append_only_validator.validate_append_only_history(
            self._ledger(prior),
            self._ledger(prior[:1]),
        )
        self.assertTrue(any("dropped one or more prior records" in item for item in errors))

    def test_rejects_mutated_prior_record(self) -> None:
        prior = [{"record_id": "obs-1", "record_kind": "failure", "source": "ci"}]
        current = [{"record_id": "obs-1", "record_kind": "failure", "source": "manual"}]
        errors = append_only_validator.validate_append_only_history(
            self._ledger(prior),
            self._ledger(current),
        )
        self.assertTrue(any("obs-1" in item and "changed or moved" in item for item in errors))

    def test_rejects_insertion_before_prior_history(self) -> None:
        prior = [{"record_id": "obs-1", "record_kind": "eval"}]
        current = [
            {"record_id": "obs-new", "record_kind": "invocation"},
            *prior,
        ]
        errors = append_only_validator.validate_append_only_history(
            self._ledger(prior),
            self._ledger(current),
        )
        self.assertTrue(any("changed or moved" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
