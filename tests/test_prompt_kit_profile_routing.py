from __future__ import annotations

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


def load_resolver():
    spec = importlib.util.spec_from_file_location("prompt_kit_profile_route_tests", RESOLVER)
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
        cls.module = load_resolver()

    def test_contract_keeps_triage_active_and_agentswitchboard_related(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(data["repository"], "EndeavorEverlasting/web-excel-repair-triage")
        related = data["related_repositories"]["agent_switchboard"]
        self.assertEqual(related["full_name"], "EndeavorEverlasting/AgentSwitchboard")
        self.assertFalse(related["mutation_allowed"])

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
        route = self.module.resolve_route("windows", "powershell", "windows", "use", main_sha="abcdef12")
        self.assertEqual(route.status, "ROUTED")
        self.assertTrue(route.command.startswith("Start-Process "))
        for token in ("termux-open-url", "command -v", "/dev/null", "pkg install", "$PREFIX"):
            self.assertNotIn(token, route.command)

    def test_android_target_from_windows_is_handoff_not_command(self):
        route = self.module.resolve_route("windows", "powershell", "android", "use")
        self.assertEqual(route.status, "HANDOFF")
        self.assertEqual(route.execution_surface, "android-termux")
        self.assertIsNone(route.command)
        self.assertIn("do not execute", route.next_action.lower())

    def test_android_termux_route_is_android_only(self):
        route = self.module.resolve_route("android", "termux-bash", "android", "use", main_sha="abcdef12")
        self.assertEqual(route.status, "ROUTED")
        self.assertTrue(route.command.startswith("termux-open-url "))
        self.assertNotIn("Start-Process", route.command)

    def test_shell_mismatch_fails_closed(self):
        route = self.module.resolve_route("windows", "termux-bash", "windows", "use")
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
        self.assertEqual(route.associated_repo_path, r"D:\Work\web-excel-repair-triage")
        self.assertEqual(route.path_source, "explicit-triage-path")

    def test_cli_returns_two_for_cross_profile_handoff(self):
        result = subprocess.run(
            [
                sys.executable,
                str(RESOLVER),
                "--host-profile", "windows",
                "--shell", "powershell",
                "--target-profile", "android",
                "--intent", "use",
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
