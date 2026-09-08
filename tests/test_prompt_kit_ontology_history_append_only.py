from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import stat
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

    def _report(self) -> dict[str, object]:
        return {
            "schema_version": "prompt-kit-ontology-history-append-only-validation/v1",
            "status": "PASS",
            "baseline_ref": "baseline",
            "baseline_records": 1,
            "current_records": 1,
            "errors": [],
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
        with TemporaryDirectory() as tmp_dir:
            output_directory = Path(tmp_dir)
            stderr = StringIO()
            with patch.object(append_only_validator, "validate", return_value=self._report()):
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
        prior_report = '{"status":"PRIOR"}\n'
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            output_path.write_text(prior_report, encoding="utf-8")
            with patch.object(Path, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    append_only_validator.write_report(output_path, self._report())

            self.assertEqual(output_path.read_text(encoding="utf-8"), prior_report)
            self.assertEqual(list(Path(tmp_dir).glob(".report.json.*")), [])

    @unittest.skipIf(os.name == "nt", "POSIX permission semantics")
    def test_atomic_replace_preserves_existing_report_permissions(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            output_path.write_text('{"status":"PRIOR"}\n', encoding="utf-8")
            output_path.chmod(0o644)

            append_only_validator.write_report(output_path, self._report())

            self.assertEqual(stat.S_IMODE(output_path.stat().st_mode), 0o644)

    @unittest.skipIf(os.name == "nt", "POSIX permission semantics")
    def test_new_report_uses_default_creation_permissions(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            reference_path = Path(tmp_dir) / "reference.json"
            reference_path.write_text("reference\n", encoding="utf-8")

            append_only_validator.write_report(output_path, self._report())

            self.assertEqual(
                stat.S_IMODE(output_path.stat().st_mode),
                stat.S_IMODE(reference_path.stat().st_mode),
            )

    @unittest.skipIf(os.name == "nt", "symlink creation may require elevated privileges")
    def test_atomic_replace_follows_existing_output_symlink(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target_dir = root / "target"
            target_dir.mkdir()
            target_path = target_dir / "report.json"
            target_path.write_text('{"status":"PRIOR"}\n', encoding="utf-8")
            target_path.chmod(0o640)
            output_path = root / "report-link.json"
            output_path.symlink_to(Path("target") / "report.json")

            append_only_validator.write_report(output_path, self._report())

            self.assertTrue(output_path.is_symlink())
            self.assertEqual(output_path.read_text(encoding="utf-8"), target_path.read_text(encoding="utf-8"))
            self.assertEqual(stat.S_IMODE(target_path.stat().st_mode), 0o640)
            self.assertEqual(json.loads(target_path.read_text(encoding="utf-8"))["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
