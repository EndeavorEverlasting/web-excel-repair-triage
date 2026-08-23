from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/prompt-kit-artifact-risk-path-20260822"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        check=check,
        text=True,
    )


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
run("git", "fetch", "origin", "main", "--prune", "--tags")
print("CURRENT_MAIN=" + subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip())
merge = run("git", "merge", "--no-commit", "--no-ff", "origin/main", check=False)
print(f"merge_rc={merge.returncode}")

# The stale PR owned these paths on an obsolete floor. Rebase their content semantically
# from current main before applying the bounded canonical-path contribution.
for path in (
    ".github/workflows/artifact-engines.yml",
    "docs/prompts.json",
    "registry/prompts/spec-architecture-prompts.v1.json",
    "registry/prompts/tutorial-discovery-prompts.v1.json",
    "web/prompt-kit/index.html",
):
    run("git", "checkout", "origin/main", "--", path)

for path in (
    "tests/test_prompt_artifact_risk_path_prompts.py",
    ".github/workflows/tmp-canonical-local-path-20260822.yml",
    ".prompt-contrib/tmp-canonical-path-trigger.txt",
):
    run("git", "rm", "-f", "--ignore-unmatch", path)

unmerged = subprocess.check_output(
    ["git", "diff", "--name-only", "--diff-filter=U"], cwd=ROOT, text=True
).strip()
if unmerged:
    raise SystemExit(f"Unresolved merge paths remain:\n{unmerged}")

# P50: strengthen the existing exact owner. Do not create another prompt identity.
docs_path = ROOT / "docs/prompts.json"
docs = json.loads(docs_path.read_text(encoding="utf-8"))
by_id = {prompt["id"]: prompt for prompt in docs}
p50 = by_id["P50"]
p50["name"] = "Canonical Local Repository Path & Freshness Guard"
p50["type"] = "SETUP + ANALYZE + DIRECTORY"
p50["class"] = "STANDARD AI / CANONICAL LOCAL REPOSITORY INTAKE"
p50["sprintRole"] = (
    "Establish and reuse one canonical local checkout mapping per machine/execution profile, "
    "verify OS/shell/root/remote identity, and refresh remote truth before repository work"
)
p50["useWhen"] = (
    "The repository is known but agents may not know which box, operating system, shell, checkout, "
    "or worktree is canonical; a path is being guessed; multiple clones/worktrees exist; or local "
    "branch freshness is uncertain."
)
p50["inspectFirst"] = (
    "Existing machine/profile path owners and local config; Hooks/Glossary/CODEBASE_MAP/AGENTS/trigger "
    "surfaces; actual OS/platform and shell; current directory; Git worktrees; candidate remotes; "
    "branch/tracking/default-branch state; remote freshness; and any operator-supplied path."
)
p50["expectedOutput"] = (
    "One verified machine/execution-profile -> canonical repository-root mapping, one reused path "
    "authority, a lightweight discoverability pointer through an existing agent-facing route, "
    "root/remote/default-branch evidence, shell-correct entry commands, refreshed remote truth, "
    "and no duplicate checkout invented merely to continue work."
)
p50["nextStep"] = (
    "If no matching checkout exists, run P61 and return here to register/verify the new checkout. "
    "If path discoverability infrastructure is absent and repository setup mutation is authorized, "
    "use P87 or the existing harness owner to install the smallest pointer to this canonical contract. "
    "After root and freshness gates pass, continue with the task-specific prompt without creating "
    "another clone or path registry."
)
p50["proofGate"] = (
    "Exactly one canonical path authority is selected per machine/execution profile; the verified root "
    "matches the requested remote; OS/shell and worktree context are explicit; at least one existing "
    "Hooks/Glossary/CODEBASE_MAP/AGENTS/trigger front door points agents to the canonical path owner "
    "without duplicating absolute-path truth; git fetch --all --prune --tags refreshes reachable remote "
    "truth before branch-sensitive iteration; the actual remote default branch is resolved; clean "
    "behind-only state is fast-forwarded while dirty/diverged work is preserved; and no foreign-machine "
    "absolute path or unnecessary duplicate clone is treated as canonical."
)

p50["copyContent"] = r'''PROMPT SURFACE: STANDARD AI. THIS IS NOT A GOODNIGHT, HAVE FUN (GNHF) PROMPT.

ESTABLISH THE CANONICAL LOCAL REPOSITORY PATH AND FRESH REMOTE FLOOR BEFORE GIVING OR RUNNING REPOSITORY COMMANDS.

Repository: xyz_repo_url_or_name
Known local path, if any: xyz_known_or_unknown
Requested task: xyz_task

MISSION
Prevent path, machine, shell, worktree, duplicate-clone, and stale-checkout assumptions from contaminating later work. Treat the execution context as evidence that must be proved on the current box, then persist or reuse one authoritative local mapping so later agents can find the same repository without guessing.

CANONICAL LOCAL PATH CONTRACT
Canonical means ONE AUTHORITATIVE REPOSITORY ROOT PER MACHINE / EXECUTION PROFILE for routine work. It does not mean one universal absolute path string copied across Windows, Linux, macOS, WSL, containers, admin boxes, CI runners, or different usernames. A path that was correct on another box is evidence about that box only.

1. PATH AUTHORITY ORDER
- Reuse the repository's existing machine/profile path owner when one exists: machine profile, workspace manifest, local config, harness profile, environment contract, or equivalent. Do not create a second path registry because another representation is convenient.
- Validate the candidate checkout against the requested repository remote and `git rev-parse --show-toplevel`; inspect `git worktree list` when worktrees exist.
- If no approved mapping exists but a matching checkout can be proven, adopt that checkout as the canonical root for the current machine/profile instead of cloning another copy.
- If no matching checkout exists, route to P61 Existing Repository Clone + Working-Directory Bootstrapper. After P61 creates the checkout, return to P50 before task work.
- Remembered chat paths, Desktop guesses, drive letters, usernames, temp directories, newest-looking folders, and paths from another machine are never sufficient authority.

2. LOCAL PERSISTENCE / INDOCTRINATION
- Persist the absolute machine-specific root only through the repository's existing approved local/profile mechanism. Prefer an already-defined machine profile or ignored/local configuration surface.
- If no machine-local path owner exists and repository setup mutation is authorized, establish the smallest compatible local-only record plus a tracked schema/pointer or routing note. The tracked repository may define HOW to resolve the path; it must not publish one person's absolute path as universal cross-machine truth.
- Install or repair a lightweight discoverability pointer in an EXISTING front-door surface such as Hooks, Glossary, CODEBASE_MAP, AGENTS, trigger routing, or the repository's equivalent. The pointer routes `where is this repo?`, `wrong directory`, `which checkout?`, `which box?`, `stale checkout`, and `pull latest` intent to the canonical path owner/P50. Do not duplicate the path algorithm or absolute-path value into every hook and document.
- Reverse ownership must also be obvious: inspecting the local-path record or route must reveal which contract owns updates to it.

3. WORKSPACE / BLOAT GUARD
- Do not create a fresh clone merely because the agent cannot remember the existing path. Discover and verify first.
- Do not scatter repo copies across Desktop, Temp, home directories, alternate drives, containers, or sibling folders without an explicit isolated-worktree/clone reason.
- When isolation is required, prefer the repository's approved worktree mechanism or workspace root, record the purpose, and keep the canonical routine-work checkout authoritative.
- Do not let two agents silently treat different ordinary checkouts as the canonical writable root for the same machine/profile.

4. MACHINE / OS / SHELL GATE
- Resolve the actual execution environment before constructing commands: operating system/platform, active shell or command host, current directory, Git availability, and execution boundary (local, RDP/SSH target, WSL, container, CI, admin box).
- Distinguish Windows PowerShell, PowerShell 7+, CMD, Git Bash, WSL/Linux, macOS, and other materially different environments when present.
- Do not infer path separator, home directory, drive letter, username, quoting rules, executable names, privilege model, or `cd`/`Set-Location` syntax from prior chat context.
- If the environment changes mid-task, re-run the machine/profile and directory gates before continuing.

5. DIRECTORY GATE
- Do not assume the current directory, remembered path, repository name, Desktop path, or newest checkout is correct.
- Match candidate checkouts to the requested repository remote and inspect worktrees before selecting the routine-work root.
- Verify the selected root with `git rev-parse --show-toplevel` and `git remote get-url origin` or repository-equivalent evidence.
- If the root cannot be proved, perform bounded discovery only. Do not build, mutate, commit, clean, deploy, or certify from a guessed directory.
- After resolution, enter the verified root with syntax valid for the verified shell and verify it again before task commands.

6. REMOTE FRESHNESS IS PART OF PATH CORRECTNESS
A correct directory with stale remote truth is not a ready repository floor. After proving the root and before branch-sensitive analysis, implementation, build/repair, or certification:
- inspect status, HEAD, tracking branch, worktrees, and remotes;
- run `git fetch --all --prune --tags` when reachable;
- resolve the remote default branch from provider metadata or `refs/remotes/origin/HEAD` instead of assuming `main` or `master`;
- compare current HEAD, tracking branch, and refreshed default-branch floor; inspect overlapping work when relevant;
- fast-forward only a clean behind-only tracking branch with `git pull --ff-only` or repository-approved equivalent;
- preserve dirty, detached, diverged, or separately owned work and reconcile/isolate it instead of force-resetting;
- if freshness cannot be proved, state the exact proof ceiling and do not certify branch-sensitive work from remembered SHAs.

7. COMMAND / NEXT-COMMAND RULE
The first executable repository action must resolve or enter the canonical root using syntax valid for the verified shell, prove `git rev-parse --show-toplevel` and remote identity, then refresh remote truth. A generic snippet such as `git switch main && git pull` from an assumed current directory is not a valid canonical-path handoff. Later command blocks must either remain anchored in the verified root or explicitly re-enter and re-verify it.

8. HARNESS / ROUTING INTEGRATION
Name repo, execution profile, canonical root owner, branch/worktree, PR/sprint, lane, owned/forbidden scope, expected artifacts, validation order, proof level, and proof ceiling. Search existing contracts, helpers, validators, manifests, Hooks, Glossary, CODEBASE_MAP, AGENTS, trigger maps, and local profile mechanisms before inventing. If discoverability is missing and mutation is authorized, use the existing P87/harness owner to add the smallest pointer back to P50; do not create parallel path truth.

FAIL-CLOSED
If multiple plausible ordinary checkouts remain and machine/profile/repository evidence cannot determine the intended canonical root, do bounded discovery only. Escalate only the smallest genuinely user-only choice after exhausting machine/profile, remote, worktree, hook, and repository evidence.

FINAL RESPONSE
Return the verified execution profile, canonical path owner/mapping evidence, root/remote/default-branch freshness evidence, branch/worktree state, shell-correct directory-entry command, any discoverability pointer installed or reused, and then bounded task commands in execution order. Name any unproved path/environment/freshness assumption instead of guessing.'''
for keyword in (
    "canonical path",
    "canonical repo path",
    "local repository path",
    "wrong directory",
    "which checkout",
    "which box",
    "stale checkout",
    "pull latest",
    "remote freshness",
    "machine profile",
    "worktree",
):
    if keyword not in p50["keywords"]:
        p50["keywords"].append(keyword)

# P61: cloning is not path closure; hand the resulting checkout back to P50.
p61 = by_id["P61"]
handoff = r'''

CANONICAL PATH REGISTRATION HANDOFF
Creating or selecting a checkout is not closure. Before task-specific work, return to P50 Canonical Local Repository Path & Freshness Guard so the new root is verified against the remote, associated with the current machine/execution profile through the existing path authority, made discoverable through the repository's existing route surface when authorized, and refreshed against the actual remote default-branch floor. Do not leave an arbitrary clone as an undocumented new canonical location, and do not clone again when P50 can prove an existing checkout.
'''
if "CANONICAL PATH REGISTRATION HANDOFF" not in p61["copyContent"]:
    p61["copyContent"] = p61["copyContent"].rstrip() + handoff
p61["nextStep"] = (
    "After the checkout exists and its remote/root are verified, run P50 Canonical Local Repository "
    "Path & Freshness Guard to register/reuse the machine-profile mapping, establish discoverability, "
    "and refresh the remote floor before task-specific work."
)
p61["proofGate"] = p61["proofGate"].rstrip(". ") + (
    "; the resulting checkout is handed to P50 for canonical machine/profile registration and freshness "
    "proof rather than left as an undocumented arbitrary path."
)
for keyword in ("canonical path", "machine profile", "P50", "path registration"):
    if keyword not in p61["keywords"]:
        p61["keywords"].append(keyword)
write_json(docs_path, docs)

# P87: strengthen the existing route owner rather than creating another hook system.
spec_path = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
spec = json.loads(spec_path.read_text(encoding="utf-8"))
p87 = next(prompt for prompt in spec["prompts"] if prompt["id"] == "P87")
route_block = r'''

CANONICAL LOCAL PATH ROUTE CASE
Treat local repository location and freshness as a first-class bidirectional route, not incidental setup prose.
- Intent-first hooks for `where is this repo`, `wrong directory`, `local repo path`, `which checkout`, `which box`, `OS/shell path mismatch`, `stale checkout`, or `pull latest before work` route to P50 Canonical Local Repository Path & Freshness Guard.
- If P50 proves no checkout exists, route to P61 to create/select it, then return to P50 before task mutation.
- Install the route in the smallest EXISTING agent front door that users/agents already inspect: Hooks, Glossary, CODEBASE_MAP, AGENTS, trigger map, capability map, or repository-equivalent. Prefer a pointer over repeating the path algorithm.
- Implementation-first reverse lookup from the local path/profile record or hook must lead back to P50 as the semantic owner so future agents know where to repair path/freshness behavior.
- Do not create a second capabilities registry, path registry, or glossary merely to advertise this route.
'''
if "CANONICAL LOCAL PATH ROUTE CASE" not in p87["copyContent"]:
    p87["copyContent"] = p87["copyContent"].rstrip() + route_block
p87["proofGate"] = p87["proofGate"].rstrip(". ") + (
    "; canonical local-path/freshness intent is discoverable from an existing front door and reverse-routes "
    "to P50 without duplicating path truth."
)
for keyword in ("canonical path hook", "local repo path route", "P50 path owner", "stale checkout route"):
    if keyword not in p87["keywords"]:
        p87["keywords"].append(keyword)
write_json(spec_path, spec)

# P65: make P50 directly discoverable from the Prompt Finder.
tutorial_path = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"
tutorial = json.loads(tutorial_path.read_text(encoding="utf-8"))
p65 = next(prompt for prompt in tutorial["prompts"] if prompt["id"] == "P65")
route = (
    "- P50 Canonical Local Repository Path & Freshness Guard: establish/reuse the machine-specific "
    "canonical checkout, verify OS/shell/root/remote identity, and fetch the current remote floor before "
    "repository work."
)
if route not in p65["copyContent"]:
    anchor = "PRIMARY ROUTING MAP\n"
    if anchor not in p65["copyContent"]:
        raise SystemExit("P65 routing anchor missing")
    p65["copyContent"] = p65["copyContent"].replace(anchor, anchor + route + "\n", 1)
for keyword in ("canonical path", "local repo path", "wrong directory", "stale checkout", "pull latest"):
    if keyword not in p65["keywords"]:
        p65["keywords"].append(keyword)
write_json(tutorial_path, tutorial)

# Focused semantic proof the generic registry helper cannot provide.
test_path = ROOT / "tests/test_prompt_canonical_path_contract.py"
test_path.write_text(
    '''from __future__ import annotations\n\nimport unittest\n\nfrom scripts import build_prompt_kit_registry\n\n\nclass CanonicalPathPromptContractTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls) -> None:\n        cls.prompts = build_prompt_kit_registry.load_prompt_kit_registry()\n        cls.by_id = {prompt["id"]: prompt for prompt in cls.prompts}\n\n    def test_p50_is_single_canonical_local_path_owner(self) -> None:\n        p50 = self.by_id["P50"]\n        self.assertEqual(p50["name"], "Canonical Local Repository Path & Freshness Guard")\n        self.assertEqual(p50["copySheet"], "P50_COPY_SAFE")\n        content = p50["copyContent"]\n        for phrase in (\n            "CANONICAL LOCAL PATH CONTRACT",\n            "ONE AUTHORITATIVE REPOSITORY ROOT PER MACHINE / EXECUTION PROFILE",\n            "LOCAL PERSISTENCE / INDOCTRINATION",\n            "WORKSPACE / BLOAT GUARD",\n            "MACHINE / OS / SHELL GATE",\n            "REMOTE FRESHNESS IS PART OF PATH CORRECTNESS",\n            "git fetch --all --prune --tags",\n            "refs/remotes/origin/HEAD",\n            "git pull --ff-only",\n            "Hooks, Glossary, CODEBASE_MAP, AGENTS",\n            "generic snippet such as `git switch main && git pull`",\n            "Do not create a fresh clone merely because the agent cannot remember the existing path",\n        ):\n            self.assertIn(phrase, content)\n        self.assertEqual([p["id"] for p in self.prompts if p["name"] == p50["name"]], ["P50"])\n\n    def test_p61_returns_new_checkout_to_p50_instead_of_stranding_a_path(self) -> None:\n        p61 = self.by_id["P61"]\n        self.assertEqual(p61["name"], "Existing Repository Clone + Working-Directory Bootstrapper")\n        self.assertIn("CANONICAL PATH REGISTRATION HANDOFF", p61["copyContent"])\n        self.assertIn("P50 Canonical Local Repository Path & Freshness Guard", p61["copyContent"])\n        self.assertIn("machine-profile mapping", p61["nextStep"])\n\n    def test_p87_installs_bidirectional_path_hook_without_second_registry(self) -> None:\n        p87 = self.by_id["P87"]\n        self.assertEqual(p87["name"], "Bidirectional Use-Case Hook & Repository Route Builder")\n        content = p87["copyContent"]\n        for phrase in (\n            "CANONICAL LOCAL PATH ROUTE CASE",\n            "route to P50 Canonical Local Repository Path & Freshness Guard",\n            "Hooks, Glossary, CODEBASE_MAP, AGENTS",\n            "reverse lookup",\n            "Do not create a second capabilities registry, path registry, or glossary",\n        ):\n            self.assertIn(phrase, content)\n\n    def test_p65_prompt_finder_exposes_canonical_path_owner(self) -> None:\n        self.assertIn(\n            "P50 Canonical Local Repository Path & Freshness Guard: establish/reuse the machine-specific canonical checkout",\n            self.by_id["P65"]["copyContent"],\n        )\n\n    def test_prompt_count_and_generated_site_remain_connected(self) -> None:\n        self.assertEqual(len(self.prompts), 100)\n        html = build_prompt_kit_registry.render()\n        self.assertIn("Canonical Local Repository Path &amp; Freshness Guard", html)\n        self.assertIn("CANONICAL LOCAL PATH CONTRACT", html)\n        self.assertIn("CANONICAL LOCAL PATH ROUTE CASE", html)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
    encoding="utf-8",
)

run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
run("python", "scripts/prompt_registry_ops.py", "validate")
run("python", "-m", "unittest", "tests.test_prompt_canonical_path_contract", "-v")
run("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "-v")
run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "-v")
run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
run("python", "scripts/validate_prompt_kit_order_navigation.py", "--summary")
run("python", "scripts/evaluate_prompt_language.py", "--summary")
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
run("git", "diff", "--check")

# The executor is transport, not durable product state.
run("git", "rm", "-f", "--ignore-unmatch", ".prompt-contrib/canonical_path_repair.py")
run("git", "add", "docs/prompts.json")
run("git", "add", "registry/prompts/spec-architecture-prompts.v1.json")
run("git", "add", "registry/prompts/tutorial-discovery-prompts.v1.json")
run("git", "add", "tests/test_prompt_canonical_path_contract.py")
run("git", "add", "web/prompt-kit/index.html")
run("git", "add", "-u")
run("git", "diff", "--cached", "--check")
run("git", "commit", "-m", "feat(prompt-kit): codify canonical local repository path")
run("git", "push", "origin", f"HEAD:{BRANCH}")
