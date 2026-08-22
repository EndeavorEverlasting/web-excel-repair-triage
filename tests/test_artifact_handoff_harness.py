from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_artifact_handoff_harness.py"
SPEC = importlib.util.spec_from_file_location("artifact_handoff_validator", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class ArtifactHandoffHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "harness" / "artifact-handoff" / "contracts" / "share-alias-download.v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_static_harness_contract_passes(self) -> None:
        report = validator.validate_static_harness()
        self.assertEqual("PASS", report["status"])
        self.assertEqual(5, len(report["fixtures"]))

    def test_literal_percent_encoded_filename_is_rejected(self) -> None:
        errors = validator.validate_alias_metadata(
            "ADMIN_SHARE_Project_CURRENT.xlsm",
            "Admin-Share - Project - CURRENT.xlsm",
            "Admin-Share%20-%20Project%20-%20CURRENT.xlsm",
            "sandbox:/mnt/data/Admin-Share%20-%20Project%20-%20CURRENT.xlsm",
        )
        self.assertTrue(any("percent-encoded" in error for error in errors))

    def test_percent_encoding_is_allowed_only_in_transport(self) -> None:
        errors = validator.validate_alias_metadata(
            "ADMIN_SHARE_Project_CURRENT.xlsm",
            "Admin-Share - Project - CURRENT.xlsm",
            "Admin-Share - Project - CURRENT.xlsm",
            "sandbox:/mnt/data/Admin-Share%20-%20Project%20-%20CURRENT.xlsm",
        )
        self.assertEqual([], errors)

    def test_encoded_slash_in_final_transport_segment_is_rejected(self) -> None:
        errors = validator.validate_alias_metadata(
            "ADMIN_SHARE_Project_CURRENT.xlsm",
            "Admin-Share - Project - CURRENT.xlsm",
            "Admin-Share - Project - CURRENT.xlsm",
            "sandbox:/mnt/data/hidden%2FAdmin-Share%20-%20Project%20-%20CURRENT.xlsm",
        )
        self.assertTrue(any("transport href" in error for error in errors))

    def test_extension_drift_is_rejected(self) -> None:
        errors = validator.validate_alias_metadata(
            "ADMIN_SHARE_Project_CURRENT.xlsm",
            "Admin-Share - Project - CURRENT.xlsx",
            "Admin-Share - Project - CURRENT.xlsx",
        )
        self.assertTrue(any("extension" in error for error in errors))

    def test_transport_target_drift_is_rejected(self) -> None:
        errors = validator.validate_alias_metadata(
            "CLIENT_SHARE_Project_SCOPE_CURRENT.xlsm",
            "Client-Share - Project Scope - CURRENT.xlsm",
            "Client-Share - Project Scope - CURRENT.xlsm",
            "sandbox:/mnt/data/Client-Share%20-%20Wrong%20Scope%20-%20CURRENT.xlsm",
        )
        self.assertTrue(any("transport href" in error for error in errors))

    def test_real_alias_pair_requires_identical_bytes_and_transport(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "ADMIN_SHARE_Project_CURRENT.xlsm"
            alias = root / "Admin-Share - Project - CURRENT.xlsm"
            canonical.write_bytes(b"same workbook bytes")
            alias.write_bytes(b"same workbook bytes")
            transport = "sandbox:/mnt/data/Admin-Share%20-%20Project%20-%20CURRENT.xlsm"
            receipt = validator.validate_runtime_pair(
                canonical,
                alias,
                "Admin-Share - Project - CURRENT.xlsm",
                transport,
            )
            self.assertTrue(receipt["byte_identical"])
            self.assertEqual(receipt["canonical_sha256"], receipt["alias_sha256"])
            self.assertEqual(transport, receipt["transport_href"])
            self.assertEqual(alias.name, receipt["transport_decoded_basename"])

    def test_real_alias_pair_rejects_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "ADMIN_SHARE_Project_CURRENT.xlsm"
            alias = root / "Admin-Share - Project - CURRENT.xlsm"
            canonical.write_bytes(b"source")
            alias.write_bytes(b"changed")
            with self.assertRaises(validator.ValidationError):
                validator.validate_runtime_pair(
                    canonical,
                    alias,
                    "Admin-Share - Project - CURRENT.xlsm",
                    "sandbox:/mnt/data/Admin-Share%20-%20Project%20-%20CURRENT.xlsm",
                )

    def test_contract_rejects_wrong_rule_keys(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["rules"].pop("byte_identity")
        payload["rules"]["unrelated"] = "not an owned rule"
        with self.assertRaises(validator.ValidationError):
            validator.validate_contract_payload(payload)

    def test_contract_rejects_non_boolean_expected_valid(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["fixtures"][0]["expected_valid"] = "true"
        with self.assertRaises(validator.ValidationError):
            validator.validate_contract_payload(payload)

    def test_output_traversal_is_rejected(self) -> None:
        with self.assertRaises(validator.ValidationError):
            validator.resolve_output_path("Outputs/../AGENTS.md")

    def test_manifest_validation_order_closes_with_patch_hygiene(self) -> None:
        manifest = json.loads(
            (ROOT / "harness" / "artifact-handoff" / "manifest.v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("git diff --check", manifest["validation_order"][-1])


if __name__ == "__main__":
    unittest.main()
