from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
FOCUSED_TEST = ROOT / "tests" / "test_prompt_registry_expansion_regression_design_teach.py"
GENERATED = ROOT / "web" / "prompt-kit" / "index.html"
TEMP_CARRIERS = (
    ROOT / ".github" / "workflows" / "tmp-p95-cohesive-context-repair.yml",
    ROOT / ".github" / "workflows" / "tmp-p95-cohesive-context-command.yml",
)


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def patch_p95() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [prompt for prompt in payload["prompts"] if prompt.get("id") == "P95"]
    if len(matches) != 1:
        raise SystemExit(f"expected one canonical P95, found {len(matches)}")
    p95 = matches[0]
    if p95.get("name") != "Program Design & Call-Stack Prototype Architect":
        raise SystemExit(f"unexpected P95 owner identity: {p95.get('name')!r}")

    inspect_clause = (
        " Do not infer whole-program architecture from one isolated file: acquire cohesive repository context "
        "covering the relevant tree, root manifests/configuration, entrypoints, state owners, composition/routing, "
        "tests, and dependency declarations before making repository-wide claims. If direct repository access is "
        "unavailable, use a bounded repo bundle or tree-plus-root-config fallback and state the resulting proof limit."
    )
    if "Do not infer whole-program architecture from one isolated file" not in p95["inspectFirst"]:
        p95["inspectFirst"] = p95["inspectFirst"].rstrip(".") + "." + inspect_clause

    section = (
        "\n\n1B. ACQUIRE COHESIVE REPOSITORY CONTEXT — NOT ONE ISOLATED FILE\n"
        "Before architecture conclusions, inspect the repository as a connected system. Prefer direct repository access "
        "and read the relevant file tree, root manifests/configuration, entrypoints, composition/routing, state owners, "
        "dependency declarations, tests, and persistence/external boundaries together. If direct repo access is unavailable, "
        "use a bounded repository bundle such as Repomix/code2prompt or a generated tree plus root configs and architecture/"
        "dependency maps. Exclude secrets, vendor/generated bulk, binaries, and unrelated paths. Do not treat a single pasted "
        "file as sufficient evidence for application-wide state, dependency, lifecycle, or configuration claims; narrow the "
        "claim explicitly when only partial context is available.\n"
    )
    marker = "\n\n2. BUILD A PRECISE DOMAIN VOCABULARY\n"
    if "1B. ACQUIRE COHESIVE REPOSITORY CONTEXT" not in p95["copyContent"]:
        if marker not in p95["copyContent"]:
            raise SystemExit("P95 insertion marker not found")
        p95["copyContent"] = p95["copyContent"].replace(marker, section + marker, 1)

    proof = (
        " Repository-wide architecture claims are grounded in cohesive repository context, or are explicitly "
        "limited when only partial context is available."
    )
    if "Repository-wide architecture claims are grounded in cohesive repository context" not in p95["proofGate"]:
        p95["proofGate"] = p95["proofGate"].rstrip(".") + "." + proof

    for keyword in ("whole repository context", "repository bundle", "repomix", "code2prompt"):
        if keyword not in p95["keywords"]:
            p95["keywords"].append(keyword)

    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_focused_regression() -> None:
    text = FOCUSED_TEST.read_text(encoding="utf-8")
    anchor = '            "Creativity is disciplined recombination",\n'
    additions = (
        '            "ACQUIRE COHESIVE REPOSITORY CONTEXT",\n'
        '            "Do not treat a single pasted file as sufficient evidence",\n'
        '            "Repomix/code2prompt",\n'
        '            "root manifests/configuration",\n'
    )
    if '"ACQUIRE COHESIVE REPOSITORY CONTEXT"' not in text:
        if anchor not in text:
            raise SystemExit("P95 focused-regression insertion anchor not found")
        text = text.replace(anchor, anchor + additions, 1)
    old_limit = '        self.assertLessEqual(len(raw["copyContent"]), 9300)\n'
    new_limit = '        self.assertLessEqual(len(raw["copyContent"]), 10000)\n'
    if old_limit in text:
        text = text.replace(old_limit, new_limit, 1)
    if new_limit not in text:
        raise SystemExit("P95 bounded-length regression limit not found after patch")
    FOCUSED_TEST.write_text(text, encoding="utf-8")


def falsify() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p95 = next(prompt for prompt in payload["prompts"] if prompt.get("id") == "P95")
    html = GENERATED.read_text(encoding="utf-8")
    required = {
        "canonical identity": p95["name"] == "Program Design & Call-Stack Prototype Architect",
        "cohesive context section": "1B. ACQUIRE COHESIVE REPOSITORY CONTEXT" in p95["copyContent"],
        "single-file rejection": "Do not treat a single pasted file as sufficient evidence" in p95["copyContent"],
        "bundle fallback": "Repomix/code2prompt" in p95["copyContent"],
        "partial-context ceiling": "narrow the claim explicitly when only partial context is available" in p95["copyContent"],
        "inspection gate": "Do not infer whole-program architecture from one isolated file" in p95["inspectFirst"],
        "proof owner": "Repository-wide architecture claims are grounded in cohesive repository context" in p95["proofGate"],
        "generated parity marker": "ACQUIRE COHESIVE REPOSITORY CONTEXT" in html,
    }
    failed = [label for label, ok in required.items() if not ok]
    if failed:
        raise SystemExit(f"P95 cohesive-context falsification failed: {failed}")
    print("P95 cohesive-context falsification: PASS", flush=True)


def main() -> None:
    print("P95 contribution executor: canonical-owner strengthening only; no new prompt identity", flush=True)
    patch_p95()
    patch_focused_regression()
    for path in TEMP_CARRIERS:
        if path.exists():
            path.unlink()

    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "-m", "unittest", "tests.test_prompt_registry_expansion_regression_design_teach", "-v")
    run("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "-v")
    run("python", "-m", "unittest", "tests.test_actionable_prompt_registry", "-v")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--summary")
    run("python", "scripts/evaluate_prompt_language.py", "--summary")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")
    falsify()

    durable = [
        "registry/prompts/spec-architecture-prompts.v1.json",
        "tests/test_prompt_registry_expansion_regression_design_teach.py",
        "web/prompt-kit/index.html",
        ".github/workflows/tmp-p95-cohesive-context-repair.yml",
        ".github/workflows/tmp-p95-cohesive-context-command.yml",
    ]
    run("git", "add", "--all", "--", *durable)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    expected = {p for p in durable if (ROOT / p).exists() or p in staged}
    if set(staged) != expected:
        raise SystemExit(f"unexpected durable staged paths: staged={staged!r} expected={sorted(expected)!r}")
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "feat(prompt-kit): ground P95 in cohesive repo context")

    run("python", "-m", "unittest", "tests.test_prompt_registry_expansion_regression_design_teach", "-v")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")
    falsify()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("working tree not clean after durable P95 commit")
    print("P95 durable contribution committed and clean; carrier cleanup may proceed", flush=True)


if __name__ == "__main__":
    main()
