from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts/resolve_prompt_kit_profile_route.py"
VALIDATOR = ROOT / "scripts/validate_prompt_kit_profile_routing.py"
CONTRACT = ROOT / "harness/contracts/prompt-kit-profile-qualified-routing.v1.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


class PromptKitProfileRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module("prompt_kit_profile_route_tests", RESOLVER)
        cls.validator = load_module("prompt_kit_profile_route_validator_tests", VALIDATOR)
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_contract_keeps_triage_active_and_agentswitchboard_related(self):
        self.validator.validate_contract_payload(copy.deepcopy(self.contract))
        self.assertEqual(
            self.contract["repository"],
            "EndeavorEverlasting/web-excel-repair-triage",
        )
        related = self.contract["related_repositories"]["agent_switchboard"]
        self.assertEqual(
            related["full_name"], "EndeavorEverlasting/AgentSwitchboard"
        )
        self.assertFalse(related["mutation_allowed"])

    def test_validator_rejects_contract_route_drift(self):
        mutations = []
        changed = copy.deepcopy(self.contract)
        changed["resolution_order"] = list(reversed(changed["resolution_order"]))
        mutations.append(changed)
        changed = copy.deepcopy(self.contract)
        changed["path_resolution"]["windows_default"] = r"C:\guessed\repo"
        mutations.append(changed)
        changed = copy.deepcopy(self.contract)
        changed["profiles"]["windows"]["shell"] = "termux-bash"
        mutations.append(changed)
        changed = copy.deepcopy(self.contract)
        changed["public_prompt_kit_url"] = "https://example.invalid/"
        mutations.append(changed)
        changed = copy.deepcopy(self.contract)
        changed["handoff_rules"] = changed["handoff_rules"][:-1]
        mutations.append(changed)
        for payload in mutations:
            with self.assertRaises(self.validator.ProfileRoutingError):
                self.validator.validate_contract_payload(payload)

    def test_windows_local_app_uses_agentswitchboard_sibling_path(self):
        route = self.module.resolve_route(
            "windows",
            "powershell",
            "windows",
            "local-app",
            agent_switchboard_repo=r"C:\Users\Profile\Desktop\Dev\AgentSwitchboard",
            main_sha="1234567890abcdef",
        )
        self.assertEqual(route.status, "ROUTED")
        self.assertEqual(
            route.associated_repo_path,
            r"C:\Users\Profile\Desktop\Dev\web-excel-repair-triage",
        )
        self.assertEqual(route.path_source, "agent-switchboard-sibling")
        self.assertIn("Open-Latest-PromptKit.cmd", route.command)

    def test_windows_browser_route_never_emits_termux_syntax(self):
        route = self.module.resolve_route(
            "windows", "powershell", "windows", "use", main_sha="abcdef12"
        )
        self.assertEqual(route.status, "ROUTED")
        self.assertTrue(route.command.startswith("Start-Process "))
        for token in (
            "termux-open-url",
            "command -v",
            "/dev/null",
            "pkg install",
            "$PREFIX",
        ):
            self.assertNotIn(token, route.command)

    def test_install_routes_use_phone_launcher(self):
        android = self.module.resolve_route(
            "android", "termux-bash", "android", "install", main_sha="abcdef12"
        )
        self.assertIn(self.module.LAUNCHER_URL, android.command)
        self.assertNotIn("/prompt-kit/", android.command)
        windows = self.module.resolve_route(
            "windows", "powershell", "windows", "install", main_sha="abcdef12"
        )
        self.assertIn(self.module.LAUNCHER_URL, windows.command)

    def test_android_target_from_windows_is_handoff_not_command(self):
        route = self.module.resolve_route(
            "windows", "powershell", "android", "use"
        )
        self.assertEqual(route.status, "HANDOFF")
        self.assertEqual(route.execution_surface, "android-termux")
        self.assertIsNone(route.command)
        self.assertIn("do not execute", route.next_action.lower())

    def test_android_termux_route_is_android_only(self):
        route = self.module.resolve_route(
            "android", "termux-bash", "android", "use", main_sha="abcdef12"
        )
        self.assertEqual(route.status, "ROUTED")
        self.assertTrue(route.command.startswith("termux-open-url "))
        self.assertNotIn("Start-Process", route.command)

    def test_shell_mismatch_fails_closed(self):
        route = self.module.resolve_route(
            "windows", "termux-bash", "windows", "use"
        )
        self.assertEqual(route.status, "BLOCKED")
        self.assertIsNone(route.command)

    def test_explicit_triage_path_beats_related_repo_sibling(self):
        route = self.module.resolve_route(
            "windows",
            "powershell",
            "windows",
            "edit",
            triage_repo=r"D:\Work\web-excel-repair-triage",
            agent_switchboard_repo=r"C:\Dev\AgentSwitchboard",
        )
        self.assertEqual(
            route.associated_repo_path, r"D:\Work\web-excel-repair-triage"
        )
        self.assertEqual(route.path_source, "explicit-triage-path")

    def test_shell_literals_escape_single_quotes(self):
        windows = self.module.resolve_route(
            "windows",
            "powershell",
            "windows",
            "edit",
            triage_repo=r"C:\Users\O'Brien\web-excel-repair-triage",
        )
        self.assertIn("O''Brien", windows.command)
        android = self.module.resolve_route(
            "android",
            "termux-bash",
            "android",
            "edit",
            triage_repo="/data/data/com.termux/files/home/O'Brien/web-excel-repair-triage",
        )
        self.assertIn("'\"'\"'", android.command)

    def test_platform_defaults_expand_in_native_shells(self):
        windows = self.module.resolve_route(
            "windows", "powershell", "windows", "edit"
        )
        self.assertIn("$env:USERPROFILE", windows.command)
        self.assertNotIn("%USERPROFILE%", windows.command)
        android = self.module.resolve_route(
            "android", "termux-bash", "android", "edit"
        )
        self.assertIn('"$HOME/web-excel-repair-triage"', android.command)

    def test_browser_only_edit_fails_closed(self):
        route = self.module.resolve_route("browser", "browser", "browser", "edit")
        self.assertEqual(route.status, "BLOCKED")
        self.assertIsNone(route.command)

    def test_malformed_sha_is_rejected_before_command_generation(self):
        with self.assertRaises(ValueError):
            self.module.resolve_route(
                "windows",
                "powershell",
                "windows",
                "use",
                main_sha="abc';Write-Host PWNED",
            )
        result = subprocess.run(
            [
                sys.executable,
                str(RESOLVER),
                "--host-profile",
                "windows",
                "--shell",
                "powershell",
                "--target-profile",
                "windows",
                "--intent",
                "use",
                "--main-sha",
                "abc';Write-Host PWNED",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertNotIn("command", payload)

    def test_cli_returns_two_for_cross_profile_handoff(self):
        result = subprocess.run(
            [
                sys.executable,
                str(RESOLVER),
                "--host-profile",
                "windows",
                "--shell",
                "powershell",
                "--target-profile",
                "android",
                "--intent",
                "use",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "HANDOFF")
        self.assertIsNone(payload["command"])

    def test_validator_passes_repository_contract(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--summary"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
