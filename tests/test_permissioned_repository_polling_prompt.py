from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
NAME = "Permissioned Repository Polling & Scheduled Sync Builder"


class PermissionedRepositoryPollingPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        cls.full = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.operational = build_prompt_kit_registry.load_prompt_registry()
        cls.raw = json.loads(RAW.read_text(encoding="utf-8"))["prompts"]

    def _one(self, prompts):
        matches = [prompt for prompt in prompts if prompt.get("name") == NAME]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_polling_prompt_is_one_distinct_spec_architecture_owner(self) -> None:
        prompt = self._one(self.operational)
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["category"], "standard")
        self.assertEqual(prompt["type"], "AUTONOMY + BUILD")
        self.assertEqual(prompt["class"], "SOFTWARE ARCHITECTURE / POLLING + SCHEDULED SYNC")
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], prompt["copyContent"])

        by_id = {item["id"]: item for item in self.operational}
        self.assertNotEqual(prompt["id"], "P69")
        self.assertNotEqual(prompt["id"], "P77")
        self.assertNotEqual(prompt["id"], "P79")
        self.assertEqual(by_id["P69"]["class"], "AI ENGINEERING / AGENT RELIABILITY")
        self.assertEqual(by_id["P77"]["type"], "MAINTENANCE + CROSS-REPO")
        self.assertEqual(by_id["P79"]["class"], "PROMPT KIT / REGISTRY OPERATIONS")

    def test_prompt_requires_repo_analysis_consent_and_safe_poll_state_machine(self) -> None:
        prompt = self._one(self.full)
        content = prompt["copyContent"]
        for phrase in (
            "ANALYZE THE REPOSITORY BEFORE DESIGNING THE POLLER",
            "DEFINE AUTHORITY AND THE CHANGE SIGNAL",
            "USER CONSENT AND ENABLE/DISABLE OWNERSHIP",
            "Recurring local execution is opt-in product state",
            "NO_CHANGE IS A SUCCESSFUL TERMINAL STATE",
            "UPDATE_AVAILABLE -> APPLY -> VALIDATE -> APPLIED",
            "Never reset, clean, force-pull, or overwrite unique work",
            "one stable repository-approved or user/profile-scoped root",
            "Do not create a fresh clone, cache tree, temp directory, or generated-site copy every interval",
            "Windows Task Scheduler, cron, systemd timer, launchd",
            "single-instance lock",
            "Back off after repeated transient failures",
            "actual due-time execution was observed or only scheduler registration/configuration was proven",
        ):
            self.assertIn(phrase, content)

    def test_agentswitchboard_example_preserves_prompt_kit_authority_and_safe_acquisition(self) -> None:
        content = self._one(self.full)["copyContent"]
        for phrase in (
            "AGENTSWITCHBOARD / PROMPT KIT REFERENCE USE CASE",
            "AgentSwitchboard profile",
            "EndeavorEverlasting/web-excel-repair-triage",
            "Keep GitHub/the canonical Triage repository authoritative",
            "rather than owning a duplicate prompt registry or rewriting prompt IDs",
            "clone only when absent",
            "fast-forward only when safe",
            "refuse destructive repair of dirty/divergent work",
            "keep the active local path stable",
            "without directory bloat",
        ):
            self.assertIn(phrase, content)

    def test_polling_prompt_is_bounded_and_discoverable(self) -> None:
        raw = self._one(self.raw)
        self.assertGreater(len(raw["copyContent"]), 3000)
        self.assertLess(len(raw["copyContent"]), 10000)
        keywords = {item.casefold() for item in raw["keywords"]}
        for keyword in (
            "polling",
            "scheduled polling",
            "repository polling",
            "scheduled sync",
            "background updater",
            "version watcher",
            "permissioned automation",
            "agentswitchboard polling",
        ):
            self.assertIn(keyword, keywords)
        rendered = build_prompt_kit_registry.render()
        self.assertIn(NAME, rendered)


if __name__ == "__main__":
    unittest.main()
