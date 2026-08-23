import json
import subprocess
import unittest
from pathlib import Path

from scripts.validate_prompt_kit_layout_harness import validate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/prompt-kit-layout/contracts/responsive-header-overlap.v1.json"


class PromptKitLayoutHarnessTests(unittest.TestCase):
    def test_harness_is_complete(self):
        errors, _, _ = validate(False)
        self.assertEqual([], errors)

    def test_product_repair_still_requires_browser_geometry(self):
        errors, _, contract = validate(True)
        self.assertEqual(
            "implemented_pending_browser_geometry",
            contract["implementation_status"],
        )
        self.assertTrue(any("not yet proven" in item for item in errors))

    def test_contract_requires_zero_overlap_and_browser_geometry(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        acceptance = contract["strict_acceptance"]
        self.assertEqual(0, acceptance["forbidden_intersections"])
        self.assertEqual(0, acceptance["forbidden_horizontal_overflow_pixels"])
        self.assertTrue(acceptance["all_viewports_required"])
        self.assertTrue(acceptance["browser_geometry_required"])
        self.assertGreaterEqual(len(contract["viewports"]), 3)

    def test_layout_requirements_cover_reported_collision_class(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        ids = {item["id"] for item in contract["requirements"]}
        self.assertIn("no_brand_search_intersection", ids)
        self.assertIn("no_filter_search_intersection", ids)
        self.assertIn("responsive_reflow", ids)

    def test_hotkey_route_points_to_executable_program_design_seam(self):
        route = (ROOT / "harness/prompt-kit-layout/CODEBASE_MAP.md").read_text(encoding="utf-8")
        design = ROOT / "docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md"
        prototype = ROOT / "docs/prompt-kit-hotkey-prototype.js"
        self.assertIn("Routing hook: hotkeys and keyboard shortcuts", route)
        self.assertIn("docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md", route)
        self.assertTrue(design.is_file())
        self.assertTrue(prototype.is_file())

        completed = subprocess.run(
            ["node", str(prototype)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        proof = json.loads(completed.stdout)
        self.assertEqual("PASS", proof["status"])
        self.assertEqual(
            {"FILTER_HIDE", "FILTER_SHOW", "FILTER_TOGGLE", "OPEN_PROMPT(P95)"},
            set(proof["success_paths"]),
        )
        self.assertEqual(
            {"EDITABLE_TARGET", "RESERVED_COLLISION", "UNKNOWN_PROMPT", "PERSISTENCE_FAILED"},
            set(proof["failure_paths"]),
        )


if __name__ == "__main__":
    unittest.main()
