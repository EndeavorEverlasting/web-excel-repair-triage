#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_DRAFT = ROOT / "tmp/job-opportunity-search-draft.json"
SYNC_DRAFT = ROOT / "tmp/job-search-workspace-sync-draft.json"
TEST = ROOT / "tests/test_job_search_prompt_registry.py"


def run(*args: str) -> str:
    proc = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    print(proc.stdout, end="")
    return proc.stdout

inspect = json.loads(run(sys.executable, "scripts/prompt_registry_ops.py", "inspect"))
management = next((item for item in inspect["registries"] if item["registry_id"] == "management-operations-prompts"), None)
if not management:
    raise SystemExit("management-operations-prompts registry not found")
print(json.dumps({"routing_receipt": {"next_id": inspect["next_id"], "registry": management}}, indent=2))

portable = json.loads(run(
    sys.executable,
    "scripts/prompt_registry_ops.py",
    "add",
    "--input",
    str(PORTABLE_DRAFT.relative_to(ROOT)),
    "--registry",
    "management-operations-prompts",
))
sync = json.loads(run(
    sys.executable,
    "scripts/prompt_registry_ops.py",
    "add",
    "--input",
    str(SYNC_DRAFT.relative_to(ROOT)),
    "--registry",
    "management-operations-prompts",
))
if portable["id"] == sync["id"]:
    raise SystemExit("helper allocated duplicate prompt identity")
print(json.dumps({"portable_helper_receipt": portable, "sync_helper_receipt": sync}, indent=2))

portable_id = portable["id"]
sync_id = sync["id"]
TEST.write_text(f'''from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "web" / "prompt-kit" / "index.html"


class JobSearchPromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {{p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}}
        cls.portable = cls.prompts[{portable_id!r}]
        cls.sync = cls.prompts[{sync_id!r}]
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
        self.assertIn("Applied? | Priority | Status | Company | Role | Work Mode", c)
        self.assertIn("Job Description / Snapshot", c)
        self.assertIn("SEARCH COVERAGE RECEIPT", c)
        self.assertIn("Do not fabricate jobs from memory", c)
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
        self.assertIn("Applied? | Priority | Status | Company | Role | Work Mode", c)
        self.assertIn("posting status and application status separate", c)
        self.assertIn("WRITE WHEN AUTHORIZED; OTHERWISE RETURN A PATCH PLAN", c)
        self.assertIn("Report exact spreadsheet ranges/row IDs/files changed", c)
        self.assertIn("NO WRITE", c)
        self.assertIn("Job Opportunity Search & Trajectory Mapper", c)
        self.assertIn("Do not mix multiple people's job searches", c)
        self.assertEqual(p["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], c)

    def test_prompt_roles_are_distinct_and_generated_site_contains_semantics(self) -> None:
        self.assertNotEqual(self.portable["id"], self.sync["id"])
        self.assertEqual(self.portable.get("profile"), "career-operations")
        self.assertEqual(self.sync.get("profile"), "career-operations")
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


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

ledger = [
    {"insight": "portable job discovery from supplied trajectory or compact interview", "current_owner": portable_id, "action": "ADD", "proof": "distinct live-search trigger and source-saturation closure"},
    {"insight": "connected tracker/workspace persistence and reconciliation", "current_owner": sync_id, "action": "ADD", "proof": "distinct write/sync trigger and mutation-receipt closure"},
    {"insight": "subject isolation for user/brother/technician/other person", "current_owner": f"{portable_id}+{sync_id}", "action": "ADD", "proof": "both prompts forbid cross-person history/credential mixing"},
    {"insight": "tracker-ready opportunity schema with fit/gaps/next action/source/description", "current_owner": f"{portable_id}+{sync_id}", "action": "ADD", "proof": "shared schema asserted in focused regression"},
    {"insight": "resume tailoring and application drafting", "current_owner": "none in this contribution", "action": "OUT OF SCOPE", "proof": "current request centers discovery and persistence; avoids career super-prompt"},
    {"insight": "generic cross-repo/Drive management synchronization", "current_owner": "P77", "action": "ALREADY COVERED", "proof": "P77 remains management evidence sync; new prompt is career-tracker-specific and user-connected"},
]
print(json.dumps({"reverse_sweep_ledger": ledger}, indent=2))
print(json.dumps({"portable_id": portable_id, "sync_id": sync_id}, indent=2))
