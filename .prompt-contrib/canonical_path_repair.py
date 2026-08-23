from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/prompt-kit-artifact-risk-path-20260822"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    return subprocess.run(list(args), cwd=ROOT, check=check, text=True)


def output(*args: str) -> str:
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
run("git", "fetch", "origin", "main", "--prune", "--tags")
print("CURRENT_MAIN=" + output("git", "rev-parse", "origin/main"), flush=True)
merge = run("git", "merge", "--no-commit", "--no-ff", "origin/main", check=False)
print(f"MERGE_RC={merge.returncode}", flush=True)

# This stale PR owned earlier prompt experiments. Rebase every canonical surface touched by
# this bounded P50 hardening from current main before applying the new semantics.
for path in (
    ".github/workflows/artifact-engines.yml",
    "docs/prompts.json",
    "tests/test_actionable_prompt_registry.py",
    "web/prompt-kit/index.html",
):
    run("git", "checkout", "origin/main", "--", path)

for path in (
    "registry/prompts/spec-architecture-prompts.v1.json",
    "registry/prompts/tutorial-discovery-prompts.v1.json",
):
    if subprocess.run(
        ["git", "cat-file", "-e", f"origin/main:{path}"], cwd=ROOT
    ).returncode == 0:
        run("git", "checkout", "origin/main", "--", path)

for path in (
    "tests/test_prompt_artifact_risk_path_prompts.py",
    "tests/test_prompt_canonical_path_contract.py",
):
    run("git", "rm", "-f", "--ignore-unmatch", path)

unmerged = output("git", "diff", "--name-only", "--diff-filter=U")
if unmerged:
    raise SystemExit(f"Unresolved merge paths remain:\n{unmerged}")

docs_path = ROOT / "docs/prompts.json"
docs = json.loads(docs_path.read_text(encoding="utf-8"))
p50 = next(prompt for prompt in docs if prompt["id"] == "P50")
identity = {
    key: p50[key]
    for key in ("id", "seq", "name", "type", "class", "color", "copySheet", "category")
}
before_chars = len(p50["copyContent"])
print(f"P50_RAW_COPY_CHARS_BEFORE={before_chars}", flush=True)

p50["sprintRole"] = (
    "Resolve, enter, and verify the intended local repository before task commands, executing the "
    "directory gate directly when tools permit and returning discovery commands only when access "
    "or proof is genuinely blocked"
)
p50["expectedOutput"] = (
    "One verified root; directory entry actually executed when agent access exists; immediate "
    "root/remote verification; branch or worktree evidence; and the first safe repository-backed "
    "task step executed from that root, or bounded discovery commands plus blocker evidence when "
    "execution access is unavailable."
)
p50["nextStep"] = (
    "After the directory gate passes, execute the first safe repository-backed step of the requested "
    "task from the verified root, then continue with P51, P52, or the task-specific canonical owner. "
    "Do not stop at printing location commands when current tools can run them."
)
p50["proofGate"] = (
    "The requested remote and active git top-level match; when shell or filesystem tools exist, the "
    "agent has entered and re-verified the root and advanced one safe requested-task step from it; "
    "discovery-only output is valid only when access, directory proof, or a genuinely user-only "
    "dependency blocks direct execution."
)
p50["copyContent"] = r'''PROMPT SURFACE: STANDARD AI. THIS IS NOT A GOODNIGHT, HAVE FUN (GNHF) PROMPT.

RESOLVE AND VERIFY THE LOCAL REPOSITORY BEFORE ANY TASK COMMAND. WHEN SHELL/FILESYSTEM ACCESS EXISTS, EXECUTE THE DIRECTORY GATE YOURSELF; DO NOT MAKE THE USER RUN AGENT-CAPABLE LOCATION COMMANDS.

Repository: xyz_repo_url_or_name
Known local path, if any: xyz_known_or_unknown
Requested task: xyz_task

DIRECTORY GATE
1. Do not assume the current directory, remembered path, repository name, Desktop path, or newest checkout is correct.
2. Resolve the intended checkout by matching candidate remotes to the requested repository and inspecting `git worktree list` when available.
3. When access exists, enter the evidence-backed root, then immediately run `git rev-parse --show-toplevel` and `git remote get-url origin`. Do not merely print directory or verification commands; a plausible path is not proof.
4. If candidates remain ambiguous, exhaust current directory, remote, worktree, and operator-supplied evidence before asking for a genuinely user-only fact.
5. If root proof or local access is unavailable, return bounded discovery commands only. Do not return tests, builds, mutations, commits, cleanup, or deployment commands from a guessed root.
6. Once proved, execute the first safe repository-backed step that advances `xyz_task`; broader work belongs to P51, P52, or the task-specific owner.
7. Re-verify the active root when shell, host, worktree, or execution context changes.

HARNESS CONTEXT
Name repo, branch or worktree, PR or sprint, lane, owned scope, forbidden scope, expected artifacts, validation order, proof level, and proof ceiling.
Search existing contracts, helpers, validators, scripts, manifests, and output patterns before inventing.

FINAL RESPONSE
Report root evidence, directory action executed, root/remote verification, branch or worktree state, and the first requested-task result. If execution was blocked, return bounded discovery commands plus the blocker and intended proof.'''

for key, value in identity.items():
    if p50[key] != value:
        raise SystemExit(f"P50 identity drifted: {key}: {value!r} -> {p50[key]!r}")

after_chars = len(p50["copyContent"])
delta = after_chars - before_chars
print(f"P50_RAW_COPY_CHARS_AFTER={after_chars}", flush=True)
print(f"P50_RAW_COPY_CHAR_DELTA={delta:+d}", flush=True)
if after_chars > 2200 or delta > 700:
    raise SystemExit(
        f"P50 anti-bloat gate failed: before={before_chars} after={after_chars} delta={delta:+d}"
    )
docs_path.write_text(json.dumps(docs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_path = ROOT / "tests/test_actionable_prompt_registry.py"
test_text = test_path.read_text(encoding="utf-8")
marker = "    def test_p50_executes_directory_gate_without_absorbing_p07(self) -> None:\n"
if marker not in test_text:
    anchor = "    def test_policy_rejects_an_empty_next_step(self) -> None:\n"
    if anchor not in test_text:
        raise SystemExit("Focused test insertion anchor missing")
    method = '''    def test_p50_executes_directory_gate_without_absorbing_p07(self) -> None:
        raw_prompts = json.loads(
            (REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8")
        )
        raw_p50 = next(prompt for prompt in raw_prompts if prompt["id"] == "P50")
        effective_p50 = {prompt["id"]: prompt for prompt in self.prompts}["P50"]

        self.assertEqual(raw_p50["name"], "Directory-First Repository Command Guard")
        self.assertEqual(raw_p50["type"], "ANALYZE + DIRECTORY")
        self.assertEqual(raw_p50["class"], "STANDARD AI / LOCAL-FIRST REPOSITORY INTAKE")
        self.assertEqual(raw_p50["copySheet"], "P50_COPY_SAFE")
        self.assertEqual(raw_p50["category"], "standard")

        for phrase in (
            "EXECUTE THE DIRECTORY GATE YOURSELF",
            "Do not merely print directory or verification commands",
            "execute the first safe repository-backed step that advances `xyz_task`",
            "asking for a genuinely user-only fact",
            "a plausible path is not proof",
        ):
            self.assertIn(phrase, raw_p50["copyContent"])

        self.assertNotIn(self.policy["marker"], raw_p50["copyContent"])
        self.assertIn(self.policy["marker"], effective_p50["copyContent"])
        for donor_role in (
            "ITERATIVE SPRINT FIXED-POINT",
            "MAINLINE CONVERGENCE",
            "merge the exact validated head",
        ):
            self.assertNotIn(donor_role, raw_p50["copyContent"])
        self.assertLessEqual(len(raw_p50["copyContent"]), 2200)

'''
    test_text = test_text.replace(anchor, method + anchor, 1)
    test_path.write_text(test_text, encoding="utf-8")

run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
run("python", "scripts/prompt_registry_ops.py", "validate")
run("python", "-m", "unittest", "tests.test_actionable_prompt_registry", "-v")
run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "-v")
run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
run("python", "scripts/validate_prompt_kit_order_navigation.py", "--summary")
run("python", "scripts/evaluate_prompt_language.py", "--summary")
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
run("git", "diff", "--check")

# Remove temporary proof machinery and restore the base-owned workflow before committing the
# exact tree that was just validated.
run("git", "checkout", "origin/main", "--", ".github/workflows/prompt-freshness-evidence.yml")
for path in (
    ".github/workflows/tmp-canonical-local-path-20260822.yml",
    ".prompt-contrib/tmp-canonical-path-trigger.txt",
    ".prompt-contrib/canonical_path_repair.py",
):
    run("git", "rm", "-f", "--ignore-unmatch", path)

run("git", "add", "docs/prompts.json", "tests/test_actionable_prompt_registry.py", "web/prompt-kit/index.html")
run("git", "add", "-u")
run("git", "diff", "--cached", "--check")
print("FINAL_STAGED_STATUS_BEGIN", flush=True)
run("git", "status", "--short")
print("FINAL_STAGED_STATUS_END", flush=True)
run("git", "commit", "-m", "feat(prompt-kit): make P50 directory guard agent-actionable")
validated_head = output("git", "rev-parse", "HEAD")
print("VALIDATED_HEAD=" + validated_head, flush=True)
run("git", "push", "origin", f"HEAD:{BRANCH}")
print("PUSHED_VALIDATED_HEAD=" + validated_head, flush=True)
