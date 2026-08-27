from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
BASE = ROOT / "docs" / "prompts.json"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
EXPECTED_NAME = "Gemini YouTube Playlist Ingestion Builder"


class GeminiYouTubePlaylistIngestionPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.prompt = next(item for item in payload["prompts"] if item["name"] == EXPECTED_NAME)
        cls.content = cls.prompt["copyContent"]

    def test_helper_allocated_identity_and_distinct_role(self) -> None:
        self.assertRegex(self.prompt["id"], r"^P\d+$")
        self.assertEqual(self.prompt["copySheet"], f"{self.prompt['id']}_COPY_SAFE")
        self.assertEqual(self.prompt["class"], "AI ENGINEERING / YOUTUBE INGESTION")
        self.assertIn("YouTube playlist", self.prompt["useWhen"])
        self.assertIn("Gemini", self.prompt["useWhen"])
        self.assertIn("standalone", self.prompt["expectedOutput"].lower())

    def test_gemini_no_repo_access_boundary_is_operational(self) -> None:
        for marker in (
            "GEMINI CAPABILITY BOUNDARY",
            "target repository is NOT accessible",
            "PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY",
            "SUPPLIED_CONTEXT",
            "PROPOSED",
            "UNKNOWN_REQUIRES_REPO_INSPECTION",
            "MUST NOT fabricate a repository patch",
        ):
            self.assertIn(marker, self.content)

    def test_yt_dlp_is_single_extraction_authority(self) -> None:
        for marker in (
            "yt-dlp owns YouTube extraction",
            "do not reimplement YouTube HTML parsing",
            "do not create two competing extraction authorities",
            "runtime `yt-dlp --version`",
        ):
            self.assertIn(marker, self.content)

    def test_windows_metadata_path_never_downloads_media(self) -> None:
        for marker in (
            "WINDOWS-FIRST EXTRACTION CONTRACT",
            "--skip-download",
            "--dump-single-json",
            "--flat-playlist",
            "--input-json",
            "without downloading media",
            "does not request media download",
        ):
            self.assertIn(marker, self.content)

    def test_normalization_preserves_order_repeats_and_json_authority(self) -> None:
        for marker in (
            "Repeated playlist entries are valid data",
            "preserve every ordered playlist occurrence separately",
            "normalized JSON is canonical",
            "CSV is a projection",
            "utf-8-sig",
            "beginning with `=`, `+`, `-`, or `@`",
            "canonical JSON must remain unchanged",
        ):
            self.assertIn(marker, self.content)

    def test_donor_license_and_standalone_packet_boundaries(self) -> None:
        for marker in (
            "TubeArchivist and NewPipeExtractor",
            "do not copy GPL implementation code",
            "source_ingest_youtube.py",
            "source_import_contract.json",
            "youtube_playlist_fixture.json",
            "test_youtube_source_ingestion.py",
            "donor_manifest.json",
            "Do not import from hypothetical consumer-repository modules",
        ):
            self.assertIn(marker, self.content)

    def test_fixture_tests_and_live_proof_ceiling_are_explicit(self) -> None:
        for marker in (
            "MINIMUM DETERMINISTIC TESTS",
            "repeated video ID preserves multiple ordered occurrences",
            "spreadsheet-safe while JSON remains",
            "fixture-mode CLI writes both JSON and CSV deterministically",
            "LIVE-PROOF CEILING",
            "do NOT prove current YouTube behavior",
        ):
            self.assertIn(marker, self.content)

    def test_repo_capable_handoff_is_complete(self) -> None:
        for marker in (
            "REPOSITORY-CAPABLE HANDOFF",
            "yt-dlp owns YouTube parsing, consumer owns normalization/schema/tests/exports",
            "find the existing source/import/domain owners",
            "Do not make the operator restate the donor research",
        ):
            self.assertIn(marker, self.content)

    def test_generated_site_contains_new_prompt_and_key_semantics(self) -> None:
        deployed = SITE.read_text(encoding="utf-8")
        for marker in (
            self.prompt["id"],
            EXPECTED_NAME,
            "GEMINI CAPABILITY BOUNDARY",
            "yt-dlp owns YouTube extraction",
            "Repeated playlist entries are valid data",
            "REPOSITORY-CAPABLE HANDOFF",
        ):
            self.assertIn(marker, deployed)

    def test_prompt_remains_distinct_from_generic_p56(self) -> None:
        base = json.loads(BASE.read_text(encoding="utf-8"))
        p56 = next(item for item in base if item["id"] == "P56")
        self.assertEqual(p56["name"], "Context-to-Artifact Generator")
        self.assertNotIn("yt-dlp owns YouTube extraction", p56["copyContent"])
        self.assertNotEqual(p56["useWhen"], self.prompt["useWhen"])
        self.assertNotIn("StudySyndicate", self.content)


if __name__ == "__main__":
    unittest.main()
