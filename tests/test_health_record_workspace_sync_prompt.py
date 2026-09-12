from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class HealthRecordWorkspaceSyncPromptTests(unittest.TestCase):
    def prompt(self) -> dict:
        prompts = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}
        return prompts["P140"]

    def test_identity_and_role_are_distinct_from_generic_repo_drive_sync(self) -> None:
        prompt = self.prompt()
        self.assertEqual(prompt["name"], "Connected Health Record Workspace Synchronizer")
        self.assertEqual(prompt["type"], "SYNC + ARTIFACT")
        self.assertEqual(prompt["class"], "HEALTH / RECORD SYNC")
        self.assertEqual(prompt["seq"], prompt["id"][1:])
        generic = next(item for item in build_prompt_kit_registry.load_prompt_registry() if item["name"] == "Repository + Google Drive Artifact Synchronizer")
        self.assertNotEqual(prompt["class"], generic["class"])
        self.assertIn("health connector discovery", prompt["keywords"])

    def test_prompt_preserves_private_canonical_health_contract(self) -> None:
        content = self.prompt()["copyContent"]
        for phrase in (
            "DISCOVER CAPABILITIES BEFORE ASKING",
            "SILENT CANONICAL RESOLUTION",
            "Capability discovery does not imply capability disclosure",
            "Subjects — one stable subject per tracked person or pet",
            "Problems — one stable row per ongoing tracked problem/condition",
            "Episodes — one row per distinct flare",
            "Checkins — append-only follow-up/progress observations",
            "Medications — longitudinal subject-medication relationships",
            "Product Reference",
            "data/Health_Subjects.csv",
            "data/Health_Problems.csv",
            "data/Health_Episodes.csv",
            "data/Health_Checkins.csv",
            "data/Health_Subject_Medications.csv",
            "SUBJ-###",
            "H-P###",
            "H-EYYYYMMDD-###",
            "H-CYYYYMMDD-###",
            "MEDREC-###",
            "Health Records/",
            "Health Records/Ledgers/",
            "Health Records/References/",
            "Health Records/Narrative/",
            "Health Records/Evidence/",
            "Health Tracking Ledger",
            "stable file identity over name-only matching or path cosmetics",
            "Treatment response is evidence about response, not proof of etiology",
            "READ BACK EVERY CLAIMED MUTATION",
            "FALLBACK WHEN THE CANONICAL WORKSPACE IS ABSENT",
        ):
            self.assertIn(phrase, content)

    def test_prompt_does_not_advertise_private_implementation_identity(self) -> None:
        content = self.prompt()["copyContent"]
        for forbidden in (
            "MedsPetsAndPeople",
            "EndeavorEverlasting",
            "1tSPSFP2v3yq6Kir0mt2gg0i1EsbLvRhiJQdlnk_ahOE",
            "0AHPtF1SfaW7gUk9PVA",
            "1QkhAVNwoucvsDx8KKd98J5hjKp8yHri_nGgbLSjUfow",
        ):
            self.assertNotIn(forbidden, content)
        self.assertIn("Do not volunteer private application names", content)
        self.assertIn("Access only resources needed for this health-record operation", content)

    def test_prompt_is_in_generated_site_and_has_tutorial_fallback_route(self) -> None:
        prompt = self.prompt()
        html = build_prompt_kit_registry.render()
        self.assertIn(f'"id": "{prompt["id"]}"', html)
        self.assertIn("Connected Health Record Workspace Synchronizer", html)
        deployed = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(deployed, html)
        coverage = json.loads((ROOT / "registry" / "prompts" / "tutorial-coverage.v1.json").read_text(encoding="utf-8"))
        wired = {item["prompt_id"] for item in coverage["wired_prompts"]}
        self.assertNotIn(prompt["id"], wired)
        self.assertEqual(coverage["fallback_status"], "CLASSIFIER_FALLBACK_NEEDS_WIRING")
        self.assertIn("Every canonical prompt", coverage["wiring_rule"])


if __name__ == "__main__":
    unittest.main()
