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
