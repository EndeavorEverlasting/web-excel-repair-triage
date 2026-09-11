#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json"
FOCUSED_TEST = ROOT / "tests/test_gemini_youtube_playlist_ingestion_prompt.py"
FIXTURE = ROOT / "tests/fixtures/p123_source_document_quality/drive_7UyhyhxdFsQ_20260910.v1.json"
QUALITY_TEST = ROOT / "tests/test_p123_source_document_quality_regression.py"

P123_COPY = r'''GEMINI YOUTUBE INGESTION. USE SOURCE; EXTRACT KNOWLEDGE, BUILD ONLY REQUESTED ARTIFACTS, AND DO NOT PRETEND REPOSITORY ACCESS.

Consumer/product: xyz_consumer_product
Target repository identity, if one exists: xyz_repo_name_for_handoff_only
YouTube source: use the immediately preceding accessible YouTube video/link/attachment when unambiguous; otherwise xyz_video_playlist_or_fixture
Verified donor dossier / pinned source research: xyz_donor_dossier
Consumer data-model requirements: xyz_consumer_contract
Required JSON fields / CSV columns: xyz_output_fields

MISSION
Turn source + mission + ledger/schema + donor evidence into grounded knowledge and only the artifacts the user's mission calls for. Never let early-source fluency substitute for full-source review.

MISSION MODE / PRIMARY DELIVERABLE ROUTING
Resolve `MISSION_MODE`: `KNOWLEDGE_EXTRACT`, `INGESTION_BUILD`, or `BOTH`.
- `KNOWLEDGE_EXTRACT`: knowledge report + ledger write/row-ready records are primary. Do not emit adapter/donor/repo-handoff boilerplate unless requested or materially required.
- `INGESTION_BUILD`: implementation packet is primary; retain source understanding needed by the build.
- `BOTH`: knowledge report first; implementation packet is secondary.
Never default every use case to the same document shape.

SOURCE INPUT RESOLUTION
- A YouTube video, Short, playlist URL, directly attached media item, saved yt-dlp JSON, or supplied transcript/captions is valid input; a single video is valid input.
- If exactly one usable source appears immediately above this prompt or in the same turn, bind it as `SOURCE_INPUT` automatically. Do not ask the operator to paste, repeat, or restate it into a placeholder.
- Record `SOURCE_INPUT_KIND` and `SOURCE_INPUT_IDENTITY`. If the video itself is directly inspectable, perform grounded semantic analysis from accessible audiovisual/transcript evidence. If only a URL is present and the environment cannot inspect its content, do not invent what the video says; state the proof ceiling.
- Source placement is input binding, not repository access.

FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT
- Inspect the available source from first through last available position. Run a chronological forward pass, then a deliberate reverse/tail pass.
- Maintain `COVERAGE_LEDGER`: `span | evidence | disposition | finding_ids`. Disposition every span as NEW_FINDING, SUPPORTS_EXISTING, NO_REUSABLE_INSIGHT, or UNAVAILABLE_UNVERIFIED.
- With timing/position metadata report `SOURCE_EXTENT`, `LAST_INSPECTED_POSITION`, `UNACCOUNTED_SPANS`, `FULL_SOURCE_COVERAGE`. `COMPLETE` is allowed only when the available extent including the tail is accounted for; otherwise report `PARTIAL` and the exact gap.
- If context/tool limits require chunking, preserve order/provenance, reconcile duplicates, and never promote a truncated pass to COMPLETE.

DOCUMENT IDENTITY / EXPORT CONTRACT
- Derive a source/use-case-specific `DOCUMENT_TITLE`; the first visible line/H1 must be that title, not code, `Python`, a raw URL, prompt name, or generic template label.
- Derive a matching safe `EXPORT_BASENAME`; do not use the raw source URL as the document/file name. Add a short source ID/date only when disambiguation is needed.
- Reusable ledgers may retain canonical names, but each per-source exported report/document must identify its source/use case distinctly.
- Do not export unresolved `xyz_` placeholders or irrelevant repository scaffolding into a knowledge-only document.
- Report `DOCUMENT_TITLE`, `EXPORT_BASENAME`, and observed file/Drive ID or URL when an actual export/write occurs.

DOMAIN-AGNOSTIC KNOWLEDGE / LEDGER CONTRACT
- Classify from source + mission, never recent conversation themes, favorite domains, or examples. Examples prove range, not defaults: Cybersecurity; Agentic Software Development; Culinary & Food.
- With a supplied ledger/schema, `Sources`, `Findings`, and `Domains` are canonical; reuse its canonical domain vocabulary. favored views are projections, not separate data authorities.
- Produce one Finding record per distinct reusable insight with provenance/evidence/confidence/validation. Use Unknown / Needs Verification when needed. Set Prompt Kit Candidate / Software Candidate only when applicable.
- Resolve spreadsheet write capability + authority. If writable and write authority exists, perform the canonical Source/Findings write and report exact written ranges/IDs as the mutation receipt. Otherwise emit row-ready Source and Findings records. Never claim the spreadsheet was updated without an observed write receipt.

GEMINI CAPABILITY BOUNDARY
Assume the target repository is NOT accessible unless actually exposed. Repository names/excerpts are not access.
- Use only supplied/accessed source material and verified donor evidence; MUST NOT fabricate a repository patch, imports, paths, schemas, tests, CI, branches, SHAs, merges, or runtime proof.
- Suggested destinations are `PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY`.
- Classify repository claims as SUPPLIED_CONTEXT, PROPOSED, or UNKNOWN_REQUIRES_REPO_INSPECTION.

SOURCE AUTHORITY / DONOR CONTRACT
- yt-dlp owns machine-readable YouTube metadata extraction; consume its JSON, do not reimplement YouTube HTML parsing, and do not create two competing extraction authorities. This does not forbid semantic analysis of video/transcript content directly available in Gemini context.
- Consumer code owns normalization/schema/tests/exports.
- TubeArchivist and NewPipeExtractor are reference sources only where license boundaries require it; do not copy GPL implementation code.
- Record supplied donor pins and runtime `yt-dlp --version`; never invent observations.

WINDOWS-FIRST EXTRACTION CONTRACT
Live metadata uses external yt-dlp with `--skip-download`, `--dump-single-json`, and `--no-warnings` when suitable, without downloading media and does not request media download. `--flat-playlist` is explicit lower-metadata census mode. Support `--input-json` for deterministic fixtures.

NORMALIZATION + IDENTITY / OCCURRENCE INVARIANTS
normalized JSON is canonical; CSV is a projection.
- A unique source/video entity represents stable identity; a playlist occurrence is ordered membership, references source identity, and must not duplicate the canonical source entity. preserve every observed occurrence.
- Tracking/share parameters such as `si=` do not create identity. Prefer extractor-supplied `playlist_index`; use encounter-order fallback only when needed and record `position_source`.
- SOURCE-LIST REGRESSION EXAMPLE: synthetic corpus has 25 URL occurrences and 23 unique video IDs; `_CuibYl_Fh0` and `bBdq2hf5R0I` repeat. A share/tracking parameter such as `si=` must not create a new video identity.
- UNAVAILABLE / COMPLETENESS CONTRACT: null/private/deleted slots retain occurrence tombstone and must not silently shrink. States: COMPLETE, PARTIAL, EMPTY_CONFIRMED, EMPTY_UNPROVEN, FAILED. Empty usable results require extractor evidence or explicit `--allow-empty`.

JSON + CSV CONTRACT
Preserve Unicode/commas/quotes/newlines/missing values. Use `utf-8-sig` and verify UTF-8 BOM for spreadsheet-facing CSV unless overridden. Cells beginning with `=`, `+`, `-`, or `@` must be spreadsheet-safe while canonical JSON must remain unchanged.

DONOR EVIDENCE / VERSION CONTRACT
Missing pins/releases/licenses/observations are NOT_SUPPLIED or UNKNOWN. Preserve ADOPT / ADAPT / REFERENCE_ONLY / REJECT / DEFER; must not silently change a supplied donor disposition. Separate `normalization_schema_version` and `adapter_version`; emit `donor_manifest.json`.

BACKEND-NEUTRAL NORMALIZATION CONTRACT
Raw extractor responses are backend-local and must not be the shared domain contract. A YouTube Data API adapter must not impersonate yt-dlp JSON. All backends adapt to the canonical schema.

IMPLEMENTATION PACKET — ONLY WHEN MISSION MODE INCLUDES `INGESTION_BUILD`
For `INGESTION_BUILD` or `BOTH`, produce standalone applicable files: `source_ingest_youtube.py`, `source_import_contract.json`, `youtube_playlist_fixture.json`, `test_youtube_source_ingestion.py`, `donor_manifest.json`, representative normalized JSON/CSV, compact Windows run sheet. Do not import from hypothetical consumer-repository modules.

OUTPUT PATH SAFETY CONTRACT
Generated outputs live under `Outputs/` by default. Resolve paths and reject equal resolved input/output paths; source fixture remains byte-identical after rejection. Any authorized non-Outputs overwrite gets a timestamped backup under `Outputs/backups/`.

RUNNABILITY GATE
Run deterministic tests when execution exists; else mark UNRUN. Tests must import subprocess when used, create/validate output directory, include actual non-ASCII Unicode fixture and embedded quote, exercise formula prefixes, verify BOM, support deterministic timestamp, and fixture-mode CLI that writes both JSON and CSV plus donor manifest.

MINIMUM DETERMINISTIC TESTS
Test full no-download command; explicit flat mode; normal metadata; repeated video ID preserves multiple ordered occurrences; CSV derives from JSON; Unicode/comma/newline round trip; spreadsheet-safe while JSON remains semantically unchanged; malformed donor case; collision rejection; fixture-mode CLI writes both JSON and CSV deterministically.

LIVE-PROOF CEILING
Fixture tests do NOT prove current YouTube behavior, live metadata/auth/private access, repository compatibility, or integration. Directly inspectable media supports only bounded semantic observations. If live proof runs, record runtime version/source identity/count/outputs/failures without credentials.

REPOSITORY-CAPABLE HANDOFF
Only when repository integration is part of `MISSION_MODE`, end with a copy-paste handoff.
PRE-MUTATION MISSION DECLARATION: declare repository and branch/worktree, lane and mission, owned and forbidden scope, expected artifacts, validation order, proof ceiling, mutation authority. Refresh remote truth; read repository governance and current Git/PR state; find the existing source/import/domain owners; enforce one writer per mutation surface. Run focused/repository gates and `git diff --check`; use normal commit and push when authorized. Report changed files, executed checks and results, commit SHA, push/PR state, blockers, Git status, proof ceiling, and the exact next command. Preserve authority: yt-dlp owns YouTube parsing, consumer owns normalization/schema/tests/exports. Do not make the operator restate the donor research.

FINAL RESPONSE
Start with `DOCUMENT_TITLE`, source identity, `MISSION_MODE`, and full-source coverage receipt. For `KNOWLEDGE_EXTRACT`, return the polished source-specific knowledge report and ledger mutation/row-ready records first and stop when that mission is complete. For `BOTH`, knowledge first, implementation second. For `INGESTION_BUILD`, return applicable packet/proof/handoff. Report `EXPORT_BASENAME` and observed export receipt. The result is incomplete if source coverage silently trails off, document identity is generic, or proof is fabricated.'''

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


def main() -> int:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p123 = next(item for item in payload["prompts"] if item.get("id") == "P123")

    p123["sprintRole"] = "Give Gemini a domain-agnostic YouTube source brief that routes knowledge extraction versus ingestion-build missions, binds the immediately preceding source, forces full-source/tail coverage for inspectable content, writes reusable findings when authorized, and produces source-specific documents or standalone ingestion artifacts without pretending repository access"
    p123["useWhen"] = "You have a YouTube video, Short, playlist, directly attached accessible media, saved yt-dlp JSON, or transcript and want Gemini to extract reusable knowledge without domain bias, build ingestion artifacts, or both; especially when prior output was front-loaded, trailed off later, buried knowledge under implementation scaffolding, or exported generic/URL-named documents."
    p123["inspectFirst"] = "Resolve the immediately preceding unambiguous source, the user's mission mode, available source extent/timestamps or transcript ordering, supplied ledger/schema and canonical domain vocabulary, export/write surface and authority, then verified donor dossier and actual available tools. Never infer inaccessible repository state."
    p123["expectedOutput"] = "A mission-routed result: for knowledge extraction, a polished source-specific report with one Finding record per distinct reusable insight, full source coverage/tail receipt, human-readable document title/export basename, and canonical ledger write with exact mutation receipt when writable/authorized or row-ready records otherwise; for ingestion build, the existing standalone yt-dlp adapter/contracts/fixtures/tests/JSON/CSV packet and repository-capable handoff; for both, knowledge first and implementation second."
    p123["nextStep"] = "Finish the primary mission at the correct proof layer: close the forward plus reverse/tail coverage ledger, write or emit reusable findings, verify source-specific document/export identity, and only when ingestion build is in scope hand the standalone packet to a repository-capable executor for integration and live acceptance."
    p123["proofGate"] = "The immediately preceding unambiguous source is bound without restatement; semantic claims are source-grounded; domain classification follows source+mission rather than favorite domains; supplied Sources/Findings/Domains ownership is preserved; writable authorized ledger mutations have exact written ranges/IDs; inspectable content is COMPLETE only when the available extent including its tail is dispositioned with no unaccounted span, otherwise PARTIAL names the gap; per-source exports have a source/use-case-specific visible title and basename rather than a raw URL or generic repeated title; knowledge-only missions are not buried under implementation scaffolding; yt-dlp remains the metadata extraction authority; existing normalization, spreadsheet-safety, donor-license, proof-ceiling, and repository-access boundaries remain enforced."
    p123["copyContent"] = P123_COPY

    for keyword in (
        "full source coverage",
        "youtube tail coverage",
        "source specific document title",
        "document export naming",
        "knowledge report",
    ):
        if keyword not in p123["keywords"]:
            p123["keywords"].append(keyword)

    if len(P123_COPY) > 12000:
        raise SystemExit(f"P123 copyContent exceeds helper ceiling: {len(P123_COPY)}")
    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    test_text = FOCUSED_TEST.read_text(encoding="utf-8")
    if "test_full_source_coverage_document_identity_and_mission_routing" not in test_text:
        if TEST_ANCHOR not in test_text:
            raise SystemExit("missing focused-test insertion anchor")
        test_text = test_text.replace(TEST_ANCHOR, TEST_METHOD + TEST_ANCHOR, 1)
    generated_section = test_text.split("def test_generated_site_contains_gemini_ingestion_semantics", 1)[1]
    if '"MISSION MODE / PRIMARY DELIVERABLE ROUTING"' not in generated_section:
        if SITE_MARKER_ANCHOR not in test_text:
            raise SystemExit("missing generated-site marker anchor")
        test_text = test_text.replace(SITE_MARKER_ANCHOR, SITE_MARKER_ANCHOR + SITE_MARKERS, 1)
    FOCUSED_TEST.write_text(test_text, encoding="utf-8")

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(FIXTURE_PAYLOAD, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    QUALITY_TEST.write_text(QUALITY_TEST_CONTENT, encoding="utf-8")

    print(f"P123_FULL_SOURCE_DOCUMENT_QUALITY_APPLIED chars={len(P123_COPY)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
