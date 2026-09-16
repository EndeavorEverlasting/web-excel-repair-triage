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
SNAPSHOT_PROFILE = "pre_commit_snapshot_prototype"
SNAPSHOT_VALIDATORS = ("harness-completeness", "harness-contract-tests")


class RequiredCheckProgramCallStackTests(unittest.TestCase):
    def load_registry(self) -> dict:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))

    def prototype_snapshot_registry(self, directory: Path) -> Path:
        canonical = self.load_registry()
        validator_by_id = {
            item["id"]: item for item in canonical["validators"]
        }
        selected = [validator_by_id[item] for item in SNAPSHOT_VALIDATORS]
        payload = {
            "schema_version": canonical["schema_version"],
            "validators": selected,
            "profiles": {SNAPSHOT_PROFILE: list(SNAPSHOT_VALIDATORS)},
            "hooks": {},
        }
        path = directory / "prototype-validators.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

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
        prototype_registry: Path,
        report: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "scripts/run_validator_profile.py",
                "--registry",
                str(prototype_registry),
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

    def test_staged_snapshot_success_and_domain_failure_use_same_real_runner(self) -> None:
        if not (ROOT / ".git").exists():
            self.skipTest("staged-index prototype requires a Git checkout")

        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            snapshot = temp / "snapshot"
            snapshot.mkdir()
            prototype_registry = self.prototype_snapshot_registry(temp)
            self.materialize_index(snapshot)

            success_report = temp / "snapshot-success.json"
            success = self.run_snapshot_profile(
                snapshot,
                prototype_registry,
                success_report,
            )
            self.assertEqual(
                success.returncode,
                0,
                f"stdout:\n{success.stdout}\nstderr:\n{success.stderr}",
            )
            success_payload = json.loads(success_report.read_text(encoding="utf-8"))
            self.assertEqual(success_payload["status"], "PASS")
            self.assertEqual(success_payload["profile"], SNAPSHOT_PROFILE)
            self.assertEqual(success_payload["observed_step_count"], 2)
            self.assertEqual(success_payload["required_step_count"], 2)
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
            failure = self.run_snapshot_profile(
                snapshot,
                prototype_registry,
                failure_report,
            )
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
            self.assertEqual(failure_payload["observed_step_count"], 1)
            self.assertEqual(failure_payload["required_step_count"], 2)
            self.assertEqual(
                failure_payload["steps"][0]["returncode"],
                1,
            )


if __name__ == "__main__":
    unittest.main()
