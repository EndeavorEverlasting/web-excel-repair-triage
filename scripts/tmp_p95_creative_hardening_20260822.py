#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_prompt_registry_expansion_regression_design_teach.py"
SITE = ROOT / "web" / "prompt-kit" / "index.html"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def append_once(value: str, addition: str) -> str:
    if addition in value:
        return value
    return value + addition


def main() -> int:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p95 = next(p for p in payload["prompts"] if p["id"] == "P95")
    if p95["name"] != "Program Design & Call-Stack Prototype Architect":
        raise RuntimeError("P95 identity drift")
    if p95["profile"] != "spec-architecture" or p95["color"] != "Cyan" or p95["category"] != "standard":
        raise RuntimeError("P95 ownership metadata drift")

    before = len(p95["copyContent"])
    print(json.dumps({"p95_raw_before": before}, indent=2), flush=True)

    p95["sprintRole"] = (
        "Design the program between governance/harness and implementation by widening the solution space, "
        "defining domain seams, state/data ownership, interfaces, failure contracts, and executable call-stack "
        "prototypes for the highest-value user journeys"
    )
    p95["inspectFirst"] = append_once(
        p95["inspectFirst"],
        " When design uncertainty is material, inspect a bounded set of relevant external repositories or structurally analogous systems for implementation mechanisms before locking local seams.",
    )
    p95["expectedOutput"] = append_once(
        p95["expectedOutput"],
        " When useful, include materially different candidate concepts and the local adaptations required before prototype evidence selects one.",
    )
    p95["nextStep"] = (
        "Choose the highest-risk user journey; when design uncertainty is material, scan a bounded set of relevant external repositories or structurally analogous systems, synthesize 2-4 materially different candidate mechanisms, then prototype the strongest competing seams with real domain logic. Inspect success/error traces and converge only after evidence selects the design."
    )
    p95["proofGate"] = append_once(
        p95["proofGate"],
        " External inspiration must be tied to inspected source/tests/config and locally adapted; exhaustive ecosystem research remains P97's job.",
    )

    content = p95["copyContent"]
    anchor = "\n\n2. BUILD A PRECISE DOMAIN VOCABULARY"
    section = """

1A. WIDEN THE DESIGN SPACE BEFORE CONVERGING
When design uncertainty is material, do not settle on the first familiar architecture. Inspect a small bounded set of relevant external repositories or structurally analogous systems when accessible. Prefer source/tests/config around the use case over README claims. Extract transferable mechanisms — ownership, interfaces, workflows, extension seams, failure handling, interaction patterns — not foreign file layouts.

Synthesize 2-4 materially different candidate designs: a simple local baseline plus, when useful, a reference-inspired and a cross-domain/compositional option. Creativity is disciplined recombination for the user's outcome, not novelty for its own sake. Compare candidates under the same acceptance criteria. Route broad ecosystem research to P97 Open-Source Prior-Art & Gap Analyst; verify license/security/dependency implications before direct reuse.
"""
    if "1A. WIDEN THE DESIGN SPACE BEFORE CONVERGING" not in content:
        if content.count(anchor) != 1:
            raise RuntimeError(f"P95 section anchor mismatch: {content.count(anchor)}")
        content = content.replace(anchor, section + anchor, 1)

    p95["copyContent"] = content
    for keyword in (
        "creative prototyping",
        "design exploration",
        "external repositories",
        "reference-inspired design",
        "cross-domain analogy",
        "solution space",
    ):
        if keyword not in p95["keywords"]:
            p95["keywords"].append(keyword)

    after = len(content)
    if after <= before:
        raise RuntimeError("P95 did not materially strengthen")
    if after - before > 850:
        raise RuntimeError(f"P95 grew too much: before={before} after={after}")
    if after > 9300:
        raise RuntimeError(f"P95 raw prompt exceeds anti-bloat ceiling: {after}")

    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    phrase_anchor = '            "semantic completion telemetry",\n'
    phrase_insert = (
        phrase_anchor
        + '            "WIDEN THE DESIGN SPACE BEFORE CONVERGING",\n'
        + '            "structurally analogous systems",\n'
        + '            "2-4 materially different candidate designs",\n'
        + '            "P97 Open-Source Prior-Art & Gap Analyst",\n'
        + '            "Creativity is disciplined recombination",\n'
    )
    if '"WIDEN THE DESIGN SPACE BEFORE CONVERGING"' not in test:
        if test.count(phrase_anchor) != 1:
            raise RuntimeError("focused test phrase anchor mismatch")
        test = test.replace(phrase_anchor, phrase_insert, 1)

    loop_anchor = "        ):\n            self.assertIn(phrase, content)\n\n    def test_teach_prompt_is_grounded_stateful_and_active"
    loop_new = """        ):
            self.assertIn(phrase, content)
        design = self.by_name[\"Program Design & Call-Stack Prototype Architect\"]
        self.assertEqual(design[\"id\"], \"P95\")
        self.assertEqual(design[\"profile\"], \"spec-architecture\")
        self.assertNotIn(\"BUILD THE SOLVED-BASELINE VS PRIORITIZED-GAP MAP\", content)
        raw_payload = json.loads((ROOT / \"registry/prompts/spec-architecture-prompts.v1.json\").read_text(encoding=\"utf-8\"))
        raw = next(p for p in raw_payload[\"prompts\"] if p[\"id\"] == \"P95\")
        self.assertLessEqual(len(raw[\"copyContent\"]), 9300)

    def test_teach_prompt_is_grounded_stateful_and_active"""
    if "self.assertNotIn(\"BUILD THE SOLVED-BASELINE VS PRIORITIZED-GAP MAP\", content)" not in test:
        if test.count(loop_anchor) != 1:
            raise RuntimeError(f"focused test loop anchor mismatch: {test.count(loop_anchor)}")
        test = test.replace(loop_anchor, loop_new, 1)

    TEST.write_text(test, encoding="utf-8")

    run("python", "scripts/build_prompt_kit_registry.py", "--output", str(SITE.relative_to(ROOT)))
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "-m", "unittest", "tests.test_prompt_registry_expansion_regression_design_teach", "-v")
    run("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "-v")
    run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "tests.test_prompt_kit_guidance", "tests.test_prompt_language_audit", "-v")
    run("python", "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "tests.test_prompt_kit_order_navigation_product", "-v")
    run("python", "scripts/evaluate_prompt_language.py", "--output", "Outputs/prompt-language-audit.json", "--summary")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--output", "Outputs/prompt-kit-order-navigation-audit.json", "--summary")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", str(SITE.relative_to(ROOT)), "--check")
    run("git", "diff", "--check")

    print(json.dumps({"p95_raw_before": before, "p95_raw_after": after, "growth": after - before}, indent=2))

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", str(REGISTRY.relative_to(ROOT)), str(TEST.relative_to(ROOT)), str(SITE.relative_to(ROOT)))
    run("git", "diff", "--cached", "--check")
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged.returncode == 0:
        print("No durable changes to commit")
        return 0
    run("git", "commit", "-m", "feat(prompt-kit): widen P95 creative design exploration")
    run("git", "push", "origin", "HEAD:feat/prompt-kit-flow-preference-telemetry-20260822")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
