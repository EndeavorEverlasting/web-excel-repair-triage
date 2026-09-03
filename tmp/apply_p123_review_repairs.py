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

old_section = """DOMAIN-AGNOSTIC KNOWLEDGE / LEDGER CONTRACT
- Classify from source + user mission, never recent conversation themes, favorites, or examples. Examples prove range, not defaults: Cybersecurity; Agentic Software Development; Culinary & Food.
- With a supplied ledger/schema, `Sources`, `Findings`, and `Domains` are canonical: reuse domains; one Source per source; one Findings row per finding; favored-domain views are projections, not separate data authorities.
- Preserve provenance/evidence/validation; use Unknown / Needs Verification. Set Prompt Kit Candidate or Software Candidate only when applicable. If unwritable, emit row-ready Source and Findings records; never pretend the spreadsheet was updated.
"""
new_section = """DOMAIN-AGNOSTIC KNOWLEDGE / LEDGER CONTRACT
- Classify from source + mission, never recent conversation themes, favorites, or examples. Examples prove range, not defaults: Cybersecurity; Agentic Software Development; Culinary & Food.
- With a ledger/schema, `Sources`, `Findings`, and `Domains` are canonical; reuse domains; favored views are projections, not separate data authorities.
- Resolve spreadsheet write capability + authority. If writable + authorized, reuse/append Source, append Findings rows, and report exact written ranges/IDs as the mutation receipt. Otherwise emit row-ready Source and Findings records. Never claim the spreadsheet was updated without an observed write receipt.
- Preserve provenance/evidence/validation; use Unknown / Needs Verification. Set Prompt Kit Candidate / Software Candidate only when applicable.
"""
if old_section not in content:
    raise SystemExit("Expected current P123 ledger section not found")
content = content.replace(old_section, new_section, 1)

# Recover copy budget by removing redundant framing, not behavior.
content = content.replace(
    "GEMINI YOUTUBE INGESTION. USE THE SUPPLIED SOURCE; EXTRACT GROUNDED KNOWLEDGE, BUILD THE STANDALONE PACKET, AND DO NOT PRETEND TO ACCESS THE TARGET REPOSITORY.",
    "GEMINI YOUTUBE INGESTION. USE THE SOURCE; EXTRACT KNOWLEDGE, BUILD THE PACKET, AND DO NOT PRETEND REPOSITORY ACCESS.",
    1,
)
content = content.replace(
    "Turn the YouTube source, user mission, supplied ledger/schema, and verified donor research into grounded knowledge plus a runnable ingestion packet. Build real artifacts; never fake repository work.",
    "Turn source + mission + ledger/schema + donor evidence into grounded knowledge and a runnable packet. Build real artifacts; never fake repo work.",
    1,
)
prompt["copyContent"] = content

prompt["expectedOutput"] = (
    "Grounded, domain-agnostic source understanding tied to the user's mission; when a ledger/schema is supplied, one Source "
    "record plus one Finding record per distinct reusable insight using its canonical Domains vocabulary and provenance/validation "
    "fields, written with exact mutation receipt when spreadsheet capability and authority permit or emitted row-ready otherwise; "
    "plus a complete standalone implementation packet: Python yt-dlp adapter, normalized JSON contract/schema, derived CSV "
    "projection contract, deterministic synthetic fixture and tests, Windows-first run commands, representative JSON and CSV "
    "output, donor/version manifest, explicit proof ceiling, and a self-contained handoff for a repository-capable agent to "
    "integrate and validate against the real consumer repository."
)
prompt["proofGate"] = (
    "The immediately preceding unambiguous YouTube source is consumed without needless restatement; semantic claims about directly "
    "inspectable media are grounded in accessible video/transcript evidence or explicitly marked unproven; domain classification "
    "follows the source plus user mission rather than recent conversation themes, favorite domains, or examples; supplied "
    "Sources/Findings/Domains owners and provenance rules are preserved; favorite-domain views never become duplicate data "
    "authorities; when the ledger is writable and write authority exists the canonical Source/Findings mutation is actually "
    "performed and bound to exact written ranges/IDs, while unwritable or unauthorized cases return row-ready records without "
    "claiming a write; Prompt Kit or software candidate fields are populated only when genuinely applicable; the standalone packet "
    "runs against a deterministic saved yt-dlp fixture; yt-dlp remains the sole machine-readable YouTube metadata extraction "
    "authority; playlist order and repeated occurrences survive normalization and CSV projection; single-video input remains valid "
    "without manufacturing playlist-only requirements; CSV spreadsheet hazards are neutralized without mutating canonical JSON; "
    "donor-license boundaries are explicit; Windows commands do not download media; and no inaccessible repository fact is presented "
    "as inspected, tested, committed, merged, or runtime-proven."
)

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
after_len = len(content)
print(f"P123_REVIEW_REPAIR_LENGTH before={before_len} after={after_len} delta={after_len-before_len}")
if after_len > 12000:
    raise SystemExit(f"P123 copyContent exceeds helper ceiling: {after_len} > 12000")

text = TESTS.read_text(encoding="utf-8")
text = text.replace(
    '            "row-ready Source and Findings records",\n            "never pretend the spreadsheet was updated",\n',
    '            "Resolve spreadsheet write capability + authority",\n            "exact written ranges/IDs as the mutation receipt",\n            "Otherwise emit row-ready Source and Findings records",\n            "Never claim the spreadsheet was updated without an observed write receipt",\n',
    1,
)
text = text.replace(
    '        self.assertIn("one Finding record per distinct reusable insight", self.prompt["expectedOutput"])\n        self.assertIn("favorite domains", self.prompt["proofGate"])\n',
    '        self.assertIn("one Finding record per distinct reusable insight", self.prompt["expectedOutput"])\n        self.assertIn("written with exact mutation receipt", self.prompt["expectedOutput"])\n        self.assertIn("writable and write authority exists", self.prompt["proofGate"])\n        self.assertIn("exact written ranges/IDs", self.prompt["proofGate"])\n        self.assertIn("favorite domains", self.prompt["proofGate"])\n',
    1,
)
old_site = '''            "PRE-MUTATION MISSION DECLARATION",\n        ):\n            self.assertIn(marker, deployed)\n'''
new_site = '''            "PRE-MUTATION MISSION DECLARATION",\n            "DOMAIN-AGNOSTIC KNOWLEDGE / LEDGER CONTRACT",\n            "`Sources`, `Findings`, and `Domains`",\n            "Resolve spreadsheet write capability + authority",\n            "exact written ranges/IDs as the mutation receipt",\n            "row-ready Source and Findings records",\n        ):\n            self.assertIn(marker, deployed)\n'''
if old_site not in text:
    raise SystemExit("Generated-site test anchor not found")
text = text.replace(old_site, new_site, 1)
TESTS.write_text(text, encoding="utf-8")
