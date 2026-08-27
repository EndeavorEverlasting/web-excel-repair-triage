from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
BASE = ROOT / "docs" / "prompts.json"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
# Identity is allocated by prompt_registry_ops.py from the refreshed combined registry.
EXPECTED_ID = "P123"
EXPECTED_NAME = "Gemini YouTube Playlist Ingestion Builder"


class GeminiYouTubePlaylistIngestionPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.prompt = next(item for item in payload["prompts"] if item["id"] == EXPECTED_ID)
        cls.content = cls.prompt["copyContent"]

    def assert_markers(self, *markers: str) -> None:
        for marker in markers:
            self.assertIn(marker, self.content)

    def test_helper_allocated_identity_and_distinct_role(self) -> None:
        self.assertEqual(self.prompt["name"], EXPECTED_NAME)
        self.assertEqual(self.prompt["seq"], "123")
        self.assertEqual(self.prompt["copySheet"], "P123_COPY_SAFE")
        self.assertEqual(self.prompt["class"], "AI ENGINEERING / YOUTUBE INGESTION")
        self.assertIn("YouTube playlist", self.prompt["useWhen"])
        self.assertIn("Gemini", self.prompt["useWhen"])
        self.assertIn("standalone", self.prompt["expectedOutput"].lower())

    def test_gemini_no_repo_access_boundary_is_operational(self) -> None:
        self.assert_markers(
            "GEMINI CAPABILITY BOUNDARY",
            "target repository is NOT accessible",
            "PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY",
            "SUPPLIED_CONTEXT",
            "PROPOSED",
            "UNKNOWN_REQUIRES_REPO_INSPECTION",
            "MUST NOT fabricate a repository patch",
        )

    def test_yt_dlp_is_single_extraction_authority(self) -> None:
        self.assert_markers(
            "yt-dlp owns YouTube extraction",
            "do not reimplement YouTube HTML parsing",
            "do not create two competing extraction authorities",
            "runtime `yt-dlp --version`",
        )

    def test_windows_metadata_path_never_downloads_media(self) -> None:
        self.assert_markers(
            "WINDOWS-FIRST EXTRACTION CONTRACT",
            "--skip-download",
            "--dump-single-json",
            "--flat-playlist",
            "--input-json",
            "without downloading media",
            "does not request media download",
        )

    def test_entity_and_occurrence_models_are_separate(self) -> None:
        self.assert_markers(
            "IDENTITY / OCCURRENCE INVARIANTS",
            "unique source/video entity",
            "playlist occurrence is ordered membership",
            "references source identity",
            "must not duplicate the canonical source entity",
            "preserve every observed occurrence",
        )

    def test_real_source_list_regression_preserves_25_occurrences_and_23_identities(self) -> None:
        self.assert_markers(
            "SOURCE-LIST REGRESSION EXAMPLE",
            "25 URL occurrences",
            "23 unique video IDs",
            "_CuibYl_Fh0",
            "bBdq2hf5R0I",
            "share/tracking parameter such as `si=`",
            "must not create a new video identity",
        )

    def test_unavailable_entries_preserve_tombstones_and_completeness(self) -> None:
        self.assert_markers(
            "UNAVAILABLE / COMPLETENESS CONTRACT",
            "occurrence tombstone",
            "must not silently shrink",
            "COMPLETE",
            "PARTIAL",
            "EMPTY_CONFIRMED",
            "EMPTY_UNPROVEN",
            "FAILED",
            "--allow-empty",
        )

    def test_ordering_prefers_extractor_position_and_records_fallback(self) -> None:
        self.assert_markers(
            "extractor-supplied `playlist_index`",
            "encounter-order fallback",
            "position_source",
        )

    def test_json_csv_and_spreadsheet_safety_contract_is_strict(self) -> None:
        self.assert_markers(
            "normalized JSON is canonical",
            "CSV is a projection",
            "utf-8-sig",
            "UTF-8 BOM",
            "beginning with `=`, `+`, `-`, or `@`",
            "canonical JSON must remain unchanged",
        )

    def test_donor_evidence_and_dispositions_cannot_be_invented(self) -> None:
        self.assert_markers(
            "DONOR EVIDENCE / VERSION CONTRACT",
            "NOT_SUPPLIED",
            "UNKNOWN",
            "ADOPT / ADAPT / REFERENCE_ONLY / REJECT / DEFER",
            "must not silently change a supplied donor disposition",
            "normalization_schema_version",
            "adapter_version",
            "donor_manifest.json",
        )

    def test_backend_contract_is_canonical_not_ytdlp_raw_shape(self) -> None:
        self.assert_markers(
            "BACKEND-NEUTRAL NORMALIZATION CONTRACT",
            "Raw extractor responses are backend-local",
            "must not be the shared domain contract",
            "YouTube Data API adapter must not impersonate yt-dlp JSON",
        )

    def test_runnability_gate_requires_actual_or_explicitly_unrun_tests(self) -> None:
        self.assert_markers(
            "RUNNABILITY GATE",
            "UNRUN",
            "import `subprocess`",
            "actual non-ASCII Unicode fixture",
            "embedded quote",
            "output directory",
            "deterministic timestamp",
            "fixture-mode CLI",
            "writes both JSON and CSV",
        )

    def test_donor_license_and_standalone_packet_boundaries(self) -> None:
        self.assert_markers(
            "TubeArchivist and NewPipeExtractor",
            "do not copy GPL implementation code",
            "source_ingest_youtube.py",
            "source_import_contract.json",
            "youtube_playlist_fixture.json",
            "test_youtube_source_ingestion.py",
            "donor_manifest.json",
            "Do not import from hypothetical consumer-repository modules",
        )

    def test_fixture_tests_and_live_proof_ceiling_are_explicit(self) -> None:
        self.assert_markers(
            "MINIMUM DETERMINISTIC TESTS",
            "repeated video ID preserves multiple ordered occurrences",
            "spreadsheet-safe while JSON remains",
            "fixture-mode CLI writes both JSON and CSV deterministically",
            "LIVE-PROOF CEILING",
            "do NOT prove current YouTube behavior",
        )

    def test_repo_capable_handoff_is_complete(self) -> None:
        self.assert_markers(
            "REPOSITORY-CAPABLE HANDOFF",
            "PRE-MUTATION MISSION DECLARATION",
            "repository and branch/worktree",
            "lane and mission",
            "owned and forbidden scope",
            "expected artifacts",
            "validation order",
            "proof ceiling",
            "mutation authority",
            "yt-dlp owns YouTube parsing, consumer owns normalization/schema/tests/exports",
            "find the existing source/import/domain owners",
            "Do not make the operator restate the donor research",
        )

    def test_generated_site_contains_gemini_ingestion_semantics(self) -> None:
        deployed = SITE.read_text(encoding="utf-8")
        for marker in (
            EXPECTED_ID,
            EXPECTED_NAME,
            "IDENTITY / OCCURRENCE INVARIANTS",
            "25 URL occurrences",
            "UNAVAILABLE / COMPLETENESS CONTRACT",
            "DONOR EVIDENCE / VERSION CONTRACT",
            "BACKEND-NEUTRAL NORMALIZATION CONTRACT",
            "RUNNABILITY GATE",
            "PRE-MUTATION MISSION DECLARATION",
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
