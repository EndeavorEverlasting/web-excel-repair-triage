from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry
import build_prompt_kit


class AIEngineeringLevelUpTests(unittest.TestCase):
    IDS = ("P67", "P68", "P69", "P70", "P71")

    def test_effective_registry_contains_five_distinct_tracks(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        by_id = {item["id"]: item for item in prompts}
        self.assertEqual(len(by_id), len(prompts))
        for prompt_id in self.IDS:
            self.assertIn(prompt_id, by_id)
            self.assertEqual(by_id[prompt_id]["progress"], "YES")
        self.assertEqual(by_id["P67"]["class"], "AI ENGINEERING / EVALS")
        self.assertEqual(by_id["P68"]["class"], "AI ENGINEERING / CONTEXT")
        self.assertEqual(by_id["P69"]["class"], "AI ENGINEERING / AGENT RELIABILITY")
        self.assertEqual(by_id["P70"]["class"], "AI ENGINEERING / LLM OPS")
        self.assertEqual(by_id["P71"]["class"], "AI ENGINEERING / ADAPTABILITY")

    def test_each_prompt_requires_executable_repository_proof(self) -> None:
        by_id = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}
        required = {
            "P67": ("deterministic", "regression", "model/judge"),
            "P68": ("context", "measure", "quality"),
            "P69": ("idempot", "timeout", "fault"),
            "P70": ("latency", "cost", "fallback", "rollback"),
            "P71": ("stable contracts", "compatibility", "rollback"),
        }
        for prompt_id, phrases in required.items():
            text = by_id[prompt_id]["copyContent"].lower()
            for phrase in phrases:
                self.assertIn(phrase.lower(), text)
            self.assertIn("exact next command", text)

    def test_hallucination_failure_modes_have_diagnostic_grounding_and_context_owners(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        by_id = {item["id"]: item for item in prompts}
        p67 = by_id["P67"]["copyContent"]
        for phrase in (
            "EVALUATE HALLUCINATION DIAGNOSIS",
            "required truth is absent versus explicitly present",
            "targeted grounding",
            "re-anchoring/compaction",
        ):
            self.assertIn(phrase, p67)
        p68 = by_id["P68"]["copyContent"]
        for phrase in (
            "RECOVER FROM ATTENTION SATURATION / THE DUMB ZONE",
            "measured or system-defined budget threshold",
            "rolling/sliding compaction",
            "fresh session",
            "do not add more context first",
        ):
            self.assertIn(phrase, p68)

        by_name = {item["name"]: item for item in prompts}
        diagnostic = by_name["Factuality vs Faithfulness Hallucination Diagnoser"]
        grounding = by_name["Grounded Agent Output & Tool-Call Gate"]
        self.assertNotEqual(diagnostic["id"], grounding["id"])
        self.assertEqual(diagnostic["seq"], diagnostic["id"][1:])
        self.assertEqual(grounding["seq"], grounding["id"][1:])
        self.assertEqual(diagnostic["copySheet"], f"{diagnostic['id']}_COPY_SAFE")
        self.assertEqual(grounding["copySheet"], f"{grounding['id']}_COPY_SAFE")
        self.assertEqual(diagnostic["class"], "AI ENGINEERING / HALLUCINATION DIAGNOSIS")
        self.assertEqual(grounding["class"], "AI ENGINEERING / GROUNDING")
        for phrase in (
            "FACTUALITY_MISSING_CONTEXT",
            "FAITHFULNESS_CONTEXT_IGNORED",
            "ATTENTION_SATURATION",
            "MATCH THE REPAIR TO THE CAUSE",
            "counterexample",
        ):
            self.assertIn(phrase, diagnostic["copyContent"])
        for phrase in (
            "BUILD JUST-IN-TIME GROUNDING",
            "REQUIRE VERIFIABLE ATTRIBUTION WHERE IT MATTERS",
            "FAIL-CLOSED INTERCEPTOR",
            "GROUNDING_FAILURE",
            "hallucinated identifier",
            "critic cannot override a deterministic schema failure",
        ):
            self.assertIn(phrase, grounding["copyContent"])
        policy = build_prompt_kit_registry.load_actionability_policy()
        for item in (diagnostic, grounding):
            self.assertEqual(item["actionabilityPolicy"], policy["policy_id"])
            self.assertIn(policy["marker"], item["copyContent"])
        raw = json.loads((ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json").read_text(encoding="utf-8"))
        raw_by_name = {item["name"]: item for item in raw["prompts"]}
        self.assertLess(len(raw_by_name[diagnostic["name"]]["copyContent"]), 8000)
        self.assertLess(len(raw_by_name[grounding["name"]]["copyContent"]), 8000)

    def test_p100_rejects_contradictory_terminal_closeout_and_preserves_true_terminal_case(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        by_id = {item["id"]: item for item in prompts}
        p100 = by_id["P100"]["copyContent"]
        for phrase in (
            "7. CLOSEOUT CONSISTENCY CHECK",
            "REMAINING GAPS, RISKS, BLOCKERS, INTEGRATION STATE",
            "acknowledged overlapping branch or identity conflict",
            "none; no safe actionable work remains",
            "FAITHFULNESS_CONTEXT_IGNORED closure failure",
            "reopen closure and execute or route the action",
            "A true terminal case",
            "do not manufacture work",
        ):
            self.assertIn(phrase, p100)
        self.assertIn("closeout contradiction", by_id["P100"]["keywords"])
        self.assertIn("no safe actionable work", by_id["P100"]["keywords"])

    def test_p68_repeats_context_refactor_until_fixed_point_and_mainline(self) -> None:
        raw = json.loads((ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json").read_text(encoding="utf-8"))
        source = next(item for item in raw["prompts"] if item["id"] == "P68")
        effective = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}["P68"]
        policy = build_prompt_kit_registry.load_actionability_policy()

        self.assertEqual(source["name"], "Context Engineering System Refactorer")
        self.assertEqual(source["class"], "AI ENGINEERING / CONTEXT")
        self.assertEqual(source["color"], "Purple")
        self.assertEqual(source["category"], "standard")
        self.assertIn("bounded fixed point", source["sprintRole"])
        self.assertIn("current default branch", source["expectedOutput"])
        self.assertIn("REFRESH -> MEASURE -> SELECT HIGHEST-IMPACT CONTEXT DEFECT -> REFACTOR -> VALIDATE -> CRITIQUE -> INTEGRATE -> REMEASURE -> CONTINUE", source["nextStep"])
        self.assertIn("branch, PR, or green CI result alone is insufficient completion", source["proofGate"])

        copy = source["copyContent"]
        for phrase in (
            "ENGINEER THE FULL CONTEXT SYSTEM AROUND THE MODEL",
            "RECOVER FROM ATTENTION SATURATION / THE DUMB ZONE",
            "CONTINUOUS CONTEXT-CONVERGENCE LOOP",
            "A pass counts only when",
            "deliberate second pass",
            "merge it into the current default branch in the same run",
            "verify the context-system changes and owning validation are present there",
            "Do not stop merely because one context slice is green or one bounded slice merged",
            "Stop only at the bounded fixed point",
        ):
            self.assertIn(phrase, copy)

        self.assertNotIn(policy["integration_marker"], copy)
        self.assertIn(policy["integration_marker"], effective["copyContent"])
        for forbidden in ("50,000 FT", "30,000 FT", "15,000 FT", "TREAT CLAIMS AS HYPOTHESES"):
            self.assertNotIn(forbidden, copy)
        self.assertLess(len(copy), 7000)

    def test_prompt_finder_and_search_route_the_five_tracks(self) -> None:
        p65 = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}["P65"]
        for prompt_id in self.IDS:
            self.assertIn(prompt_id, p65["copyContent"])
        for keyword in ("ai engineering", "evals", "context engineering", "production agents", "llm ops", "adaptability"):
            self.assertIn(keyword, p65["keywords"])
        order = json.loads(build_prompt_kit_registry.DISPLAY_ORDER_POLICY.read_text(encoding="utf-8"))
        positions = [order["promoted_prompt_ids"].index(prompt_id) for prompt_id in self.IDS]
        self.assertEqual(positions, list(range(positions[0], positions[0] + 5)))

    def test_reference_panel_maps_prompts_and_variables(self) -> None:
        ref = json.loads((ROOT / "docs/reference.json").read_text(encoding="utf-8"))
        seq = {item["promptId"]: item for item in ref["promptSequence"]}
        for prompt_id in self.IDS:
            self.assertIn(prompt_id, seq)
            self.assertEqual(seq[prompt_id]["mutatesRepo"], "YES")
        legend = [item for item in ref["classLegend"] if item.get("promptIds") == "P67-P71"]
        self.assertEqual(len(legend), 1)
        variables = {item["variable"] for item in ref["variables"]}
        for variable in ("xyz_ai_surface", "xyz_eval_risks", "xyz_context_problem", "xyz_agent_runtime", "xyz_provider_runtime", "xyz_ai_dependency", "xyz_review_window"):
            self.assertIn(variable, variables)

    def test_doctrine_contains_all_five_production_disciplines(self) -> None:
        doctrine = build_prompt_kit.build_doctrine()
        self.assertIn("ai_engineering", doctrine)
        block = doctrine["ai_engineering"]
        self.assertEqual(block["title"], "Production AI Engineering Doctrine")
        text = "\n".join(section["heading"] + "\n" + section["content"] for section in block["sections"]).lower()
        for phrase in ("evals", "context engineering", "production agents", "llm ops", "adaptability", "p67", "p71"):
            self.assertIn(phrase, text)

    def test_tutorial_manifest_is_complete_and_prompt_mapped(self) -> None:
        root = ROOT / "docs/tutorials/ai-engineering-level-up"
        manifest = json.loads((root / "tutorial-manifest.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "ai-engineering-level-up-tutorial/v1")
        self.assertEqual([item["prompt_id"] for item in manifest["modules"]], list(self.IDS))
        for module in manifest["modules"]:
            path = ROOT / module["path"]
            self.assertTrue(path.is_file(), path)
            content = path.read_text(encoding="utf-8")
            self.assertIn(module["prompt_id"], content)
            self.assertIn("Completion gate", content)
        readme = (root / "README.md").read_text(encoding="utf-8")
        for prompt_id in self.IDS:
            self.assertIn(prompt_id, readme)

    def test_checked_in_site_contains_tracks_and_doctrine(self) -> None:
        site = (ROOT / "web/prompt-kit/index.html").read_text(encoding="utf-8")
        for prompt_id in self.IDS:
            self.assertIn(f'"id": "{prompt_id}"', site)
        for phrase in (
            "Repository Eval Framework Builder",
            "Context Engineering System Refactorer",
            "Production Agent Reliability Hardener",
            "LLM Ops Production Readiness Builder",
            "AI Toolchain Adaptability Review + Upgrade",
            "Production AI Engineering Doctrine",
        ):
            self.assertIn(phrase, site)
        self.assertEqual(site, build_prompt_kit_registry.render())


if __name__ == "__main__":
    unittest.main()
