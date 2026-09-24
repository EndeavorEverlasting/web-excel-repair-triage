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
old_trigger = (
    "Activate only when work creates, updates, offers, exports, syncs, or closes out a material artifact, "
    "or scoped evidence says a cloud counterpart may matter."
)
new_trigger = (
    "Activate when work creates, updates, offers, exports, syncs, or closes out a material artifact; "
    "when the response is about to create or surface a user-facing local/download artifact; or scoped evidence says a cloud counterpart may matter.\n"
    "A planned or imminent local/download deliverable counts as artifact-bearing work. When the current project/workspace has a scoped cloud binding, "
    "resolve cloud relevance before final handoff; do not wait until after the local artifact is surfaced."
)
old_classification = (
    "2. Classify each material artifact LOCAL_ONLY_VERIFIED, MAPPED_CLOUD_VERIFIED, CLOUD_RELEVANCE_UNKNOWN, or BLOCKED. "
    "`CLOUD=NONE` is valid only when scoped current evidence establishes no relevant cloud counterpart; "
    "lack of an obvious connector/file is not proof of NONE."
)
new_classification = (
    "2. Classify each material artifact LOCAL_ONLY_VERIFIED, MAPPED_CLOUD_VERIFIED, CLOUD_RELEVANCE_UNKNOWN, or BLOCKED. "
    "`CLOUD=NONE` is valid only when scoped current evidence establishes no relevant cloud counterpart; "
    "lack of an obvious connector/file is not proof of NONE.\n"
    "2a. A known project/workspace cloud binding with no resolved per-artifact mapping is `CLOUD_RELEVANCE_UNKNOWN`, not `LOCAL_ONLY_VERIFIED`. "
    "Before closeout route the artifact through P111 or the applicable provider owner to resolve or reuse the cloud identity and obtain required write/readback proof. "
    "`LOCAL_ONLY_VERIFIED` requires either explicit local-only/private/do-not-sync authority or synchronizer proof that no relevant cloud counterpart should exist."
)
old_local = (
    "- `LOCAL_ONLY_VERIFIED => LOCAL_ONLY_ALLOWED`: A verified local-only artifact remains valid when scoped evidence proves no relevant cloud mapping exists."
)
new_local = (
    "- `LOCAL_ONLY_VERIFIED => LOCAL_ONLY_ALLOWED`: allow local-only handoff only when explicit local-only/private/do-not-sync authority or synchronizer proof establishes that no relevant cloud counterpart should exist."
)
old_unknown = (
    "- `CLOUD_RELEVANCE_UNKNOWN => CLOUD_CLOSURE_BLOCKED`: name the exact identity, access, write, or readback gate before local fallback; never claim sync succeeded."
)
new_unknown = (
    "- `CLOUD_RELEVANCE_UNKNOWN => CLOUD_CLOSURE_BLOCKED`: when a project/workspace cloud binding exists, route resolution through P111 or the applicable provider owner before local fallback; if resolution is blocked, name the exact identity, access, write, or readback gate and never claim sync succeeded."
)

for old, new, label in (
    (old_trigger, new_trigger, "artifact-bearing trigger"),
    (old_classification, new_classification, "bound-workspace classification"),
    (old_local, new_local, "local-only decision"),
    (old_unknown, new_unknown, "unknown-cloud decision"),
):
    if old not in content:
        raise SystemExit(f"expected P114 {label} text not found")
    content = content.replace(old, new, 1)

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
            "Close the project-cloud binding ambiguity so an unresolved per-artifact mapping cannot be treated as local-only; route resolution through the existing P111/provider owner while preserving P114 capability ownership.",
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
    '            f"{local}: allow local-only handoff only when explicit local-only/private/do-not-sync authority or synchronizer proof establishes that no relevant cloud counterpart should exist.",\n'
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
            "A planned or imminent local/download deliverable counts as artifact-bearing work.",
            "When the current project/workspace has a scoped cloud binding, resolve cloud relevance before final handoff",
            "A known project/workspace cloud binding with no resolved per-artifact mapping is `CLOUD_RELEVANCE_UNKNOWN`, not `LOCAL_ONLY_VERIFIED`.",
            "Before closeout route the artifact through P111 or the applicable provider owner",
            "`LOCAL_ONLY_VERIFIED` requires either explicit local-only/private/do-not-sync authority or synchronizer proof",
            "route resolution through P111 or the applicable provider owner before local fallback",
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
