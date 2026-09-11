#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json"
FOCUSED_TEST = ROOT / "tests/test_gemini_youtube_playlist_ingestion_prompt.py"
FIXTURE = ROOT / "tests/fixtures/p123_source_document_quality/drive_7UyhyhxdFsQ_20260910.v1.json"
QUALITY_TEST = ROOT / "tests/test_p123_source_document_quality_regression.py"

MISSION_OLD = """MISSION
Turn source + mission + ledger/schema + donor evidence into grounded knowledge + runnable packet. Build real artifacts; never fake repo work."""
MISSION_NEW = """MISSION
Turn source + mission + ledger/schema + donor evidence into grounded knowledge and only the artifacts the user's mission actually calls for. Build real artifacts; never fake repo work, bury the requested knowledge behind implementation scaffolding, or let an early-source summary stand in for full-source review.

MISSION MODE / PRIMARY DELIVERABLE ROUTING
Resolve `MISSION_MODE` from the user's actual request before producing artifacts: `KNOWLEDGE_EXTRACT`, `INGESTION_BUILD`, or `BOTH`.
- `KNOWLEDGE_EXTRACT`: the primary deliverable is the source-specific knowledge report plus ledger writes/row-ready records. Do not emit the Python adapter, donor packet, repository handoff, or implementation appendix unless the user requested implementation or those artifacts are materially required.
- `INGESTION_BUILD`: the implementation packet is primary; still preserve bounded source understanding needed by the build.
- `BOTH`: present the knowledge report first, then implementation artifacts as a clearly secondary section/appendix.
Never default every source/use case to the same document shape merely because P123 can build an ingestion adapter."""

SOURCE_ANCHOR = "- Source placement is input binding, not repository access."
SOURCE_INSERT = """

FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT
- When source content is inspectable, traverse the available source from its first position through its last available position. Do not stop after the first few useful themes establish a plausible summary.
- Run a chronological forward pass, then a deliberate reverse/tail pass from the end toward the beginning to catch insights skipped as attention or novelty declines.
- Maintain `COVERAGE_LEDGER` rows as `span | evidence | disposition | finding_ids`. Every available span is dispositioned as `NEW_FINDING`, `SUPPORTS_EXISTING`, `NO_REUSABLE_INSIGHT`, or `UNAVAILABLE_UNVERIFIED`; no span silently disappears merely because it yields no new finding.
- When timing/position metadata exists, report `SOURCE_EXTENT`, `LAST_INSPECTED_POSITION`, `UNACCOUNTED_SPANS`, and `FULL_SOURCE_COVERAGE`. `COMPLETE` is allowed only when the available source extent, including the tail, is accounted for; otherwise use `PARTIAL` and name the unprocessed span/reason.
- If context/tool limits prevent one-pass review, chunk or iterate while preserving order/provenance, then reconcile duplicate findings. Never convert a truncated pass into a COMPLETE claim.

DOCUMENT IDENTITY / EXPORT CONTRACT
- Before any body content, derive a human-readable source-specific `DOCUMENT_TITLE` from the actual source title/topic plus the user's extraction mission. The first visible line/H1 of a generated report must be that title, not code, `Python`, a raw URL, the prompt name, or a generic template label.
- Derive a matching filesystem/Drive-safe `EXPORT_BASENAME`; do not use the raw source URL as the document/file name. If disambiguation is needed, append a short source ID/date rather than collapsing unrelated use cases to the same generic name.
- A reusable ledger/template may keep its canonical workbook name, but any per-source exported report/document must identify the source/use case distinctly.
- Do not export unresolved `xyz_` placeholders or irrelevant consumer/repository scaffolding into a knowledge-only document. Omit unavailable optional sections or mark genuinely required unknowns explicitly.
- Report the final `DOCUMENT_TITLE` and `EXPORT_BASENAME`, plus the observed Drive/file ID or URL when an actual write/export occurs."""

IMPLEMENTATION_OLD = """IMPLEMENTATION PACKET — PRODUCE ALL APPLICABLE FILES
Return complete contents for:"""
IMPLEMENTATION_NEW = """IMPLEMENTATION PACKET — ONLY WHEN MISSION MODE INCLUDES `INGESTION_BUILD`
When `MISSION_MODE` is `INGESTION_BUILD` or `BOTH`, return complete contents for:"""

FINAL_OLD = """FINAL RESPONSE
Return capability mode; source/donor authority ledger; complete standalone files; deterministic test results actually run; representative outputs; Windows commands; live proof performed or explicitly unperformed; repository claim ledger; risks/gaps; proof ceiling; and repo-capable handoff. The result is incomplete if it is only design, pseudocode, a repository plan, or a fake repository patch."""
FINAL_NEW = """FINAL RESPONSE
Always start with `DOCUMENT_TITLE`, source identity, `MISSION_MODE`, and the full-source coverage receipt. For `KNOWLEDGE_EXTRACT`, return the polished source-specific knowledge report and ledger mutation/row-ready records first and stop when that mission is complete; do not append unrelated implementation boilerplate. For `BOTH`, keep that knowledge report first, then the standalone implementation packet. For `INGESTION_BUILD`, return the applicable standalone files, deterministic test results actually run, representative outputs, Windows commands, live proof performed or explicitly unperformed, repository claim ledger, risks/gaps, proof ceiling, and repo-capable handoff. Report `EXPORT_BASENAME` and any observed export/write receipt. The result is incomplete if source coverage silently trails off, the visible/exported document identity is generic, or proof is fabricated."""

TEST_METHOD = r'''
    def test_full_source_coverage_document_identity_and_mission_routing(self) -> None:
        self.assert_markers(
            "MISSION MODE / PRIMARY DELIVERABLE ROUTING",
            "`KNOWLEDGE_EXTRACT`",
            "`INGESTION_BUILD`",
            "`BOTH`",
            "knowledge report first",
            "FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT",
            "chronological forward pass",
            "reverse/tail pass",
            "`COVERAGE_LEDGER`",
            "`UNACCOUNTED_SPANS`",
            "`FULL_SOURCE_COVERAGE`",
            "`COMPLETE` is allowed only",
            "DOCUMENT IDENTITY / EXPORT CONTRACT",
            "`DOCUMENT_TITLE`",
            "first visible line/H1",
            "`EXPORT_BASENAME`",
            "do not use the raw source URL",
            "Do not export unresolved `xyz_` placeholders",
            "per-source exported report/document",
            "source coverage silently trails off",
        )
        self.assertIn("full source", self.prompt["expectedOutput"].lower())
        self.assertIn("source-specific", self.prompt["expectedOutput"].lower())
        self.assertIn("tail", self.prompt["proofGate"].lower())
        self.assertIn("generic", self.prompt["proofGate"].lower())
        for keyword in (
            "full source coverage",
            "youtube tail coverage",
            "source specific document title",
            "document export naming",
            "knowledge report",
        ):
            self.assertIn(keyword, self.prompt["keywords"])

'''
TEST_ANCHOR = "    def test_yt_dlp_is_single_extraction_authority(self) -> None:\n"

SITE_MARKER_ANCHOR = '            "row-ready Source and Findings records",\n'
SITE_MARKERS = '''            "MISSION MODE / PRIMARY DELIVERABLE ROUTING",\n            "FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT",\n            "DOCUMENT IDENTITY / EXPORT CONTRACT",\n            "`DOCUMENT_TITLE`",\n            "`EXPORT_BASENAME`",\n'''

FIXTURE_PAYLOAD = {
    "schema_version": "p123-source-document-quality/v1",
    "case_id": "drive-7UyhyhxdFsQ-20260910",
    "owner": "P123",
    "eval_owner": "P67",
    "source": {
        "kind": "youtube_short",
        "identity": "7UyhyhxdFsQ",
        "title": "How WhatsApp Video Sharing Works?",
        "channel": "KodeKloud",
        "duration_seconds": 128,
    },
    "observed_output": {
        "exported_document_name": "https:__youtube.com_shorts_7UyhyhxdFsQ?is=TeA49Ke...",
        "first_visible_heading": "Python",
        "knowledge_section_first_page": 15,
        "last_timestamped_finding_seconds": 97,
        "explicit_end_coverage_receipt": False,
        "implementation_packet_precedes_knowledge": True,
        "generic_or_source_unsafe_document_identity": True,
    },
    "derived_regression_facts": {
        "unaccounted_tail_seconds_from_last_timestamped_finding": 31,
        "finding": "The observed artifact does not prove that the available tail from 01:37 through the 02:08 source extent was reviewed; absence of a coverage receipt is the regression, not an assertion that the tail contains a specific missing fact.",
    },
    "required_repairs": [
        "mission_mode_routing",
        "knowledge_first_when_knowledge_is_the_user_mission",
        "forward_plus_reverse_full_source_coverage",
        "explicit_tail_and_unaccounted_span_receipt",
        "source_specific_visible_document_title",
        "source_specific_export_basename",
        "no_raw_url_or_generic_template_export_name",
        "no_unresolved_xyz_placeholders_in_user_facing_knowledge_report",
    ],
    "proof_ceiling": "This fixture preserves observable structure from the supplied P123 result: source duration, visible document start, placement of the knowledge section, last explicit timestamped finding, and exported document name. It does not claim what unrepresented source time contains; it proves the prior result lacked explicit end-of-source coverage evidence and source-specific document presentation.",
}

QUALITY_TEST_CONTENT = r'''from __future__ import annotations

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
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"missing anchor for {label}")
    return text.replace(old, new, 1)


def main() -> int:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p123 = next(item for item in payload["prompts"] if item.get("id") == "P123")

    p123["sprintRole"] = (
        p123["sprintRole"].rstrip(".")
        + "; route knowledge-only versus ingestion-build missions explicitly, force full-source/tail coverage when source content is inspectable, and give every per-source report a source-specific visible/exported document identity."
    )
    p123["useWhen"] = (
        p123["useWhen"].rstrip(".")
        + " This owner also applies when prior Gemini/P123 output summarized the beginning well but trailed off later, buried knowledge under implementation output, or exported generic/URL-named documents without a source-specific title."
    )
    p123["inspectFirst"] = (
        p123["inspectFirst"].rstrip(".")
        + " Resolve the user's primary mission mode, available source extent/timestamps or transcript ordering, and the actual export/write surface so coverage and document identity can be proven rather than assumed."
    )
    p123["expectedOutput"] = (
        p123["expectedOutput"].rstrip(".")
        + " The primary artifact is mission-routed: knowledge extraction produces a polished source-specific report first, with a human-readable document title/export basename and a full source coverage/tail receipt; implementation artifacts are emitted only when requested or materially required."
    )
    p123["proofGate"] = (
        p123["proofGate"].rstrip(".")
        + " When source content is inspectable, coverage may be COMPLETE only after the available source extent including its tail is dispositioned and unaccounted spans are empty; otherwise it is PARTIAL with the exact gap. Per-source exports must use a source/use-case-specific visible title and basename rather than a raw URL or generic repeated template title, and knowledge-only missions must not be buried under implementation scaffolding."
    )
    p123["nextStep"] = (
        "Finish the user's primary mission at the correct proof layer: for knowledge extraction, reconcile the forward and reverse/tail passes, close the coverage ledger, write or emit the ledger findings, and verify the source-specific document/export identity; when ingestion build is also requested, then hand the completed packet to a repository-capable executor for integration and live acceptance."
    )

    content = p123["copyContent"]
    content = replace_once(content, MISSION_OLD, MISSION_NEW, "mission routing")
    if "FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT" not in content:
        if SOURCE_ANCHOR not in content:
            raise SystemExit("missing source-resolution insertion anchor")
        content = content.replace(SOURCE_ANCHOR, SOURCE_ANCHOR + SOURCE_INSERT, 1)
    content = replace_once(content, IMPLEMENTATION_OLD, IMPLEMENTATION_NEW, "conditional implementation packet")
    content = replace_once(content, FINAL_OLD, FINAL_NEW, "mission-routed final response")
    p123["copyContent"] = content

    for keyword in (
        "full source coverage",
        "youtube tail coverage",
        "source specific document title",
        "document export naming",
        "knowledge report",
    ):
        if keyword not in p123["keywords"]:
            p123["keywords"].append(keyword)

    if len(content) > 12000:
        raise SystemExit(f"P123 copyContent exceeds helper ceiling: {len(content)}")
    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    test_text = FOCUSED_TEST.read_text(encoding="utf-8")
    if "test_full_source_coverage_document_identity_and_mission_routing" not in test_text:
        if TEST_ANCHOR not in test_text:
            raise SystemExit("missing focused-test insertion anchor")
        test_text = test_text.replace(TEST_ANCHOR, TEST_METHOD + TEST_ANCHOR, 1)
    if '"MISSION MODE / PRIMARY DELIVERABLE ROUTING"' not in test_text.split("def test_generated_site_contains_gemini_ingestion_semantics", 1)[1]:
        if SITE_MARKER_ANCHOR not in test_text:
            raise SystemExit("missing generated-site marker anchor")
        test_text = test_text.replace(SITE_MARKER_ANCHOR, SITE_MARKER_ANCHOR + SITE_MARKERS, 1)
    FOCUSED_TEST.write_text(test_text, encoding="utf-8")

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(FIXTURE_PAYLOAD, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    QUALITY_TEST.write_text(QUALITY_TEST_CONTENT, encoding="utf-8")

    print(f"P123_FULL_SOURCE_DOCUMENT_QUALITY_APPLIED chars={len(content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
