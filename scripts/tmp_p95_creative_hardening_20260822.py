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

    p95["sprintRole"] = (
        "Design the program between governance/harness and implementation by widening the solution space, "
        "defining domain seams, state/data ownership, interfaces, failure contracts, and executable call-stack "
        "prototypes for the highest-value user journeys"
    )
    p95["inspectFirst"] = append_once(
        p95["inspectFirst"],
        " When material design uncertainty remains, inspect a bounded set of relevant external repositories or structurally analogous systems for source-backed implementation mechanisms and alternative design ideas before locking the local seams.",
    )
    p95["expectedOutput"] = append_once(
        p95["expectedOutput"],
        " Where the design space is genuinely uncertain, include a small evidence-backed set of materially different candidate concepts, the external or cross-domain mechanisms that inspired them, and the local adaptations required before prototype evidence selects one.",
    )
    p95["nextStep"] = (
        "Choose the highest-risk user journey; when design uncertainty is material, run a bounded inspiration scan of relevant external repositories or structurally analogous systems, synthesize 2-4 materially different candidate mechanisms, then build the thinnest executable vertical prototype(s) through the strongest competing seams using real domain logic and stubbed external boundaries only. Inspect success/error traces and converge only after evidence selects the design."
    )
    p95["proofGate"] = append_once(
        p95["proofGate"],
        " When external inspiration is used, the transferred mechanism is tied to inspected source/tests/config rather than README popularity, local constraints and adaptations are explicit, and materially different alternatives are considered when uncertainty warrants them; P95 does not claim exhaustive ecosystem research that belongs to P97.",
    )

    content = p95["copyContent"]
    anchor = "\n\n2. BUILD A PRECISE DOMAIN VOCABULARY"
    section = """

1A. WIDEN THE DESIGN SPACE BEFORE CONVERGING
Do not default to the first familiar architecture. When the user's outcome leaves material design uncertainty, inspect a small set of relevant external repositories or structurally analogous systems before locking seams. Read enough source, tests, and configuration around the use case to understand the mechanism; README claims alone are inspiration, not proof. Extract transferable mechanisms — state ownership, interfaces, workflows, extension seams, failure handling, interaction patterns — rather than foreign directory layouts. Capture the reference identity when available, why the mechanism may transfer, and what local constraints require adaptation.

Synthesize 2-4 materially different candidate designs: preserve a simple local baseline and, when useful, include a reference-inspired option plus a non-obvious cross-domain or compositional option. Creativity is disciplined recombination in service of the user's use case, not novelty for its own sake. Prototype the strongest competing concepts against the same acceptance criteria. If external precedent becomes the main research task, route to P97 Open-Source Prior-Art & Gap Analyst instead of expanding P95 into an ecosystem survey. Verify license, dependency, security, and maintenance implications before direct code reuse.
"""
    if "1A. WIDEN THE DESIGN SPACE BEFORE CONVERGING" not in content:
        if content.count(anchor) != 1:
            raise RuntimeError(f"P95 section anchor mismatch: {content.count(anchor)}")
        content = content.replace(anchor, section + anchor, 1)

    critique_anchor = "- Would one likely future change touch too many unrelated modules?"
    critique_add = "- Did we converge on the first familiar pattern before testing a stronger reference-inspired or cross-domain alternative?"
    if critique_add not in content:
        if content.count(critique_anchor) != 1:
            raise RuntimeError("P95 critique anchor mismatch")
        content = content.replace(critique_anchor, critique_anchor + "\n" + critique_add, 1)

    deliver_anchor = "Report: user outcomes/invariants; domain vocabulary; program module/interface map; state/data owners; dependency direction; success and failure call stacks; executable prototypes created; alternatives compared; tests/traces; design changes made after prototype evidence; unresolved decisions; proof ceiling; exact implementation seam ready for the next build sprint."
    deliver_new = "Report: user outcomes/invariants; bounded inspiration sources and mechanisms when used; candidate concepts considered; domain vocabulary; program module/interface map; state/data owners; dependency direction; success and failure call stacks; executable prototypes created; alternatives compared; tests/traces; design changes made after prototype evidence; unresolved decisions; proof ceiling; exact implementation seam ready for the next build sprint."
    if deliver_new not in content:
        if content.count(deliver_anchor) != 1:
            raise RuntimeError("P95 deliver anchor mismatch")
        content = content.replace(deliver_anchor, deliver_new, 1)

    p95["copyContent"] = content
    for keyword in (
        "creative prototyping",
        "design exploration",
        "external repositories",
        "reference-inspired design",
        "cross-domain analogy",
        "creative architecture",
        "solution space",
    ):
        if keyword not in p95["keywords"]:
            p95["keywords"].append(keyword)

    after = len(content)
    if after <= before:
        raise RuntimeError("P95 did not materially strengthen")
    if after - before > 1800:
        raise RuntimeError(f"P95 grew too much: before={before} after={after}")
    if after > 9000:
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
        self.assertLessEqual(len(raw[\"copyContent\"]), 9000)

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
