from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
RAW_SPEC = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
RAW_DISCOVERY = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"

NAMES = {
    "architect": "UX Product Designer & Interaction Architect",
    "emulate": "Reference UX Emulator & Adaptation Builder",
    "polish": "UX Polish & Sophistication Refiner",
    "system": "Cross-App UX Design System & Pattern Factorer",
    "accept": "UX Integrity & Cross-Viewport Acceptance Guard",
}
EXPECTED_IDS = {
    "UX Product Designer & Interaction Architect": "P106",
    "Reference UX Emulator & Adaptation Builder": "P107",
    "UX Polish & Sophistication Refiner": "P108",
    "Cross-App UX Design System & Pattern Factorer": "P109",
    "UX Integrity & Cross-Viewport Acceptance Guard": "P110"
}


class UXDesignPromptSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}
        cls.by_name = {p["name"]: p for p in cls.full.values()}
        cls.raw_spec = json.loads(RAW_SPEC.read_text(encoding="utf-8"))["prompts"]
        cls.raw_by_name = {p["name"]: p for p in cls.raw_spec}
        cls.policy = build_prompt_kit_registry.load_actionability_policy()

    def test_suite_has_five_distinct_helper_allocated_owners(self) -> None:
        prompts = [self.by_name[name] for name in NAMES.values()]
        self.assertEqual(len({p["id"] for p in prompts}), 5)
        for prompt in prompts:
            self.assertEqual(prompt["id"], EXPECTED_IDS[prompt["name"]])
            self.assertEqual(prompt["seq"], prompt["id"][1:])
            self.assertEqual(prompt["copySheet"], f"{prompt['id']}_COPY_SAFE")
            self.assertEqual(prompt["profile"], "spec-architecture")
            self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
            self.assertIn(self.policy["marker"], prompt["copyContent"])
            self.assertLess(len(self.raw_by_name[prompt["name"]]["copyContent"]), 8000)

    def test_architect_owns_creation_without_absorbing_program_design_or_flow_telemetry(self) -> None:
        prompt = self.by_name[NAMES["architect"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX ARCHITECTURE")
        content = prompt["copyContent"]
        for phrase in (
            "RECOVER THE USER JOB AND TERMINAL VALUE",
            "DESIGN INFORMATION ARCHITECTURE BEFORE CHROME",
            "MODEL INTERACTION STATE EXPLICITLY",
            "DESIGN RESPONSIVE + ACCESSIBLE BEHAVIOR AS CORE BEHAVIOR",
            "IMPLEMENT ONE REAL VERTICAL UX SLICE",
            "Preserve orthogonal state",
            "Use P95 Program Design & Call-Stack Prototype Architect",
            "Use P99 User-Flow Friction & Preference Telemetry Refiner",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("DERIVE THE DASHBOARD FROM EVENTS", content)
        self.assertNotIn("PROTOTYPE FAILURE CALL STACKS TOO", content)

    def test_reference_emulator_requires_observed_vs_inferred_functional_fidelity(self) -> None:
        prompt = self.by_name[NAMES["emulate"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX REFERENCE EMULATION")
        content = prompt["copyContent"]
        for phrase in (
            "PIN THE REFERENCE EVIDENCE",
            "BUILD A FIDELITY MATRIX",
            "OBSERVED, INFERRED, TARGET-SPECIFIC, or INTENTIONAL DEVIATION",
            "EXTRACT RULES, NOT JUST COORDINATES",
            "IMPLEMENT REAL BEHAVIOR",
            "COMPARE MATCHED STATES",
            "Static HTML/source inspection is not proof",
        ):
            self.assertIn(phrase, content)
        self.assertIn("unknown", prompt["proofGate"].lower())
        self.assertNotIn("Do not present a prototype as final", content)

    def test_polisher_revisits_craft_to_bounded_fixed_point_without_flow_role_collapse(self) -> None:
        prompt = self.by_name[NAMES["polish"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX POLISH")
        content = prompt["copyContent"]
        for phrase in (
            "BUILD A POLISH LEDGER",
            "VISUAL HIERARCHY",
            "COMPONENT CONSISTENCY",
            "EDGE STATES",
            "MAKE FEEDBACK FEEL COMPLETE",
            "POLISH RESPONSIVELY",
            "deliberate second sweep",
            "bounded polish fixed point",
            "route to P99 rather than hiding flow debt with styling",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("INSTRUMENT SEMANTIC USAGE, NOT NOISE", content)

    def test_design_system_factors_cross_app_rules_without_forcing_uniformity(self) -> None:
        prompt = self.by_name[NAMES["system"]]
        self.assertEqual(prompt["class"], "PRODUCT / DESIGN SYSTEM")
        content = prompt["copyContent"]
        for phrase in (
            "DEFINE SEMANTIC TOKENS BEFORE COMPONENT SPRAWL",
            "FACTOR COMPLETE COMPONENT CONTRACTS",
            "CENTRALIZE INTERACTION PATTERNS WHERE THEY ARE SHARED",
            "shortcut/command",
            "PRESERVE PRODUCT IDENTITY THROUGH CONTROLLED EXTENSION",
            "MIGRATE INCREMENTALLY",
            "GUARD AGAINST DRIFT",
        ):
            self.assertIn(phrase, content)
        self.assertIn("without becoming identical", prompt["sprintRole"])

    def test_acceptance_guard_requires_live_geometry_input_and_composed_state_proof(self) -> None:
        prompt = self.by_name[NAMES["accept"]]
        self.assertEqual(prompt["class"], "PRODUCT / UX ACCEPTANCE")
        content = prompt["copyContent"]
        for phrase in (
            "PIN THE ACCEPTANCE SUBJECT",
            "BUILD THE MODE + STATE MATRIX",
            "DO NOT OVERCLAIM STATIC PROOF",
            "Static HTML/CSS/DOM/string checks",
            "PROTECT COMPOSED INTERACTION STATE",
            "active search -> unrelated filter show/hide/toggle",
            "clear temporary mode -> prior relevant context restores",
            "Favorites/selection membership changes",
            "shortcut -> terminal action occurs exactly once",
            "CHECK VISUAL GEOMETRY + ACTION REACHABILITY",
            "exact head",
        ):
            self.assertIn(phrase, content)
        self.assertIn("40px", content)
        self.assertIn("P94 Regression Test & Live Behavior Guard", content)

    def test_existing_iteration_flow_program_and_regression_owners_remain_distinct(self) -> None:
        for prompt_id, expected in (
            ("P82", "ENGINEERING / PROTOTYPING"),
            ("P94", "TESTING / REGRESSION"),
            ("P95", "SOFTWARE ARCHITECTURE / PROGRAM DESIGN"),
            ("P99", "PRODUCT / UX FLOW + TELEMETRY"),
        ):
            self.assertEqual(self.full[prompt_id]["class"], expected)
        self.assertIn("HYPOTHESIS -> BUILD -> MEASURE -> CRITIQUE -> DECIDE", self.full["P82"]["copyContent"])
        self.assertIn("PRESERVE ORTHOGONAL STATE", self.full["P99"]["copyContent"])
        self.assertIn("PROTECT COMPOSED UI STATE AND INTERACTION SEQUENCES", self.full["P94"]["copyContent"])
        self.assertIn("PROTOTYPE FAILURE CALL STACKS TOO", self.full["P95"]["copyContent"])

    def test_p65_routes_the_full_ux_lifecycle_without_replacing_existing_owners(self) -> None:
        raw = json.loads(RAW_DISCOVERY.read_text(encoding="utf-8"))["prompts"]
        p65 = next(p for p in raw if p["id"] == "P65")
        self.assertIn("routes the UX design lifecycle", p65["useWhen"])
        self.assertIn("creation/interaction architecture", p65["expectedOutput"])
        for name, prompt_id in EXPECTED_IDS.items():
            self.assertIn(f"{prompt_id} {name}", p65["copyContent"])
        for keyword in (
            "ux design", "interaction design", "reference ux", "ux polish",
            "design system", "ux acceptance", "responsive ux", "visual regression",
        ):
            self.assertIn(keyword, p65["keywords"])
        for existing in (
            "P82 Prototype-Measure-Refine Delivery Loop",
            "P94 Regression Test & Live Behavior Guard",
            "P99 User-Flow Friction & Preference Telemetry Refiner",
            "P95 Program Design & Call-Stack Prototype Architect",
        ):
            self.assertIn(existing, p65["copyContent"])

    def test_generated_site_is_exact_and_contains_ux_suite(self) -> None:
        expected = build_prompt_kit_registry.render()
        actual = (ROOT / "web/prompt-kit/index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        for name in NAMES.values():
            self.assertIn(name, actual)


if __name__ == "__main__":
    unittest.main()
