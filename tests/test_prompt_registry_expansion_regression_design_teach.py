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
            "WIDEN THE DESIGN SPACE BEFORE CONVERGING",
            "structurally analogous systems",
            "2-4 materially different candidates",
            "P97 Open-Source Prior-Art & Gap Analyst",
            "Creativity is disciplined recombination",
            "ACQUIRE COHESIVE REPOSITORY CONTEXT",
            "Do not treat a single pasted file as sufficient evidence",
            "Repomix/code2prompt",
            "root manifests/configuration",
        ):
            self.assertIn(phrase, content)
        design = self.by_name["Program Design & Call-Stack Prototype Architect"]
        self.assertEqual(design["id"], "P95")
        self.assertEqual(design["profile"], "spec-architecture")
        self.assertNotIn("BUILD THE SOLVED-BASELINE VS PRIORITIZED-GAP MAP", content)
        raw_payload = json.loads((ROOT / "registry/prompts/spec-architecture-prompts.v1.json").read_text(encoding="utf-8"))
        raw = next(p for p in raw_payload["prompts"] if p["id"] == "P95")
        self.assertLessEqual(len(raw["copyContent"]), 10000)

    def test_greenfield_repository_architecture_selects_hosting_tier_from_evidence(self) -> None:
        design = self.by_name["Program Design & Call-Stack Prototype Architect"]
        content = design["copyContent"]
        for phrase in (
            "CHOOSE THE DEPLOYMENT OPERATING MODEL FROM EVIDENCE",
            "managed PaaS/serverless",
            "Docker or Podman",
            "Kubernetes/managed orchestration",
            "millions someday",
            "OCI containers",
            "p95/p99/SLO",
        ):
            self.assertIn(phrase, content)
        p03 = self.full["P03"]["copyContent"]
        self.assertIn("GREENFIELD REPOSITORY CREATION", p03)
        self.assertIn("route that bounded design decision to P95", p03)
        self.assertIn("Do not make Docker, Podman, Kubernetes", p03)
        self.assertIn("P00 remains governance owner", p03)
        self.assertIn("P01 remains harness", p03)

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

    def test_teach_immersive_local_html_demos_are_first_class_learning_tools(self) -> None:
        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]
        content = teach["copyContent"]
        for phrase in (
            "BUILD IMMERSIVE LOCAL HTML/JS LEARNING DEMOS WHEN INTERACTION CAN CARRY THE CONCEPT",
            "Do not treat interactive artifacts as a rare flourish",
            ".teach/lessons/<NN>-<topic>.html",
            "IMMERSIVE DEMO LOOP — PREDICT -> MANIPULATE -> OBSERVE -> EXPLAIN",
            "step/back/reset",
            "Design for active causality, not passive animation",
            "meaningful agency, visible causality, and rapid feedback",
            "Keep demos local-first and self-contained when practical",
            "exact local path and launch/open command",
            "one reset/failure path",
            "keep that interaction UNPROVEN",
            "Do not build decorative UI that does not improve comprehension",
        ):
            self.assertIn(phrase, content)
        self.assertIn("immersive local HTML/JS learning demos", teach["sprintRole"])
        self.assertIn("local self-contained HTML/JS learning demo", teach["expectedOutput"])
        self.assertIn("interactive demo materially lowers abstraction cost", teach["proofGate"])
        for keyword in ("immersive teaching demos", "local html learning demo", "interactive html lesson"):
            self.assertIn(keyword, teach["keywords"])

        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]
        self.assertIn("folders + Markdown/HTML lesson artifacts", bootstrap["copyContent"])
        self.assertIn("`.html` is allowed when a visual simulator materially helps", bootstrap["copyContent"])

    def test_teach_mermaid_is_optional_structural_layer_not_interactive_replacement(self) -> None:
        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]
        content = teach["copyContent"]
        for phrase in (
            "OFFER MERMAID AS AN OPTIONAL STRUCTURAL LAYER",
            "Treat Mermaid as a layer or option, not a mandatory artifact",
            "Mermaid plus HTML/JS only when the static map genuinely helps",
            "architecture/dependency maps",
            "sequence/call flows",
            "entity/class relationships",
            "ownership/lifecycle boundaries",
            "ask the learner to predict a missing edge",
            "Do not install a Mermaid package, add a CDN",
            "visual rendering is UNPROVEN",
            "Do not create Mermaid for ceremony",
        ):
            self.assertIn(phrase, content)
        self.assertIn("optional Mermaid structural overlays", teach["sprintRole"])
        self.assertIn("compact Mermaid diagram as an optional explanatory layer", teach["expectedOutput"])
        self.assertIn("Mermaid structural overlay first", teach["nextStep"])
        self.assertIn("A Mermaid layer is optional and evidence-grounded", teach["proofGate"])
        for keyword in ("mermaid diagram", "mermaid teaching", "architecture diagram", "data flow diagram"):
            self.assertIn(keyword, teach["keywords"])

        # Preserve the immersive-demo owner and bootstrap boundary while adding a diagram layer.
        self.assertIn("IMMERSIVE DEMO LOOP — PREDICT -> MANIPULATE -> OBSERVE -> EXPLAIN", content)
        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]
        self.assertIn("folders + Markdown/HTML lesson artifacts", bootstrap["copyContent"])

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

    def test_teach_repo_data_structure_grill_upscales_the_human(self) -> None:
        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]
        content = teach["copyContent"]
        for phrase in (
            "REPOSITORY DATA-STRUCTURE GRILL MODE",
            "MATT POCOCK'S `grill-me` DISCIPLINE",
            "GROUND THE STRUCTURE MAP BEFORE ASKING FACT QUESTIONS",
            "identity and keys",
            "ownership and lifecycle",
            "serializers/deserializers",
            "If a question can be answered by exploring the codebase",
            "SKILL_UNAVAILABLE",
            "Ask exactly one data-structure question at a time",
            "TRACE REAL DATA THROUGH THE REPOSITORY",
            "COMPLEMENT-AI MASTERY GATE",
            "predict which structures and boundaries",
            "challenge an AI-generated design or diff",
            "the human must upscale enough",
        ):
            self.assertIn(phrase, content)
        self.assertIn("repository data-structure grilling", teach["useWhen"])
        self.assertIn("evidence-backed structure map", teach["expectedOutput"])
        self.assertIn("critically review an AI-generated change", teach["proofGate"])
        self.assertIn("repository data structures", teach["keywords"])

    def test_p65_routes_repository_data_structure_grilling_to_p96(self) -> None:
        p65 = self.full["P65"]
        content = p65["copyContent"]
        self.assertIn("Explicit requests to be grilled on a repository’s data structures", content)
        self.assertIn("P65’s own grilling is only for selecting the right Prompt Kit route", content)
        self.assertIn("repository data structure grill", p65["keywords"])
        self.assertIn("grill repo data model", p65["keywords"])

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
        self.assertIn("Re-derive regression controls", p83["copyContent"])
        self.assertIn("run safe runtime proof yourself or keep it UNPROVEN", p83["copyContent"])
        self.assertIn("UNPROVEN", p83["copyContent"])
        self.assertIn("impacted callers/call stacks", p83["inspectFirst"])
        self.assertIn("independently derives a regression/control set", p83["proofGate"])
        self.assertIn("canonical live proof when safely executable", p83["proofGate"])

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
