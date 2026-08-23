#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import tmp_teach_workspace_contribution_20260822 as base

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"
FOCUSED = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save_registry(payload: dict) -> None:
    REGISTRY.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def expand_p96_from_complete_framework() -> None:
    payload = load_registry()
    p = next(
        item
        for item in payload["prompts"]
        if item["name"] == "Stateful Socratic Technical Tutor Workspace"
    )

    p["sprintRole"] = (
        "Turn a repository, technical system, or other structured skill into a persistent "
        "multi-session mastery workspace using grounded resources, first-principles decomposition, "
        "active retrieval, atomic practice, reusable visual lesson assets, and evidence-backed learning records"
    )
    p["useWhen"] = (
        "The user invokes `/teach <topic>`, `/teach recap`, or otherwise wants to genuinely learn "
        "a technical system, architecture, algorithm, repository, tool, workflow, or other structured "
        "skill rather than receive a passive guide, opaque calculation, or black-box implementation."
    )
    p["expectedOutput"] = (
        "A stateful `/teach` session centered on one testable invariant at a time: update the current "
        "mission, create or reuse one atomic lesson, ground explanations in repository/authoritative truth, "
        "end with exactly one conceptual trade-off/mechanism question plus one code diagnostic or edge-case "
        "exercise when code is applicable, wait for the learner response, and record mastery only after "
        "demonstrated retrieval/application; `/teach recap` rebuilds working memory from verified records "
        "with a brief roughly three-minute diagnostic."
    )
    p["nextStep"] = (
        "Read teaching state before explaining. For `/teach <topic>`, recover the mission/resources and prior "
        "records, teach one atomic frontier invariant, then stop at the checkpoint until the learner responds. "
        "For `/teach recap`, read verified records first, run a roughly three-minute refresher, and resume only "
        "at the first decayed or unmastered concept."
    )
    p["proofGate"] = (
        "The `.teach/` workspace is repository-local protocol state rather than an external package; a passive "
        "guide is not treated as mastery; factual teaching is grounded in RESOURCES.md/repository truth; teaching "
        "state is read before explanation; lessons stay atomic around one testable invariant; `/teach <topic>` "
        "updates MISSION.md and creates/reuses a numbered lesson; each lesson ends with exactly one conceptual "
        "trade-off/mechanism question plus one practical diagnostic/edge-case exercise appropriate to the skill; "
        "the tutor stops for the learner response; failed diagnostics lower or change scaffolding instead of "
        "revealing the solution; no final production implementation is supplied during teaching; learning records "
        "are written only after verification; and `/teach recap` reads persistent learning records before a short refresher."
    )
    keywords = list(p.get("keywords", []))
    for keyword in ("system understanding", "structured skill", "skill acquisition", "atomic lessons"):
        if keyword not in keywords:
            keywords.append(keyword)
    p["keywords"] = keywords

    c = p["copyContent"]
    mission_old = (
        "Help the learner build a durable mental model through first-principles decomposition, active retrieval, "
        "practical exercises, and persistent evidence of what has actually been understood. Treat teaching as a "
        "multi-session state machine rather than a one-shot explanation. Ground factual claims in repository truth "
        "and high-trust sources, preserve the learner's exact frontier, and adapt scaffolding when a concept is not yet secure."
    )
    mission_new = (
        mission_old
        + " A passive guide or opaque answer is not success: the learner must be able to reconstruct the mechanism, "
          "diagnose failure, and apply the invariant without cargo-culting the tutor's output."
    )
    if c.count(mission_old) != 1:
        raise SystemExit(f"P96 mission anchor mismatch: {c.count(mission_old)}")
    c = c.replace(mission_old, mission_new, 1)

    atomic_old = "Do not introduce five abstraction layers when one prerequisite is still unstable."
    atomic_new = (
        atomic_old
        + " Keep each lesson atomic around a single testable invariant so broad topics do not dilute context or hide which relation failed."
    )
    if c.count(atomic_old) != 1:
        raise SystemExit(f"P96 atomic anchor mismatch: {c.count(atomic_old)}")
    c = c.replace(atomic_old, atomic_new, 1)

    diagnostic_old = "Do not quiz trivia for ceremony. Use the result to choose the next atomic lesson."
    diagnostic_new = (
        diagnostic_old
        + " The diagnostic is a progression gate, not decoration: if the learner cannot explain the mechanism, lower the scaffolding one level before continuing."
    )
    if c.count(diagnostic_old) != 1:
        raise SystemExit(f"P96 diagnostic anchor mismatch: {c.count(diagnostic_old)}")
    c = c.replace(diagnostic_old, diagnostic_new, 1)

    tdl_old = "Do not write tests so broad that the learner can cargo-cult a giant solution."
    tdl_new = (
        "Use this pattern for consequential failure modes such as concurrency bugs, memory churn, state edge cases, "
        "routing mistakes, or contract violations when they match the skill being learned. "
        + tdl_old
    )
    if c.count(tdl_old) != 1:
        raise SystemExit(f"P96 TDL anchor mismatch: {c.count(tdl_old)}")
    c = c.replace(tdl_old, tdl_new, 1)

    visual_old = "Use sliders, stepping, highlighting, traces, or diagrams to expose state changes."
    visual_new = (
        "Use sliders, stepping, highlighting, traces, canvas renders, or diagrams to expose state changes."
    )
    if c.count(visual_old) != 1:
        raise SystemExit(f"P96 visualizer anchor mismatch: {c.count(visual_old)}")
    c = c.replace(visual_old, visual_new, 1)

    c = c.replace("roughly two-minute quiz", "roughly three-minute quiz")
    p["copyContent"] = c
    save_registry(payload)


def strengthen_helper_added_bootstrap(receipt: dict) -> None:
    payload = load_registry()
    bootstrap = next(item for item in payload["prompts"] if item["id"] == receipt["id"])
    c = bootstrap["copyContent"]
    c = c.replace(
        "runs a quick roughly two-minute refresher quiz",
        "runs a quick roughly three-minute refresher quiz",
    )
    version_anchor = (
        "Do not invent completed lessons, resources, or MASTERED records. Empty directories may use the repository's "
        "established placeholder convention only when version control requires it."
    )
    version_replacement = (
        version_anchor
        + " Treat `.teach/` as version-controlled mental documentation when repository policy and data sensitivity permit, "
          "so future maintainers and future sessions can recover the verified model alongside the code; never commit secrets, "
          "private data, or sensitive learning evidence."
    )
    if c.count(version_anchor) != 1:
        raise SystemExit(f"bootstrap version-control anchor mismatch: {c.count(version_anchor)}")
    c = c.replace(version_anchor, version_replacement, 1)
    bootstrap["copyContent"] = c
    bootstrap["proofGate"] = (
        bootstrap["proofGate"]
        + " When repository policy permits tracked teaching state, the bootstrap keeps knowledge state versionable without recording fabricated mastery or sensitive data."
    )
    save_registry(payload)


def broaden_discovery_route(receipt: dict) -> None:
    payload = load_registry()
    p65 = next(item for item in payload["prompts"] if item["id"] == "P65")
    old = "- P96 Stateful Socratic Technical Tutor Workspace: learn a technical topic through persistent grounded lessons, active retrieval, practical exercises, visualizers, and mastery records."
    new = "- P96 Stateful Socratic Technical Tutor Workspace: learn a system or structured skill through persistent grounded lessons, active retrieval, practical exercises, visualizers, and verified mastery records."
    if p65["copyContent"].count(old) != 1:
        raise SystemExit(f"P65 P96 broadening anchor mismatch: {p65['copyContent'].count(old)}")
    p65["copyContent"] = p65["copyContent"].replace(old, new, 1)
    save_registry(payload)


def strengthen_focused_proof(receipt: dict) -> None:
    t = FOCUSED.read_text(encoding="utf-8")
    anchor = '            ".teach/learning-records/<date>_<topic>.md",\n        ):'
    extra = (
        '            ".teach/learning-records/<date>_<topic>.md",\n'
        '            "passive guide",\n'
        '            "single testable invariant",\n'
        '            "diagnostic is a progression gate",\n'
        '            "concurrency bugs",\n'
        '            "memory churn",\n'
        '            "canvas renders",\n'
        '            "roughly three-minute quiz",\n'
        '        ):'
    )
    if t.count(anchor) != 1:
        raise SystemExit(f"P96 expanded-proof anchor mismatch: {t.count(anchor)}")
    t = t.replace(anchor, extra, 1)

    bootstrap_anchor = '            "Do not silently cross into the lesson itself",\n        ):'
    bootstrap_extra = (
        '            "Do not silently cross into the lesson itself",\n'
        '            "version-controlled mental documentation",\n'
        '            "roughly three-minute refresher quiz",\n'
        '        ):'
    )
    if t.count(bootstrap_anchor) != 1:
        raise SystemExit(f"bootstrap expanded-proof anchor mismatch: {t.count(bootstrap_anchor)}")
    t = t.replace(bootstrap_anchor, bootstrap_extra, 1)

    method_anchor = "    def test_p79_harvests_whole_chat_twice_and_complements_utility(self) -> None:\n"
    method = '''    def test_teach_owner_covers_non_code_structured_system_learning(self) -> None:\n        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]\n        self.assertIn("structured skill", teach["useWhen"])\n        self.assertIn("system understanding", teach["keywords"])\n        self.assertIn("Read teaching state before explaining", teach["nextStep"])\n\n'''
    if t.count(method_anchor) != 1:
        raise SystemExit(f"structured-skill proof anchor mismatch: {t.count(method_anchor)}")
    t = t.replace(method_anchor, method + method_anchor, 1)
    FOCUSED.write_text(t, encoding="utf-8")


def main() -> None:
    base.strengthen_p96()
    expand_p96_from_complete_framework()
    receipt = base.add_bootstrap()
    base.route_and_test(receipt)
    strengthen_helper_added_bootstrap(receipt)
    broaden_discovery_route(receipt)
    strengthen_focused_proof(receipt)

    base.run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    base.run("python", "scripts/prompt_registry_ops.py", "validate")
    base.run(
        "python",
        "-m",
        "unittest",
        "tests.test_prompt_registry_expansion_regression_design_teach",
        "tests.test_prompt_kit_discovery",
        "-v",
    )
    base.run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    base.run("python", "scripts/evaluate_prompt_language.py", "--output", ".teach-language-audit.tmp.json", "--summary")
    base.run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    base.run("git", "diff", "--check")


if __name__ == "__main__":
    main()
