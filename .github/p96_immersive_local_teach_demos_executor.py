from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path("registry/prompts/tutorial-discovery-prompts.v1.json")
TEST = Path("tests/test_prompt_registry_expansion_regression_design_teach.py")


def append_once(text: str, sentence: str) -> str:
    return text if sentence in text else f"{text.rstrip()} {sentence}"


def main() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p96 = next(p for p in payload["prompts"] if p["id"] == "P96")
    p98 = next(p for p in payload["prompts"] if p["id"] == "P98")

    # Owner check: P96 owns actual teaching; P98 already owns local Markdown/HTML workspace setup.
    assert p96["name"] == "Stateful Socratic Technical Tutor Workspace"
    assert p98["name"] == "Teach Workspace Protocol Bootstrapper"
    assert "folders + Markdown/HTML lesson artifacts" in p98["copyContent"]
    assert "`.html` is allowed when a visual simulator materially helps" in p98["copyContent"]

    p96["sprintRole"] = p96["sprintRole"].replace(
        "reusable visual lesson assets",
        "immersive local HTML/JS learning demos, reusable visual lesson assets",
    )

    p96["expectedOutput"] = append_once(
        p96["expectedOutput"],
        "When interaction materially helps, the session also creates or reuses a local self-contained HTML/JS learning demo tied to the current invariant and learner checkpoint, with an exact local path and launch/open instruction.",
    )
    p96["nextStep"] = append_once(
        p96["nextStep"],
        "Before defaulting to prose for a structurally visual, spatial, temporal, or stateful concept, decide whether a local interactive demo would materially lower abstraction cost and create or reuse it before the checkpoint when it would.",
    )
    p96["proofGate"] = append_once(
        p96["proofGate"],
        "When an interactive demo materially lowers abstraction cost, the tutor creates or reuses a repo-local self-contained HTML/JS artifact, ties it to the current invariant and retrieval checkpoint, exposes meaningful manipulation/reset and visible state change, gives its exact local path and launch/open instruction, and reports browser-proof limits rather than claiming unobserved interaction.",
    )

    old_section = """9. BUILD VISUAL/INTERACTIVE LESSONS WHEN THEY REDUCE ABSTRACTION COST
For algorithms, ASTs, state machines, event loops, packet routing, memory behavior, concurrency, call stacks, geometry, or other structural topics, create a small self-contained HTML/JS visualizer when interaction materially improves understanding. Use sliders, stepping, highlighting, traces, canvas renders, or diagrams to expose state changes.
Reuse components from existing `.teach/assets/` or lesson assets before creating new ones. If a new component is generally reusable, extract it into the teaching asset owner rather than inlining copies into multiple lessons. Do not build decorative UI that does not improve comprehension.
"""

    new_section = """9. BUILD IMMERSIVE LOCAL HTML/JS LEARNING DEMOS WHEN INTERACTION CAN CARRY THE CONCEPT
Do not treat interactive artifacts as a rare flourish. During lesson design, explicitly ask whether the current invariant would become easier to predict, manipulate, observe, or diagnose through a local demo. For algorithms, ASTs, state machines, event loops, packet routing, memory behavior, concurrency, call stacks, data structures, geometry, or other structural topics, prefer a small self-contained local HTML/JS learning lab over another page of prose when interaction materially reduces abstraction cost. Treat each learning lab as a self-contained HTML/JS visualizer whose interactions are tied to the lesson invariant, not as a generic mini-app. Store a lesson-specific demo under `.teach/lessons/<NN>-<topic>.html`; put genuinely reusable controls, renderers, fixtures, or visualization helpers in `.teach/assets/`.

IMMERSIVE DEMO LOOP — PREDICT -> MANIPULATE -> OBSERVE -> EXPLAIN
- PREDICT: before changing the demo, ask the learner what state transition, output, ownership change, call path, or failure they expect and why.
- MANIPULATE: let the learner change a meaningful input or system state with controls such as step/back/reset, sliders, toggles, data injection, drag/reorder, breakpoint or phase controls, and trace filters.
- OBSERVE: make causality visible with highlighting, traces, state snapshots, counters, diagrams, canvas renders, before/after views, or success/failure paths that expose what actually changed.
- EXPLAIN: require the learner to reconcile prediction with observation and name the invariant or mechanism before the lesson advances.

Design for active causality, not passive animation. Engagement must come from meaningful agency, visible causality, and rapid feedback rather than decorative motion or gamification theater. A good demo lets the learner perturb the model, replay or reset it, and see why the system behaves differently. Where useful, expose both a healthy path and a representative failure/edge state so the learner can diagnose rather than merely watch.

Keep demos local-first and self-contained when practical. Do not add an external build system, CDN, framework, service, or package merely to make a lesson flashy when plain HTML/CSS/JS can express the concept. Use sanitized fixtures and repository-grounded shapes; never embed secrets, private data, production credentials, or unsafe live endpoints in a teaching demo.

When creating or reusing a demo, give the learner its exact local path and launch/open command. Smoke-check that the artifact exists and is structurally loadable; when browser execution is available, exercise the primary interaction plus one reset/failure path. If browser/runtime proof is unavailable, say so and keep that interaction UNPROVEN instead of claiming the demo was observed.

Reuse components from existing `.teach/assets/` or lesson assets before creating new ones. If a new component is generally reusable, extract it into the teaching asset owner rather than inlining copies into multiple lessons. Do not build decorative UI that does not improve comprehension.
"""

    content = p96["copyContent"]
    if "9. BUILD IMMERSIVE LOCAL HTML/JS LEARNING DEMOS WHEN INTERACTION CAN CARRY THE CONCEPT" not in content:
        assert old_section in content, "P96 visual lesson owner moved; inspect only the named P96 section"
        content = content.replace(old_section, new_section, 1)
    p96["copyContent"] = content

    for keyword in (
        "immersive teaching demos",
        "local html learning demo",
        "interactive html lesson",
        "teach visualizer",
        "learning lab",
    ):
        if keyword not in p96["keywords"]:
            p96["keywords"].append(keyword)

    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    test_text = TEST.read_text(encoding="utf-8")
    method_name = "test_teach_immersive_local_html_demos_are_first_class_learning_tools"
    if method_name not in test_text:
        marker = "    def test_teach_bootstrap_is_distinct_pure_workspace_setup(self) -> None:\n"
        assert marker in test_text, "focused teaching regression owner moved"
        method = '''    def test_teach_immersive_local_html_demos_are_first_class_learning_tools(self) -> None:\n        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]\n        content = teach["copyContent"]\n        for phrase in (\n            "BUILD IMMERSIVE LOCAL HTML/JS LEARNING DEMOS WHEN INTERACTION CAN CARRY THE CONCEPT",\n            "Do not treat interactive artifacts as a rare flourish",\n            ".teach/lessons/<NN>-<topic>.html",\n            "IMMERSIVE DEMO LOOP — PREDICT -> MANIPULATE -> OBSERVE -> EXPLAIN",\n            "step/back/reset",\n            "Design for active causality, not passive animation",\n            "meaningful agency, visible causality, and rapid feedback",\n            "Keep demos local-first and self-contained when practical",\n            "exact local path and launch/open command",\n            "one reset/failure path",\n            "keep that interaction UNPROVEN",\n            "Do not build decorative UI that does not improve comprehension",\n        ):\n            self.assertIn(phrase, content)\n        self.assertIn("immersive local HTML/JS learning demos", teach["sprintRole"])\n        self.assertIn("local self-contained HTML/JS learning demo", teach["expectedOutput"])\n        self.assertIn("interactive demo materially lowers abstraction cost", teach["proofGate"])\n        for keyword in ("immersive teaching demos", "local html learning demo", "interactive html lesson"):\n            self.assertIn(keyword, teach["keywords"])\n\n        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]\n        self.assertIn("folders + Markdown/HTML lesson artifacts", bootstrap["copyContent"])\n        self.assertIn("`.html` is allowed when a visual simulator materially helps", bootstrap["copyContent"])\n\n'''
        test_text = test_text.replace(marker, method + marker, 1)
        TEST.write_text(test_text, encoding="utf-8")


if __name__ == "__main__":
    main()
