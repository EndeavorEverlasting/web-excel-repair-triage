from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.failure_observatory import derive_local_run_key, load_or_create_local_secret
from scripts.validate_cursor_failure_observatory_installation import (
    STATE_IGNORE_PROBE,
    _state_dir_is_ignored,
    validate as validate_installation,
)

ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = ROOT / ".cursor" / "hooks.json"
SENTINEL = ROOT / "scripts" / "cursor_failure_sentinel.py"


class CursorFailureObservatoryInstallationTests(unittest.TestCase):
    def _sentinel(self, state_dir: Path, *args: str, payload: dict | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SENTINEL), "--state-dir", str(state_dir), *args],
            cwd=ROOT,
            input=None if payload is None else json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

    def _hook(self, state_dir: Path, generation_id: str, hook_name: str, payload: dict) -> None:
        raw = {"generation_id": generation_id, **payload}
        completed = self._sentinel(state_dir, "hook", hook_name, payload=raw)
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        expected = {"continue": True} if hook_name == "beforeSubmitPrompt" else {}
        self.assertEqual(json.loads(completed.stdout), expected)

    def _run_key(self, state_dir: Path, generation_id: str) -> str:
        secret = load_or_create_local_secret(state_dir / "correlation.key")
        return derive_local_run_key(generation_id, secret)

    def _capsule(self, state_dir: Path, generation_id: str) -> dict:
        completed = self._sentinel(
            state_dir,
            "capsule",
            "--run-key",
            self._run_key(state_dir, generation_id),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        return json.loads(completed.stdout)

    def test_repository_project_hooks_validate(self) -> None:
        summary = validate_installation()
        self.assertEqual(summary["hooks"], 5)
        hooks = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(hooks["version"], 1)

    def test_installed_hook_commands_are_project_relative_and_passive(self) -> None:
        hooks = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))["hooks"]
        for hook_name, entries in hooks.items():
            with self.subTest(hook_name=hook_name):
                self.assertEqual(len(entries), 1)
                entry = entries[0]
                self.assertIn("scripts/cursor_failure_sentinel.py", entry["command"])
                self.assertIn("--state-dir .afk-observatory", entry["command"])
                self.assertFalse(entry["failClosed"])

    def test_git_ignore_proof_rejects_comments_and_negated_state_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(
                ["git", "init", "-q"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            ignore = root / ".gitignore"

            ignore.write_text("# .afk-observatory/\n", encoding="utf-8")
            self.assertFalse(_state_dir_is_ignored(root))

            ignore.write_text(".afk-observatory/\n!.afk-observatory/**\n", encoding="utf-8")
            self.assertFalse(_state_dir_is_ignored(root))

            ignore.write_text(".afk-observatory/\n", encoding="utf-8")
            self.assertTrue(_state_dir_is_ignored(root))
            self.assertEqual(STATE_IGNORE_PROBE, ".afk-observatory/privacy-canary.json")

    def test_synthetic_cursor_stdio_covers_p1_terminal_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            success = "generation-success"
            self._hook(root, success, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]] private body"})
            run_key = self._run_key(root, success)
            receipt = self._sentinel(
                root,
                "receipt",
                "--run-key",
                run_key,
                "--prompt-id",
                "P07",
                "--release",
                "2026.09",
                "--proof-state",
                "VALIDATED",
            )
            self.assertEqual(receipt.returncode, 0, receipt.stderr or receipt.stdout)
            self._hook(root, success, "stop", {"status": "completed", "loop_count": 0})
            self.assertEqual(self._capsule(root, success)["outcome"], "SUCCESS")

            abandonment = "generation-abandonment"
            self._hook(root, abandonment, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]]"})
            self._hook(
                root,
                abandonment,
                "postToolUseFailure",
                {"tool_name": "Shell", "failure_type": "timeout", "is_interrupt": False, "error_message": "PRIVATE"},
            )
            self._hook(root, abandonment, "stop", {"status": "completed", "loop_count": 0})
            self.assertEqual(
                self._capsule(root, abandonment)["boundary_class"],
                "EC_SEMANTIC_ABANDONMENT",
            )

            cancelled = "generation-cancelled"
            self._hook(root, cancelled, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]]"})
            self._hook(
                root,
                cancelled,
                "postToolUseFailure",
                {"tool_name": "Shell", "failure_type": "error", "is_interrupt": True},
            )
            self._hook(root, cancelled, "stop", {"status": "aborted", "loop_count": 0})
            self.assertEqual(self._capsule(root, cancelled)["boundary_class"], "UC_CANCELLED")

            host_error = "generation-host-error"
            self._hook(root, host_error, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]]"})
            self._hook(
                root,
                host_error,
                "sessionEnd",
                {"reason": "error", "error_message": "PRIVATE", "session_id": "PRIVATE-ID"},
            )
            self.assertEqual(
                self._capsule(root, host_error)["boundary_class"],
                "HT_HOST_FORCED_TERMINATION",
            )


if __name__ == "__main__":
    unittest.main()
