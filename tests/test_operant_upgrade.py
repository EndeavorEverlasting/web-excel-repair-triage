from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "operant_upgrade.py"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-feedback-afk-routing.v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-feedback-hook.yml"


def load_engine():
    spec = importlib.util.spec_from_file_location("operant_upgrade", ENGINE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load canonical Operant upgrade engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OperantUpgradeEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = load_engine()
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    @staticmethod
    def request(**overrides):
        payload = {
            "schema_version": "prompt-kit-afk-work-request/v1",
            "created_at": "2026-09-10T03:20:00Z",
            "coordinator": "P115 AFK Feedback-Driven Development Loop Executor",
            "preferred_mutation_owner": "P07 Repo Sprint Executor",
            "signal_class": "ACTIONABLE_REPAIR",
            "target": "Operant surface tutorial",
            "evidence": {
                "signal_id": "tutorial-route-miss-3",
                "event_type": "operant_friction",
                "value": "route_miss",
                "sequence": 12,
                "timestamp": "2026-09-10T03:20:00Z",
                "surface_id": "tutorial",
                "evidence_kind": "repeated_local_pattern",
                "occurrence_count": 3,
                "source_hash": "a" * 64,
            },
            "owned_surface": "Resolve the smallest current canonical owner for the implicated Operant behavior before mutation.",
            "acceptance_condition": "Repair only the current owning surface when warranted and retain regression proof.",
            "forbidden_scope": [
                "raw usage/session/navigation history",
                "force push",
                "direct merge from the feedback router",
            ],
            "telemetry_semantic_owner": "P99",
            "promotion_owner": "P105/pr-floor-integration",
        }
        payload.update(overrides)
        return payload

    def test_compilation_is_deterministic_and_binds_exact_lane(self) -> None:
        request = self.request()
        first = self.engine.compile_recipe(request)
        second = self.engine.compile_recipe(json.loads(json.dumps(request)))
        self.assertEqual(first, second)
        digest = self.engine.request_digest(request)
        self.assertEqual(first["source_request_sha256"], digest)
        self.assertEqual(first["lane"]["branch"], f"automation/operant-upgrade-{digest[:12]}")
        self.assertTrue(first["lane"]["isolation_required"])
        self.assertFalse(first["lane"]["force_push_allowed"])
        self.assertFalse(first["lane"]["merge_authority"])

    def test_recipe_preserves_authority_but_drops_private_comment_body(self) -> None:
        request = self.request()
        request["evidence"]["private_comment"] = "raw local-only feedback text"
        recipe = self.engine.compile_recipe(request)
        encoded = json.dumps(recipe, sort_keys=True)
        self.assertNotIn("raw local-only feedback text", encoded)
        self.assertTrue(recipe["evidence"]["private_evidence_present"])
        self.assertEqual(recipe["coordinator"], "P115 AFK Feedback-Driven Development Loop Executor")
        self.assertEqual(recipe["mutation_owner"], "P07 Repo Sprint Executor")
        self.assertEqual(recipe["promotion_owner"], "P105/pr-floor-integration")
        self.assertEqual(recipe["executor"]["prompt_id"], "P07")

    def test_recipe_carries_canonical_generator_validators_and_p105_gate(self) -> None:
        recipe = self.engine.compile_recipe(self.request())
        self.assertEqual(
            recipe["generator"]["command"],
            ["python", "build_prompt_kit.py", "--output", "web/prompt-kit/index.html"],
        )
        self.assertEqual(recipe["generator"]["output"], "web/prompt-kit/index.html")
        self.assertIn("python scripts/validate_prompt_kit_feedback_afk_routing.py --summary", recipe["validators"])
        self.assertIn("python scripts/validate_operant_upgrade.py --summary", recipe["validators"])
        self.assertEqual(recipe["integration"]["owner"], "P105/pr-floor-integration")
        self.assertEqual(recipe["integration"]["contract"], "harness/contracts/pr-merge-gate.v1.json")

    def test_invalid_authority_or_non_actionable_request_fails_closed(self) -> None:
        with self.assertRaises(self.engine.UpgradeError):
            self.engine.compile_recipe(self.request(preferred_mutation_owner="P999 Imaginary Owner"))
        with self.assertRaises(self.engine.UpgradeError):
            self.engine.compile_recipe(self.request(signal_class="INFORMATION_ONLY"))
        with self.assertRaises(self.engine.UpgradeError):
            self.engine.compile_recipe(self.request(promotion_owner="direct-merge"))

    def test_plan_and_validate_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            request_path = root / "request.json"
            output_dir = root / "recipes"
            request_path.write_text(json.dumps(self.request(), indent=2) + "\n", encoding="utf-8")
            self.assertEqual(
                self.engine.main(
                    ["plan", "--request", str(request_path), "--output-dir", str(output_dir)]
                ),
                0,
            )
            recipes = list(output_dir.glob("recipe-*.json"))
            self.assertEqual(len(recipes), 1)
            self.assertEqual(
                self.engine.main(
                    ["validate", "--request", str(request_path), "--recipe", str(recipes[0])]
                ),
                0,
            )

    def test_contract_and_github_adapter_route_to_canonical_engine_without_merge_authority(self) -> None:
        engine = self.contract["surfaces"]["canonical_upgrade_engine"]
        self.assertEqual(engine["path"], "scripts/operant_upgrade.py")
        self.assertEqual(engine["recipe_schema"], "operant-upgrade-recipe/v1")
        self.assertFalse(engine["mutation_authority"])
        self.assertFalse(engine["merge_authority"])
        self.assertIn("PROMPT_KIT_AFK_WORKER_ARGV_JSON", self.workflow)
        self.assertIn("scripts/operant_upgrade.py", self.workflow)
        self.assertIn("Outputs/operant-upgrade", self.workflow)
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertNotIn("pull-requests: write", self.workflow)


if __name__ == "__main__":
    unittest.main()
