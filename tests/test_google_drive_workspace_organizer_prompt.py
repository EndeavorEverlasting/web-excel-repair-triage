from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
EXPECTED_ID = "P142"
EXPECTED_NAME = "Google Drive Workspace Organizer"


class GoogleDriveWorkspaceOrganizerPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.prompt = next(item for item in payload["prompts"] if item["id"] == EXPECTED_ID)
        cls.p111 = next(item for item in payload["prompts"] if item["id"] == "P111")
        cls.content = cls.prompt["copyContent"]

    def assert_markers(self, *markers: str) -> None:
        for marker in markers:
            self.assertIn(marker, self.content)

    def test_helper_allocated_identity_and_distinct_role(self) -> None:
        self.assertEqual(self.prompt["name"], EXPECTED_NAME)
        self.assertEqual(self.prompt["seq"], "142")
        self.assertEqual(self.prompt["copySheet"], "P142_COPY_SAFE")
        self.assertEqual(self.prompt["type"], "CLEANUP")
        self.assertEqual(self.prompt["class"], "DRIVE / WORKSPACE ORGANIZATION")
        self.assertIn("without requiring a repository", self.prompt["sprintRole"])
        self.assertIn("rather than repository↔Drive artifact synchronization", self.prompt["useWhen"])

    def test_distinct_from_p111_sync_owner(self) -> None:
        self.assertEqual(self.p111["name"], "Repository + Google Drive Artifact Synchronizer")
        self.assertIn("P142", self.p111["copyContent"])
        self.assertIn("route to P111", self.content)
        self.assertNotEqual(self.prompt["sprintRole"], self.p111["sprintRole"])
        self.assertIn("organize google drive", self.prompt["keywords"])
        self.assertIn("google drive sync", self.p111["keywords"])

    def test_non_destructive_organization_contract(self) -> None:
        self.assert_markers(
            "ORGANIZE AN EXISTING GOOGLE DRIVE WORKSPACE",
            "DO NOT REQUIRE A REPOSITORY",
            "KEEP_IN_PLACE",
            "DEDUPE_KEEP",
            "PRESERVE IDENTITY, LINKS, AND PERMISSIONS",
            "FAIL CLOSED ON AMBIGUITY",
            "READ BACK AND VERIFY",
            "route to P77",
            "route to P140",
        )

    def test_generated_site_contains_organizer(self) -> None:
        deployed = SITE.read_text(encoding="utf-8")
        for marker in (
            "P142",
            "Google Drive Workspace Organizer",
            "ORGANIZE AN EXISTING GOOGLE DRIVE WORKSPACE",
            "PRESERVE IDENTITY, LINKS, AND PERMISSIONS",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
