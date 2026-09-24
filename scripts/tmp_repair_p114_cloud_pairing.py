#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_conversation_context_canary_prompt.py"
PLAN = ROOT / "docs" / "plans" / "CLOUD_PAIRED_ARTIFACT_HANDOFF_SPRINT_MAP.md"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
target = next((row for row in payload["prompts"] if row.get("id") == "P114"), None)
if target is None:
    raise SystemExit("P114 not found in canonical registry")

content = target["copyContent"]
start_marker = "CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF\n"
end_marker = "AUTHORITATIVE CONTEXT RULE"
start = content.find(start_marker)
end = content.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("P114 cloud-handoff section markers not found")

new_cloud = """CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF
Trigger for artifact work, an imminent user-facing local/download artifact, or scoped evidence a cloud counterpart may matter.
1. Inspect the scoped artifact manifest, registry, mapping, sync receipt, or workspace binding. Do not sweep unrelated cloud files.
2. Use LOCAL_ONLY_VERIFIED, MAPPED_CLOUD_VERIFIED, CLOUD_RELEVANCE_UNKNOWN, or BLOCKED. A project/workspace cloud binding with unresolved mapping is `CLOUD_RELEVANCE_UNKNOWN`, not `LOCAL_ONLY_VERIFIED`; route through P111/provider owner before closeout. `LOCAL_ONLY_VERIFIED` requires explicit local-only/private/do-not-sync authority or synchronizer proof of no cloud counterpart. `CLOUD=NONE` is valid only when scoped current evidence establishes no relevant cloud counterpart; lack of an obvious connector/file is not proof of NONE.
DELIVERY DECISION TABLE
- `MAPPED_CLOUD_VERIFIED + LOCAL_SURFACED => PAIR_REQUIRED`: surface both together: usable canonical provider link plus local/download reference.
- `LOCAL_ONLY_VERIFIED => LOCAL_ONLY_ALLOWED`: require explicit local-only/private/do-not-sync authority or synchronizer proof.
- `CLOUD_RELEVANCE_UNKNOWN => CLOUD_CLOSURE_BLOCKED`: name the exact identity, access, write, or readback gate before local fallback; never claim sync succeeded.
3. Before claiming synchronized/current, require provider-owner identity/readback evidence. Reuse the stable provider identity; never create a second CURRENT artifact just to get a link.
4. Google Drive uses `P111 Repository + Google Drive Artifact Synchronizer` and `harness/artifact-handoff/WORKFLOW.md`; other providers use their owner or remain UNKNOWN/BLOCKED.
P114 detects and routes; it does not become the sync engine. Offering a local artifact without the mapped cloud link is a Canary/closure failure when a healthy verified cloud counterpart exists.

"""
content = content[:start] + new_cloud + content[end:]
if len(content) > 12000:
    raise SystemExit(f"compacted P114 still exceeds helper ceiling: {len(content)}")
patch = {"copyContent": content}

with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False, dir=ROOT) as handle:
    json.dump(patch, handle, ensure_ascii=False, indent=2)
    patch_path = Path(handle.name)
try:
    subprocess.run(
        [
            sys.executable,
            "scripts/prompt_registry_ops.py",
            "edit",
            "--prompt-id",
            "P114",
            "--input",
            str(patch_path),
            "--disposition",
            "NO_CAPABILITY_CHANGE",
            "--evidence-ref",
            "tests/test_conversation_context_canary_prompt.py",
            "--evidence-ref",
            "docs/plans/CLOUD_PAIRED_ARTIFACT_HANDOFF_SPRINT_MAP.md",
            "--evidence-ref",
            "registry/prompts/repository-work-ledger-prompts.v1.json",
            "--rationale",
            "Close the project-cloud binding ambiguity so unresolved artifact mapping cannot be treated as local-only; route through the existing provider owner while preserving P114 capability ownership.",
        ],
        cwd=ROOT,
        check=True,
    )
finally:
    patch_path.unlink(missing_ok=True)

test_text = TEST.read_text(encoding="utf-8")
old_assertion = (
    '            f"{local}: A verified local-only artifact remains valid when scoped evidence proves no relevant cloud mapping exists.",\n'
)
new_assertion = (
    '            f"{local}: require explicit local-only/private/do-not-sync authority or synchronizer proof.",\n'
)
if old_assertion not in test_text:
    raise SystemExit("expected local-only assertion not found")
test_text = test_text.replace(old_assertion, new_assertion, 1)

marker = "    def test_p114_has_accepted_semantic_profile_after_adoption(self) -> None:\n"
new_test = '''    def test_bound_cloud_workspace_requires_resolution_before_local_handoff(self) -> None:
        content = self.target["copyContent"]
        cloud = content.split("CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF", 1)[1].split(
            "AUTHORITATIVE CONTEXT RULE", 1
        )[0]
        for phrase in (
            "an imminent user-facing local/download artifact",
            "A project/workspace cloud binding with unresolved mapping is `CLOUD_RELEVANCE_UNKNOWN`, not `LOCAL_ONLY_VERIFIED`",
            "route through P111/provider owner before closeout",
            "`LOCAL_ONLY_VERIFIED` requires explicit local-only/private/do-not-sync authority or synchronizer proof",
        ):
            self.assertIn(phrase, cloud)
        self.assertNotIn(
            "`LOCAL_ONLY_VERIFIED => LOCAL_ONLY_ALLOWED`: A verified local-only artifact remains valid when scoped evidence proves no relevant cloud mapping exists.",
            cloud,
        )

'''
if marker not in test_text:
    raise SystemExit("P114 semantic-profile test marker not found")
test_text = test_text.replace(marker, new_test + marker, 1)
TEST.write_text(test_text, encoding="utf-8")

plan_text = PLAN.read_text(encoding="utf-8")
PLAN.write_text("\n".join(line.rstrip() for line in plan_text.splitlines()) + "\n", encoding="utf-8")
