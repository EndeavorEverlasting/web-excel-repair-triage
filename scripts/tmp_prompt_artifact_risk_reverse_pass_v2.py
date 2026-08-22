#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tmp_prompt_artifact_risk_reverse_pass as base


def main() -> int:
    base.run("git", "fetch", "--all", "--prune", "--tags")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"],
        cwd=base.ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        base.run("git", "config", "user.name", "EndeavorEverlasting")
        base.run("git", "config", "user.email", "71802818+EndeavorEverlasting@users.noreply.github.com")
        base.run("git", "merge", "--no-edit", "origin/main")
    base.patch_p50()
    base.patch_test()
    base.run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    base.run("python", "scripts/prompt_registry_ops.py", "validate")
    base.run("python", "-m", "unittest", "tests.test_prompt_artifact_risk_path_prompts", "-v")
    base.run("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "tests.test_skill_prompt_registry", "-v")
    base.run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "tests.test_prompt_kit_guidance", "tests.test_prompt_language_audit", "-v")
    base.run("python", "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "tests.test_prompt_kit_order_navigation_product", "-v")
    base.run("python", "scripts/evaluate_prompt_language.py", "--output", "Outputs/prompt-language-audit.json", "--summary")
    base.run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    base.run("python", "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--output", "Outputs/prompt-kit-order-navigation-audit.json", "--summary")
    base.run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    base.run("git", "diff", "--check")
    base.run("git", "config", "user.name", "EndeavorEverlasting")
    base.run("git", "config", "user.email", "71802818+EndeavorEverlasting@users.noreply.github.com")
    base.run("git", "add", "docs/prompts.json", "tests/test_prompt_artifact_risk_path_prompts.py", "web/prompt-kit/index.html")
    base.run("git", "diff", "--cached", "--check")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=base.ROOT).returncode != 0:
        base.run("git", "commit", "-m", "test(prompt-kit): preserve P50 routing and root proof")
    base.run("git", "push", "origin", f"HEAD:{base.BRANCH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
