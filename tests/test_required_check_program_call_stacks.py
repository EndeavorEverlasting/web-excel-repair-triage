from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "harness-contract.yml"
REGISTRY = ROOT / "harness" / "validators.v1.json"
SNAPSHOT_PROFILE = "pre_commit_snapshot"
SNAPSHOT_VALIDATORS = (
    "repository-work-ledger-audit",
    "repository-work-ledger-tests",
    "prompt-kit-cross-device-access-audit",
    "prompt-kit-cross-device-access-tests",
    "prompt-kit-freshness-guidance-audit",
    "prompt-kit-freshness-guidance-tests",
    "pr-merge-gate-audit",
    "pr-merge-gate-tests",
    "artifact-handoff-harness-audit",
    "artifact-handoff-harness-tests",
    "artifact-derivation-harness-audit",
    "artifact-derivation-harness-tests",
    "harness-completeness",
    "harness-contract-tests",
)


class RequiredCheckProgramCallStackTests(unittest.TestCase):
    def load_registry(self) -> dict:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))

    def materialize_index(self, destination: Path) -> None:
        prefix = destination.as_posix().rstrip("/") + "/"
        result = subprocess.run(
            ["git", "checkout-index", "--all", "--prefix", prefix],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((destination / "scripts" / "run_validator_profile.py").is_file())
        self.assertTrue((destination / "harness" / "validators.v1.json").is_file())

    def run_snapshot_profile(
        self,
        snapshot: Path,
        report: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "scripts/run_validator_profile.py",
                "--profile",
                SNAPSHOT_PROFILE,
                "--report",
                str(report),
            ],
            cwd=snapshot,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def test_actions_wrapper_delegates_portable_harness_profile_once(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        registry = self.load_registry()
        validators = {item["id"]: item for item in registry["validators"]}

        self.assertEqual(workflow.count("python scripts/run_validator_profile.py"), 1)
        self.assertEqual(workflow.count("--profile harness"), 1)
        self.assertIn("--report \"$RUNNER_TEMP/harness-validator-profile.json\"", workflow)

        provider_only_markers = (
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            "shell: pwsh",
            "actions/upload-artifact@v7",
            "name: harness-validator-profile",
            "git diff --check origin/main...HEAD",
        )
        for marker in provider_only_markers:
            self.assertIn(marker, workflow)

        for validator_id in registry["profiles"]["harness"]:
            if validator_id == "patch-hygiene":
                # CI intentionally owns exact-candidate diff proof, which is
                # stronger/different than the local working-tree command.
                continue
            self.assertNotIn(
                validators[validator_id]["command"],
                workflow,
                f"portable harness command duplicated in Actions wrapper: {validator_id}",
            )

    def test_durable_snapshot_profile_membership_and_hook_delegation(self) -> None:
        registry = self.load_registry()
        hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")

        self.assertEqual(
            registry["profiles"][SNAPSHOT_PROFILE],
            list(SNAPSHOT_VALIDATORS),
        )
        self.assertEqual(
            registry["hooks"]["pre_commit"]["profile"],
            SNAPSHOT_PROFILE,
        )
        self.assertIn(
            f"python3 scripts/run_validator_profile.py --profile {SNAPSHOT_PROFILE}",
            hook,
        )
        validators = {item["id"]: item for item in registry["validators"]}
        for validator_id in SNAPSHOT_VALIDATORS:
            self.assertNotIn(
                validators[validator_id]["command"],
                hook,
                f"snapshot validator duplicated in pre-commit hook: {validator_id}",
            )

    def test_staged_snapshot_success_and_domain_failure_use_same_real_runner(self) -> None:
        if not (ROOT / ".git").exists():
            self.skipTest("staged-index proof requires a Git checkout")

        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            snapshot = temp / "snapshot"
            snapshot.mkdir()
            self.materialize_index(snapshot)

            success_report = temp / "snapshot-success.json"
            success = self.run_snapshot_profile(snapshot, success_report)
            self.assertEqual(
                success.returncode,
                0,
                f"stdout:\n{success.stdout}\nstderr:\n{success.stderr}",
            )
            success_payload = json.loads(success_report.read_text(encoding="utf-8"))
            self.assertEqual(success_payload["status"], "PASS")
            self.assertEqual(success_payload["profile"], SNAPSHOT_PROFILE)
            self.assertEqual(success_payload["observed_step_count"], 14)
            self.assertEqual(success_payload["required_step_count"], 14)
            self.assertEqual(
                [step["id"] for step in success_payload["steps"]],
                list(SNAPSHOT_VALIDATORS),
            )

            manifest_path = snapshot / "harness" / "manifest.v1.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["default_branch"] = "prototype-invalid"
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )

            failure_report = temp / "snapshot-failure.json"
            failure = self.run_snapshot_profile(snapshot, failure_report)
            self.assertEqual(
                failure.returncode,
                1,
                f"stdout:\n{failure.stdout}\nstderr:\n{failure.stderr}",
            )
            failure_payload = json.loads(failure_report.read_text(encoding="utf-8"))
            self.assertEqual(failure_payload["status"], "FAIL")
            self.assertEqual(
                failure_payload["failed_validator"],
                "harness-completeness",
            )
            # The 12 leading snapshot-safe validators still pass; fail-fast stops
            # at the corrupted harness completeness gate and skips the successor.
            self.assertEqual(failure_payload["observed_step_count"], 13)
            self.assertEqual(failure_payload["required_step_count"], 14)
            self.assertEqual(
                failure_payload["steps"][-1]["returncode"],
                1,
            )
            self.assertEqual(
                failure_payload["steps"][-1]["id"],
                "harness-completeness",
            )

    def test_unstaged_working_tree_mutation_does_not_enter_staged_snapshot(self) -> None:
        if not (ROOT / ".git").exists():
            self.skipTest("staged-index proof requires a Git checkout")

        target = ROOT / "harness" / "manifest.v1.json"
        original = target.read_text(encoding="utf-8")
        try:
            mutated = json.loads(original)
            mutated["default_branch"] = "unstaged-working-tree-only"
            target.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")

            with tempfile.TemporaryDirectory() as temporary:
                snapshot = Path(temporary) / "snapshot"
                snapshot.mkdir()
                self.materialize_index(snapshot)
                snap_manifest = json.loads(
                    (snapshot / "harness" / "manifest.v1.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    snap_manifest.get("default_branch"),
                    json.loads(original).get("default_branch"),
                )
                self.assertNotEqual(
                    snap_manifest.get("default_branch"),
                    "unstaged-working-tree-only",
                )
        finally:
            target.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
