from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/p55-provider-neutral-repo-bootstrap-20260920"
EXPECTED_MAIN = "017702c738dc951cd694310e04b66dd3ebe61429"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def validate() -> None:
    commands = (
        (
            "python",
            "-m",
            "unittest",
            "tests.test_p55_repository_bootstrap",
            "tests.test_spec_architecture_prompt_registry",
            "tests.test_prompt_kit_discovery",
            "tests.test_skill_prompt_registry",
            "tests.test_actionable_prompt_registry",
            "tests.test_p02_continuity_regression_matrix",
            "-v",
        ),
        ("python", "scripts/prompt_registry_ops.py", "validate"),
        ("python", "scripts/evaluate_prompt_language.py", "--summary"),
        ("python", "scripts/validate_prompt_kit_discovery.py", "--summary"),
        ("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"),
        ("git", "diff", "--check"),
    )
    for command in commands:
        run(*command)


def main() -> None:
    run("git", "fetch", "--all", "--prune", "--tags")
    current_main = subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=ROOT, text=True
    ).strip()
    if current_main != EXPECTED_MAIN:
        raise SystemExit(
            f"main moved during P55 reconciliation: expected {EXPECTED_MAIN}, got {current_main}"
        )
    run("git", "merge-base", "--is-ancestor", EXPECTED_MAIN, "HEAD")

    run(
        "python",
        "scripts/build_prompt_kit_registry.py",
        "--output",
        "web/prompt-kit/index.html",
    )
    validate()

    run(
        "git",
        "rm",
        "-f",
        ".github/workflows/tmp-p55-current-main-reconcile.yml",
        ".github/p55-current-main-reconcile-trigger",
        "scripts/tmp_p55_current_main_reconcile.py",
    )
    run("git", "add", "web/prompt-kit/index.html")
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "fix(prompt-kit): regenerate P55 on current prompt builder")
    validate()
    run("git", "status", "--short")
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
