#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs/prompts.json"
TEST = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"
MARKER = "CONTEXT-GROUNDED PRE-CREATION RECONSTRUCTION"

payload = json.loads(PROMPTS.read_text(encoding="utf-8"))
records = [item for item in payload if item.get("id") == "P55"]
if len(records) != 1:
    raise SystemExit(f"expected exactly one P55 record, found {len(records)}")
p = records[0]

p["name"] = "Context-Grounded Repository Bootstrapper"
p["sprintRole"] = (
    "Recover project and repository identity from available context, then safely create or adopt the correct GitHub repository "
    "through the strongest available remote/local tool surface and verify the strongest reachable state"
)
p["useWhen"] = (
    "The operator wants a new repository, wants to publish or adopt an existing project, or wants an existing artifact/app/spreadsheet/workflow "
    "turned into a repository even when repository name, owner, visibility, source location, or remote/local execution context is incomplete."
)
p["inspectFirst"] = (
    "Preceding/surrounding operator guidance; named or recoverable prior chats/handoffs; source artifacts and product vocabulary; existing local/remote repositories and GitHub ownership; "
    "requested or inferable owner/name/visibility/description; verified parent or source directory when locally accessible; available Git/GitHub connector/API/gh capabilities; active account/policy; "
    "bootstrap choices; collision checks; deployment-topology relevance; and mutation authority."
)
p["expectedOutput"] = (
    "A compact project/repository identity ledger with RESOLVED, INFERRED, and USER_ONLY fields; reuse of an existing canonical repository when found or a verified new GitHub repository when creation is justified; "
    "the strongest reachable remote/local root and origin evidence; bootstrap/history exactly as authorized; command or provider evidence; repository URL; branch state; proof ceiling; and next command."
)
p["proofGate"] = (
    "Relevant context and source assets are recovered before naming; compatible existing repository ownership is ruled in or out before creation; inferred metadata is evidence-backed and reversible; unresolved consequential identity choices are USER_ONLY; "
    "visibility never defaults to public; authentication is healthy without token exposure; collision checks pass; the authorized remote creation/adoption succeeds through the available GitHub surface; and remote/local claims match what was actually observed."
)

for keyword in (
    "repository creation",
    "create repository",
    "new repository",
    "name repository",
    "publish project",
    "remote repository",
    "local repository",
    "context grounded bootstrap",
):
    if keyword not in p["keywords"]:
        p["keywords"].append(keyword)

content = p["copyContent"]
if MARKER not in content:
    anchor = "Bootstrap options: xyz_readme_license_gitignore_template_or_none\n\nDIRECTORY GATE"
    if anchor not in content:
        raise SystemExit("P55 bootstrap-options/DIRECTORY GATE anchor changed; refusing blind mutation")
    section = r'''Bootstrap options: xyz_readme_license_gitignore_template_or_none

CONTEXT-GROUNDED PRE-CREATION RECONSTRUCTION
Before naming or creating anything, recover the project that already exists in the user's intent and environment.
1. Treat preceding/surrounding operator guidance, named or recoverable prior chats/handoffs, source files/spreadsheets/apps, connected GitHub state, and discoverable local/remote repositories as evidence. Recover accessible context yourself; do not ask the operator to restate it.
2. Build a compact PROJECT IDENTITY ledger: intended user outcome; existing source artifacts; existing repository/local/remote owners; product boundary; durable product vocabulary and naming signals; owner/visibility policy; publish-vs-clone intent; deployment/runtime relevance; unresolved material choices. Mark each field RESOLVED, INFERRED, or USER_ONLY with its evidence source.
3. Check `already exists` before `create new`. Search plausible current repositories and source roots. If a compatible canonical repository already owns the product, adopt/repair/publish that owner instead of minting a duplicate merely because the current artifact began as a spreadsheet, script, prototype, folder, or other narrower form.
4. Name from durable product responsibility and operator vocabulary, not the first artifact, temporary implementation, or one feature. Preserve an explicit operator name unless current evidence proves a collision or ownership conflict. When the name is missing, derive a concise collision-free candidate from the recovered product boundary and vocabulary and use it when one choice clearly dominates. Escalate only when competing names materially change product identity.
5. Fill reversible blanks from current evidence rather than interrogating the operator. Description, bootstrap choices, local mode, owner, and similar metadata may be inferred when current context/policy makes one choice clearly supported. Never infer public visibility from silence; when visibility is not explicit or policy-backed, mark it USER_ONLY and block creation at that narrow gate.
6. This is execution, not a Socratic vision interview. P96 owns deliberate challenge/teaching and deep clarification. P55 asks only the smallest material USER_ONLY question left after context recovery and safe inference.
7. If initial repository shape genuinely depends on deployment topology, route that bounded design choice to P95. Keep platform-specific PaaS/serverless, Docker/Podman, or Kubernetes detail demand-loaded until evidence makes it decision-relevant; ordinary repository creation must not preload or require orchestration doctrine.

EXECUTION SURFACE
- BOTH: local filesystem/Git plus GitHub write access are available; create/adopt and verify both sides.
- REMOTE_ONLY: a connected GitHub API/app/connector can create or inspect the remote but no local filesystem is available; complete the remote side and do not claim a local clone/root.
- LOCAL_ONLY: local Git/filesystem is available but remote mutation/auth is unavailable; prepare and verify the local source, then stop at the exact remote authorization/credential gate without fabricating GitHub completion.
- CLI commands below are the canonical local shape when `gh` exists. When a connected GitHub API/app is the available authorized remote surface, perform the equivalent lookup/create/verification operations there and report provider evidence instead of pretending the CLI ran.

DIRECTORY GATE'''
    content = content.replace(anchor, section, 1)

old_precondition = "4. Require explicit owner/name and exactly one visibility choice. Never default to public."
new_precondition = (
    "4. Resolve owner/name and visibility from explicit guidance or strong recovered policy/context evidence. A missing name may be inferred only from a clear durable product identity and collision-free repository check. Never default to public; unresolved visibility is USER_ONLY and blocks creation."
)
if old_precondition in content:
    content = content.replace(old_precondition, new_precondition, 1)
elif new_precondition not in content:
    raise SystemExit("P55 precondition 4 changed; refusing blind mutation")

old_opening = "CREATE AND VERIFY A NEW GITHUB REPOSITORY THROUGH GIT AND GITHUB CLI. DO NOT RETURN A PLAN ONLY WHEN CREATION IS EXPLICITLY AUTHORIZED."
new_opening = "RECOVER THE PROJECT IDENTITY, THEN CREATE OR ADOPT AND VERIFY THE CORRECT GITHUB REPOSITORY THROUGH THE STRONGEST AVAILABLE GIT/GITHUB SURFACE. DO NOT RETURN A PLAN ONLY WHEN SAFE CREATION OR ADOPTION IS AUTHORIZED."
if old_opening in content:
    content = content.replace(old_opening, new_opening, 1)
elif new_opening not in content:
    raise SystemExit("P55 opening changed; refusing blind mutation")

old_final = "FINAL RESPONSE\nReport repo, verified parent and root, active account without token material, creation mode and command, visibility and bootstrap flags, remote and origin URLs, branch and commit evidence, files, validation, skips, blockers, proof, ceiling, final Git state, and one exact next command."
new_final = "FINAL RESPONSE\nReport the PROJECT IDENTITY ledger and evidence sources; whether an existing canonical repository was reused or a new one was justified; repo, verified parent/root when observable, execution surface, active account without token material, creation/adoption mode and actual command/provider action, visibility and bootstrap flags, remote/origin evidence, branch and commit evidence, files, validation, skips, USER_ONLY gates, blockers, proof, ceiling, final Git state, and one exact next command."
if old_final in content:
    content = content.replace(old_final, new_final, 1)
elif new_final not in content:
    raise SystemExit("P55 final-response anchor changed; refusing blind mutation")

p["copyContent"] = content
PROMPTS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

source = TEST.read_text(encoding="utf-8")
method_marker = "    def test_p55_repo_creation_recovers_context_before_naming(self) -> None:\n"
if method_marker not in source:
    insertion = r'''
    def test_p55_repo_creation_recovers_context_before_naming(self) -> None:
        bootstrap = self.full["P55"]
        self.assertEqual(bootstrap["name"], "Context-Grounded Repository Bootstrapper")
        content = bootstrap["copyContent"]
        for phrase in (
            "CONTEXT-GROUNDED PRE-CREATION RECONSTRUCTION",
            "preceding/surrounding operator guidance",
            "do not ask the operator to restate it",
            "PROJECT IDENTITY ledger",
            "RESOLVED, INFERRED, or USER_ONLY",
            "Check `already exists` before `create new`",
            "durable product responsibility and operator vocabulary",
            "Never infer public visibility from silence",
            "P96 owns deliberate challenge/teaching",
            "route that bounded design choice to P95",
            "Docker/Podman",
            "Kubernetes detail demand-loaded",
            "REMOTE_ONLY",
            "do not claim a local clone/root",
            "connected GitHub API/app",
        ):
            self.assertIn(phrase, content)
        for preserved in (
            "Never use --show-token",
            "gh repo view xyz_owner/xyz_repo_name",
            "never delete or overwrite it automatically",
            "unowned dirty work",
        ):
            self.assertIn(preserved, content)
        self.assertIn("repository creation", bootstrap["keywords"])
        self.assertIn("name repository", bootstrap["keywords"])
        self.assertIn("preceding/surrounding operator guidance", bootstrap["inspectFirst"])
        self.assertIn("RESOLVED, INFERRED, and USER_ONLY", bootstrap["expectedOutput"])
        self.assertIn("visibility never defaults to public", bootstrap["proofGate"])
'''
    class_end = source.rfind("\nif __name__ == \"__main__\":")
    if class_end == -1:
        source = source.rstrip() + insertion + "\n"
    else:
        source = source[:class_end].rstrip() + "\n" + insertion + "\n" + source[class_end:]
    TEST.write_text(source, encoding="utf-8")

print("P55 strengthened with context-grounded pre-creation reconstruction and remote/local execution semantics")
