from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_cross_device_access as cross_device


class PromptKitCrossDeviceAccessTests(unittest.TestCase):
    def load_contract(self) -> dict:
        return json.loads(cross_device.CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_focused_validator_passes(self) -> None:
        self.assertEqual(cross_device.main([]), 0)

    def test_load_json_rejects_non_object_root(self) -> None:
        with mock.patch.object(Path, "read_text", return_value="null"):
            with self.assertRaisesRegex(
                cross_device.CrossDeviceAccessError,
                "JSON root must be an object",
            ):
                cross_device.load_json(cross_device.CONTRACT_PATH)

    def test_normal_phone_use_never_requires_clone(self) -> None:
        modes = cross_device.validate_contract_payload(self.load_contract())
        self.assertFalse(modes["browser-use"]["manual_clone_required"])
        self.assertFalse(modes["phone-install"]["manual_clone_required"])
        self.assertEqual(
            modes["browser-use"]["entry_point"], cross_device.PUBLIC_URL
        )
        self.assertEqual(
            modes["phone-install"]["entry_point"], cross_device.LAUNCHER_URL
        )

    def test_windows_checkout_policy_is_canonical_and_duplicate_safe(self) -> None:
        payload = self.load_contract()
        policy = payload["windows_checkout_policy"]
        self.assertEqual(policy["desktop_dev_relative_root"], r"Desktop\dev")
        self.assertEqual(policy["repository_folder"], "web-excel-repair-triage")
        self.assertEqual(policy["automatic_duplicate_checkout_fallback"], "forbidden")
        self.assertFalse(policy["launcher_location_is_checkout_root"])
        self.assertEqual(policy["persistent_browser_proof_root"], "repository-owned Outputs only")

        acquire = (ROOT / "scripts" / "Acquire-LatestPromptKit.ps1").read_text(encoding="utf-8")
        portable = (ROOT / "scripts" / "Open-LatestPromptKitPortable.ps1").read_text(encoding="utf-8")
        launcher = (ROOT / "Open-Latest-PromptKit.cmd").read_text(encoding="utf-8")
        self.assertIn("[Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)", acquire)
        self.assertIn("no '-latest' sibling clone was created", acquire)
        self.assertIn("no '-latest' sibling clone was created", portable)
        self.assertIn("canonical Desktop\\dev\\web-excel-repair-triage", launcher)
        for forbidden in (
            r"%~dp0dev\web-excel-repair-triage",
            "$RepositoryFolderName-latest",
            '"$RepositoryFolderName-$suffix"',
            "OG Laptop Backup\\Desktop\\dev",
        ):
            self.assertNotIn(forbidden, acquire + portable + launcher)

    def test_editable_android_checkout_requires_state_gates_and_ff_only_merge(self) -> None:
        modes = cross_device.validate_contract_payload(self.load_contract())
        editable = modes["editable-checkout"]
        self.assertTrue(editable["manual_clone_required"])
        self.assertIn("--branch main --single-branch", editable["entry_point"])
        self.assertEqual(
            editable["existing_checkout_requirements"],
            cross_device.EDITABLE_CHECKOUT_REQUIREMENTS,
        )
        self.assertEqual(
            editable["update_sequence"],
            cross_device.EDITABLE_UPDATE_SEQUENCE,
        )
        self.assertNotIn("git pull", "\n".join(editable["update_sequence"]))
        prereqs = "\n".join(editable["android_prerequisites"])
        for phrase in ("Termux", "F-Droid", "pkg update", "pkg install git"):
            self.assertIn(phrase, prereqs)

    def test_browser_clone_regression_fails_closed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        for mode in payload["modes"]:
            if mode["id"] == "browser-use":
                mode["manual_clone_required"] = True
                break
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "browser use must never require a manual clone",
        ):
            cross_device.validate_contract_payload(payload)

    def test_unsafe_editable_update_sequence_fails_closed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        for mode in payload["modes"]:
            if mode["id"] == "editable-checkout":
                mode["update_sequence"][-1] = "git merge origin/main"
                break
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "safe update sequence drifted",
        ):
            cross_device.validate_contract_payload(payload)

    def test_missing_editable_branch_gate_fails_closed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        for mode in payload["modes"]:
            if mode["id"] == "editable-checkout":
                mode["existing_checkout_requirements"]["branch"] = "any"
                break
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "safety requirements drifted",
        ):
            cross_device.validate_contract_payload(payload)

    def test_normal_use_section_rejects_contradictory_clone_instruction(self) -> None:
        text = "\n".join(
            (
                "## Phone, tablet, or any browser",
                cross_device.PUBLIC_URL,
                "No clone is required.",
                "git clone https://example.invalid/repo.git",
                "## Next section",
            )
        )
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "contradictory normal-use instruction",
        ):
            cross_device.require_markdown_section(
                text,
                "## Phone, tablet, or any browser",
                required=(cross_device.PUBLIC_URL, "No clone is required."),
                forbidden=("git clone",),
                label="synthetic.md",
            )

    def test_workflow_entry_point_drift_fails_closed(self) -> None:
        payload = json.loads(
            cross_device.WORKFLOWS_PATH.read_text(encoding="utf-8")
        )
        mutated = copy.deepcopy(payload)
        acquisition = next(
            item
            for item in mutated["workflows"]
            if item["id"] == "technician-acquisition"
        )
        acquisition["entry_points"] = ["Open-Latest-PromptKit.cmd"]
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "entry points drifted",
        ):
            cross_device.validate_workflow_registration(mutated)

    def test_capability_owner_drift_fails_closed(self) -> None:
        payload = json.loads(
            cross_device.CAPABILITIES_PATH.read_text(encoding="utf-8")
        )
        mutated = copy.deepcopy(payload)
        capability = next(
            item
            for item in mutated["capabilities"]
            if item["id"] == "technician-prompt-kit-acquisition"
        )
        capability["implementation"] = {"kind": "script", "path": "other.py"}
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "implementation ownership drifted",
        ):
            cross_device.validate_capability_registration(mutated)

    def test_trigger_route_drift_fails_closed(self) -> None:
        payload = json.loads(
            cross_device.TRIGGERS_PATH.read_text(encoding="utf-8")
        )
        mutated = copy.deepcopy(payload)
        trigger = next(
            item
            for item in mutated["triggers"]
            if item["id"] == cross_device.ACQUISITION_TRIGGER
        )
        trigger["workflow"] = "WORKFLOW.md#wrong"
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "trigger workflow drifted",
        ):
            cross_device.validate_trigger_registration(mutated)

    def test_repository_surfaces_are_connected(self) -> None:
        cross_device.validate_repository_surfaces()


if __name__ == "__main__":
    unittest.main()
