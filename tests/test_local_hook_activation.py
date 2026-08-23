"""Focused regression tests for repository-local hook activation."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.install_local_hooks import (
    HOOKS_PATH,
    HookInstallError,
    check_local_hooks,
    install_local_hooks,
)


class LocalHookActivationTests(unittest.TestCase):
    def _git(self, repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=check,
            capture_output=True,
            text=True,
        )

    def _repo_with_hooks(self, *, executable: bool = True, track: bool = True) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        repo = Path(temp_dir.name)
        self._git(repo, "init")
        hooks = repo / HOOKS_PATH
        hooks.mkdir()
        for name in ("pre-commit", "pre-push"):
            (hooks / name).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        if track:
            self._git(repo, "add", ".githooks/pre-commit", ".githooks/pre-push")
            if executable:
                self._git(
                    repo,
                    "update-index",
                    "--chmod=+x",
                    ".githooks/pre-commit",
                    ".githooks/pre-push",
                )
        return repo

    def test_installer_sets_only_local_hooks_path(self) -> None:
        repo = self._repo_with_hooks()
        configured = install_local_hooks(repo)
        self.assertEqual(configured, HOOKS_PATH)
        local_value = self._git(
            repo, "config", "--local", "--get", "core.hooksPath"
        ).stdout.strip()
        self.assertEqual(local_value, HOOKS_PATH)

    def test_installer_is_idempotent(self) -> None:
        repo = self._repo_with_hooks()
        self.assertEqual(install_local_hooks(repo), HOOKS_PATH)
        self.assertEqual(install_local_hooks(repo), HOOKS_PATH)
        self.assertEqual(check_local_hooks(repo), HOOKS_PATH)

    def test_installer_preserves_different_local_hook_setup(self) -> None:
        repo = self._repo_with_hooks()
        self._git(repo, "config", "--local", "core.hooksPath", ".custom-hooks")
        with self.assertRaises(HookInstallError):
            install_local_hooks(repo)
        value = self._git(
            repo, "config", "--local", "--get", "core.hooksPath"
        ).stdout.strip()
        self.assertEqual(value, ".custom-hooks")

    def test_replace_is_explicit_and_local(self) -> None:
        repo = self._repo_with_hooks()
        self._git(repo, "config", "--local", "core.hooksPath", ".custom-hooks")
        self.assertEqual(install_local_hooks(repo, replace=True), HOOKS_PATH)
        self.assertEqual(check_local_hooks(repo), HOOKS_PATH)

    def test_check_refuses_unconfigured_checkout(self) -> None:
        repo = self._repo_with_hooks()
        with self.assertRaises(HookInstallError):
            check_local_hooks(repo)

    def test_installer_refuses_untracked_hook_files(self) -> None:
        repo = self._repo_with_hooks(track=False)
        with self.assertRaisesRegex(HookInstallError, "untracked"):
            install_local_hooks(repo)

    def test_installer_refuses_non_executable_git_mode(self) -> None:
        repo = self._repo_with_hooks(executable=False)
        with self.assertRaisesRegex(HookInstallError, "expected=100755"):
            install_local_hooks(repo)

    def test_source_never_writes_global_git_config(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "install_local_hooks.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"--global"', source)
        self.assertIn('"--local"', source)


if __name__ == "__main__":
    unittest.main()
