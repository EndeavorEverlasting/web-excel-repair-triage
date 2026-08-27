#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
TEST = ROOT / "tests" / "test_gemini_youtube_playlist_ingestion_prompt.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
matches = [p for p in payload["prompts"] if p.get("id") == "P123" and p.get("name") == "Gemini YouTube Playlist Ingestion Builder"]
if len(matches) != 1:
    raise SystemExit(f"expected exactly one P123 Gemini prompt, found {len(matches)}")
prompt = matches[0]
content = prompt["copyContent"]

packet_anchor = "Do not import from hypothetical consumer-repository modules. Keep the packet standalone except for external yt-dlp on live extraction.\n\nRUNNABILITY GATE"
packet_replacement = """Do not import from hypothetical consumer-repository modules. Keep the packet standalone except for external yt-dlp on live extraction.

OUTPUT PATH SAFETY CONTRACT
Generated JSON, CSV, donor manifests, and deterministic examples go under `Outputs/` by default. Resolve every input and output path before writing and reject equal resolved input/output paths, including `--input-json`, fixtures, donor evidence, and generated artifacts. A source fixture or saved yt-dlp JSON must remain byte-identical after a rejected collision. If an explicitly supplied consumer contract authorizes overwriting a non-Outputs destination, create a timestamped backup under `Outputs/backups/` before the overwrite; never invent overwrite authority.

RUNNABILITY GATE"""
if "OUTPUT PATH SAFETY CONTRACT" not in content:
    if packet_anchor not in content:
        raise SystemExit("implementation packet anchor not found")
    content = content.replace(packet_anchor, packet_replacement, 1)

minimum_anchor = "and fixture-mode CLI writes both JSON and CSV deterministically.\n\nBACKEND-NEUTRAL NORMALIZATION CONTRACT"
minimum_replacement = "and fixture-mode CLI writes both JSON and CSV deterministically. Add a collision fixture proving equal resolved input/output paths are rejected before any write and the source fixture remains byte-identical.\n\nBACKEND-NEUTRAL NORMALIZATION CONTRACT"
if "collision fixture proving equal resolved input/output paths" not in content:
    if minimum_anchor not in content:
        raise SystemExit("minimum-test anchor not found")
    content = content.replace(minimum_anchor, minimum_replacement, 1)

handoff_anchor = """PRE-MUTATION MISSION DECLARATION
Before tracked mutation, that agent declares repository and branch/worktree, lane and mission, owned and forbidden scope, expected artifacts, validation order, proof ceiling, and mutation authority. It then refreshes remote truth and find the existing source/import/domain owners, schemas, CLI patterns, artifact registry, validators, and tests.
Preserve the authority boundary:"""
handoff_replacement = """PRE-MUTATION MISSION DECLARATION
Before tracked mutation, that agent declares repository and branch/worktree, lane and mission, owned and forbidden scope, expected artifacts, validation order, proof ceiling, and mutation authority. It then refreshes remote truth; reads repository governance and current Git/PR state; inspects relevant source files, registered artifacts, validators/tests, and recent relevant history; and finds the existing source/import/domain owners, schemas, CLI patterns, and artifact registry. Preserve dirty or separately owned work and enforce one writer per mutation surface. After mutation, run the focused owner checks plus repository-required gates and `git diff --check`; use normal commit and push when authorized and never force-push merely to converge.
The handoff's final report must name changed files, executed checks and results, commit SHA, push/PR state, blockers, Git status, proof ceiling, and the exact next command. A branch, PR, or green check is not completion while safe authorized integration remains.
Preserve the authority boundary:"""
if "one writer per mutation surface" not in content:
    if handoff_anchor not in content:
        raise SystemExit("repository-capable handoff anchor not found")
    content = content.replace(handoff_anchor, handoff_replacement, 1)

if len(content) > 12000:
    raise SystemExit(f"P123 copyContent exceeds helper ceiling after review repair: {len(content)}")
prompt["copyContent"] = content
REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
insert_after = """    def test_helper_contribution_stays_within_copy_ceiling(self) -> None:
        # prompt_registry_ops.py owns the 12,000-character contribution ceiling.
        # Keep this regression on the durable semantic record so a future edit
        # cannot recreate the oversized P122/P123 collision-repair failure.
        self.assertGreaterEqual(len(self.content), 300)
        self.assertLessEqual(len(self.content), 12000)

"""
new_test = """    def test_review_repair_requires_path_safety_and_repo_closeout(self) -> None:
        self.assert_markers(
            "OUTPUT PATH SAFETY CONTRACT",
            "under `Outputs/` by default",
            "reject equal resolved input/output paths",
            "source fixture remains byte-identical",
            "timestamped backup under `Outputs/backups/`",
            "repository governance and current Git/PR state",
            "one writer per mutation surface",
            "`git diff --check`",
            "normal commit and push when authorized",
            "changed files, executed checks and results, commit SHA, push/PR state, blockers, Git status, proof ceiling, and the exact next command",
        )

"""
if "test_review_repair_requires_path_safety_and_repo_closeout" not in test:
    if insert_after not in test:
        raise SystemExit("copy-ceiling test anchor not found")
    test = test.replace(insert_after, insert_after + new_test, 1)
    TEST.write_text(test, encoding="utf-8")

print(json.dumps({"status": "patched", "id": "P123", "copy_length": len(content)}))
