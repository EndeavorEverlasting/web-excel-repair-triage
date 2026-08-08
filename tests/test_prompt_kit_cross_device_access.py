from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

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

    def test_editable_android_checkout_is_explicit_and_ff_only(self) -> None:
        modes = cross_device.validate_contract_payload(self.load_contract())
        editable = modes["editable-checkout"]
        self.assertTrue(editable["manual_clone_required"])
        self.assertIn("--branch main --single-branch", editable["entry_point"])
        self.assertEqual(editable["update_command"], "git pull --ff-only origin main")
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

    def test_non_ff_only_editable_update_fails_closed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        for mode in payload["modes"]:
            if mode["id"] == "editable-checkout":
                mode["update_command"] = "git pull origin main"
                break
        with self.assertRaisesRegex(
            cross_device.CrossDeviceAccessError,
            "editable checkout must update with ff-only",
        ):
            cross_device.validate_contract_payload(payload)

    def test_repository_surfaces_are_connected(self) -> None:
        cross_device.validate_repository_surfaces()


if __name__ == "__main__":
    unittest.main()
