from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "repository-local-proof-continuity.v1.json"
COMPILER_POLICY = ROOT / "harness" / "contracts" / "prompt-language-compiler-policy.v1.json"
P07 = ROOT / "harness" / "prompt-compilation" / "semantics" / "P07.json"
PROMPT_OPS = ROOT / "harness" / "specs" / "prompt-operations.md"


class RepositoryLocalProofContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.policy = json.loads(COMPILER_POLICY.read_text(encoding="utf-8"))
        cls.p07 = json.loads(P07.read_text(encoding="utf-8"))
        cls.prompt_ops = PROMPT_OPS.read_text(encoding="utf-8")

    def test_contract_is_fail_closed_and_proof_typed(self) -> None:
        self.assertEqual(
            self.contract["schema_version"],
            "repository-local-proof-continuity/v1",
        )
        for state in (
            "QUOTA_EXHAUSTED",
            "RATE_LIMITED",
            "RUNNER_UNAVAILABLE",
            "PERMISSION_DENIED",
            "UNKNOWN",
        ):
            self.assertIn(state, self.contract["provider_states"])
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

    def test_p07_always_activates_local_proof_continuity(self) -> None:
        obligations = {item["id"]: item for item in self.p07["obligations"]}
        self.assertIn("local_proof_continuity", obligations)
        local = obligations["local_proof_continuity"]
        self.assertEqual(local["when"], "always")
        self.assertEqual(local["modality"], "MUST")
        self.assertEqual(local["action"], "establish_or_use_repository_local_proof_path")
        self.assertEqual(local["failure_state"], "LOCAL_PROOF_GAP")
        self.assertIn(
            "local_proof_does_not_promote_hosted_or_live_proof",
            self.p07["invariants"],
        )

    def test_language_policy_renders_imperative_non_retry_contract(self) -> None:
        renderer = self.policy["action_renderers"][
            "establish_or_use_repository_local_proof_path"
        ]
        phrases = renderer["imperative_required_phrases"]
        self.assertTrue(renderer["failure_state_required"])
        self.assertTrue(renderer["proof_required"])
        self.assertEqual(
            self.policy["when_predicates"]["always"]["requires"],
            {"min_dependency_ready_width": 0, "min_safe_capacity": 0},
        )
        text = "\n".join(phrases)
        self.assertIn("MUST establish or reuse", text)
        self.assertIn("quota-exhausted", text)
        self.assertIn("MUST suppress blind retries", text)
        for weak in ("consider", "where useful", "if appropriate", " could ", " may "):
            self.assertNotIn(weak, text.lower())

    def test_prompt_operations_binds_planning_and_building(self) -> None:
        for phrase in (
            "Hosted CI / local proof continuity",
            "planning, build/repair, validation, and integration prompts",
            "before hosted CI becomes a dependency",
            "execution-posture evidence, not automatic whole-sprint blockers",
            "Known non-transient provider limits suppress blind workflow retries",
            "Local PASS never promotes to hosted-runner",
            "P07's Prompt Semantic IR carries the executable MUST obligation",
        ):
            self.assertIn(phrase, self.prompt_ops)


if __name__ == "__main__":
    unittest.main()
