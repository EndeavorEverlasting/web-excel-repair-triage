from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
import run_repository_action

REGISTRY = ROOT / "harness" / "repository-actions.v1.json"
CONTRACT = ROOT / "harness" / "contracts" / "repository-local-proof-continuity.v1.json"


class RepositoryActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_registry_is_allowlisted_local_first_and_exact_candidate_aware(self) -> None:
        self.assertEqual(self.registry["schema_version"], "repository-actions/v1")
        self.assertEqual(self.registry["runner"], "scripts/run_repository_action.py")
        ids = [item["id"] for item in self.registry["actions"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("prompt-kit-proof", ids)
        self.assertIn("pre-push-proof", ids)
        self.assertIn("required-checks-proof", ids)
        for action in self.registry["actions"]:
            for step in action["steps"]:
                self.assertIsInstance(step["argv"], list)
                self.assertNotIn("sh -c", " ".join(step["argv"]))
            self.assertTrue(
                any(step["argv"] == ["git", "diff", "--check", "{base_sha}...{head_sha}"]
                    for step in action["steps"]),
                action["id"],
            )

    def test_runner_resolves_only_declared_placeholders(self) -> None:
        context = {
            "base_sha":"1"*40,
            "head_sha":"2"*40,
            "base_head_sha":"3"*40,
        }
        self.assertEqual(run_repository_action.resolve_argv(["{python}", "-V"], context)[0], sys.executable)
        self.assertEqual(
            run_repository_action.resolve_argv(["git","diff","--check","{base_sha}...{head_sha}"], context)[-1],
            f"{'1'*40}...{'2'*40}",
        )
        with self.assertRaises(run_repository_action.RepositoryActionError):
            run_repository_action.resolve_argv(["{operator_shell}"], context)
        self.assertEqual(run_repository_action.validate_base_ref("origin/main"), "origin/main")
        for unsafe in ("--help", "origin/main..evil", "main@{1}", "main;touch"):
            with self.assertRaises(run_repository_action.RepositoryActionError):
                run_repository_action.validate_base_ref(unsafe)

    def test_contract_routes_provider_loss_to_local_proof_without_promotion(self) -> None:
        joined = "\n".join(
            self.contract["principles"]
            + self.contract["planning_requirements"]
            + self.contract["execution_requirements"]
            + self.contract["anti_patterns"]
        )
        self.assertIn("before hosted CI becomes a single point of failure", joined)
        self.assertIn("Suppress blind hosted retries", joined)
        self.assertIn("do not relabel local PASS as hosted PASS", joined)
        self.assertIn("Stopping the whole sprint solely because hosted Actions", joined)


if __name__ == "__main__":
    unittest.main()
