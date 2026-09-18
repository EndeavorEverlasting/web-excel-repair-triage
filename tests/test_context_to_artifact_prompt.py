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


    def test_p56_recovers_target_from_relevant_context_without_context_courier_work(self) -> None:
        for marker in (
            "THE IMMEDIATELY PRECEDING REQUEST IS THE ANCHOR, NOT THE CONTEXT BOUNDARY",
            "CONTEXT HARVEST — PASS 1",
            "CONTEXT HARVEST — PASS 2 / ARTIFACT RECONCILIATION",
            "Do not ask the operator to restate recoverable context.",
            "insight | source/evidence | authority/status | artifact impact",
        ):
            self.assertIn(marker, self.content)

    def test_p56_resolves_artifact_owner_identity_and_operation_before_generation(self) -> None:
        for marker in (
            "ARTIFACT TARGET RESOLUTION",
            "CANONICAL OWNER / ENGINE",
            "CREATE_NEW",
            "UPDATE_EXISTING",
            "preferred read-only reference",
            "artifact-derivation harness",
            "owning artifact engine",
            "Never infer overwrite authority",
        ):
            self.assertIn(marker, self.content)

    def test_p56_requires_real_artifact_inspection_and_reverse_reconciliation(self) -> None:
        for marker in (
            "Generate the actual requested deliverable now",
            "A generator exit code is not artifact proof",
            "open/read/inspect the generated artifact itself",
            "Disposition every material harvested insight once",
            "bounded fixed point",
            "Do not substitute the artifact-generation prompt for the artifact.",
        ):
            self.assertIn(marker, self.content)
        self.assertIn("conversation to artifact", self.p56["keywords"])
        self.assertIn("artifact derivation", self.p56["keywords"])

    def test_generated_site_contains_strengthened_p56(self) -> None:
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "CAPABILITY BOUNDARY — CHOOSE ONE MODE",
            "CONTEXT HARVEST — PASS 1",
            "ARTIFACT TARGET RESOLUTION",
            "CREATE_NEW",
            "CONTEXT HARVEST — PASS 2 / ARTIFACT RECONCILIATION",
            "DOSSIER-ONLY REPOSITORY-CAPABLE HANDOFF",
            "UNKNOWN_REQUIRES_REPO_INSPECTION",
            "complete standalone code/schemas/tests/examples",
            "Never inflate proof",
            "PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY",
        ):
            self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
