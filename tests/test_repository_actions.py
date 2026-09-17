from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_prompt_kit_registry
import run_repository_action

REGISTRY = ROOT / "harness" / "repository-actions.v1.json"
CONTRACT = ROOT / "harness" / "contracts" / "repository-local-proof-continuity.v1.json"
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
MARKER = "REPOSITORY LOCAL ACTION CONTINUITY CONTRACT"


class RepositoryActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def test_registry_is_allowlisted_and_local_first(self) -> None:
        self.assertEqual(self.registry["schema_version"], "repository-actions/v1")
        self.assertEqual(self.registry["runner"], "scripts/run_repository_action.py")
        self.assertEqual(self.registry["provider_adapter"], ".github/workflows/repository-local-action.yml")
        ids = [item["id"] for item in self.registry["actions"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("prompt-kit-build-proof", ids)
        self.assertIn("pre-push-proof", ids)
        for action in self.registry["actions"]:
            for step in action["steps"]:
                self.assertIsInstance(step["argv"], list)
                self.assertNotIn("sh -c", " ".join(step["argv"]))

    def test_runner_resolves_only_declared_python_placeholder(self) -> None:
        self.assertEqual(run_repository_action.resolve_argv(["{python}", "-V"])[0], sys.executable)
        with self.assertRaises(run_repository_action.RepositoryActionError):
            run_repository_action.resolve_argv(["{operator_shell}"])

    def test_contract_points_to_executable_local_action_owner(self) -> None:
        self.assertEqual(self.contract["canonical_local_action_registry"], "harness/repository-actions.v1.json")
        self.assertEqual(self.contract["canonical_local_action_runner"], "scripts/run_repository_action.py")
        self.assertEqual(self.contract["provider_adapter"], ".github/workflows/repository-local-action.yml")
        self.assertIn("thin optional delegate", self.contract["provider_adapter_rule"])

    def test_shared_policy_reaches_every_effective_prompt(self) -> None:
        self.assertIn(MARKER, self.policy["copy_content_appendix"])
        prompts = build_prompt_kit_registry.load_prompt_registry()
        self.assertGreater(len(prompts), 100)
        missing = [prompt["id"] for prompt in prompts if MARKER not in prompt["copyContent"]]
        self.assertEqual(missing, [])

    def test_provider_adapter_is_dispatch_only_and_delegates_to_runner(self) -> None:
        workflow = (ROOT / ".github/workflows/repository-local-action.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("push:", workflow)
        self.assertIn("scripts/run_repository_action.py", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("contents: read", workflow)


if __name__ == "__main__":
    unittest.main()
