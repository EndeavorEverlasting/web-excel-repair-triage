from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_prompt_registry_harness as cli
import prompt_registry_harness_contracts as contracts
import prompt_registry_profiles as passage


class PromptRegistryHarnessTests(unittest.TestCase):
    def test_domain_harness_is_complete_and_connected(self) -> None:
        harness = contracts.validate_domain_harness()
        manifest = harness["manifest"]
        self.assertEqual(manifest["schema_version"], "prompt-registry-harness/v1")
        self.assertEqual(set(manifest["components"]), contracts.REQUIRED_COMPONENT_IDS)
        self.assertEqual(len(manifest["skills"]), 6)
        self.assertEqual(
            set(harness["capabilities"]),
            {
                "conversation-entry",
                "repository-inspection",
                "bounded-repository-mutation",
                "validation-proof-routing",
                "integration-handoff",
                "prompt-registry-passage",
            },
        )
        self.assertEqual(len(harness["triggers"]), 9)

    def test_every_domain_skill_is_small_structured_and_indexed(self) -> None:
        manifest = contracts.load_json(contracts.DOMAIN_MANIFEST)
        domain_map = (ROOT / "harness" / "prompt-registry" / "CODEBASE_MAP.md").read_text(
            encoding="utf-8"
        )
        root_index = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
        for relative_path in manifest["skills"]:
            self.assertIn(relative_path, domain_map)
            self.assertIn(relative_path, root_index)
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            for heading in contracts.REQUIRED_SKILL_SECTIONS:
                self.assertIn(heading, text)

    def test_canary_contract_is_exact_and_identity_free(self) -> None:
        canary = contracts.load_json(contracts.CANARY)
        self.assertEqual(
            canary["required_first_nonempty_lines"],
            [
                "OBJECTIVE: <the current concrete objective>",
                "REPOS: <canonical owner/repository names with active branch when known, separated by semicolons; or none>",
            ],
        )
        rendered = json.dumps(canary).lower()
        for personal_marker in ("richard", "username", "user name", "call me"):
            self.assertNotIn(personal_marker, rendered)

    def test_every_effective_prompt_has_one_compact_profile(self) -> None:
        report = passage.build_report()
        self.assertTrue(report["coverage_complete"])
        self.assertEqual(report["profile_count"], report["prompt_count"])
        self.assertEqual(
            len(report["passage_order"]),
            len(set(report["passage_order"])),
        )
        self.assertEqual(
            {item["prompt_id"] for item in report["profiles"]},
            set(report["passage_order"]),
        )

    def test_profiles_reference_shared_contracts_without_prompt_text(self) -> None:
        harness = contracts.validate_domain_harness()
        forbidden = set(harness["profile_schema"]["forbidden_fields"])
        report = passage.build_report()
        for profile in report["profiles"]:
            self.assertFalse(forbidden & set(profile))
            self.assertIn(
                "harness/contracts/conversation-canary.v1.json",
                profile["shared_instruction_refs"],
            )
            self.assertIn(
                "registry/prompts/actionable-next-step-policy.v1.json",
                profile["shared_instruction_refs"],
            )
            self.assertEqual(
                profile["primary_skill"],
                passage.IMPACT_CAPABILITY_SKILL[profile["impact_class"]],
            )

    def test_impact_routing_is_deterministic_for_representative_prompts(self) -> None:
        def prompt(prompt_type: str, **overrides: object) -> dict[str, object]:
            payload: dict[str, object] = {
                "id": "PX",
                "seq": "999",
                "name": "Representative",
                "type": prompt_type,
                "class": "standard",
                "sprintRole": "operator",
                "useWhen": "",
                "inspectFirst": "",
                "expectedOutput": "",
                "nextStep": "",
                "proofGate": "",
                "keywords": [],
                "copyContent": "This body intentionally must not drive routing.",
            }
            payload.update(overrides)
            return payload

        self.assertEqual(passage.classify_impact(prompt("PLAN")), "plan")
        self.assertEqual(passage.classify_impact(prompt("BUILD")), "mutate")
        self.assertEqual(passage.classify_impact(prompt("VALIDATE")), "validate")
        self.assertEqual(passage.classify_impact(prompt("INTEGRATE")), "integrate")
        self.assertEqual(
            passage.classify_impact(
                prompt("REVIEW + REPAIR", proofGate="validator and runtime proof")
            ),
            "mixed",
        )
        self.assertEqual(passage.classify_impact(prompt("HARVEST")), "inspect")

    def test_prompt_filter_returns_one_known_profile(self) -> None:
        full = passage.build_report()
        first = full["passage_order"][0]
        filtered = passage.build_report(prompt_id=first.lower())
        self.assertTrue(filtered["coverage_complete"])
        self.assertEqual(filtered["profile_count"], 1)
        self.assertEqual(filtered["profiles"][0]["prompt_id"], first)

    def test_unknown_prompt_fails_closed(self) -> None:
        with self.assertRaises(contracts.PromptRegistryHarnessError):
            passage.build_report(prompt_id="P-NOT-REAL")

    def test_non_strict_audit_records_canary_gap_without_hiding_it(self) -> None:
        report = passage.build_report(strict_canary=False)
        self.assertEqual(
            report["canary_coverage_count"] + report["canary_missing_count"],
            report["profile_count"],
        )
        if report["canary_missing_count"]:
            self.assertFalse(report["canary_ready"])
            self.assertEqual(report["findings"][0]["severity"], "warning")
        else:
            self.assertTrue(report["canary_ready"])
            self.assertEqual(report["findings"], [])

    def test_strict_canary_exit_matches_current_registry_state(self) -> None:
        report = passage.build_report(strict_canary=True)
        expected = 0 if report["canary_ready"] else 3
        self.assertEqual(cli.main(["--strict-canary"]), expected)

    def test_report_schema_and_safe_output(self) -> None:
        report = passage.build_report()
        self.assertEqual(
            report["schema_version"],
            "prompt-registry-harness-audit-result/v1",
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "prompt-registry-harness-audit.json"
            written = passage.write_report(report, output)
            loaded = json.loads(written.read_text(encoding="utf-8"))
            self.assertEqual(loaded["profile_count"], report["profile_count"])
            self.assertEqual(loaded["passage_order"], report["passage_order"])

    def test_protected_output_roots_are_rejected(self) -> None:
        for protected in contracts.PROTECTED_OUTPUT_ROOTS:
            with self.assertRaises(contracts.PromptRegistryHarnessError):
                contracts.validate_output_path(protected / "forbidden.json")


if __name__ == "__main__":
    unittest.main()
