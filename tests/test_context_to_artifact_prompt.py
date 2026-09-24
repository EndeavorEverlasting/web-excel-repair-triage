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

    def test_p56_recovers_whole_relevant_context_and_resolves_target(self) -> None:
        for marker in (
            "THE CURRENT REQUEST IS THE ANCHOR, NOT THE CONTEXT BOUNDARY",
            "CONTEXT IS AN ANCHOR, NOT A BOUNDARY",
            "accepted and rejected decisions",
            "internal context ledger",
            "PASS 1 reads forward",
            "PASS 2 traverses the same relevant context from the opposite direction",
            "ARTIFACT TARGET RESOLUTION",
            "CREATE_NEW",
            "UPDATE_EXISTING",
            "REPAIR_EXISTING",
            "EXPORT/PUBLISH",
            "IMPLEMENTATION_PACKET",
        ):
            self.assertIn(marker, self.content)
        self.assertIn("Recover facts yourself before asking the user to repeat them.", self.p56["inspectFirst"])
        self.assertIn("whole relevant context", self.p56["expectedOutput"].lower())
        ordered_sections = (
            "CONTEXT IS AN ANCHOR, NOT A BOUNDARY",
            "ARTIFACT TARGET RESOLUTION",
            "CAPABILITY BOUNDARY — CHOOSE ONE MODE",
            "CANONICAL OWNER + DERIVATION CONTRACT",
            "ARTIFACT EXECUTION CONTRACT",
            "SECOND-PASS COMPLETENESS REVIEW",
        )
        positions = [self.content.index(marker) for marker in ordered_sections]
        self.assertEqual(positions, sorted(positions), "P56 must recover context before target resolution and artifact execution")

    def test_p56_reuses_artifact_derivation_and_provider_owners(self) -> None:
        for marker in (
            "CANONICAL OWNER + DERIVATION CONTRACT",
            "Creation language such as create/generate/build/produce/make/draft/export defaults to CREATE_NEW",
            "preferred read-only reference",
            "Same-identity mutation requires explicit update/repair-in-place intent",
            "artifact-derivation owner",
            "choose a distinct output identity before opening a writer/save path",
            "reuse the existing stable identity and specialized synchronization owner",
            "Do not hand-edit generated output as source truth",
            "COMPLEMENT — DO NOT MERELY TRANSCRIBE",
            "SECOND-PASS COMPLETENESS REVIEW",
        ):
            self.assertIn(marker, self.content)

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
            "complete standalone code/schemas/tests/examples",
            "Never inflate proof",
            "PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY",
        ):
            self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
