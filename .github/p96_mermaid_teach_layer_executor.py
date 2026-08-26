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

    assert p96["name"] == "Stateful Socratic Technical Tutor Workspace"
    assert p98["name"] == "Teach Workspace Protocol Bootstrapper"
    assert "BUILD IMMERSIVE LOCAL HTML/JS LEARNING DEMOS" in p96["copyContent"]
    assert "folders + Markdown/HTML lesson artifacts" in p98["copyContent"]

    p96["sprintRole"] = p96["sprintRole"].replace(
        "immersive local HTML/JS learning demos, reusable visual lesson assets",
        "immersive local HTML/JS learning demos, optional Mermaid structural overlays, reusable visual lesson assets",
    )
    p96["expectedOutput"] = append_once(
        p96["expectedOutput"],
        "For structure-heavy concepts, the tutor may also offer a compact Mermaid diagram as an optional explanatory layer when it clarifies relationships without replacing a needed interactive demo.",
    )
    p96["nextStep"] = append_once(
        p96["nextStep"],
        "When a concept is primarily relational rather than manipulable, consider a Mermaid structural overlay first; when state manipulation or causal experimentation matters, keep the HTML/JS learning lab as the primary artifact and use Mermaid only as a supporting map if it adds value.",
    )
    p96["proofGate"] = append_once(
        p96["proofGate"],
        "A Mermaid layer is optional and evidence-grounded: diagram nodes/edges must map to repository or lesson truth, Mermaid must not displace interaction when manipulation is the learning objective, no Mermaid package/CDN/runtime is installed merely to render it, and rendered appearance is not claimed unless the current environment actually rendered it.",
    )

    content = p96["copyContent"]
    marker = "\n10. VERIFY BEFORE WRITING THE LEARNING RECORD\n"
    section = """
9A. OFFER MERMAID AS AN OPTIONAL STRUCTURAL LAYER
Use Mermaid when a compact declarative diagram would lower the learner's structural load without requiring a full interactive control surface. Good candidates include architecture/dependency maps, sequence/call flows, state transitions, entity/class relationships, ER-style data relationships, and data-flow or ownership boundaries. Treat Mermaid as a layer or option, not a mandatory artifact and not a substitute for the immersive HTML/JS learning lab when the learner needs to manipulate state, replay transitions, inject data, or observe causal behavior.

Choose the lightest useful representation:
- prose when the relation is already simple;
- Mermaid when the learner mainly needs to see stable relationships, order, ownership, or topology;
- interactive HTML/JS when meaningful manipulation, stepping, reset, or experimentation carries the concept;
- Mermaid plus HTML/JS only when the static map genuinely helps the learner orient before or after interacting with the demo.

Keep Mermaid evidence-grounded. Every important node, edge, state, or relationship should correspond to repository evidence, a trusted source, or the explicit toy model used by the lesson. Prefer the smallest diagram that makes the current invariant legible; do not dump an entire repository graph when one bounded slice teaches the concept better. For repository data-structure lessons, Mermaid can visualize entity relationships, ownership/lifecycle boundaries, transformation seams, or representative data flow before the learner is grilled on them.

MERMAID + SOCRATIC USE
When it improves retrieval rather than revealing the answer too early, ask the learner to predict a missing edge, next state, call hop, ownership boundary, or failure path before showing or completing that part of the diagram. Then use the diagram as evidence for the explanation checkpoint, not as a replacement for the learner's explanation.

RENDERING / PORTABILITY RULES
- Prefer fenced Mermaid source in a Markdown lesson or a colocated `.mmd`/text snippet when the environment already supports Mermaid rendering.
- Do not install a Mermaid package, add a CDN, or introduce a build/runtime dependency merely to render a teaching diagram unless the user separately authorizes that environment change.
- If the current viewer cannot render Mermaid, preserve the Mermaid source as a readable artifact and continue the lesson; do not block teaching on rendering support.
- Distinguish source proof from render proof. If the agent did not actually render the diagram, say the Mermaid source was created but visual rendering is UNPROVEN.
- Keep diagram labels sanitized and free of secrets, private data, credentials, or sensitive production values.

Do not create Mermaid for ceremony. If a diagram adds no structural insight beyond the existing prose or interactive demo, omit it.
"""
    if "9A. OFFER MERMAID AS AN OPTIONAL STRUCTURAL LAYER" not in content:
        assert marker in content, "P96 lesson verification boundary moved; inspect the named section only"
        content = content.replace(marker, "\n" + section + marker, 1)
    p96["copyContent"] = content

    for keyword in (
        "mermaid diagram",
        "mermaid teaching",
        "architecture diagram",
        "sequence diagram",
        "data flow diagram",
        "structural overlay",
    ):
        if keyword not in p96["keywords"]:
            p96["keywords"].append(keyword)

    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    test_text = TEST.read_text(encoding="utf-8")
    method_name = "test_teach_mermaid_is_optional_structural_layer_not_interactive_replacement"
    if method_name not in test_text:
        marker_test = "    def test_teach_bootstrap_is_distinct_pure_workspace_setup(self) -> None:\n"
        assert marker_test in test_text, "focused teaching regression owner moved"
        method = '''    def test_teach_mermaid_is_optional_structural_layer_not_interactive_replacement(self) -> None:\n        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]\n        content = teach["copyContent"]\n        for phrase in (\n            "OFFER MERMAID AS AN OPTIONAL STRUCTURAL LAYER",\n            "Treat Mermaid as a layer or option, not a mandatory artifact",\n            "Mermaid plus HTML/JS only when the static map genuinely helps",\n            "architecture/dependency maps",\n            "sequence/call flows",\n            "entity/class relationships",\n            "ownership/lifecycle boundaries",\n            "ask the learner to predict a missing edge",\n            "Do not install a Mermaid package, add a CDN",\n            "visual rendering is UNPROVEN",\n            "Do not create Mermaid for ceremony",\n        ):\n            self.assertIn(phrase, content)\n        self.assertIn("optional Mermaid structural overlays", teach["sprintRole"])\n        self.assertIn("compact Mermaid diagram as an optional explanatory layer", teach["expectedOutput"])\n        self.assertIn("Mermaid structural overlay first", teach["nextStep"])\n        self.assertIn("A Mermaid layer is optional and evidence-grounded", teach["proofGate"])\n        for keyword in ("mermaid diagram", "mermaid teaching", "architecture diagram", "data flow diagram"):\n            self.assertIn(keyword, teach["keywords"])\n\n        # Preserve the immersive-demo owner and bootstrap boundary while adding a diagram layer.\n        self.assertIn("IMMERSIVE DEMO LOOP — PREDICT -> MANIPULATE -> OBSERVE -> EXPLAIN", content)\n        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]\n        self.assertIn("folders + Markdown/HTML lesson artifacts", bootstrap["copyContent"])\n\n'''
        test_text = test_text.replace(marker_test, method + marker_test, 1)
        TEST.write_text(test_text, encoding="utf-8")


if __name__ == "__main__":
    main()
