#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/prompt-kit-artifact-risk-path-20260822"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def patch_p50() -> None:
    path = ROOT / "docs" / "prompts.json"
    prompts = json.loads(path.read_text(encoding="utf-8"))
    p50 = next(prompt for prompt in prompts if prompt.get("id") == "P50")
    marker = "\n\nACTIONABLE NEXT COMMAND AND NEXT STEPS CONTRACT"
    if marker not in p50["copyContent"]:
        raise RuntimeError("P50 shared-policy boundary not found")
    suffix = marker + p50["copyContent"].split(marker, 1)[1]
    prefix = '''PROMPT SURFACE: STANDARD AI. THIS IS NOT A GOODNIGHT, HAVE FUN (GNHF) PROMPT.

ESTABLISH THE MACHINE, SHELL, LOCAL REPOSITORY ROOT, AND REMOTE FRESHNESS BEFORE GIVING OR RUNNING REPOSITORY COMMANDS.

Repository: xyz_repo_url_or_name
Known local path, if any: xyz_known_or_unknown
Requested task: xyz_task

MISSION
Prevent path, shell, platform, worktree, and stale-checkout assumptions from contaminating later work. Treat execution context as evidence that must be proved on the current box, not remembered from another machine, username, operating system, terminal, or prior chat.

MACHINE / OS / SHELL GATE
1. Resolve the actual execution environment before constructing commands: operating system/platform, active shell or command host, current directory, and Git availability. Distinguish Windows PowerShell, PowerShell 7+, CMD, Git Bash, WSL/Linux, macOS, and other materially different environments when present.
2. Do not infer OS, shell, path separator, home directory, drive letter, username, quoting rules, executable names, or privilege model from the repository name, a previous machine, or remembered context.
3. Emit commands in the syntax of the verified shell. Do not hand Bash syntax to PowerShell/CMD, Windows paths to a Linux/WSL context, or shell-specific quoting to the wrong host.
4. If the environment changes mid-task (new terminal, SSH/RDP target, container, WSL boundary, admin box, CI runner), re-run the environment and directory gates before continuing.

DIRECTORY GATE
1. Do not assume the current directory, remembered path, repository name, Desktop path, or newest checkout is correct.
2. Resolve the intended checkout by matching its remote to the requested repository and inspecting git worktree list when available.
3. When the root is reachable, verify it with git rev-parse --show-toplevel and git remote get-url origin.
4. When no matching checkout exists, route to P61 Existing Repository Clone + Working-Directory Bootstrapper rather than inventing a path.
5. When a root cannot yet be proven, return or run bounded discovery only. Do not start tests, builds, mutations, commits, cleanup, or deployment against an unverified directory.
6. After resolution, make the first executable task command Set-Location -LiteralPath "<verified-root>" in PowerShell or cd -- "<verified-root>" in Bash, then verify git rev-parse --show-toplevel again.

REMOTE FRESHNESS GATE
1. After the root is proven and before branch-sensitive analysis or iteration, inspect git status, branch, tracking branch, worktrees, and remotes.
2. Refresh remote truth with git fetch --all --prune --tags when the remote is reachable. Resolve the actual remote default branch from provider metadata or refs/remotes/origin/HEAD; do not assume main/master or reuse a remembered SHA.
3. Compare current HEAD, its tracking branch, and the refreshed default-branch floor. Inspect open/recent overlapping branches or PRs when the task could collide with them.
4. If a clean tracking branch is behind-only, use git pull --ff-only or the repository-approved equivalent. If dirty, diverged, detached, or separately owned work exists, preserve it and reconcile or isolate with a worktree; never force-reset merely to become current.
5. If remote freshness cannot be proved, state the exact limitation. Do not silently perform branch-sensitive mutation, build/repair decisions, or certification from a stale assumed floor.

COMMAND EMISSION GATE
- Every later command block must be valid for the verified OS/shell and begin from, or explicitly enter, the verified repository root.
- Prefer environment variables, repository-relative paths, manifests, and tracked launchers over person-specific absolute paths.
- Recheck root and shell before commands copied to another box or execution profile.
- Search existing contracts, helpers, validators, scripts, manifests, and output patterns before inventing replacements.

FINAL RESPONSE
Return the verified environment profile (OS/platform + shell), root evidence, root/remote/default-branch freshness evidence, branch/worktree state, the shell-correct directory-change command, and then the bounded task commands in execution order. Name any unproved environment or freshness assumption instead of guessing.'''
    p50.update(
        sprintRole="Resolve and verify the machine environment, local repository directory, shell, and remote freshness before emitting or executing repository commands",
        useWhen="The repository is known but the exact local checkout, operating system/shell context, worktree, or remote freshness is unknown, stale, or easy to confuse with another box or checkout.",
        inspectFirst="Repository URL or name; actual OS/platform and active shell; current directory; Git availability; Git worktrees; candidate remotes; branch/tracking/default-branch state; remote freshness; and any operator-supplied path.",
        expectedOutput="One verified execution profile (OS/platform + shell), one verified repository root, root/remote/default-branch evidence, reconciled freshness state, a shell-matched directory change, branch/worktree evidence, then bounded task commands.",
        nextStep="If no matching checkout exists, run P61. Otherwise continue to the task-specific prompt only after the environment, directory, and freshness gates pass; preserve dirty/diverged work instead of resetting it.",
        proofGate="The execution OS/platform and shell are explicitly resolved; the intended root is matched to the requested remote and git rev-parse --show-toplevel; remote refs/default branch are refreshed when reachable and compared with current/tracking HEAD; clean behind-only state is fast-forwarded or non-clean/diverged work is preserved and isolated/reconciled; and later commands use the verified shell and root rather than remembered machine paths.",
        keywords=["directory", "command guard", "directory first", "repo command", "repository path", "local repository", "local repo path", "working directory", "operating system", "os", "shell", "powershell", "cmd", "bash", "wsl", "worktree", "git fetch", "pull latest", "remote freshness", "stale checkout", "path problems"],
        copyContent=prefix + suffix,
    )
    path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_p97() -> None:
    draft = {
        "name": "Artifact Risk Review & Triage",
        "type": "ANALYZE + RISK",
        "class": "ANALYSIS / ARTIFACT RISK TRIAGE",
        "sprintRole": "Inspect supplied or generated artifacts before repair and surface the highest-signal correctness, integrity, provenance, usability, operational, and proof risks with evidence-backed triage",
        "useWhen": "The user has one or more files, screenshots, reports, manifests, generated outputs, documents, spreadsheets, logs, UI captures, or other artifacts and asks what stands out as risky, weak, inconsistent, stale, unsafe, or most worth investigating before deciding what to repair.",
        "inspectFirst": "The actual supplied artifacts and their readable content/metadata; the user's intended outcome or claimed use; artifact provenance/version/commit/generator/schema when available; related reference or accepted artifact when supplied; current validators/contracts; and surrounding context needed to distinguish a real observation from an inference.",
        "expectedOutput": "A prioritized artifact-risk ledger that separates OBSERVED, INFERRED, and UNKNOWN findings; cites the exact artifact evidence for each retained risk; explains consequence and confidence without fake precision; notes important counterevidence; identifies cross-artifact contradictions or provenance drift; and routes each actionable risk to the smallest next proof or repair owner.",
        "nextStep": "Execute the strongest safe next proof for the highest-priority evidence-backed risk, or route a discovered defect class to P91, a production-vs-test proof gap to P92, a closure-claim concern to P93, a regression-preservation concern to P94, or required artifact construction to the canonical builder such as P56. Do not mutate artifacts merely because analysis found a concern unless repair is requested or already in scope.",
        "proofGate": "Every reported risk is traceable to supplied/repository artifact evidence or explicitly labeled INFERRED/UNKNOWN; unreadable or missing content is never pretended to be inspected; risk priority reflects consequence plus evidence rather than unsupported scoring; at least one deliberate cross-artifact/provenance second pass checks contradictions, stale versions, omissions, and counterevidence; and the highest-priority actionable finding has an exact next proof/owner without collapsing into P91/P92/P93/P94 repair roles.",
        "copyContent": '''ANALYZE THE ARTIFACTS AND TELL ME WHAT STANDS OUT AS A RISK. DO NOT JUMP STRAIGHT INTO REPAIR OR INVENT PROBLEMS TO FILL A CHECKLIST.

Artifacts / source material: resolve from the current conversation, attached files, repository evidence, or named artifact paths.
Intended use or claim, if known: xyz_intended_use
Risk focus, if any: xyz_focus_or_general_review

MISSION
Inspect the actual artifacts first and identify the few risks that materially deserve attention. This is an evidence-led review, not a generic security scan and not a defect-repair sprint. Preserve the difference between what the artifact directly proves, what it reasonably suggests, and what remains unknown.

1. ESTABLISH THE ARTIFACT SET AND PROVENANCE
- Enumerate the artifacts actually available to inspect. Do not claim to have read missing, inaccessible, truncated, or image-only content that was not actually inspected.
- Record useful provenance when available: filename/path, artifact type, source vs generated output, timestamp/version, commit/build/generator/schema/profile, and any accepted reference supplied by the user or repository.
- If multiple artifacts belong to one workflow, identify their expected relationships before judging them independently.

2. PASS 1 — INSPECT EACH ARTIFACT FOR MATERIAL RISK
Apply only categories that fit the artifact. Look for evidence of correctness/internal-consistency defects; malformed, incomplete, corrupted, or structurally invalid content; stale versions, wrong inputs, generator/schema/profile drift, or source/output identity confusion; missing controls, proof, provenance, reconciliation, or acceptance evidence needed for the claimed use; unsafe, destructive, privacy/security, permission, or disclosure exposure visible in the material; operational/usability traps likely to make a real user choose the wrong path, misread state, lose work, or require hidden developer knowledge; and runtime/deployment assumptions contradicted by artifact or environment evidence. Do not turn taste, formatting preference, or speculative edge cases into material risk without a concrete consequence.

3. KEEP EVIDENCE STATES EXPLICIT
Classify every retained finding as OBSERVED (directly supported), INFERRED (reasonable risk with the inference named), or UNKNOWN (material proof is missing and the uncertainty matters). Never collapse UNKNOWN into PASS or describe an inference as an observed defect. Point to the smallest artifact region, field, screenshot feature, log line, manifest entry, or repository path supporting the finding.

4. PRIORITIZE WITHOUT FAKE PRECISION
For each retained risk record: risk ID; state; affected artifact; evidence; likely consequence; confidence; priority only when justified; and the smallest next proof or owner. Prefer a short ranked set of material risks over a long undifferentiated checklist. State important counterevidence or controls that reduce a risk.

5. PASS 2 — CROSS-ARTIFACT / PROVENANCE REVIEW
Review the set again from the opposite direction. Compare artifacts with each other and any declared contract/reference. Look for contradictions, stale generated output, mismatched versions or identities, omissions between source and derivative artifacts, metadata/timestamp drift, unsupported completion claims, and risks that disappear when counterevidence is considered. Promote, downgrade, merge, or remove findings based on this second pass.

6. ROUTE RATHER THAN ABSORB DOWNSTREAM WORK
Concrete defect that may represent a wider failure class -> P91 Failure-Class Generalization & Repository Audit. Tests/evidence may bypass the shipped/user path -> P92 Production-Path Proof Gap Auditor. Someone is claiming the use case is done/closed -> P93 Use-Case Closure Certification. A change may break previously accepted behavior -> P94 Regression Test & Live Behavior Guard. A new/rebuilt artifact is actually required -> use the canonical artifact builder/producer, such as P56 when appropriate. Keep this prompt focused on finding and triaging risk. If repair is explicitly in scope, hand the evidence ledger to the correct repair owner and continue there rather than silently broadening this prompt.

7. USER-ONLY GATE
Inspect files, screenshots, repository artifacts, metadata, validators, and references yourself when accessible. Do not ask the user to become the file reader or test runner. Ask only for a genuinely missing artifact, password/protected access, physical observation, or product preference that materially changes the risk judgment and cannot be resolved from current evidence.

DELIVER
Start with the highest-priority risks and why they matter. Then give the compact risk ledger, important counterevidence, unknowns/proof ceiling, and the exact next proof or downstream owner for the top actionable item. If no material risk is supported, say that clearly and state what was actually inspected rather than manufacturing findings.''',
        "keywords": ["artifact risk", "analyze artifacts", "artifact review", "risk review", "what stands out", "artifact audit", "artifact triage", "artifact weakness", "generated output risk", "cross artifact", "provenance drift", "stale artifact", "artifact inconsistency"],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(draft, handle, ensure_ascii=False, indent=2)
        draft_path = handle.name
    run(sys.executable, "scripts/prompt_registry_ops.py", "add", "--input", draft_path, "--registry", "spec-architecture-prompts")


def write_focused_test() -> None:
    test = ROOT / "tests" / "test_prompt_artifact_risk_path_prompts.py"
    test.write_text('''from __future__ import annotations
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_prompt_kit_registry

class PromptArtifactRiskPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = build_prompt_kit_registry.load_prompt_registry()
        cls.by_id = {p["id"]: p for p in cls.prompts}
    def test_p50_machine_shell_path_and_freshness(self):
        p=self.by_id["P50"]; c=p["copyContent"]
        self.assertEqual(p["name"], "Directory-First Repository Command Guard")
        self.assertEqual(p["copySheet"], "P50_COPY_SAFE")
        for m in ("MACHINE / OS / SHELL GATE","REMOTE FRESHNESS GATE","COMMAND EMISSION GATE","Windows PowerShell, PowerShell 7+, CMD, Git Bash, WSL/Linux, macOS","git fetch --all --prune --tags","refs/remotes/origin/HEAD","git pull --ff-only","P61 Existing Repository Clone + Working-Directory Bootstrapper","Do not infer OS, shell, path separator"):
            self.assertIn(m,c)
        self.assertIn("operating system",p["useWhen"].lower()); self.assertIn("shell",p["proofGate"].lower()); self.assertIn("remote",p["proofGate"].lower())
    def test_p97_bounded_artifact_risk_analysis(self):
        matches=[p for p in self.prompts if p["name"]=="Artifact Risk Review & Triage"]
        self.assertEqual(len(matches),1); p=matches[0]
        self.assertEqual((p["id"],p["seq"],p["copySheet"]),("P97","97","P97_COPY_SAFE"))
        self.assertEqual(p["class"],"ANALYSIS / ARTIFACT RISK TRIAGE")
        for m in ("OBSERVED","INFERRED","UNKNOWN","PASS 2 — CROSS-ARTIFACT / PROVENANCE REVIEW","DO NOT JUMP STRAIGHT INTO REPAIR","P91 Failure-Class Generalization & Repository Audit","P92 Production-Path Proof Gap Auditor","P93 Use-Case Closure Certification","P94 Regression Test & Live Behavior Guard","If no material risk is supported"):
            self.assertIn(m,p["copyContent"])
        self.assertIn("real defect",self.by_id["P91"]["useWhen"].lower()); self.assertNotIn("real defect",p["useWhen"].lower())
    def test_raw_and_generated_parity(self):
        spec=json.loads((ROOT/"registry/prompts/spec-architecture-prompts.v1.json").read_text(encoding="utf-8"))
        raw=next(p for p in spec["prompts"] if p["id"]=="P97")
        self.assertGreaterEqual(len(raw["copyContent"]),3000); self.assertLessEqual(len(raw["copyContent"]),8000)
        site=(ROOT/"web/prompt-kit/index.html").read_text(encoding="utf-8")
        self.assertIn("Artifact Risk Review",site); self.assertIn("MACHINE / OS / SHELL GATE",site)
if __name__ == "__main__": unittest.main()
''', encoding="utf-8")


def validate() -> None:
    commands = [
        [sys.executable, "scripts/prompt_registry_ops.py", "validate"],
        [sys.executable, "-m", "unittest", "tests.test_prompt_artifact_risk_path_prompts", "-v"],
        [sys.executable, "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "tests.test_skill_prompt_registry", "-v"],
        [sys.executable, "-m", "unittest", "tests.test_prompt_kit_discovery", "tests.test_prompt_kit_guidance", "tests.test_prompt_language_audit", "-v"],
        [sys.executable, "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "tests.test_prompt_kit_order_navigation_product", "-v"],
        [sys.executable, "scripts/evaluate_prompt_language.py", "--output", "Outputs/prompt-language-audit.json", "--summary"],
        [sys.executable, "scripts/validate_prompt_kit_discovery.py", "--summary"],
        [sys.executable, "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--output", "Outputs/prompt-kit-order-navigation-audit.json", "--summary"],
        [sys.executable, "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        run(*command)


def commit_and_push() -> None:
    run("git", "config", "user.name", "EndeavorEverlasting")
    run("git", "config", "user.email", "71802818+EndeavorEverlasting@users.noreply.github.com")
    run("git", "add", "docs/prompts.json", "registry/prompts/spec-architecture-prompts.v1.json", "tests/test_prompt_artifact_risk_path_prompts.py", "web/prompt-kit/index.html")
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "feat(prompt-kit): harden repository context and artifact risk review")
    run("git", "push", "origin", f"HEAD:{BRANCH}")


def main() -> int:
    run("git", "fetch", "--all", "--prune", "--tags")
    run("git", "merge-base", "--is-ancestor", "origin/main", "HEAD")
    registry = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
    if '"id": "P97"' in registry.read_text(encoding="utf-8"):
        print("P97 already present; durable contribution already applied.")
        return 0
    patch_p50()
    add_p97()
    write_focused_test()
    validate()
    commit_and_push()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
