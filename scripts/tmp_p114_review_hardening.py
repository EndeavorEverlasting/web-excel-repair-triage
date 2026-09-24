from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_conversation_context_canary_prompt.py"
PATCH = ROOT / "Outputs" / "p114-review-hardening-patch.json"

registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
prompt = next(row for row in registry["prompts"] if row.get("id") == "P114")
content = prompt["copyContent"]

old_network = """REQUIRED NETWORK SEMANTICS
`NETWORK` is the network the user should be on, not observed connectivity. Use WAB, Guest, Hardwire, Local, or Arbitrary/N/A. `Arbitrary/N/A` means the task has no specific network requirement; it is not unknown. Network-sensitive unresolved state is `NETWORK=UNKNOWN`. Never invent SSIDs, VPNs, credentials, or trust state.

"""
new_network = """REQUIRED NETWORK SEMANTICS
`NETWORK` is the network the user should be on, not observed connectivity. Use WAB, Guest, Hardwire, Local, or Arbitrary/N/A. `Arbitrary/N/A` means the task has no specific network requirement; it is not unknown. Network-sensitive unresolved state is `NETWORK=UNKNOWN`. If observed live connectivity is available and differs from the required network, preserve the required NETWORK value and surface the mismatch; do not redefine the requirement to match observation. Never invent SSIDs, VPNs, credentials, or trust state.

"""

old_cloud = """CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF
Activate only when work creates, updates, offers, exports, syncs, or closes out a material artifact, or scoped evidence says a cloud counterpart may matter.
1. Inspect the scoped artifact manifest, registry, mapping, sync receipt, or workspace binding plus task-relevant provider evidence. Do not sweep unrelated cloud files or search the account broadly just to populate CLOUD.
2. Classify each material artifact LOCAL_ONLY_VERIFIED, MAPPED_CLOUD_VERIFIED, CLOUD_RELEVANCE_UNKNOWN, or BLOCKED. `CLOUD=NONE` is valid only when scoped current evidence establishes no relevant cloud counterpart; lack of an obvious connector/file is not proof of NONE.
3. If a local, repo-output, CI, temporary, downloadable, or `sandbox:/...` artifact is surfaced and a healthy canonical cloud counterpart exists, surface both together: usable canonical provider link plus local/download reference. Local is supplemental, not a replacement.
4. If a cloud artifact is surfaced and its local/generated counterpart matters for verification, editing, or reproducibility, pair both references.
5. Before claiming synchronized/current, route through the canonical provider owner and require identity/readback evidence. Reuse the stable provider identity; do not create a second CURRENT file/workspace because local is easier to link.
6. If identity resolution, access, write, or readback is blocked, name the exact identity, access, write, or readback gate before local fallback; never claim sync succeeded.
7. Google Drive repo mapping/sync routes to `P111 Repository + Google Drive Artifact Synchronizer` and `harness/artifact-handoff/WORKFLOW.md`. OneDrive, SharePoint, or another provider routes to an established provider/workspace owner when one exists; otherwise preserve UNKNOWN/BLOCKED instead of inventing sync.
P114 detects and routes; it does not become the sync engine. Offering a local artifact without the mapped cloud link is a Canary/closure failure when a healthy verified cloud counterpart exists. A verified local-only artifact remains valid when scoped evidence proves no relevant cloud mapping exists.

"""
new_cloud = """CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF
Activate only when work creates, updates, offers, exports, syncs, or closes out a material artifact, or scoped evidence says a cloud counterpart may matter.
1. Inspect the scoped artifact manifest, registry, mapping, sync receipt, or workspace binding plus task-relevant provider evidence. Do not sweep unrelated cloud files or search the account broadly just to populate CLOUD.
2. Classify each material artifact LOCAL_ONLY_VERIFIED, MAPPED_CLOUD_VERIFIED, CLOUD_RELEVANCE_UNKNOWN, or BLOCKED. `CLOUD=NONE` is valid only when scoped current evidence establishes no relevant cloud counterpart; lack of an obvious connector/file is not proof of NONE.
DELIVERY DECISION TABLE
- `MAPPED_CLOUD_VERIFIED + LOCAL_SURFACED => PAIR_REQUIRED`: surface both together: usable canonical provider link plus local/download reference.
- `LOCAL_ONLY_VERIFIED => LOCAL_ONLY_ALLOWED`: A verified local-only artifact remains valid when scoped evidence proves no relevant cloud mapping exists.
- `CLOUD_RELEVANCE_UNKNOWN => CLOUD_CLOSURE_BLOCKED`: name the exact identity, access, write, or readback gate before local fallback; never claim sync succeeded.
3. Before claiming synchronized/current, route through the canonical provider owner and require identity/readback evidence. Reuse the stable provider identity; do not create a second CURRENT file/workspace because local is easier to link.
4. Google Drive repo mapping/sync routes to `P111 Repository + Google Drive Artifact Synchronizer` and `harness/artifact-handoff/WORKFLOW.md`. OneDrive, SharePoint, or another provider routes to an established provider/workspace owner when one exists; otherwise preserve UNKNOWN/BLOCKED instead of inventing sync.
P114 detects and routes; it does not become the sync engine. Offering a local artifact without the mapped cloud link is a Canary/closure failure when a healthy verified cloud counterpart exists.

"""

if old_network not in content or old_cloud not in content:
    raise SystemExit("P114 review-hardening anchors changed; refusing blind mutation")
content = content.replace(old_network, new_network).replace(old_cloud, new_cloud)
if len(content) > 12000:
    raise SystemExit(f"P114 review-hardened copy exceeds lifecycle ceiling: {len(content)}")

PATCH.parent.mkdir(parents=True, exist_ok=True)
PATCH.write_text(json.dumps({"copyContent": content}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

cmd = [
    sys.executable,
    "scripts/prompt_registry_ops.py",
    "edit",
    "--prompt-id",
    "P114",
    "--input",
    str(PATCH),
    "--disposition",
    "NO_CAPABILITY_CHANGE",
    "--evidence-ref",
    "tests/test_conversation_context_canary_prompt.py",
    "--evidence-ref",
    "registry/prompts/spec-architecture-prompts.v1.json",
    "--rationale",
    "Review hardening restores observed-network mismatch semantics and makes local/cloud delivery branches explicit without changing P114 capability ownership.",
]
subprocess.run(cmd, cwd=ROOT, check=True)

test = TEST.read_text(encoding="utf-8")
old_network_assert = '''            "NETWORK=UNKNOWN",
            "EXEC=<shell>@<kernel/runtime>",
'''
new_network_assert = '''            "NETWORK=UNKNOWN",
            "If observed live connectivity is available and differs from the required network, preserve the required NETWORK value and surface the mismatch; do not redefine the requirement to match observation.",
            "EXEC=<shell>@<kernel/runtime>",
'''
if old_network_assert not in test:
    raise SystemExit("network test anchor changed")
test = test.replace(old_network_assert, new_network_assert, 1)

old_cloud_tests = '''    def test_cloud_artifact_relevance_pairs_local_and_provider_handoff(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF",
            "CLOUD=<GoogleDrive|OneDrive|SharePoint|Other|MULTIPLE|NONE|UNKNOWN>",
            "artifact manifest, registry, mapping, sync receipt, or workspace binding",
            "Do not sweep unrelated cloud files",
            "surface both together",
            "P111 Repository + Google Drive Artifact Synchronizer",
            "harness/artifact-handoff/WORKFLOW.md",
            "Reuse the stable provider identity",
            "name the exact identity, access, write, or readback gate",
            "P114 detects and routes; it does not become the sync engine",
            "Offering a local artifact without the mapped cloud link is a Canary/closure failure",
        ):
            self.assertIn(phrase, content)

    def test_cloud_artifact_gate_has_negative_and_positive_controls(self) -> None:
        content = self.target["copyContent"]
        self.assertIn(
            "`CLOUD=NONE` is valid only when scoped current evidence establishes no relevant cloud counterpart",
            content,
        )
        self.assertIn("lack of an obvious connector/file is not proof of NONE", content)
        self.assertIn(
            "A verified local-only artifact remains valid when scoped evidence proves no relevant cloud mapping exists",
            content,
        )
        self.assertIn(
            "Never let local/download silently replace a healthy mapped cloud artifact",
            content,
        )
'''
new_cloud_tests = '''    def test_cloud_artifact_relevance_pairs_local_and_provider_handoff(self) -> None:
        content = self.target["copyContent"]
        cloud = content.split("CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF", 1)[1].split(
            "AUTHORITATIVE CONTEXT RULE", 1
        )[0]
        for phrase in (
            "artifact manifest, registry, mapping, sync receipt, or workspace binding",
            "Do not sweep unrelated cloud files",
            "DELIVERY DECISION TABLE",
            "`MAPPED_CLOUD_VERIFIED + LOCAL_SURFACED => PAIR_REQUIRED`: surface both together: usable canonical provider link plus local/download reference.",
            "P111 Repository + Google Drive Artifact Synchronizer",
            "harness/artifact-handoff/WORKFLOW.md",
            "Reuse the stable provider identity",
            "P114 detects and routes; it does not become the sync engine",
            "Offering a local artifact without the mapped cloud link is a Canary/closure failure",
        ):
            self.assertIn(phrase, cloud)

    def test_cloud_artifact_gate_has_negative_and_positive_controls(self) -> None:
        content = self.target["copyContent"]
        cloud = content.split("CLOUD ARTIFACT RELEVANCE / PAIRED HANDOFF", 1)[1].split(
            "AUTHORITATIVE CONTEXT RULE", 1
        )[0]
        pair = "`MAPPED_CLOUD_VERIFIED + LOCAL_SURFACED => PAIR_REQUIRED`"
        local = "`LOCAL_ONLY_VERIFIED => LOCAL_ONLY_ALLOWED`"
        blocked = "`CLOUD_RELEVANCE_UNKNOWN => CLOUD_CLOSURE_BLOCKED`"
        self.assertIn(
            "`CLOUD=NONE` is valid only when scoped current evidence establishes no relevant cloud counterpart",
            cloud,
        )
        self.assertIn("lack of an obvious connector/file is not proof of NONE", cloud)
        self.assertIn(
            f"{local}: A verified local-only artifact remains valid when scoped evidence proves no relevant cloud mapping exists.",
            cloud,
        )
        self.assertIn(
            f"{blocked}: name the exact identity, access, write, or readback gate before local fallback; never claim sync succeeded.",
            cloud,
        )
        self.assertLess(cloud.index(pair), cloud.index(local))
        self.assertLess(cloud.index(local), cloud.index(blocked))
        self.assertIn(
            "Never let local/download silently replace a healthy mapped cloud artifact",
            content,
        )
'''
if old_cloud_tests not in test:
    raise SystemExit("cloud test anchors changed")
TEST.write_text(test.replace(old_cloud_tests, new_cloud_tests, 1), encoding="utf-8")
