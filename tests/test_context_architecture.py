from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_context_architecture


class ContextArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "harness/contracts/context-architecture.v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_context_validator_passes(self) -> None:
        self.assertEqual(validate_context_architecture.main(["--summary"]), 0)

    def test_default_load_is_only_governance_and_router(self) -> None:
        self.assertEqual(
            self.contract["default_entrypoints"],
            ["AGENTS.md", "harness/CONTEXT.md"],
        )
        router = (ROOT / "harness/CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("Do not eagerly read", router)
        self.assertIn("50,000-foot", router)

    def test_three_zoom_layers_are_machine_bounded(self) -> None:
        layers = self.contract["layers"]
        self.assertEqual(layers["50000"]["soft_max_approx_tokens"], 1000)
        self.assertEqual(layers["30000"]["soft_max_additional_approx_tokens"], 2000)
        self.assertEqual(layers["15000"]["soft_max_additional_approx_tokens"], 4000)

    def test_hard_bloat_budgets_hold(self) -> None:
        for path, ceiling in self.contract["hard_char_budgets"].items():
            self.assertLessEqual(
                len((ROOT / path).read_text(encoding="utf-8")),
                ceiling,
                path,
            )

    def test_root_indexes_route_instead_of_preloading(self) -> None:
        codebase = (ROOT / "CODEBASE_MAP.md").read_text(encoding="utf-8")
        skills = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
        self.assertIn("harness/CONTEXT.md", codebase)
        self.assertIn("harness/CONTEXT.md", skills)
        self.assertIn("selection index", skills)
        self.assertIn("Do **not** preload", codebase)

    def test_binding_domain_law_is_demand_loaded_and_incorporated(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for path in self.contract["binding_specs"].values():
            self.assertTrue((ROOT / path).is_file(), path)
            self.assertIn(path, agents)

    def test_two_largest_active_skills_are_factored(self) -> None:
        for path in (
            ".ai/skills/harness-infrastructure-maintenance/SKILL.md",
            ".ai/skills/technician-prompt-kit-acquisition/SKILL.md",
        ):
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertLessEqual(text.__len__(), self.contract["hard_char_budgets"][path])
            self.assertIn("## Procedure", text)
            self.assertIn("## Proof ceiling", text)


if __name__ == "__main__":
    unittest.main()
