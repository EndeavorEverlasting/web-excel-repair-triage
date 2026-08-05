#!/usr/bin/env python3
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs" / "prompts.json"
BUILDER = ROOT / "build_prompt_kit.py"

prompt = {
  "id": "P63",
  "seq": "63",
  "name": "Existing Repository Clone + Working-Directory Bootstrapper",
  "type": "BUILD + BOOTSTRAP",
  "class": "STANDARD AI / EXISTING REPOSITORY CLONE + DIRECTORY",
  "sprintRole": "Safely resolve or clone an existing repository, enter its verified root, and leave the terminal ready for the requested work",
  "progress": "Support",
  "useWhen": "The agent has been given a repository URL or owner/name but no proven local checkout, or the operator repeatedly needs the agent to clone the repository and place the terminal in the correct working directory before beginning work.",
  "inspectFirst": "The supplied repository URL or owner/name, current shell and working directory, existing local directories, Git availability, matching Git remotes, requested branch or ref, repository instructions, and any operator-provided preferred parent directory.",
  "expectedOutput": "A reused or newly cloned non-destructive checkout whose origin matches the requested repository, with the terminal set to the verified repository root and a report containing local path, origin, branch/ref, HEAD, status, clone-versus-reuse decision, and one exact next command.",
  "nextStep": "Run the requested repository task from the verified root; when the task itself is not yet specified, report the ready checkout and ask only for that task.",
  "proofGate": "The repository root is proven by git rev-parse, origin matches the requested repository, the active branch/ref and HEAD are reported, git status is captured, and the final working directory equals the verified root.",
  "color": "Ocean",
  "copySheet": "P63_COPY_SAFE",
  "category": "standard",
  "copyContent": "CLONE OR RESOLVE THE REQUESTED REPOSITORY AND SET THE TERMINAL TO ITS VERIFIED ROOT. DO NOT STOP AT INSTRUCTIONS OR GUESS A LOCAL PATH.\n\nINPUTS\n- Repository: xyz_repository_url_or_owner_name\n- Preferred local parent or destination: xyz_local_parent_or_destination_or_unknown\n- Branch/ref: xyz_branch_or_ref_or_default\n- Requested follow-on task: xyz_task_or_not_yet_supplied\n\nMISSION\nLeave this terminal inside the correct, verified checkout of the requested existing repository, ready to perform the follow-on task. Reuse a healthy matching checkout when one already exists; otherwise clone safely.\n\nNON-DESTRUCTIVE BOUNDARY\n- Do not delete, reset, clean, overwrite, rename, or move an existing directory to make room.\n- Do not force checkout, force-push, discard local changes, expose credentials, or rewrite repository history.\n- Do not assume a conventional path such as Desktop/dev, ~/src, or C:\\repos unless evidence or the operator establishes it.\n- Do not clone a duplicate merely because the current terminal is outside the repository.\n- Do not begin the follow-on task until repository identity and root are proven.\n\nPROCEDURE\n1. Identify the current shell, current directory, Git availability, requested repository identity, and any explicit branch/ref.\n2. Normalize repository identity for comparison without printing embedded credentials. Accept a full Git URL or owner/name.\n3. Inspect bounded likely locations only when the environment or operator has supplied them. Detect an existing checkout by reading its Git root and remotes; do not infer identity from directory name alone.\n4. If a healthy existing checkout has a remote matching the requested repository, reuse it. Preserve its current work and report any dirty state before doing anything else.\n5. If no matching checkout is proven and the exact clone parent/destination is unknown, ask one focused clarification: \"Which local parent directory should contain this repository?\" Do not guess and do not emit task commands yet.\n6. Before cloning, prove the chosen parent exists and inspect the intended child path. If the child path exists:\n   - reuse it only when it is a Git checkout whose remote matches the requested repository;\n   - otherwise stop with a collision report and request a different destination.\n7. Clone the existing repository non-destructively. Use the repository's default branch unless an explicit branch/ref was supplied. Do not add --depth, --single-branch, submodule recursion, or LFS behavior unless requested or required by tracked repository instructions.\n8. Enter the checkout using a shell-correct literal-path command:\n   - PowerShell: Set-Location -LiteralPath '<verified-root>'\n   - POSIX shell: cd -- '<verified-root>'\n9. Prove identity and state from inside the checkout:\n   - git rev-parse --show-toplevel\n   - git remote get-url origin\n   - git branch --show-current\n   - git rev-parse HEAD\n   - git status --short --branch\n10. Read the repository's governing instructions before performing the follow-on task. If the task was supplied and is authorized, proceed from this verified root. If no task was supplied, stop only after reporting the ready state.\n\nBRANCH/REF RULES\n- When no branch/ref is supplied, retain the clone's default checked-out branch.\n- When a branch name is explicitly supplied, verify it exists before switching or clone with that branch only when safe.\n- When a tag or commit is supplied, report detached-HEAD state explicitly and do not create a branch unless requested.\n- Never switch branches in a dirty reused checkout without first preserving and reporting its state.\n\nSUCCESS REPORT\n- repository requested\n- outcome: REUSED_EXISTING_CHECKOUT or CLONED_NEW_CHECKOUT\n- verified local root\n- origin URL with credentials redacted\n- active branch/ref\n- HEAD SHA\n- clean/dirty status\n- governing instruction files found\n- follow-on task status\n- one exact next command\n\nACTIONABLE NEXT COMMAND\nEnd with exactly one copy-paste-safe next command appropriate to the detected shell and current state. The command must run from, or explicitly enter, the verified repository root. Never use placeholders when the value was resolved. If a required value remains unknown, ask the single targeted clarification instead of inventing a command.",
  "keywords": [
    "clone repo", "clone repository", "existing repository", "git clone",
    "set terminal directory", "set working directory", "enter repo", "repository checkout",
    "local checkout", "working directory bootstrap", "resolve repository path", "cd repo"
  ]
}

items = json.loads(PROMPTS.read_text(encoding="utf-8"))
ids = [p["id"] for p in items]
if "P63" in ids:
    raise SystemExit("P63 already exists; refusing duplicate insertion")
if ids[-1] != "P62":
    raise SystemExit(f"Expected P62 as registry tail, found {ids[-1]}")
items.append(prompt)
PROMPTS.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

builder = BUILDER.read_text(encoding="utf-8")
needle = '    "directory": "P50", "command guard": "P50",\n'
replacement = needle + '    "clone repo": "P63", "clone repository": "P63", "git clone": "P63",\n    "set terminal directory": "P63", "set working directory": "P63", "repository checkout": "P63",\n'
if needle not in builder:
    raise SystemExit("Could not locate SYNONYMS insertion anchor")
builder = builder.replace(needle, replacement, 1)
builder = builder.replace("AI Harness Prompt Kit v39", "AI Harness Prompt Kit v40")
builder = builder.replace("Prompt Kit v39", "Prompt Kit v40")
BUILDER.write_text(builder, encoding="utf-8")

subprocess.run(["python", str(BUILDER)], cwd=ROOT, check=True)
subprocess.run(["python", str(BUILDER), "--output", "web/prompt-kit/index.html"], cwd=ROOT, check=True)

# Deterministic post-build checks.
items2 = json.loads(PROMPTS.read_text(encoding="utf-8"))
assert len({p["id"] for p in items2}) == len(items2)
assert items2[-1]["id"] == "P63"
for rel in ("docs/prompt-kit.html", "web/prompt-kit/index.html"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert '"id":"P63"' in text or '"id": "P63"' in text
    assert "Existing Repository Clone + Working-Directory Bootstrapper" in text
    assert "clone repo" in text
print("P63 registry, synonyms, and generated prompt-kit outputs validated")
