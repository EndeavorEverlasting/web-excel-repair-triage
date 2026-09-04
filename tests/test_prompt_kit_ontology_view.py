from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as builder
from scripts import validate_prompt_kit_ontology_evidence as evidence_validator

ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = ROOT / "harness" / "capabilities.v1.json"
EVIDENCE_CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-ontology-evidence.v1.json"
ONTOLOGY_RUNTIME = ROOT / "docs" / "prompt-kit-ontology.js"
TEACHING_RECORD = ROOT / ".teach" / "learning-records" / "2026-08-29_prompt-kit-ontology.md"


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
        self.assertEqual(len(model["implementations"]), len(model["capabilities"]))
        self.assertTrue(
            {"prompt", "script", "launcher"}.issubset(
                {item["kind"] for item in model["implementations"]}
            )
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

    def test_evidence_history_contract_extends_mastered_ontology_without_fabricating_runs(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        report = evidence_validator.validate()

        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertEqual(
            contract["relation_chain"],
            ["capability", "skill", "implementation", "invocation", "run", "evidence", "proof_ceiling"],
        )
        self.assertEqual(contract["record_kinds"]["favorite"]["proof_effect"], "none")
        self.assertEqual(contract["record_kinds"]["failure"]["proof_effect"], "lower_or_block")
        self.assertEqual(contract["record_kinds"]["feedback"]["raw_payload_transport"], "out_of_scope")
        self.assertIn("does not assert that any invocation", contract["proof_ceiling"])

    def test_evidence_history_validator_rejects_preference_as_proof(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(contract)
        mutated["record_kinds"]["favorite"]["proof_effect"] = "supports_observed_claim"

        report = evidence_validator.validate_payload(
            mutated,
            ONTOLOGY_RUNTIME.read_text(encoding="utf-8"),
            TEACHING_RECORD.read_text(encoding="utf-8"),
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("favorites must not count as proof", report["errors"])


if __name__ == "__main__":
    unittest.main()
