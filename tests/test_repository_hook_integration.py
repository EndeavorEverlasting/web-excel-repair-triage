from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryHookIntegrationTests(unittest.TestCase):
    def load(self, path: str) -> dict:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_capability_trigger_skill_and_implementation_are_connected(self) -> None:
        capabilities = self.load("harness/capabilities.v1.json")["capabilities"]
        triggers = self.load("harness/triggers.v1.json")["triggers"]
        manifest = self.load("harness/manifest.v1.json")
        capability = next(item for item in capabilities if item["id"] == "repository-hook-integration")
        trigger = next(item for item in triggers if item["id"] == "repository-hook-installation-needed")
        self.assertEqual(capability["implementation"], {"kind": "script", "path": "scripts/install_local_hooks.py"})
        self.assertEqual(trigger["capability_id"], capability["id"])
        self.assertEqual(trigger["skill"], capability["skill"])
        self.assertIn(trigger["id"], capability["trigger_ids"])
        self.assertIn(capability["skill"], manifest["skills"])

    def test_existing_installer_remains_preservation_first(self) -> None:
        source = (ROOT / "scripts/install_local_hooks.py").read_text(encoding="utf-8")
        for marker in (
            "require_single_worktree",
            "existing_default_hooks",
            "core.hooksPath",
            "--replace",
            "No global hook setting is changed",
        ):
            self.assertIn(marker, source)
        self.assertTrue((ROOT / ".githooks/pre-commit").is_file())
        self.assertTrue((ROOT / ".githooks/pre-push").is_file())

    def test_skill_requires_provider_adapters_to_remain_subordinate(self) -> None:
        text = (ROOT / ".ai/skills/repository-hook-integration/SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "Claude",
            "Codex",
            "DeepSeek Harness",
            "adapter",
            "do not assume dialect compatibility",
            "Never change global Git hook configuration",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
