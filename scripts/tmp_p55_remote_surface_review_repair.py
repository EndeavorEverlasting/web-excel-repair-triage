#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs/prompts.json"
TESTS = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"

payload = json.loads(PROMPTS.read_text(encoding="utf-8"))
records = [item for item in payload if item.get("id") == "P55"]
if len(records) != 1:
    raise SystemExit(f"expected exactly one P55 record, found {len(records)}")
p = records[0]
p["class"] = "STANDARD AI / CONTEXT-GROUNDED REPOSITORY CREATION"
content = p["copyContent"]

start_marker = "EXECUTION SURFACE\n"
end_marker = "MODE A — NEW REMOTE AND LOCAL CLONE\n"
if start_marker not in content or end_marker not in content:
    raise SystemExit("P55 execution-surface anchors changed; refusing blind repair")
start = content.index(start_marker)
end = content.index(end_marker)
replacement = '''EXECUTION SURFACE — RESOLVE BEFORE TOOL CHECKS
- BOTH: local filesystem/Git plus GitHub write access are available; create/adopt and verify both sides.
- REMOTE_ONLY: a connected GitHub API/app/connector can authenticate, inspect, and mutate the remote but no usable local filesystem/Git surface is available; complete the remote side and do not claim a local clone/root.
- LOCAL_ONLY: local filesystem/Git is available but remote mutation/auth is unavailable; prepare and verify the local source, then stop at the exact remote authorization/credential gate without fabricating GitHub completion.
- CLI commands below are the canonical local shape when those tools exist. A connected GitHub API/app is an equivalent remote execution surface, not a degraded CLI path.
- Resolve the execution surface first. Do not run `git --version`, `gh --version`, `gh auth status`, or other local-only probes merely because they appear in examples when the selected surface is REMOTE_ONLY.

DIRECTORY GATE — ONLY WHEN A LOCAL FILESYSTEM SURFACE EXISTS
1. In BOTH or LOCAL_ONLY, resolve and verify the intended parent directory for clone mode or the exact existing Git root for publish-existing mode before local mutation.
2. Enter that path first with Set-Location -LiteralPath or cd --.
3. In publish-existing mode, when Git is available, run git rev-parse --show-toplevel, git status --short, git branch --show-current, git log --oneline --decorate -5, and git remote -v. Refuse the wrong root, ambiguous history, unowned dirty work, or conflicting origin.
4. In clone mode verify the intended child path does not contain unknown work and never delete or overwrite it automatically.
5. In REMOTE_ONLY, record `LOCAL_ROOT=UNOBSERVABLE` and skip this gate; absence of a local path is not failure for an authorized remote-only creation.

PRECONDITIONS BY EXECUTION SURFACE
COMMON
1. Resolve requested outcome, owner/name candidate, visibility, description, existing-owner evidence, creation/adoption intent, and mutation authority from the PROJECT IDENTITY ledger.
2. Never default to public. A missing name may be inferred only from a clear durable product identity plus a collision-free check. Unresolved visibility or another consequential identity choice is USER_ONLY and blocks only the mutation that depends on it.
3. Distinguish an existing repository, confirmed not-found, authentication failure, permission denial, network/provider failure, and ambiguous lookup. UNKNOWN is not permission to create a duplicate.
4. Validate optional license, gitignore, and template choices before using them.

BOTH / CLI-CAPABLE REMOTE
1. When local Git work is required and Git is available, run git --version before relying on Git behavior.
2. When `gh` is the selected remote executor, run gh --version and gh auth status --active --hostname github.com. Never use --show-token, print token-bearing environment variables, request credentials in chat, or automate gh auth login.
3. Confirm the active account can create under xyz_owner.
4. Check gh repo view xyz_owner/xyz_repo_name and classify its result before creation.

REMOTE_ONLY — PROVIDER/API
1. Use the connected GitHub API/app/connector's exposed identity/authorization result to prove which account or installation is acting and whether repository creation/inspection is permitted. Never expose token material or invent an account identity the provider did not return.
2. Perform a provider repository lookup equivalent to `gh repo view xyz_owner/xyz_repo_name`; classify FOUND / CONFIRMED_NOT_FOUND / AUTH_BLOCKED / PERMISSION_BLOCKED / PROVIDER_OR_NETWORK_ERROR / UNKNOWN.
3. Only after CONFIRMED_NOT_FOUND plus resolved mutation fields, create the repository through the authorized provider operation. If a compatible repository is FOUND, adopt/reuse it rather than creating a duplicate.
4. Immediately read the repository back through the provider and verify owner/name, URL, visibility, and default-branch state when exposed. Record unavailable fields as UNKNOWN rather than substituting local Git evidence.
5. Do not run `git --version` or `gh --version` as a prerequisite in REMOTE_ONLY and do not claim local origin, branch, commit, clone, or root proof that the provider cannot observe.

LOCAL_ONLY
1. Run only the local Git/filesystem checks required for the selected source/publish preparation and preserve existing work.
2. Do not treat lack of GitHub credentials as permission to invent or claim a remote. End at the exact remote authorization/connection gate with the prepared local identity and collision-check requirement.

'''
content = content[:start] + replacement + content[end:]

old_verify = '''VERIFICATION
1. Run gh repo view xyz_owner/xyz_repo_name --json nameWithOwner,url,visibility,defaultBranchRef.
2. Run git remote get-url origin, git branch --show-current, git log --oneline --decorate -5, and git status --short from the verified new root.
3. Confirm owner/name, visibility, and origin exactly match the request.
4. When push was requested, confirm the remote branch contains the expected commit.
'''
new_verify = '''VERIFICATION BY EXECUTION SURFACE
1. BOTH with `gh`: run gh repo view xyz_owner/xyz_repo_name --json nameWithOwner,url,visibility,defaultBranchRef; from the verified local root run git remote get-url origin, git branch --show-current, git log --oneline --decorate -5, and git status --short; confirm owner/name, visibility, origin, and any requested pushed commit.
2. REMOTE_ONLY: use the provider read-back operation to verify the repository identity, URL, visibility, and exposed default-branch state. Report local root/origin/branch/commit as UNOBSERVABLE unless the provider independently exposes them; remote existence is not local clone proof.
3. LOCAL_ONLY: verify the prepared local root/history/status and expected future remote identity, but report REMOTE_CREATION=BLOCKED until provider authentication/authorization and collision lookup can run.
4. Never substitute one surface's proof for another. Report the strongest observed state and the exact next gate for every unobservable field.
'''
if old_verify not in content:
    raise SystemExit("P55 verification anchor changed; refusing blind repair")
content = content.replace(old_verify, new_verify, 1)
p["copyContent"] = content
p["proofGate"] = (
    "Relevant context and source assets are recovered before naming; compatible existing repository ownership is ruled in or out before creation; inferred metadata is evidence-backed and reversible; unresolved consequential identity choices are USER_ONLY; visibility never defaults to public; authentication/authorization and collision checks are proven through the selected execution surface without token exposure; REMOTE_ONLY provider/API execution is not blocked by unavailable local Git/gh probes; the authorized creation/adoption succeeds through the available GitHub surface; and remote/local claims match what was actually observed."
)
PROMPTS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

source = TESTS.read_text(encoding="utf-8")
anchor = '            "connected GitHub API/app",\n'
extra = '''            "EXECUTION SURFACE — RESOLVE BEFORE TOOL CHECKS",\n            "REMOTE_ONLY — PROVIDER/API",\n            "Do not run `git --version` or `gh --version` as a prerequisite in REMOTE_ONLY",\n            "CONFIRMED_NOT_FOUND",\n            "provider read-back operation",\n            "remote existence is not local clone proof",\n'''
if extra not in source:
    if anchor not in source:
        raise SystemExit("P55 focused assertion anchor changed; refusing blind repair")
    source = source.replace(anchor, anchor + extra, 1)
TESTS.write_text(source, encoding="utf-8")
print("P55 remote/API execution contract repaired")
