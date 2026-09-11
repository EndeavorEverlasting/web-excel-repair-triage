from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json"
SITE = ROOT / "web/prompt-kit/index.html"
FIXTURE = ROOT / "tests/fixtures/p123_source_document_quality/drive_7UyhyhxdFsQ_20260910.v1.json"


class P123SourceDocumentQualityRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.prompt = next(item for item in payload["prompts"] if item["id"] == "P123")
        cls.content = cls.prompt["copyContent"]
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_preserves_observed_quality_regression_without_inventing_tail_content(self) -> None:
        source = self.fixture["source"]
        observed = self.fixture["observed_output"]
        derived = self.fixture["derived_regression_facts"]
        self.assertEqual(source["identity"], "7UyhyhxdFsQ")
        self.assertEqual(source["duration_seconds"], 128)
        self.assertEqual(observed["first_visible_heading"], "Python")
        self.assertEqual(observed["knowledge_section_first_page"], 15)
        self.assertEqual(observed["last_timestamped_finding_seconds"], 97)
        self.assertFalse(observed["explicit_end_coverage_receipt"])
        self.assertTrue(observed["implementation_packet_precedes_knowledge"])
        self.assertEqual(
            source["duration_seconds"] - observed["last_timestamped_finding_seconds"],
            derived["unaccounted_tail_seconds_from_last_timestamped_finding"],
        )
        self.assertIn("does not prove", derived["finding"])
        self.assertIn("does not claim", self.fixture["proof_ceiling"])

    def test_p123_strengthens_existing_owner_instead_of_creating_a_new_identity(self) -> None:
        self.assertEqual(self.prompt["id"], "P123")
        self.assertEqual(self.prompt["name"], "Gemini YouTube Video / Playlist Ingestion Builder")
        self.assertIn("full source", self.prompt["expectedOutput"].lower())
        self.assertIn("source-specific", self.prompt["expectedOutput"].lower())

    def test_prompt_requires_mission_routing_full_coverage_tail_sweep_and_document_identity(self) -> None:
        markers = (
            "MISSION MODE / PRIMARY DELIVERABLE ROUTING",
            "`KNOWLEDGE_EXTRACT`",
            "knowledge report first",
            "FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT",
            "chronological forward pass",
            "reverse/tail pass",
            "`COVERAGE_LEDGER`",
            "`LAST_INSPECTED_POSITION`",
            "`UNACCOUNTED_SPANS`",
            "`FULL_SOURCE_COVERAGE`",
            "DOCUMENT IDENTITY / EXPORT CONTRACT",
            "`DOCUMENT_TITLE`",
            "first visible line/H1",
            "`EXPORT_BASENAME`",
            "do not use the raw source URL",
            "Do not export unresolved `xyz_` placeholders",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.content)

    def test_generated_site_contains_the_new_quality_contract(self) -> None:
        deployed = SITE.read_text(encoding="utf-8")
        for marker in (
            "P123",
            "MISSION MODE / PRIMARY DELIVERABLE ROUTING",
            "FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT",
            "DOCUMENT IDENTITY / EXPORT CONTRACT",
            "DOCUMENT_TITLE",
            "EXPORT_BASENAME",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
