from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "web" / "prompt-kit" / "index.html"
TUTORIAL = ROOT / "docs" / "JOB_APPLICATION_PROMPT_WORKFLOW.md"


class JobSearchPromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}
        cls.portable = cls.prompts['P126']
        cls.sync = cls.prompts['P127']
        cls.application_pack = next(
            p for p in cls.prompts.values()
            if p["name"] == 'Verified Job Opportunity Application Pack Builder'
        )
        cls.tutorial = TUTORIAL.read_text(encoding="utf-8")
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        cls.site = SITE.read_text(encoding="utf-8")

    def test_portable_job_search_prompt_is_interactive_broad_and_subject_safe(self) -> None:
        p = self.portable
        c = p["copyContent"]
        self.assertEqual(p["name"], "Job Opportunity Search & Trajectory Mapper")
        self.assertEqual(p["type"], "RESEARCH + EVIDENCE")
        self.assertEqual(p["class"], "CAREER / OPPORTUNITY DISCOVERY")
        self.assertIn("TRAJECTORY MODE", c)
        self.assertIn("INTERVIEW MODE", c)
        self.assertIn("one compact batch of questions", c)
        self.assertIn("Never silently apply the current chat user's credentials", c)
        self.assertIn("SEARCH BROADLY, THEN PREFER PRIMARY SOURCES", c)
        self.assertIn("direct employer career pages", c)
        self.assertIn("SEARCH TO BOUNDED SOURCE SATURATION", c)
        self.assertIn("at least 10 viable current leads", c)
        self.assertIn("Hard constraints are gates", c)
        self.assertIn("Applied? | Priority | Posting Status | Application Status | Company | Role | Work Mode", c)
        self.assertIn("Job Description / Snapshot", c)
        self.assertIn("SEARCH COVERAGE RECEIPT", c)
        self.assertIn("Do not fabricate jobs from memory", c)
        self.assertIn("page accessibility alone is insufficient", c)
        self.assertIn("Company + role + location/work mode alone is not sufficient identity", c)
        self.assertIn("preserve separate rows when identity remains uncertain", c)
        self.assertEqual(p["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], c)

    def test_connected_workspace_prompt_reuses_tracker_and_binds_writes(self) -> None:
        p = self.sync
        c = p["copyContent"]
        self.assertEqual(p["name"], "Connected Job Search Workspace & Tracker Synchronizer")
        self.assertEqual(p["type"], "MAINTENANCE")
        self.assertEqual(p["class"], "CAREER / WORKSPACE OPERATIONS")
        self.assertIn("DISCOVER BEFORE CREATING", c)
        self.assertIn("Do not create `Job Tracker 2`", c)
        self.assertIn("Google Drive / Google Sheets application tracker", c)
        self.assertIn("user-authorized Gmail", c)
        self.assertIn("user-authorized Calendar", c)
        self.assertIn("Applied? | Priority | Posting Status | Application Status | Company | Role | Work Mode", c)
        self.assertIn("posting status and application status separate", c)
        self.assertIn("Company + role + location/work mode alone is discovery evidence, not identity", c)
        self.assertIn("append a separate row when identity remains uncertain", c)
        self.assertIn("Date Applied, Application Status, Follow-Up Due", c)
        self.assertIn("WRITE WHEN AUTHORIZED; OTHERWISE RETURN A PATCH PLAN", c)
        self.assertIn("Report exact spreadsheet ranges/row IDs/files changed", c)
        self.assertIn("NO WRITE", c)
        self.assertIn("Job Opportunity Search & Trajectory Mapper", c)
        self.assertIn("Do not mix multiple people's job searches", c)
        self.assertEqual(p["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], c)

    def test_prompt_roles_are_distinct_and_generated_site_contains_semantics(self) -> None:
        self.assertNotEqual(self.portable["id"], self.sync["id"])
        self.assertNotIn("profile", self.portable)
        self.assertNotIn("profile", self.sync)
        for marker in (
            "Job Opportunity Search & Trajectory Mapper",
            "Connected Job Search Workspace & Tracker Synchronizer",
            "SEARCH TO BOUNDED SOURCE SATURATION",
            "SEARCH COVERAGE RECEIPT",
            "DISCOVER BEFORE CREATING",
            "MUTATION RECEIPT",
            "Job Description / Snapshot",
        ):
            self.assertIn(marker, self.site)

    def test_chat_harvest_constraints_survive_without_person_specific_assumptions(self) -> None:
        p = self.portable["copyContent"]
        self.assertIn("quality", p.casefold())
        self.assertIn("direct employer", p.casefold())
        self.assertIn("requirements / gaps", p.casefold())
        self.assertIn("follow-up due", p.casefold())
        self.assertNotIn("Richard Perez", p)
        self.assertNotIn("Pat", p)


def test_application_pack_verifies_tailors_and_stops_before_submission(self) -> None:
    p = self.application_pack
    c = p["copyContent"]
    self.assertEqual(p["id"], 'P139')
    self.assertEqual(p["name"], 'Verified Job Opportunity Application Pack Builder')
    self.assertEqual(p["type"], "BUILD + ARTIFACT")
    self.assertEqual(p["class"], "CAREER / APPLICATION EXECUTION")
    for required in (
        "OPPORTUNITY VERIFICATION RECEIPT",
        "FIT / GAP MATRIX",
        "Ready to Apply",
        "DO NOT AUTO-SUBMIT",
        "recruiter message is evidence of outreach",
        "Job Opportunity Search & Trajectory Mapper",
        "Connected Job Search Workspace & Tracker Synchronizer",
        "EndeavorEverlasting/EscapeHatch",
        "sensitive PII",
        "MUTATION RECEIPT",
    ):
        self.assertIn(required, c)
    self.assertNotIn("Richard Perez", c)
    self.assertNotIn("micro1", c.casefold())
    self.assertEqual(p["actionabilityPolicy"], self.policy["policy_id"])
    self.assertIn(self.policy["marker"], c)
    self.assertIn(p["name"], self.site)

def test_job_application_tutorial_connects_discovery_pack_and_sync(self) -> None:
    self.assertIn("P126", self.tutorial)
    self.assertIn('P139', self.tutorial)
    self.assertIn("P127", self.tutorial)
    self.assertIn('Verified Job Opportunity Application Pack Builder', self.tutorial)
    self.assertIn("manual submission", self.tutorial.casefold())
    self.assertIn("Ready to Apply", self.tutorial)

if __name__ == "__main__":
    unittest.main()
