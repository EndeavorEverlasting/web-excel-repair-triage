from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_prompt_semantic_coverage as semantic

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
PROFILES = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
MIGRATIONS = ROOT / "harness" / "prompt-topology" / "prompt-capability-migrations.v1.json"
SITE = ROOT / "web" / "prompt-kit" / "index.html"


class RepositoryDriveArtifactSynchronizerPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.prompt = next(item for item in payload["prompts"] if item["id"] == "P111")
        cls.content = cls.prompt["copyContent"]
        cls.profiles_payload = json.loads(PROFILES.read_text(encoding="utf-8"))
        cls.profile = next(
            row
            for row in cls.profiles_payload["profiles"]
            if row["prompt_id"] == "P111" and row["profile_status"] == "ACCEPTED"
        )
        cls.migrations = json.loads(MIGRATIONS.read_text(encoding="utf-8"))["migrations"]

    def assert_markers(self, *markers: str) -> None:
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.content)

    def test_specialized_artifact_closure_is_mandatory(self) -> None:
        self.assert_markers(
            "SPECIALIZED ARTIFACT CLOSURE / NO DEFERRED EVIDENCE",
            "photo, screenshot, attachment, evidence row, workbook, generated artifact",
            "MUST invoke or route through that canonical owner whenever it is safely executable",
            "MUST NOT classify the dependency as SKIP or PRIVATE merely because the generic synchronizer does not own its bytes",
            "PRIVATE / DO-NOT-SYNC forbids inappropriate generic/repository publication",
            "approved private evidence owner",
            "durable canonical identity and readback proof",
            "hardware photo",
            "BLOCKED with its exact owner, target, dependency, and next action",
        )

    def test_current_conversation_attachments_are_candidate_artifacts(self) -> None:
        self.assertIn(
            "Current-conversation attachments count as candidate artifacts whenever the synchronized artifact cites, describes, depends on, or derives a factual claim from them.",
            self.content,
        )
        self.assertIn(
            "Do not omit an attachment from the artifact set merely because its bytes should stay out of Git.",
            self.content,
        )

    def test_private_boundary_preserves_privacy_without_destroying_evidence(self) -> None:
        self.assert_markers(
            "PRIVATE / DO-NOT-SYNC — excluded from generic/repository publication",
            "does not mean",
            "do not persist",
            "Do not place private photo/screenshot/workbook bytes in the repository unless the specialized owner explicitly permits it.",
        )

    def test_specialized_owner_blocker_prevents_false_completion(self) -> None:
        self.assert_markers(
            "Synchronization is incomplete while a material supporting reference lacks its required durable identity/readback proof.",
            "If the specialized workflow cannot execute",
            "do not convert that dependency into SKIP",
            "do not claim the overall synchronization complete",
        )

    def test_p111_has_accepted_profile_bound_to_final_body(self) -> None:
        self.assertGreaterEqual(self.profile["profile_version"], 2)
        self.assertEqual(
            self.profile["canonical_prompt_hash"],
            semantic.compute_canonical_prompt_hash(self.prompt),
        )
        self.assertTrue(self.profile["direct_assignments"])
        self.assertEqual(
            self.profiles_payload["profile_count"],
            len(self.profiles_payload["profiles"]),
        )
        p111_migrations = [
            row
            for row in self.migrations
            if row.get("prompt_id") == "P111" and row.get("migration_kind") == "STRENGTHEN"
        ]
        self.assertTrue(p111_migrations)
        latest = p111_migrations[-1]
        self.assertEqual(latest["from_profile_version"], 1)
        self.assertEqual(latest["to_profile_version"], 2)
        self.assertTrue(latest["source_history_migration_id"])

    def test_generated_site_contains_strengthened_p111(self) -> None:
        deployed = SITE.read_text(encoding="utf-8")
        for marker in (
            "P111",
            "Repository + Google Drive Artifact Synchronizer",
            "SPECIALIZED ARTIFACT CLOSURE / NO DEFERRED EVIDENCE",
            "Current-conversation attachments count as candidate artifacts",
            "approved private evidence owner",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
