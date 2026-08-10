import json
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


if __name__ == "__main__":
    unittest.main()
