from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as builder

ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = ROOT / "harness" / "capabilities.v1.json"
ONTOLOGY_RUNTIME = ROOT / "docs" / "prompt-kit-ontology.js"


class PromptKitOntologyViewTests(unittest.TestCase):
    def test_model_preserves_canonical_capability_contracts(self) -> None:
        registry = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        prompts = builder.load_prompt_kit_registry()
        model = builder.build_ontology_model(prompts)

        self.assertEqual(model["schema_version"], "prompt-kit-ontology/v1")
        self.assertEqual(
            [item["id"] for item in model["capabilities"]],
            [item["id"] for item in registry["capabilities"]],
        )
        expected = {item["id"]: item for item in registry["capabilities"]}
        actual = {item["id"]: item for item in model["capabilities"]}
        for capability_id, source in expected.items():
            with self.subTest(capability=capability_id):
                self.assertEqual(actual[capability_id]["skill"], source["skill"])
                self.assertEqual(actual[capability_id]["implementation"], source["implementation"])
                self.assertEqual(actual[capability_id]["proof_ceiling"], source["proof_ceiling"])

    def test_skill_inventory_matches_actual_skill_files(self) -> None:
        model = builder.build_ontology_model(builder.load_prompt_kit_registry())
        expected_paths = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / ".ai" / "skills").glob("*/SKILL.md")
        }
        actual_paths = {item["path"] for item in model["skills"]}
        self.assertEqual(actual_paths, expected_paths)

    def test_prompt_implementation_is_relationship_not_skill_identity(self) -> None:
        model = builder.build_ontology_model(builder.load_prompt_kit_registry())
        capability = next(
            item for item in model["capabilities"] if item["id"] == "skill-evaluation"
        )
        implementation = next(
            item
            for item in model["implementations"]
            if item["capability_id"] == "skill-evaluation"
        )
        self.assertEqual(capability["skill"], ".ai/skills/skill-evaluation/SKILL.md")
        self.assertEqual(implementation["kind"], "prompt")
        self.assertEqual(implementation["prompt_id"], "P62")
        self.assertTrue(implementation["prompt_name"])
        self.assertNotEqual(implementation["skill"], implementation["prompt_id"])

    def test_render_embeds_ontology_data_and_runtime(self) -> None:
        html = builder.render()
        runtime = ONTOLOGY_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("window.PROMPT_KIT_ONTOLOGY", html)
        self.assertIn("prompt-kit-ontology/v1", html)
        self.assertIn("Repository-backed agentic map", html)
        self.assertIn(runtime, html)
        self.assertIn("Declared proof, not run history.", html)


if __name__ == "__main__":
    unittest.main()
