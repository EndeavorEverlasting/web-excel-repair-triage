from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "tutorial-discovery-prompts.v1.json"
GENERATED = ROOT / "web" / "prompt-kit" / "index.html"
LEGACY_CARRIER = ROOT / ".github" / "workflows" / "tmp-p65-legacy-marker-repair.yml"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def repair_marker() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p65 = next(p for p in payload["prompts"] if p.get("id") == "P65")
    if p65.get("name") != "Guided Prompt Finder Questionnaire":
        raise SystemExit(f"unexpected P65 identity: {p65.get('name')!r}")

    old = (
        "Use the AI Harness Prompt Kit prompt IDs and names below as the recommendation vocabulary. Run an adaptive, granular routing "
        "interview: ask one concise question at a time, wait for my answer, and choose the next question from the unresolved decision "
        "tree instead of marching through a fixed script."
    )
    new = (
        "Use the AI Harness Prompt Kit prompt IDs and names below as the recommendation vocabulary. Run an adaptive, granular routing "
        "interview. Ask one concise question at a time, wait for my answer, and choose the next question from the unresolved decision "
        "tree instead of marching through a fixed script."
    )
    if new not in p65["copyContent"]:
        if old not in p65["copyContent"]:
            raise SystemExit("P65 adaptive intro repair anchor missing")
        p65["copyContent"] = p65["copyContent"].replace(old, new, 1)

    required = (
        "ADAPTIVE ROUTING INTERVIEW",
        "GRANULAR GRILLING DISCIPLINE",
        "Facts are agent-owned; decisions are user-owned",
        "Desired prompt behavior:",
        "ROUTE CONFIDENCE GATE",
    )
    missing = [phrase for phrase in required if phrase not in p65["copyContent"]]
    if missing:
        raise SystemExit(f"granular P65 semantics regressed during repair: {missing}")

    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    repair_marker()
    if LEGACY_CARRIER.exists():
        LEGACY_CARRIER.unlink()

    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run(
        "python", "-m", "unittest",
        "tests.test_skill_prompt_registry.SkillPromptRegistryTests.test_guided_prompt_finder_is_bounded_and_registry_aware",
        "-v",
    )
    run("python", "-m", "unittest", "tests.test_skill_prompt_registry", "-v")
    run("python", "-m", "unittest", "tests.test_actionable_prompt_registry", "-v")
    run(
        "python", "-m", "unittest",
        "tests.test_prompt_kit_discovery.PromptKitDiscoveryTests.test_guided_finder_granularly_resolves_need_and_prompt_behavior",
        "-v",
    )
    run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "-v")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--summary")
    run("python", "scripts/evaluate_prompt_language.py", "--summary")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")

    run(
        "git", "add", "--",
        "registry/prompts/tutorial-discovery-prompts.v1.json",
        "web/prompt-kit/index.html",
        ".github/workflows/tmp-p65-legacy-marker-repair.yml",
    )
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    allowed = {
        "registry/prompts/tutorial-discovery-prompts.v1.json",
        "web/prompt-kit/index.html",
        ".github/workflows/tmp-p65-legacy-marker-repair.yml",
    }
    if not staged or not set(staged).issubset(allowed):
        raise SystemExit(f"unexpected P65 repair staged paths: {staged!r}")
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "fix(prompt-kit): preserve P65 concise-question marker")

    run(
        "python", "-m", "unittest",
        "tests.test_skill_prompt_registry.SkillPromptRegistryTests.test_guided_prompt_finder_is_bounded_and_registry_aware",
        "-v",
    )
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
