from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

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

    def test_output_io_failure_returns_2_without_traceback(self) -> None:
        report = {
            "schema_version": "prompt-kit-ontology-history-append-only-validation/v1",
            "status": "PASS",
            "baseline_ref": "baseline",
            "baseline_records": 1,
            "current_records": 1,
            "errors": [],
        }
        with TemporaryDirectory() as tmp_dir:
            output_directory = Path(tmp_dir)
            stderr = StringIO()
            with patch.object(append_only_validator, "validate", return_value=report):
                with redirect_stderr(stderr):
                    return_code = append_only_validator.main(
                        [
                            "--baseline-ref",
                            "baseline",
                            "--output",
                            str(output_directory),
                        ]
                    )

        self.assertEqual(return_code, 2)
        self.assertIn("Prompt Kit ontology append-only validation failed", stderr.getvalue())

    def test_failed_atomic_replace_preserves_existing_report_and_cleans_temp(self) -> None:
        report = {
            "schema_version": "prompt-kit-ontology-history-append-only-validation/v1",
            "status": "PASS",
            "baseline_ref": "baseline",
            "baseline_records": 1,
            "current_records": 1,
            "errors": [],
        }
        prior_report = '{"status":"PRIOR"}\n'
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            output_path.write_text(prior_report, encoding="utf-8")
            with patch.object(Path, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    append_only_validator.write_report(output_path, report)

            self.assertEqual(output_path.read_text(encoding="utf-8"), prior_report)
            self.assertEqual(list(Path(tmp_dir).glob(".report.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
