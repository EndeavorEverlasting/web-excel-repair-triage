#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
TESTS = ROOT / "tests" / "test_gemini_youtube_playlist_ingestion_prompt.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
prompt = next(item for item in payload["prompts"] if item["id"] == "P123")
content = prompt["copyContent"]
before_len = len(content)

prompt["sprintRole"] = (
    "Give Gemini a domain-agnostic YouTube video or playlist ingestion brief that binds an immediately preceding "
    "accessible source, extracts grounded reusable knowledge into a supplied ledger/schema when present, and turns "
    "verified donor evidence into standalone implementation artifacts without pretending Gemini can inspect or modify "
    "the consumer repository"
)
prompt["useWhen"] = (
    "You have a YouTube video, Short, playlist, directly attached accessible media, saved yt-dlp JSON, or supplied "
    "transcript plus a knowledge-extraction mission and possibly a ledger/schema, and you want Gemini to understand the "
    "source without domain bias, classify reusable findings, and produce row-ready knowledge records plus the actual "
    "YouTube-metadata ingestion adapter, contracts, fixtures, tests, JSON/CSV examples, and repository-capable handoff "
    "while the target repository itself is not accessible to Gemini."
)
prompt["inspectFirst"] = (
    "First resolve the YouTube source from the immediately preceding current-turn context when one unambiguous "
    "video/link/attachment exists; otherwise use the explicitly supplied video, Short, playlist URL, saved yt-dlp JSON, "
    "or transcript. Then inspect the user's extraction mission and any supplied knowledge ledger/schema, especially its "
    "Sources, Findings, Domains, provenance, validation, and reuse fields; reuse its canonical domain vocabulary before "
    "inventing categories. Only then inspect verified donor dossier and pinned donor identities, consumer requirements/data "
    "model, required metadata fields and export rules, accepted/rejected architecture decisions, and Gemini's actual "
    "available files/tools. Do not infer repository paths, modules, schemas, tests, CI, branches, or runtime state that "
    "were not supplied."
)
prompt["expectedOutput"] = (
    "Grounded, domain-agnostic source understanding tied to the user's mission; when a ledger/schema is supplied, a "
    "row-ready Source record plus one Finding record per distinct reusable insight using its canonical Domains vocabulary "
    "and provenance/validation fields; plus a complete standalone implementation packet: Python yt-dlp adapter, normalized "
    "JSON contract/schema, derived CSV projection contract, deterministic synthetic fixture and tests, Windows-first run "
    "commands, representative JSON and CSV output, donor/version manifest, explicit proof ceiling, and a self-contained "
    "handoff for a repository-capable agent to integrate and validate against the real consumer repository."
)
prompt["proofGate"] = (
    "The immediately preceding unambiguous YouTube source is consumed without needless restatement; semantic claims about "
    "directly inspectable media are grounded in accessible video/transcript evidence or explicitly marked unproven; domain "
    "classification follows the source plus user mission rather than recent conversation themes, favorite domains, or "
    "examples; supplied Sources/Findings/Domains owners and provenance rules are preserved; favorite-domain views never "
    "become duplicate data authorities; Prompt Kit or software candidate fields are populated only when genuinely applicable; "
    "the standalone packet runs against a deterministic saved yt-dlp fixture; yt-dlp remains the sole machine-readable "
    "YouTube metadata extraction authority; playlist order and repeated occurrences survive normalization and CSV projection; "
    "single-video input remains valid without manufacturing playlist-only requirements; CSV spreadsheet hazards are "
    "neutralized without mutating canonical JSON; donor-license boundaries are explicit; Windows commands do not download "
    "media; and no inaccessible repository fact is presented as inspected, tested, committed, merged, or runtime-proven."
)

old_open = (
    "GEMINI YOUTUBE VIDEO / PLAYLIST INGESTION BUILD. USE THE SUPPLIED SOURCE DIRECTLY; PRODUCE THE ACTUAL STANDALONE "
    "IMPLEMENTATION PACKET, AND DO NOT PRETEND YOU CAN ACCESS THE TARGET REPOSITORY."
)
new_open = (
    "GEMINI YOUTUBE INGESTION. USE THE SUPPLIED SOURCE; EXTRACT GROUNDED KNOWLEDGE, BUILD THE STANDALONE PACKET, AND DO "
    "NOT PRETEND TO ACCESS THE TARGET REPOSITORY."
)
if old_open in content:
    content = content.replace(old_open, new_open, 1)

old_mission = (
    "Turn the supplied YouTube source, requirements, and verified donor research into grounded source understanding when "
    "available plus a complete runnable standalone ingestion packet for later repository integration. Implementation "
    "synthesis is required; fake repository work is forbidden."
)
new_mission = (
    "Turn the YouTube source, user mission, supplied ledger/schema, and verified donor research into grounded knowledge "
    "plus a runnable ingestion packet. Build real artifacts; never fake repository work."
)
if old_mission in content:
    content = content.replace(old_mission, new_mission, 1)

anchor = "Source placement is input binding, not repository access.\n\n"
section = """DOMAIN-AGNOSTIC KNOWLEDGE / LEDGER CONTRACT
- Classify from source + user mission, never recent conversation themes, favorites, or examples. Examples prove range, not defaults: Cybersecurity; Agentic Software Development; Culinary & Food.
- With a supplied ledger/schema, `Sources`, `Findings`, and `Domains` are canonical: reuse domains; one Source per source; one Findings row per finding; favored-domain views are projections, not separate data authorities.
- Preserve provenance/evidence/validation; use Unknown / Needs Verification. Set Prompt Kit Candidate or Software Candidate only when applicable. If unwritable, emit row-ready Source and Findings records; never pretend the spreadsheet was updated.

"""
if "DOMAIN-AGNOSTIC KNOWLEDGE / LEDGER CONTRACT" not in content:
    if anchor not in content:
        raise SystemExit("P123 source-input anchor not found")
    content = content.replace(anchor, anchor + section, 1)

prompt["copyContent"] = content
for keyword in (
    "youtube knowledge extraction",
    "youtube knowledge base",
    "domain agnostic youtube",
    "knowledge ledger",
    "youtube findings ledger",
):
    if keyword not in prompt["keywords"]:
        prompt["keywords"].append(keyword)

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

after_len = len(content)
print(f"P123_COPY_LENGTH before={before_len} after={after_len} delta={after_len-before_len}")
if after_len > 12000:
    raise SystemExit(f"P123 copyContent exceeds helper ceiling: {after_len} > 12000")

test_text = TESTS.read_text(encoding="utf-8")
marker = "    def test_domain_agnostic_knowledge_ledger_contract(self) -> None:"
if marker not in test_text:
    method = '''\n    def test_domain_agnostic_knowledge_ledger_contract(self) -> None:\n        self.assert_markers(\n            "DOMAIN-AGNOSTIC KNOWLEDGE / LEDGER CONTRACT",\n            "recent conversation themes",\n            "Examples prove range, not defaults",\n            "Cybersecurity",\n            "Agentic Software Development",\n            "Culinary & Food",\n            "`Sources`, `Findings`, and `Domains`",\n            "favored-domain views are projections, not separate data authorities",\n            "Unknown / Needs Verification",\n            "Prompt Kit Candidate",\n            "Software Candidate",\n            "row-ready Source and Findings records",\n            "never pretend the spreadsheet was updated",\n        )\n        self.assertIn("domain-agnostic", self.prompt["sprintRole"])\n        self.assertIn("without domain bias", self.prompt["useWhen"])\n        self.assertIn("canonical domain vocabulary", self.prompt["inspectFirst"])\n        self.assertIn("one Finding record per distinct reusable insight", self.prompt["expectedOutput"])\n        self.assertIn("favorite domains", self.prompt["proofGate"])\n        for keyword in (\n            "youtube knowledge extraction",\n            "youtube knowledge base",\n            "domain agnostic youtube",\n            "knowledge ledger",\n            "youtube findings ledger",\n        ):\n            self.assertIn(keyword, self.prompt["keywords"])\n\n'''
    insertion = "    def test_yt_dlp_is_single_extraction_authority(self) -> None:\n"
    if insertion not in test_text:
        raise SystemExit("P123 test insertion anchor not found")
    test_text = test_text.replace(insertion, method + insertion, 1)
    TESTS.write_text(test_text, encoding="utf-8")
