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
            "RUN THE CANONICAL LIVE PATH WHEN THE CLAIM IS LIVE",
            "requested new/repaired behavior",
            "impacted previously working control",
            "Do not modify expected results, snapshots, fixtures, mocks, or tolerances merely to fit the broken candidate",
            "What behavior could this change break that our selected tests would not notice?",
            "PROTECT COMPOSED UI STATE AND INTERACTION SEQUENCES",
            "visibility toggle should not erase an active search query",
            "shortcut that is meant to complete a user action",
        ):
            self.assertIn(phrase, content)

    def test_program_design_prototypes_success_and_failure_call_stacks(self) -> None:
        content = self.by_name["Program Design & Call-Stack Prototype Architect"]["copyContent"]
        for phrase in (
            "GOVERNANCE: rules for how work is performed",
            "PROGRAM DESIGN: runtime/application modules",
            "DESIGN DEEP MODULES AND CLEAN SEAMS",
            "PROTOTYPE REPRESENTATIVE CALL STACKS",
            "ENTRYPOINT/CONTROLLER",
            "PROTOTYPE FAILURE CALL STACKS TOO",
            "needs one canonical owner",
            "COMPARE SEAMS WHEN THE DESIGN IS UNCERTAIN",
            "This prompt may create design artifacts, thin prototypes",
            "END THE JOURNEY AT USER VALUE, NOT AN INTERMEDIATE SCREEN",
            "OPTIONAL INSPECTION",
            "semantic completion telemetry",
        ):
            self.assertIn(phrase, content)

    def test_teach_prompt_is_grounded_stateful_and_active(self) -> None:
        content = self.by_name["Stateful Socratic Technical Tutor Workspace"]["copyContent"]
        for phrase in (
            ".teach/",
            "GROUND BEFORE EXPLAINING",
            "Treat unsupported model memory as a hypothesis, not a citation",
            "DECOMPOSE FROM FIRST PRINCIPLES",
            "CONCEPTUAL TRADE-OFF / MECHANISM",
            "CODE DIAGNOSTIC / EDGE CASE",
            "ZERO BLACK-BOX PRODUCTION GENERATION DURING TEACHING",
            "USE TEST-DRIVEN LEARNING WHEN CODE IS THE SKILL",
            "self-contained HTML/JS visualizer",
            "Reuse components from existing `.teach/assets/`",
            "VERIFY BEFORE WRITING THE LEARNING RECORD",
            "`/teach <topic>`",
            "`/teach recap`",
            "EXACTLY TWO LEARNER CHECKPOINTS",
            ".teach/learning-records/<date>_<topic>.md",
            "passive guide",
            "single testable invariant",
            "diagnostic is a progression gate",
            "concurrency bugs",
            "memory churn",
            "canvas renders",
            "roughly three-minute quiz",
        ):
            self.assertIn(phrase, content)

    def test_teach_bootstrap_is_distinct_pure_workspace_setup(self) -> None:
        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]
        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]
        self.assertNotEqual(bootstrap["id"], teach["id"])
        self.assertIn("use P96 instead", bootstrap["useWhen"])
        content = bootstrap["copyContent"]
        for phrase in (
            "NO PACKAGE OR CLONE DEPENDENCY", ".teach/", "MISSION.md", "RESOURCES.md",
            "lessons/", "learning-records/", "`/teach <topic>`", "`/teach recap`",
            "exactly one conceptual trade-off/mechanism question", "one code diagnostic or edge-case exercise",
            "Do not silently cross into the lesson itself",
            "version-controlled mental documentation",
            "roughly three-minute refresher quiz",
        ):
            self.assertIn(phrase, content)

    def test_teach_owner_covers_non_code_structured_system_learning(self) -> None:
        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]
        self.assertIn("structured skill", teach["useWhen"])
        self.assertIn("system understanding", teach["keywords"])
        self.assertIn("Read teaching state before explaining", teach["nextStep"])

    def test_p79_harvests_whole_chat_twice_and_complements_utility(self) -> None:
        p79 = self.full["P79"]
        content = p79["copyContent"]
        for phrase in (
            "CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION IS THE ANCHOR, NOT THE CONTEXT BOUNDARY",
            "WHOLE-CHAT HARVEST — PASS 1",
            "insight | current owner | action | proof",
            "No material insight may silently disappear",
            "COMPLEMENT — DO NOT MERELY TRANSCRIBE",
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
        self.assertIn("green test/live run is historical evidence", p83["copyContent"])
        self.assertIn("Re-derive impacted regression controls", p83["copyContent"])
        self.assertIn("canonical path yourself", p83["copyContent"])
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
