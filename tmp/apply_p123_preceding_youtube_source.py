#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
TEST = ROOT / "tests" / "test_gemini_youtube_playlist_ingestion_prompt.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
prompt = next(item for item in payload["prompts"] if item["id"] == "P123")

prompt["name"] = "Gemini YouTube Video / Playlist Ingestion Builder"
prompt["sprintRole"] = (
    "Give Gemini a self-contained YouTube video or playlist ingestion brief that binds an immediately preceding accessible source, "
    "uses direct media only for grounded semantic understanding, and turns verified donor evidence into standalone implementation artifacts "
    "without pretending Gemini can inspect or modify the consumer repository"
)
prompt["useWhen"] = (
    "You have a YouTube video, Short, playlist, directly attached accessible media, saved yt-dlp JSON, or supplied transcript plus vetted implementation research, "
    "and you want Gemini to understand the supplied source when possible and produce the actual YouTube-metadata ingestion adapter, contracts, fixtures, tests, JSON/CSV examples, "
    "and repository-capable handoff while the target repository itself is not accessible to Gemini."
)
prompt["inspectFirst"] = (
    "First resolve the YouTube source from the immediately preceding current-turn context when one unambiguous video/link/attachment exists; otherwise use the explicitly supplied video, Short, playlist URL, saved yt-dlp JSON, or transcript. "
    "Then inspect verified donor dossier and pinned donor identities, consumer requirements/data model, required metadata fields and export rules, accepted/rejected architecture decisions, and Gemini's actual available files/tools. "
    "Do not infer repository paths, modules, schemas, tests, CI, branches, or runtime state that were not supplied."
)
prompt["expectedOutput"] = (
    "When directly inspectable video or transcript content is supplied, a concise source-grounded context/insight note tied to the requested mission; plus a complete standalone implementation packet: "
    "Python yt-dlp adapter, normalized JSON contract/schema, derived CSV projection contract, deterministic synthetic fixture and tests, Windows-first run commands, representative JSON and CSV output, donor/version manifest, explicit proof ceiling, "
    "and a self-contained handoff for a repository-capable agent to integrate and validate against the real consumer repository."
)
prompt["nextStep"] = (
    "Give the completed packet to a repository-capable executor, which must refresh the target repository, discover the real canonical owners and contracts, adapt rather than duplicate them, "
    "run focused and repository-owned validation plus an appropriate live single-video or playlist acceptance path, and integrate the exact validated change through the repository's actual policy."
)
prompt["proofGate"] = (
    "The immediately preceding unambiguous YouTube source is consumed without needless restatement; semantic claims about directly inspectable media are grounded in accessible video/transcript evidence or explicitly marked unproven; "
    "the standalone packet runs against a deterministic saved yt-dlp fixture; yt-dlp remains the sole machine-readable YouTube metadata extraction authority; playlist order and repeated occurrences survive normalization and CSV projection; "
    "single-video input remains valid without manufacturing playlist-only requirements; CSV spreadsheet hazards are neutralized without mutating canonical JSON; donor-license boundaries are explicit; Windows commands do not download media; "
    "and no inaccessible repository fact is presented as inspected, tested, committed, merged, or runtime-proven."
)

content = prompt["copyContent"]
replacements = {
    "GEMINI YOUTUBE PLAYLIST INGESTION BUILD. PRODUCE THE ACTUAL STANDALONE IMPLEMENTATION PACKET; DO NOT RETURN ONLY AN ARCHITECTURE ESSAY, AND DO NOT PRETEND YOU CAN ACCESS THE TARGET REPOSITORY.":
        "GEMINI YOUTUBE VIDEO / PLAYLIST INGESTION BUILD. USE THE SUPPLIED SOURCE DIRECTLY; PRODUCE THE ACTUAL STANDALONE IMPLEMENTATION PACKET, AND DO NOT PRETEND YOU CAN ACCESS THE TARGET REPOSITORY.",
    "YouTube playlist URL or saved yt-dlp playlist JSON: xyz_playlist_or_fixture":
        "YouTube source: use the immediately preceding accessible YouTube video/link/attachment when unambiguous; otherwise xyz_video_playlist_or_fixture",
    "Turn supplied playlist requirements and verified donor research into a complete runnable standalone ingestion packet for later repository integration. Implementation synthesis is required; fake repository work is forbidden.":
        "Turn the supplied YouTube source, requirements, and verified donor research into grounded source understanding when available plus a complete runnable standalone ingestion packet for later repository integration. Implementation synthesis is required; fake repository work is forbidden.",
    "- yt-dlp owns YouTube extraction; consume its JSON and do not reimplement YouTube HTML parsing, InnerTube continuation/signature/player behavior, or playlist scraping.":
        "- yt-dlp owns machine-readable YouTube metadata extraction for the adapter; consume its JSON and do not reimplement YouTube HTML parsing, InnerTube continuation/signature/player behavior, or playlist scraping. This does not forbid semantic analysis of video/transcript content directly available in Gemini context.",
    "Canonical normalized JSON owns playlist identity/provenance plus video/source records and ordered occurrences. Preserve supplied metadata and repeated occurrences; tracking parameters do not create new source identity.":
        "Canonical normalized JSON owns YouTube source identity/provenance plus video/source records and, for playlists, ordered occurrences. A single video is valid input with one source identity and no invented playlist-only requirement. Preserve supplied metadata and repeated occurrences; tracking parameters do not create new source identity.",
    "If real yt-dlp execution is unavailable, say so: fixture tests do NOT prove current YouTube behavior, authentication/private-playlist access, real playlist metadata, target-repository compatibility, or integration.":
        "If real yt-dlp execution is unavailable, say so: fixture tests do NOT prove current YouTube metadata behavior, authentication/private-playlist access, real video/playlist metadata, target-repository compatibility, or integration. Directly inspectable media may still support bounded semantic observations, but those observations do not prove metadata extraction."
}
for old, new in replacements.items():
    if old not in content:
        raise SystemExit(f"missing P123 anchor: {old[:80]!r}")
    content = content.replace(old, new, 1)

source_section = """
SOURCE INPUT RESOLUTION
- A YouTube video, Short, playlist URL, directly attached media item, saved yt-dlp JSON, or supplied transcript/captions can be the source input.
- If exactly one usable YouTube source appears immediately above this prompt or elsewhere in the same user turn, bind it as `SOURCE_INPUT` automatically. Do not ask the operator to paste, repeat, or restate it into a placeholder.
- If several candidates exist, use the nearest unambiguous source that matches the request and state the selection. Ask only when unresolved ambiguity would materially change the work.
- Record `SOURCE_INPUT_KIND` and `SOURCE_INPUT_IDENTITY` before synthesis.
- If the video itself is directly inspectable, use accessible audiovisual/transcript content for grounded semantic analysis and timestamps when available. If only a URL is present and the environment cannot inspect its content, do not invent what the video says; use supplied transcript/metadata when available and state the exact proof ceiling.
- Source placement is input binding, not repository access.
""".strip()
anchor = "\n\nGEMINI CAPABILITY BOUNDARY\n"
if "SOURCE INPUT RESOLUTION" not in content:
    if anchor not in content:
        raise SystemExit("missing Gemini capability boundary anchor")
    content = content.replace(anchor, "\n\n" + source_section + anchor, 1)

prompt["copyContent"] = content
for keyword in (
    "youtube video ingestion",
    "single youtube video",
    "youtube short",
    "youtube video attachment",
    "video above prompt",
    "preceding youtube video",
):
    if keyword not in prompt["keywords"]:
        prompt["keywords"].append(keyword)

if len(prompt["copyContent"]) > 12000:
    raise SystemExit(f"P123 copyContent exceeded helper ceiling: {len(prompt['copyContent'])}")

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

text = TEST.read_text(encoding="utf-8")
text = text.replace(
    'EXPECTED_NAME = "Gemini YouTube Playlist Ingestion Builder"',
    'EXPECTED_NAME = "Gemini YouTube Video / Playlist Ingestion Builder"',
    1,
)
text = text.replace(
    '        self.assertIn("YouTube playlist", self.prompt["useWhen"])\n        self.assertIn("Gemini", self.prompt["useWhen"])',
    '        self.assertIn("YouTube video", self.prompt["useWhen"])\n        self.assertIn("playlist", self.prompt["useWhen"])\n        self.assertIn("Gemini", self.prompt["useWhen"])',
    1,
)
text = text.replace(
    '            "yt-dlp owns YouTube extraction",',
    '            "yt-dlp owns machine-readable YouTube metadata extraction",\n            "does not forbid semantic analysis of video/transcript content directly available in Gemini context",',
    1,
)

new_test = '''\n    def test_immediately_preceding_video_or_link_is_implicit_source_input(self) -> None:\n        self.assert_markers(\n            "SOURCE INPUT RESOLUTION",\n            "immediately above this prompt",\n            "bind it as `SOURCE_INPUT` automatically",\n            "Do not ask the operator to paste, repeat, or restate it into a placeholder",\n            "`SOURCE_INPUT_KIND`",\n            "`SOURCE_INPUT_IDENTITY`",\n            "If the video itself is directly inspectable",\n            "grounded semantic analysis",\n            "If only a URL is present and the environment cannot inspect its content, do not invent what the video says",\n            "Source placement is input binding, not repository access",\n        )\n        self.assertIn("single video is valid input", self.content)\n        for keyword in (\n            "youtube video ingestion",\n            "single youtube video",\n            "youtube short",\n            "youtube video attachment",\n            "video above prompt",\n            "preceding youtube video",\n        ):\n            self.assertIn(keyword, self.prompt["keywords"])\n\n'''
marker = "    def test_yt_dlp_is_single_extraction_authority(self) -> None:\n"
if "test_immediately_preceding_video_or_link_is_implicit_source_input" not in text:
    if marker not in text:
        raise SystemExit("missing focused-test insertion anchor")
    text = text.replace(marker, new_test + marker, 1)

site_marker_old = '            "IDENTITY / OCCURRENCE INVARIANTS",\n'
site_marker_new = '            "SOURCE INPUT RESOLUTION",\n            "bind it as `SOURCE_INPUT` automatically",\n            "IDENTITY / OCCURRENCE INVARIANTS",\n'
if site_marker_new not in text:
    if site_marker_old not in text:
        raise SystemExit("missing generated-site marker anchor")
    text = text.replace(site_marker_old, site_marker_new, 1)

TEST.write_text(text, encoding="utf-8")
print(json.dumps({
    "id": prompt["id"],
    "name": prompt["name"],
    "copy_chars": len(prompt["copyContent"]),
    "keywords": prompt["keywords"][-6:],
    "source_binding": "immediately preceding unambiguous YouTube source",
}, indent=2, ensure_ascii=False))
