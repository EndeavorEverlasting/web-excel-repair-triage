#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/prompt-kit-artifact-risk-path-20260822"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def patch_p50() -> None:
    path = ROOT / "docs" / "prompts.json"
    prompts = json.loads(path.read_text(encoding="utf-8"))
    p50 = next(p for p in prompts if p.get("id") == "P50")
    p50["nextStep"] = (
        "If no matching checkout exists, run P61. Otherwise, after the environment, directory, and freshness gates pass, "
        "use P51 for local tests, P52 for factoring analysis, or the task-specific prompt; preserve dirty/diverged work instead of resetting it."
    )
    old = (
        "- Prefer environment variables, repository-relative paths, manifests, and tracked launchers over person-specific absolute paths.\n"
        "- Recheck root and shell before commands copied to another box or execution profile."
    )
    new = (
        "- Prefer environment variables, repository-relative paths, manifests, and tracked launchers over person-specific absolute paths.\n"
        "- Verify the active repository root immediately before every later command block. Re-resolve the shell/host as well whenever execution moves to another box or execution profile."
    )
    if old not in p50["copyContent"]:
        raise RuntimeError("P50 command-emission preservation seam not found")
    p50["copyContent"] = p50["copyContent"].replace(old, new, 1)
    path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_test() -> None:
    path = ROOT / "tests" / "test_prompt_artifact_risk_path_prompts.py"
    text = path.read_text(encoding="utf-8")
    old = '"P61 Existing Repository Clone + Working-Directory Bootstrapper","Do not infer OS, shell, path separator"):'
    new = '"P61 Existing Repository Clone + Working-Directory Bootstrapper","Do not infer OS, shell, path separator","Verify the active repository root immediately before every later command block"):'
    if old not in text:
        raise RuntimeError("focused P50 marker tuple not found")
    text = text.replace(old, new, 1)
    old2 = 'self.assertIn("operating system",p["useWhen"].lower()); self.assertIn("shell",p["proofGate"].lower()); self.assertIn("remote",p["proofGate"].lower())'
    new2 = old2 + '; self.assertIn("P51",p["nextStep"]); self.assertIn("P52",p["nextStep"]); self.assertIn("P61",p["nextStep"])'
    if old2 not in text:
        raise RuntimeError("focused P50 metadata assertion not found")
    path.write_text(text.replace(old2, new2, 1), encoding="utf-8")


def main() -> int:
    run("git", "fetch", "--all", "--prune", "--tags")
    run("git", "merge-base", "--is-ancestor", "origin/main", "HEAD")
    patch_p50()
    patch_test()
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "-m", "unittest", "tests.test_prompt_artifact_risk_path_prompts", "-v")
    run("python", "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "tests.test_prompt_kit_order_navigation_product", "-v")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")
    run("git", "config", "user.name", "EndeavorEverlasting")
    run("git", "config", "user.email", "71802818+EndeavorEverlasting@users.noreply.github.com")
    run("git", "add", "docs/prompts.json", "tests/test_prompt_artifact_risk_path_prompts.py", "web/prompt-kit/index.html")
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "test(prompt-kit): preserve P50 routing and root proof")
    run("git", "push", "origin", f"HEAD:{BRANCH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
