from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "prompts.json"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


class ContextToArtifactPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        prompts = json.loads(BASE.read_text(encoding="utf-8"))
        cls.p56 = next(item for item in prompts if item["id"] == "P56")
        cls.content = cls.p56["copyContent"]

    def test_p56_retains_canonical_artifact_identity(self) -> None:
        self.assertEqual(self.p56["name"], "Context-to-Artifact Generator")
        self.assertEqual(self.p56["type"], "BUILD + ARTIFACT")
        self.assertIn("actual requested artifact", self.p56["expectedOutput"].lower())

    def test_p56_has_explicit_capability_modes_and_no_repo_access_failure_boundary(self) -> None:
        for marker in (
            "CAPABILITY BOUNDARY — CHOOSE ONE MODE",
            "REPO_CAPABLE",
            "DOSSIER_ONLY",
            "ARTIFACT_ONLY",
            "A repository name in the request does not grant repository access.",
            "Do not claim repository inspection",
        ):
            self.assertIn(marker, self.content)

    def test_p56_labels_repository_claim_authority_in_dossier_only_mode(self) -> None:
        for marker in (
            "SUPPLIED_CONTEXT",
            "PROPOSED",
            "UNKNOWN_REQUIRES_REPO_INSPECTION",
            "PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY",
        ):
            self.assertIn(marker, self.content)
        self.assertIn("fake repository patch", self.content)
        self.assertIn("fabricated SHA, PR, CI result", self.content)

    def test_p56_requires_real_standalone_artifacts_and_repo_capable_handoff(self) -> None:
        for marker in (
            "complete standalone code/schemas/tests/examples",
            "Do not use fake imports from hypothetical repository modules.",
            "DOSSIER-ONLY REPOSITORY-CAPABLE HANDOFF",
            "strengthen rather than duplicate authority",
            "repository's actual branch/PR/promotion policy",
        ):
            self.assertIn(marker, self.content)

    def test_p56_preserves_proof_ceiling(self) -> None:
        self.assertIn("Never inflate proof", self.content)
        self.assertIn("do not prove compatibility with an inaccessible repository", self.content)
        self.assertIn("proof ceiling", self.p56["proofGate"].lower())

    def test_generated_site_contains_strengthened_p56(self) -> None:
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "CAPABILITY BOUNDARY — CHOOSE ONE MODE",
            "DOSSIER-ONLY REPOSITORY-CAPABLE HANDOFF",
            "UNKNOWN_REQUIRES_REPO_INSPECTION",
        ):
            self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
