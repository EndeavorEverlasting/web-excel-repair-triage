from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_browser_proof_cleanup as cleanup_validator


class PromptKitBrowserProofCleanupHarnessTests(unittest.TestCase):
    def test_completeness_validator_passes_repository_contract(self) -> None:
        self.assertEqual(cleanup_validator.validate(), [])

    def test_manifest_is_preview_first_and_browser_state_is_out_of_scope(self) -> None:
        manifest = json.loads(
            (ROOT / "harness/browser-proof-cleanup/manifest.v1.json").read_text(encoding="utf-8")
        )
        contract = manifest["scratch_contract"]
        self.assertTrue(contract["preview_is_default"])
        self.assertTrue(contract["apply_requires_explicit_switch"])
        self.assertTrue(contract["system_temp_only"])
        self.assertTrue(contract["reject_reparse_points"])
        self.assertTrue(contract["browser_profile_data_out_of_scope"])
        self.assertTrue(contract["favorites_local_storage_out_of_scope"])

    def test_cleanup_runner_has_exact_scope_and_no_broad_temp_or_favorites_mutation(self) -> None:
        text = (ROOT / "scripts/Clear-PromptKitBrowserProofScratch.ps1").read_text(encoding="utf-8")
        self.assertIn("^prompt-kit-browser-proof-[0-9a-fA-F]{16,64}$", text)
        self.assertIn("web\\prompt-kit\\index.html", text)
        self.assertIn("ReparsePoint", text)
        self.assertIn("[switch]$Apply", text)
        self.assertIn("ShouldProcess", text)
        self.assertIn("$records.ToArray()", text)
        self.assertNotIn("candidates = @($records)", text)
        self.assertNotIn("Remove-Item -Path $env:TEMP", text)
        self.assertNotIn("Remove-Item $env:TEMP", text)
        self.assertNotIn("localStorage.clear(", text)
        self.assertNotIn("promptKit.favoritePromptIds.v1", text)

    def test_cleanup_runner_retains_previous_receipt_before_overwrite(self) -> None:
        text = (ROOT / "scripts/Clear-PromptKitBrowserProofScratch.ps1").read_text(encoding="utf-8")
        self.assertIn("backups/prompt-kit-browser-proof-cleanup", text)
        self.assertIn("Copy-Item -LiteralPath $ResolvedReportPath", text)
        self.assertIn("previous_receipt_backup", text)

    def test_root_harness_registers_cleanup_capability_and_trigger(self) -> None:
        manifest = json.loads((ROOT / "harness/manifest.v1.json").read_text(encoding="utf-8"))
        self.assertIn("prompt_kit_browser_proof_cleanup", manifest["domain_contracts"])
        caps = json.loads((ROOT / "harness/capabilities.v1.json").read_text(encoding="utf-8"))["capabilities"]
        triggers = json.loads((ROOT / "harness/triggers.v1.json").read_text(encoding="utf-8"))["triggers"]
        self.assertIn("prompt-kit-browser-proof-scratch-cleanup", {item["id"] for item in caps})
        self.assertIn("prompt-kit-browser-proof-temp-path", {item["id"] for item in triggers})

    def test_artifact_registry_keeps_scratch_noncanonical(self) -> None:
        registry = json.loads(
            (ROOT / "harness/browser-proof-cleanup/artifacts.v1.json").read_text(encoding="utf-8")
        )
        self.assertFalse(registry["ephemeral_inputs"]["canonical"])
        self.assertTrue(registry["ephemeral_inputs"]["must_not_be_committed"])
        artifact = registry["artifacts"][0]
        self.assertEqual(artifact["path"], "Outputs/prompt-kit-browser-proof-cleanup-report.json")


if __name__ == "__main__":
    unittest.main()
