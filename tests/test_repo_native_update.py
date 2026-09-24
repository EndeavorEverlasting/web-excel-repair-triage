import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import repo_native_update_lib as lib
import run_repo_native_update as generator
import validate_repo_native_update_harness as harness


OWNED_OUTPUT = "harness/repo-native-update/generated/canary_constants.py"

VALID_CANARY_INPUT = {
    "schema_version": lib.CANARY_INPUT_SCHEMA,
    "surface_id": "canary-constants",
    "module_name": "canary_constants",
    "description": "Bounded canary constants for repository-native update proof",
    "ordered_keys": [
        "ACTIONS_REQUIRED",
        "CONTRACT_SCHEMA",
        "GENERATOR_ID",
        "SURFACE_ID",
        "TRIGGER_PRIMARY",
    ],
    "constants": {
        "ACTIONS_REQUIRED": False,
        "CONTRACT_SCHEMA": "repo-native-update/v1",
        "GENERATOR_ID": "repo-native-update",
        "SURFACE_ID": "canary-constants",
        "TRIGGER_PRIMARY": "cli",
    },
}


class RepoNativeUpdateTests(unittest.TestCase):
    def test_static_harness_is_complete(self):
        self.assertEqual(harness.validate_static_harness()["status"], "PASS")

    def test_generate_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            self._seed_harness(temp_root)
            first = generator.cmd_generate(
                "canary-constants",
                check_only=False,
                receipt_raw="Outputs/repo-native-update/receipt.json",
            )
            self.assertEqual(first, 0)
            output_path = temp_root / OWNED_OUTPUT
            first_text = output_path.read_text(encoding="utf-8")

            second = generator.cmd_generate(
                "canary-constants",
                check_only=True,
                receipt_raw="Outputs/repo-native-update/receipt.json",
            )
            self.assertEqual(second, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), first_text)

    def test_malformed_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            self._seed_harness(temp_root)
            bad_input = temp_root / "harness/repo-native-update/inputs/canary-constants.v1.json"
            bad_input.write_text(
                json.dumps(
                    {
                        "schema_version": lib.CANARY_INPUT_SCHEMA,
                        "ordered_keys": ["ONLY_ONE"],
                        "constants": {
                            "ONLY_ONE": True,
                            "EXTRA": False,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(lib.RepoNativeUpdateError):
                generator.validate_input_for_surface(
                    lib.resolve_surface(lib.load_contract(), "canary-constants")
                )

    def test_undeclared_destination_is_rejected(self):
        surface = {
            "id": "canary-constants",
            "owned_outputs": [OWNED_OUTPUT],
        }
        with self.assertRaises(lib.RepoNativeUpdateError):
            lib.resolve_owned_output("harness/repo-native-update/generated/other.py", surface)

    def test_path_traversal_and_forbidden_prefix_rejected(self):
        surface = {
            "id": "canary-constants",
            "owned_outputs": [OWNED_OUTPUT, ".github/workflows/evil.yml"],
        }
        for target in ("../outside.py", "harness/../outside.py"):
            with self.assertRaises(lib.RepoNativeUpdateError):
                lib.resolve_owned_output(target, surface)
        with self.assertRaises(lib.RepoNativeUpdateError):
            lib.resolve_owned_output(
                ".github/workflows/evil.yml",
                surface,
                contract={
                    "forbidden_output_prefixes": [".github/", "AGENTS.md"],
                },
            )

    def test_check_detects_drift_when_file_corrupted(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            self._seed_harness(temp_root)
            self.assertEqual(
                generator.cmd_generate(
                    "canary-constants",
                    check_only=False,
                    receipt_raw="Outputs/repo-native-update/receipt.json",
                ),
                0,
            )
            output_path = temp_root / OWNED_OUTPUT
            output_path.write_text("# corrupted\n", encoding="utf-8")
            self.assertEqual(
                generator.cmd_generate(
                    "canary-constants",
                    check_only=True,
                    receipt_raw="Outputs/repo-native-update/receipt.json",
                ),
                2,
            )

    def _seed_harness(self, temp_root: Path) -> None:
        contract = {
            "schema_version": lib.CONTRACT_SCHEMA,
            "generator_id": "repo-native-update",
            "generator_version": "1.0.0",
            "forbidden_output_prefixes": [".github/", "AGENTS.md", "Candidates/", "Active/"],
            "surfaces": [
                {
                    "id": "canary-constants",
                    "input_path": "harness/repo-native-update/inputs/canary-constants.v1.json",
                    "owned_outputs": [OWNED_OUTPUT],
                    "trigger": "cli",
                    "proof_ceiling": "Deterministic constant module generation from pinned JSON input.",
                }
            ],
        }
        input_path = (
            temp_root / "harness/repo-native-update/inputs/canary-constants.v1.json"
        )
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(json.dumps(VALID_CANARY_INPUT, indent=2) + "\n", encoding="utf-8")
        contract_path = (
            temp_root / "harness/repo-native-update/contracts/repo-native-update.v1.json"
        )
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

        patches = [
            mock.patch.object(lib, "ROOT", temp_root),
            mock.patch.object(generator, "ROOT", temp_root),
            mock.patch.object(lib, "CONTRACT_PATH", contract_path),
            mock.patch.object(lib, "DOMAIN", temp_root / "harness/repo-native-update"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)


if __name__ == "__main__":
    unittest.main()
