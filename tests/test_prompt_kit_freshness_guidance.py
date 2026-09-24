from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_freshness_guidance as freshness


class PromptKitFreshnessGuidanceTests(unittest.TestCase):
    def load_contract(self) -> dict:
        return json.loads(freshness.CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_focused_validator_passes(self) -> None:
        self.assertEqual(freshness.main([]), 0)

    def test_version_label_is_a_required_freshness_trigger(self) -> None:
        payload = self.load_contract()
        self.assertIn(freshness.FRESHNESS_TRIGGER, payload["freshness_triggers"])

    def test_missing_version_trigger_fails_closed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["freshness_triggers"].remove(freshness.FRESHNESS_TRIGGER)
        with self.assertRaisesRegex(
            freshness.FreshnessGuidanceError,
            "version-label freshness trigger is missing",
        ):
            freshness.validate_contract(payload)

    def test_browser_refresh_never_requires_git(self) -> None:
        payload = self.load_contract()
        route = payload["freshness_routes"]["browser-use"]
        self.assertIn(freshness.PUBLIC_URL, route)
        self.assertNotIn("git ", route.lower())
        self.assertNotIn("clone", route.lower())
        self.assertNotIn("pull", route.lower())

    def test_declined_refresh_stays_visible_as_unverified(self) -> None:
        behavior = "\n".join(self.load_contract()["required_agent_behavior"])
        self.assertIn("explicitly declines to refresh", behavior)
        self.assertIn("stale-or-unverified", behavior)

    def test_manifest_registers_freshness_domain(self) -> None:
        payload = json.loads(freshness.MANIFEST_PATH.read_text(encoding="utf-8"))
        freshness.validate_manifest(payload)

    def test_manifest_freshness_owner_drift_fails_closed(self) -> None:
        payload = json.loads(freshness.MANIFEST_PATH.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(payload)
        mutated["domain_contracts"]["prompt_kit_freshness_guidance"]["workflow"] = "WORKFLOW.md#wrong"
        with self.assertRaisesRegex(
            freshness.FreshnessGuidanceError,
            "freshness domain ownership drifted",
        ):
            freshness.validate_manifest(mutated)

    def test_skill_and_report_are_connected(self) -> None:
        freshness.validate_skill()
        freshness.validate_report()


if __name__ == "__main__":
    unittest.main()
