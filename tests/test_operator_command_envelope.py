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

import validate_operator_command_envelope as envelope


class OperatorCommandEnvelopeTests(unittest.TestCase):
    def test_complete_contract_and_fixture_suite_passes(self) -> None:
        result = envelope.validate_all()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["fixture_count"], 8)
        self.assertEqual(result["rules"], sorted(envelope.EXPECTED_RULES))

    def test_hardcoded_user_path_is_rejected(self) -> None:
        findings = envelope.audit_command(
            "$ErrorActionPreference='Stop'\n"
            "$Repo='C:\\Users\\Someone\\Desktop\\repo'\n"
            "Set-Location $Repo\n"
            "git fetch origin main --prune\n"
            "if($LASTEXITCODE -ne 0){throw 'failed'}"
        )
        self.assertIn("OC001", {item.rule_id for item in findings})

    def test_markdown_wrapped_url_is_rejected(self) -> None:
        findings = envelope.audit_command(
            "$Origin='[http://127.0.0.1:8765/](http://127.0.0.1:8765/)'"
        )
        self.assertEqual({item.rule_id for item in findings}, {"OC002"})

    def test_top_level_exit_is_rejected(self) -> None:
        findings = envelope.audit_command(
            "$ErrorActionPreference='Stop'\n"
            "Set-Location $env:TEMP\n"
            "if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }"
        )
        self.assertIn("OC003", {item.rule_id for item in findings})

    def test_fetch_before_location_gate_is_rejected(self) -> None:
        findings = envelope.audit_command(
            "$ErrorActionPreference='Stop'\n"
            "git fetch origin main --prune\n"
            "if($LASTEXITCODE -ne 0){throw 'failed'}"
        )
        self.assertIn("OC004", {item.rule_id for item in findings})

    def test_remote_fetch_requires_exact_pin(self) -> None:
        findings = envelope.audit_command(
            "$ErrorActionPreference='Stop'\n"
            "$Repo=Join-Path $env:TEMP 'repo'\n"
            "Set-Location $Repo\n"
            "git fetch origin main --prune\n"
            "if($LASTEXITCODE -ne 0){throw 'failed'}\n"
            "Get-Content harness/artifacts.v1.json"
        )
        self.assertIn("OC005", {item.rule_id for item in findings})

    def test_canonical_template_has_no_machine_specific_path_or_raw_url(self) -> None:
        text = envelope.validate_template()
        self.assertNotIn("C:\\Users\\", text)
        self.assertNotIn("https://github.com/", text)
        self.assertNotRegex(text, envelope.MARKDOWN_LINK)
        self.assertNotRegex(text, envelope.INTERACTIVE_EXIT)

    def test_report_is_bounded_to_outputs_when_repository_local(self) -> None:
        with self.assertRaisesRegex(ValueError, "under Outputs"):
            envelope._resolve_report("harness/reports/operator-command-runtime.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            external = envelope._resolve_report(str(Path(temp_dir) / "result.json"))
            self.assertIsNotNone(external)

    def test_manifest_domain_contract_shape_is_machine_readable(self) -> None:
        contract = json.loads(envelope.CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["canonical_artifact_id"], "harness-completeness-report")
        self.assertEqual(contract["validator"], "scripts/validate_operator_command_envelope.py")
        self.assertEqual(contract["tests"], "tests/test_operator_command_envelope.py")


if __name__ == "__main__":
    unittest.main()
