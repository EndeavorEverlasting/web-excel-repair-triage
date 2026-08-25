from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "tests" / "test_prompt_kit_discovery.py"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def patch_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    old = '''        self.assertNotIn("ask no more than four questions", content.lower())\n        self.assertIn("adaptive", p65["sprintRole"].lower())\n        self.assertIn("probe granularly", p65["useWhen"].lower())\n        self.assertIn("2-4 questions", p65["proofGate"])\n        self.assertIn("up to six", p65["proofGate"])\n        self.assertIn("desired prompt behavior", p65["proofGate"].lower())\n        self.assertIn("grill me", p65["keywords"])\n'''
    new = '''        question_pool = content.split("QUESTION POOL — ASK ONLY UNRESOLVED BRANCHES", 1)[1].split(\n            "GRANULAR GRILLING DISCIPLINE", 1\n        )[0]\n        grilling = content.split("GRANULAR GRILLING DISCIPLINE", 1)[1].split(\n            "ROUTE CONFIDENCE GATE", 1\n        )[0]\n        confidence = content.split("ROUTE CONFIDENCE GATE", 1)[1].split(\n            "PRIMARY ROUTING MAP", 1\n        )[0]\n\n        self.assertIn("2. User outcome:", question_pool)\n        self.assertIn("3. Desired prompt behavior:", question_pool)\n        self.assertIn("For each question, state your current read and recommended answer", grilling)\n        self.assertIn("After each answer, recompute the unresolved frontier", grilling)\n        self.assertIn("stop early as soon as one primary route", grilling)\n        self.assertIn("If a missing user-owned decision could change the primary prompt, ask it before routing", confidence)\n        self.assertIn("If remaining uncertainty would change only a follow-on detail, recommend the primary prompt now", confidence)\n        self.assertNotIn("ask no more than four questions", content.lower())\n        self.assertNotIn("marching through a fixed script", question_pool)\n        self.assertIn("adaptive", p65["sprintRole"].lower())\n        self.assertIn("probe granularly", p65["useWhen"].lower())\n        self.assertIn("recomputes only the unresolved routing frontier after each response", p65["proofGate"])\n        self.assertIn("2-4 questions", p65["proofGate"])\n        self.assertIn("up to six", p65["proofGate"])\n        self.assertIn("desired prompt behavior", p65["proofGate"].lower())\n        self.assertIn("grill me", p65["keywords"])\n'''
    if new not in text:
        if old not in text:
            raise SystemExit("P65 focused-test strengthening anchor missing")
        text = text.replace(old, new, 1)
    TEST.write_text(text, encoding="utf-8")


def main() -> None:
    patch_test()
    run(
        "python", "-m", "unittest",
        "tests.test_prompt_kit_discovery.PromptKitDiscoveryTests.test_guided_finder_granularly_resolves_need_and_prompt_behavior",
        "-v",
    )
    run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "-v")
    run("python", "-m", "unittest", "tests.test_skill_prompt_registry", "-v")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--summary")
    run("python", "scripts/evaluate_prompt_language.py", "--summary")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")
    run("git", "add", "--", "tests/test_prompt_kit_discovery.py")
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "test(prompt-kit): prove P65 adaptive decision semantics")
    run(
        "python", "-m", "unittest",
        "tests.test_prompt_kit_discovery.PromptKitDiscoveryTests.test_guided_finder_granularly_resolves_need_and_prompt_behavior",
        "-v",
    )
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")


if __name__ == "__main__":
    main()
