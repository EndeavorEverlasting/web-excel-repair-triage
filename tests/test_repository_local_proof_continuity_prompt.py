from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "repository-local-proof-continuity.v1.json"
REGISTRY = ROOT / "harness" / "repository-actions.v1.json"
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
DEFECTS = ROOT / "harness" / "evals" / "prompt-regression" / "defect-families.v1.json"


class RepositoryLocalProofContinuityPromptTests(unittest.TestCase):
    def test_contract_and_registry_bind_local_owner(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(contract["canonical_local_action_registry"], "harness/repository-actions.v1.json")
        self.assertEqual(contract["canonical_local_action_runner"], "scripts/run_repository_action.py")
        self.assertEqual(registry["provider_adapter"], ".github/workflows/repository-local-action.yml")
        self.assertIn("thin optional delegate", contract["provider_adapter_rule"])

    def test_provider_loss_is_not_a_terminal_sprint_rule(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        joined = "\n".join(contract["execution_requirements"] + contract["anti_patterns"])
        self.assertIn("continue through the canonical local proof path", joined)
        self.assertIn("Suppress blind hosted retries", joined)
        self.assertIn("Stopping the whole sprint solely because hosted Actions", joined)

    def test_local_proof_ceiling_stays_typed(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        text = "\n".join(contract["principles"] + [contract["proof_ceiling"]])
        for phrase in ("hosted-runner execution", "deployment", "live runtime behavior", "operator acceptance"):
            self.assertIn(phrase, text)

    def test_global_prompt_policy_requires_local_first_provider_resilience(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        appendix = policy["copy_content_appendix"]
        self.assertIn("REGRESSION SAFETY / RECURRING DEFECT CONTRACT", appendix)
        self.assertIn("Prefer repository-owned local required-check profiles", appendix)
        self.assertIn("Provider unavailability does not erase valid repository-defined local proof", appendix)

    def test_provider_quota_termination_is_registered_as_systemic(self) -> None:
        defects = json.loads(DEFECTS.read_text(encoding="utf-8"))
        family = next(item for item in defects["families"] if item["id"] == "PROVIDER_QUOTA_TERMINATION")
        self.assertEqual(family["status"], "SYSTEMIC")
        self.assertEqual(family["classification"], "WORKFLOW_CONTROL")
        self.assertGreaterEqual(len(family["occurrences"]), 2)
        self.assertEqual(family["regression_gate"], "tests/test_repository_local_proof_continuity_prompt.py")


if __name__ == "__main__":
    unittest.main()
