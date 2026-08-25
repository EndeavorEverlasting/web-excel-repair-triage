from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts import fetch_google_sheet_tab as fetcher
from scripts import prompt_kit_expert_insight_intake as intake

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "prompt-kit-expert-insights" / "sample.csv"


class PromptKitExpertInsightIntakeTests(unittest.TestCase):
    def test_fixture_emits_one_review_candidate_without_mutation_authority(self):
        report = intake.build_report(intake.load_rows(FIXTURE), "synthetic-fixture")
        self.assertEqual(report["schema_version"], intake.REPORT_SCHEMA)
        self.assertEqual(report["input_rows"], 2)
        self.assertEqual(report["candidate_count"], 1)
        self.assertFalse(report["mutation_authority"])
        self.assertEqual(report["candidates"][0]["insight_id"], "INS-SYNTH-001")
        rendered = json.dumps(report)
        self.assertNotIn("PRIVATE_SENTINEL_SHOULD_NOT_APPEAR_IN_REPORT", rendered)
        self.assertNotIn("PRIVATE_SENTINEL_NOTE", rendered)

    def test_duplicate_insight_id_fails_closed(self):
        rows = intake.load_rows(FIXTURE)
        with self.assertRaises(SystemExit):
            intake.build_report([rows[0], rows[0]], "synthetic-fixture")

    def test_ready_for_repo_requires_owner_action_and_proof(self):
        row = intake.load_rows(FIXTURE)[0]
        cases = [
            {**row, "Candidate Owner": "UNKNOWN"},
            {**row, "Candidate Action": "ASSESS"},
            {**row, "Acceptance / Proof Idea": ""},
            {**row, "Validation Lenses": ""},
            {**row, "CI Eligible": "NO"},
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate), self.assertRaises(SystemExit):
                intake.normalize_row(candidate)

    def test_schema_is_exact_and_rejects_extra_columns(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.csv"
            rows = list(csv.reader(FIXTURE.read_text(encoding="utf-8").splitlines()))
            rows[0].append("Untracked Extra")
            rows[1].append("nope")
            rows[2].append("nope")
            with path.open("w", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerows(rows)
            with self.assertRaises(SystemExit):
                intake.load_rows(path)

    def test_contract_surfaces_keep_drive_read_only_and_registry_mutation_out(self):
        workflow = (
            ROOT / ".github/workflows/prompt-kit-expert-insight-intake.yml"
        ).read_text(encoding="utf-8")
        doc = (ROOT / "docs/PROMPT_KIT_EXPERT_INSIGHT_INTAKE.md").read_text(
            encoding="utf-8"
        )
        fetcher_text = (ROOT / "scripts/fetch_google_sheet_tab.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("PROMPT_KIT_EXPERT_INSIGHTS_GOOGLE_CREDENTIALS", workflow)
        self.assertIn("spreadsheets.readonly", fetcher_text)
        self.assertIn("mutation_authority: false", doc)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)

    def test_google_values_to_csv_preserves_literal_video_timestamps(self):
        text = fetcher.rows_to_csv(
            [
                ["Insight ID", "Timestamp"],
                ["INS-X", "28:20"],
                ["INS-Y", "01:07:13"],
            ]
        )
        self.assertIn("28:20", text)
        self.assertIn("01:07:13", text)
        self.assertEqual(list(csv.reader(text.splitlines()))[1][1], "28:20")


if __name__ == "__main__":
    unittest.main()
