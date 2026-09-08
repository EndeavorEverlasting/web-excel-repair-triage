from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-cross-input-modality.v1.json"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
BASE = ROOT / "docs" / "prompt-kit.js"

REQUIRED_CAPABILITY_IDS = {
    "browse_profiles",
    "search",
    "find_prompt",
    "favorites_view",
    "inspect_open",
    "copy_act",
    "locate_known_id",
    "copy_known_id",
    "filters",
    "reference",
    "scroll_edges",
    "reset_recover",
    "zero_results",
    "command_surface",
}

MODE_KEYS = ("mouse", "keyboard", "phone")
ROW_KEYS = MODE_KEYS + ("capability", "semantic_action", "state_owner", "proof")


class PromptKitCrossInputModalityTests(unittest.TestCase):
    def test_contract_pins_complete_three_mode_matrix(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "prompt-kit-cross-input-modality-contract/v1")
        self.assertEqual(payload["contract_id"], "prompt-kit-cross-input-modality")
        self.assertEqual(payload["routing_boundary"]["owner"], "P129")

        capabilities = payload["capabilities"]
        ids = [item["id"] for item in capabilities]
        self.assertEqual(set(ids), REQUIRED_CAPABILITY_IDS)
        self.assertEqual(len(ids), len(REQUIRED_CAPABILITY_IDS))

        for item in capabilities:
            for key in ROW_KEYS:
                value = item.get(key)
                self.assertIsInstance(value, str, msg=f"{item.get('id')} missing {key}")
                self.assertTrue(value.strip(), msg=f"{item.get('id')} empty {key}")
            for mode in MODE_KEYS:
                route = item[mode].strip().lower()
                self.assertNotEqual(
                    route,
                    "use the desktop control",
                    msg=f"{item['id']} {mode} must not defer to desktop chrome",
                )
                if route.startswith("supported_exclusion"):
                    self.assertIn(":", item[mode])

        for path_key in (
            "canonical_site",
            "behavior_source",
            "polish_source",
            "phone_guide",
            "mobile_contract",
            "interaction_contract",
        ):
            rel = payload["surface"][path_key]
            self.assertTrue((ROOT / rel).is_file(), msg=f"missing surface {rel}")

    def test_phone_reference_converges_on_toggle_ref_not_click_synthesis(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        base = BASE.read_text(encoding="utf-8")
        self.assertIn("function toggleRef()", base)
        start = polish.index("function performMobileQuickAction")
        end = polish.index("function mobilePromptJumpDigits", start)
        body = polish[start:end]
        self.assertIn("if(action==='reference')", body)
        self.assertIn("typeof toggleRef==='function'", body)
        self.assertIn("toggleRef();return true", body)
        self.assertNotIn("ref.click()", body)
        self.assertNotIn("getElementById('refBtn')", body)

    def test_phone_more_actions_reuse_canonical_semantic_owners(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        start = polish.index("function performMobileQuickAction")
        end = polish.index("function mobilePromptJumpDigits", start)
        body = polish[start:end]
        for marker in (
            "window.openPromptFinder",
            "mobileQuickFocusSearch()",
            "mobileQuickCycleProfile(-1)",
            "mobileQuickCycleProfile(1)",
            "activateFavoritesView()",
            "toggleCompactFilters()",
            "toggleRef()",
            "scrollPromptKitTo('top')",
            "scrollPromptKitTo('bottom')",
        ):
            self.assertIn(marker, body)

    def test_matrix_routes_phone_known_id_to_card_copy_without_detail(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in payload["capabilities"]}
        self.assertIn("Go to P#", by_id["locate_known_id"]["phone"])
        self.assertIn("detail closed", by_id["locate_known_id"]["phone"])
        self.assertEqual(by_id["locate_known_id"]["semantic_action"], "revealPromptShortcutTarget")
        self.assertIn("tap/click any non-control area", by_id["copy_known_id"]["phone"])
        self.assertIn("copyPrompt", by_id["copy_known_id"]["semantic_action"])
        self.assertNotIn("supported_exclusion", by_id["copy_known_id"]["phone"].lower())
        self.assertIn("digits only", by_id["copy_known_id"]["keyboard"].lower())
        self.assertIn("no dedicated known-ID digit grammar", by_id["copy_known_id"]["mouse"])
        self.assertEqual(by_id["reference"]["semantic_action"], "toggleRef")
        rules = payload.get("semantic_convergence_rules") or []
        convergence = next(rule for rule in rules if "terminal copy converges on copyPrompt" in rule)
        self.assertIn("Go to P# must not auto-open detail", convergence)

    def test_generated_site_embeds_converged_reference_route(self) -> None:
        generated = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertIn("if(typeof toggleRef==='function'){toggleRef();return true}", generated)
        self.assertNotIn("if(ref){ref.click();return true}", generated)
        self.assertIn("Go to P#", generated)


if __name__ == "__main__":
    unittest.main()
