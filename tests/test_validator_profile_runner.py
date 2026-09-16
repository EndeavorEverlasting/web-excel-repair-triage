from __future__ import annotations

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

import run_validator_profile as runner


class ValidatorProfileRunnerTests(unittest.TestCase):
    def real_registry(self) -> dict:
        return json.loads(
            (ROOT / "harness" / "validators.v1.json").read_text(encoding="utf-8")
        )

    def registry_payload(self, *, second_blocking: bool = True) -> dict:
        return {
            "schema_version": runner.SCHEMA_VERSION,
            "validators": [
                {
                    "id": "first",
                    "class": "test",
                    "command": "python -m unittest tests.test_validator_profile_runner -v",
                    "blocking": True,
                    "output": "process log",
                    "proof_ceiling": "first proof ceiling",
                },
                {
                    "id": "second",
                    "class": "lint",
                    "command": "git diff --check",
                    "blocking": second_blocking,
                    "output": "process log",
                    "proof_ceiling": "second proof ceiling",
                },
            ],
            "profiles": {"sample": ["first", "second"]},
            "hooks": {},
        }

    def write_registry(self, directory: str, payload: dict) -> Path:
        path = Path(directory) / "validators.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def step(self, validator_id: str, returncode: int, blocking: bool) -> dict:
        return {
            "id": validator_id,
            "class": "test",
            "command": "noop",
            "argv": ["noop"],
            "blocking": blocking,
            "output": "process log",
            "proof_ceiling": "fixture",
            "returncode": returncode,
            "status": "PASS" if returncode == 0 else "FAIL",
            "duration_seconds": 0.001,
            "stdout_tail": "",
            "stderr_tail": "",
        }

    def test_real_harness_profile_resolves_in_registered_order(self) -> None:
        payload = self.real_registry()
        resolved = runner.resolve_profile(payload, "harness")
        self.assertEqual(
            [item["id"] for item in resolved],
            payload["profiles"]["harness"],
        )
        self.assertTrue(all(item["blocking"] is True for item in resolved))

    def test_python_entrypoint_uses_current_interpreter(self) -> None:
        argv = runner.command_argv("python scripts/validate_harness.py --summary")
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[1:], ["scripts/validate_harness.py", "--summary"])

    def test_unknown_profile_fails_closed(self) -> None:
        with self.assertRaisesRegex(runner.ProfileContractError, "missing or empty"):
            runner.resolve_profile(self.registry_payload(), "unknown")

    def test_duplicate_validator_identity_fails_closed(self) -> None:
        payload = self.registry_payload()
        payload["validators"].append(dict(payload["validators"][0]))
        with self.assertRaisesRegex(runner.ProfileContractError, "duplicate validator id"):
            runner.resolve_profile(payload, "sample")

    def test_blocking_failure_stops_remaining_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = self.write_registry(directory, self.registry_payload())
            report_path = Path(directory) / "report.json"
            with mock.patch.object(
                runner,
                "run_command",
                side_effect=[self.step("first", 7, True)],
            ) as run_command, mock.patch.object(
                runner, "git_value", return_value="fixture"
            ):
                code, report = runner.execute_profile("sample", registry, report_path)
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["failed_validator"], "first")
        self.assertEqual(report["observed_step_count"], 1)
        self.assertEqual(report["required_step_count"], 2)
        self.assertEqual(run_command.call_count, 1)

    def test_nonblocking_failure_continues_and_preserves_metadata(self) -> None:
        payload = self.registry_payload(second_blocking=False)
        with tempfile.TemporaryDirectory() as directory:
            registry = self.write_registry(directory, payload)
            report_path = Path(directory) / "report.json"
            with mock.patch.object(
                runner,
                "run_command",
                side_effect=[
                    self.step("first", 0, True),
                    self.step("second", 9, False),
                ],
            ), mock.patch.object(runner, "git_value", return_value="fixture"):
                code, report = runner.execute_profile("sample", registry, report_path)
            persisted = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PASS_WITH_WARNINGS")
        self.assertEqual(report["warning_failure_count"], 1)
        self.assertEqual([step["id"] for step in report["steps"]], ["first", "second"])
        self.assertEqual(persisted["steps"][1]["proof_ceiling"], "fixture")
        self.assertEqual(
            persisted["proof_relevance_fingerprint"][0]["kind"],
            "validator_registry",
        )

    def test_repository_local_report_must_use_outputs(self) -> None:
        with self.assertRaisesRegex(runner.ProfileContractError, "under Outputs"):
            runner.resolve_report_path(Path("harness/profile-report.json"))
        target = runner.resolve_report_path(Path("Outputs/profile-report.json"))
        self.assertEqual(target, (ROOT / "Outputs" / "profile-report.json").resolve())

    def test_execute_profile_invalid_report_path_fails_closed_without_rethrow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = self.write_registry(directory, self.registry_payload())
            invalid_report = ROOT / "harness" / "invalid-profile-report.json"
            code, report = runner.execute_profile(
                "sample", registry, invalid_report
            )
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["failed_validator"], "contract")
        self.assertIn("under Outputs", report["error"])
        self.assertFalse(invalid_report.exists())

    def test_profile_with_unknown_validator_fails_closed(self) -> None:
        payload = self.registry_payload()
        payload["profiles"]["sample"].append("missing")
        with self.assertRaisesRegex(runner.ProfileContractError, "unknown id"):
            runner.resolve_profile(payload, "sample")

    def test_profile_fingerprint_changes_when_command_changes(self) -> None:
        payload = self.registry_payload()
        with tempfile.TemporaryDirectory() as directory:
            registry = self.write_registry(directory, payload)
            _, digest = runner.read_registry(registry)
            validators = runner.resolve_profile(payload, "sample")
            before = runner.profile_fingerprint(registry, digest, "sample", validators)
            payload["validators"][0]["command"] += " --buffer"
            registry = self.write_registry(directory, payload)
            _, digest = runner.read_registry(registry)
            validators = runner.resolve_profile(payload, "sample")
            after = runner.profile_fingerprint(registry, digest, "sample", validators)
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
