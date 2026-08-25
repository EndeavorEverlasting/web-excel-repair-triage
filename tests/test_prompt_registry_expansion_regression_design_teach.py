from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]


class PromptRegistryExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}
        cls.by_name = {p["name"]: p for p in cls.full.values()}

    def test_new_prompts_are_distinct_and_visible(self) -> None:
        regression = self.by_name["Regression Test & Live Behavior Guard"]
        design = self.by_name["Program Design & Call-Stack Prototype Architect"]
        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]
        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]
        self.assertEqual(regression["class"], "TESTING / REGRESSION")
        self.assertEqual(design["class"], "SOFTWARE ARCHITECTURE / PROGRAM DESIGN")
        self.assertEqual(bootstrap["class"], "LEARNING / WORKSPACE BOOTSTRAP")
        self.assertEqual(teach["class"], "LEARNING / STATEFUL TUTOR")
        self.assertEqual(len({regression["id"], design["id"], bootstrap["id"], teach["id"]}), 4)
        for prompt in (regression, design, bootstrap, teach):
            self.assertRegex(prompt["id"], r"^P\d+$")
            self.assertEqual(prompt["copySheet"], f"{prompt['id']}_COPY_SAFE")
        html = build_prompt_kit_registry.render()
        for name in (regression["name"], design["name"], teach["name"]):
            self.assertIn(name, html)

    def test_regression_prompt_protects_old_behavior_and_requires_live_controls(self) -> None:
        content = self.by_name["Regression Test & Live Behavior Guard"]["copyContent"]
        for phrase in (
            "BUILD THE PROTECTED-BEHAVIOR LEDGER",
            "TRACE CHANGE IMPACT THROUGH CALL STACKS",
            "Do not let deleting or rewriting a test silently delete an accepted behavior",
            "TEST THE CHANGED PATH AND THE IMPACTED CONTROL",
            "Before closure, exercise the canonical runtime path",
        ):
            self.assertIn(phrase, content)

    def test_program_design_prompt_requires_call_stack_and_runnable_prototype(self) -> None:
        content = self.by_name["Program Design & Call-Stack Prototype Architect"]["copyContent"]
        for phrase in (
            "MAP THE CURRENT PROGRAM",
            "TRACE CALL STACKS BEFORE REDESIGN",
            "BUILD A RUNNABLE PROTOTYPE",
            "COMPARE AGAINST CURRENT BEHAVIOR",
            "PROMOTE ONLY AFTER INTEGRATION PROOF",
        ):
            self.assertIn(phrase, content)

    def test_teach_workspace_prompt_preserves_state_and_adapts(self) -> None:
        content = self.by_name["Stateful Socratic Technical Tutor Workspace"]["copyContent"]
        for phrase in (
            "BUILD THE LEARNER MODEL",
            "SOCRATIC LOOP",
            "ADAPT FROM EVIDENCE",
            "PERSIST STATE ACROSS SESSIONS",
            "Do not leak hidden answer keys",
        ):
            self.assertIn(phrase, content)

    def test_bootstrap_prompt_builds_workspace_protocol(self) -> None:
        content = self.by_name["Teach Workspace Protocol Bootstrapper"]["copyContent"]
        for phrase in (
            "BOOTSTRAP A DURABLE TEACHING WORKSPACE",
            "WORKSPACE CONTRACT",
            "LEARNER STATE",
            "SESSION PROTOCOL",
            "VALIDATE THE WORKSPACE",
        ):
            self.assertIn(phrase, content)

    def test_p65_routes_all_four_new_prompts(self) -> None:
        p65 = self.full["P65"]["copyContent"]
        for name in (
            "Regression Test & Live Behavior Guard",
            "Program Design & Call-Stack Prototype Architect",
            "Teach Workspace Protocol Bootstrapper",
            "Stateful Socratic Technical Tutor Workspace",
        ):
            prompt = self.by_name[name]
            self.assertIn(f"{prompt['id']} {name}", p65)

    def test_expansion_prompts_are_in_generated_site(self) -> None:
        html = build_prompt_kit_registry.render()
        for name in (
            "Regression Test & Live Behavior Guard",
            "Program Design & Call-Stack Prototype Architect",
            "Teach Workspace Protocol Bootstrapper",
            "Stateful Socratic Technical Tutor Workspace",
        ):
            self.assertIn(name, html)

    def test_prompt_kit_site_matches_current_registry(self) -> None:
        expected = build_prompt_kit_registry.render()
        actual = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)

    def test_teach_workspace_has_bounded_registry_source(self) -> None:
        raw = json.loads((ROOT / "registry/prompts/spec-architecture-prompts.v1.json").read_text(encoding="utf-8"))
        teach = next(p for p in raw["prompts"] if p["name"] == "Stateful Socratic Technical Tutor Workspace")
        self.assertLess(len(teach["copyContent"]), 7000)

    def test_p79_harvests_whole_chat_and_uses_helper_for_new_prompts(self) -> None:
        content = self.full["P79"]["copyContent"]
        for phrase in (
            "WHOLE-CHAT HARVEST — PASS 1",
            "OWNER MAP BEFORE NEW IDS",
            "python scripts/prompt_registry_ops.py add",
            "Do NOT set id, seq, or copySheet",
            "Multiple genuinely distinct prompts may be added from one chat",
            "WHOLE-CHAT HARVEST — PASS 2",
            "Stop at a bounded fixed point",
        ):
            self.assertIn(phrase, content)
        raw = json.loads((ROOT / "registry/prompts/spec-architecture-prompts.v1.json").read_text(encoding="utf-8"))
        source = next(p for p in raw["prompts"] if p["id"] == "P79")
        self.assertLess(len(source["copyContent"]), 5000)

    def test_runtime_and_review_owners_add_regression_live_proof(self) -> None:
        p08 = self.full["P08"]["copyContent"]
        self.assertIn("Regression control:", p08)
        self.assertIn("requested new/repaired behavior", p08)
        self.assertIn("impacted protected control", p08)
        self.assertIn("After any runtime repair, rerun both paths", p08)

        p14 = self.full["P14"]["copyContent"]
        self.assertIn("REVIEW AXES — KEEP THEM SEPARATE", p14)
        self.assertIn("A. STANDARDS", p14)
        self.assertIn("B. SPEC", p14)
        self.assertIn("no spec available", p14)
        self.assertIn("REGRESSION + CALL-STACK GATE", p14)
        self.assertIn("canonical runtime", p14)

    def test_agent_verifier_independently_derives_regressions_and_live_proof(self) -> None:
        p83 = self.full["P83"]
        self.assertIn("Re-derive regression controls", p83["copyContent"])
        self.assertIn("run safe runtime proof yourself or keep it UNPROVEN", p83["copyContent"])
        self.assertIn("canonical live proof when safely executable", p83["proofGate"])
        self.assertIn("UNPROVEN", p83["copyContent"])
        self.assertIn("impacted callers/call stacks", p83["inspectFirst"])
        self.assertIn("independently derives a regression/control set", p83["proofGate"])

    def test_p65_routes_all_three_new_capabilities(self) -> None:
        p65 = self.full["P65"]["copyContent"]
        for name in (
            "Regression Test & Live Behavior Guard",
            "Program Design & Call-Stack Prototype Architect",
            "Stateful Socratic Technical Tutor Workspace",
            "Teach Workspace Protocol Bootstrapper",
            "Prototype-Measure-Refine Delivery Loop",
            "User-Flow Friction & Preference Telemetry Refiner",
        ):
            prompt = self.by_name[name]
            self.assertIn(f"{prompt['id']} {name}", p65)


if __name__ == "__main__":
    unittest.main()
