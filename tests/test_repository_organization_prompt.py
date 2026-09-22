import unittest
from scripts.build_prompt_kit_registry import load_prompt_registry

class RepositoryOrganizationPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = load_prompt_registry()
        cls.prompt = next(
            p for p in cls.prompts
            if p.get("name") == "Repository Organization Auditor & Organizer"
        )

    def test_identity_and_distinct_domain(self):
        self.assertEqual(self.prompt["id"], "P144")
        self.assertEqual(self.prompt["type"], "AUDIT + REPAIR")
        self.assertEqual(self.prompt["class"], "REPOSITORY / ORGANIZATION & LIFECYCLE")
        self.assertNotEqual(self.prompt["id"], "P142")

    def test_audit_is_read_only_and_zero_change_is_valid(self):
        content = self.prompt["copyContent"]
        for phrase in (
            "AUDIT THE REPOSITORY'S ORGANIZATION BEFORE CHANGING IT",
            "AUDIT: read-only",
            "A later generic execution clause never promotes AUDIT into ORGANIZE",
            "AUDIT STOP CONDITION",
            "Zero changes is a valid conclusion",
            "Do not mutate the repository under AUDIT",
        ):
            self.assertIn(phrase, content)
        self.assertLess(
            content.index("7. PRODUCE THE READ-ONLY AUDIT LEDGER"),
            content.index("8. ORGANIZE ONLY AFTER THE EXECUTION GATE"),
        )

    def test_topology_lifecycle_reachability_and_inflight_are_owned(self):
        content = self.prompt["copyContent"]
        for phrase in (
            "CANONICAL_OWNER",
            "GENERATED / DERIVED",
            "ACTIVE_IN_FLIGHT",
            "MISPLACED",
            "STALE / SUPERSEDED",
            "ARCHIVE_CANDIDATE",
            "ORPHANED",
            "TRACE REACHABILITY BEFORE ANY PROPOSED MOVE",
            "workflow references",
            "generated-owner declarations",
            "IN-FLIGHT STATE",
            "HYGIENE",
            "NAVIGATION",
        ):
            self.assertIn(phrase, content)

    def test_specialist_boundaries_remain_distinct(self):
        content = self.prompt["copyContent"]
        for prompt_id in ("P03", "P06", "P76", "P78", "P92", "P95", "P124", "P142"):
            self.assertIn(prompt_id, content)
        self.assertIn("ORGANIZATION IS NOT ARCHITECTURE", content)
        self.assertIn("Google Drive workspace organization", content)
        self.assertIn("source-code readability", self.prompt["useWhen"])

if __name__ == "__main__":
    unittest.main()
