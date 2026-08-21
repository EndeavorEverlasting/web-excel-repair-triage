from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
MARKER = "OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT"


class OperationalCloseoutContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        cls.effective = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}
        cls.base = {p["id"]: p for p in json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))}
        ledger = json.loads((ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json").read_text(encoding="utf-8"))
        cls.ledger = {p["id"]: p for p in ledger["prompts"]}

    def test_shared_policy_requires_gap_risk_blocker_and_executable_continuation(self) -> None:
        self.assertEqual(self.policy["closeout_marker"], MARKER)
        appendix = self.policy["copy_content_appendix"]
        for phrase in (
            "REMAINING GAPS", "RISKS", "BLOCKERS", "PROOF CEILING",
            "INTEGRATION STATE", "NEXT ACTION / NEXT STEPS",
            "owner, dependency, exact command or operator action",
            "none; no safe actionable work remains",
        ):
            self.assertIn(phrase, appendix)

    def test_operational_effective_prompts_inherit_closeout_contract(self) -> None:
        tokens = ("BUILD", "REPAIR", "ARTIFACT", "RUNTIME", "CERT", "DEPLOY", "VERIFY", "ADVANCE")
        selected = [p for p in self.effective.values() if any(t in str(p["type"]).upper() for t in tokens)]
        self.assertGreater(len(selected), 0)
        for prompt in selected:
            with self.subTest(prompt_id=prompt["id"], prompt_type=prompt["type"]):
                content = prompt["copyContent"]
                self.assertIn(MARKER, content)
                self.assertIn("REMAINING GAPS", content)
                self.assertIn("PROOF CEILING", content)
                self.assertIn("first executable continuation", content)

    def test_p03_p07_p48_and_p83_are_strong_even_without_policy_injection(self) -> None:
        for prompt in (self.base["P03"], self.base["P07"], self.base["P48"], self.ledger["P83"]):
            with self.subTest(prompt_id=prompt["id"]):
                self.assertIn(MARKER, prompt["copyContent"])
                self.assertIn("remaining gaps, risks, blockers, proof ceiling, integration state", prompt["expectedOutput"].lower())
                self.assertIn("Report the current gap/risk/blocker", prompt["nextStep"])
                self.assertIn("Closeout is incomplete", prompt["proofGate"])
        self.assertLess(len(self.ledger["P83"]["copyContent"]), 8000)

    def test_builder_upgrades_legacy_appendix_missing_closeout(self) -> None:
        prompt = dict(self.base["P07"])
        marker = self.policy["marker"]
        prompt["copyContent"] = "BASE\n\n" + marker + "\n- Do not leave NEXT COMMAND blank.\n\n" + self.policy["integration_marker"] + "\n- merge.\n\n" + self.policy["freshness_marker"] + "\n- fetch."
        upgraded = build_prompt_kit_registry.apply_actionability_policy(prompt, self.policy)
        self.assertIn(MARKER, upgraded["copyContent"])
        self.assertEqual(upgraded["copyContent"].count(marker), 1)
        self.assertEqual(upgraded["copyContent"].count(MARKER), 1)

    def test_live_cert_domain_law_requires_actionable_closeout(self) -> None:
        text = (ROOT / "harness" / "specs" / "operator-delivery.md").read_text(encoding="utf-8")
        self.assertIn("## Actionable runtime / live-cert closeout", text)
        self.assertIn("remaining gaps; risks; blockers; proof ceiling; integration state", text)
        self.assertIn("owner, dependency, exact command or operator action", text)
        self.assertIn("genuine operator-only gate", text)

    def test_generated_site_is_exact_and_contains_closeout_contract(self) -> None:
        actual = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, build_prompt_kit_registry.render())
        self.assertIn(MARKER, actual)


if __name__ == "__main__":
    unittest.main()
