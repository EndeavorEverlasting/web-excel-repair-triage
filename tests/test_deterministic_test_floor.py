from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import run_deterministic_test_floor as floor
from scripts import run_private_input_test_floor as private_floor


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "harness" / "test-floor.v1.json"
VALIDATORS = REPO_ROOT / "harness" / "validators.v1.json"
ARTIFACT_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "artifact-engines.yml"
FLOOR_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deterministic-test-floor.yml"
PRODUCT_REQUIREMENTS = REPO_ROOT / "requirements.txt"
TEST_REQUIREMENTS = REPO_ROOT / "requirements-test-floor.txt"


def requirement_name(line: str) -> str:
    value = line.split("#", 1)[0].strip()
    value = re.split(r"[<>=!~]", value, maxsplit=1)[0]
    return value.split("[", 1)[0].strip().casefold()


class DeterministicTestFloorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.validators = json.loads(VALIDATORS.read_text(encoding="utf-8"))

    def test_manifest_is_nonempty_and_all_owned_paths_exist(self) -> None:
        self.assertEqual(self.manifest["schema_version"], "deterministic-test-floor/v1")
        self.assertEqual(self.manifest["python_version"], "3.11")
        self.assertEqual(self.manifest["dependency_file"], "requirements-test-floor.txt")
        self.assertGreater(len(self.manifest["self_tests"]), 0)
        self.assertGreater(len(self.manifest["prompt_semantic_test_globs"]), 0)
        self.assertGreater(len(self.manifest["artifact_imports"]), 0)
        self.assertGreater(len(self.manifest["artifact_tests"]), 0)
        self.assertTrue(TEST_REQUIREMENTS.is_file())
        for rel in self.manifest["compile_targets"] + self.manifest["self_tests"] + self.manifest["artifact_tests"]:
            self.assertTrue((REPO_ROOT / rel).exists(), rel)

    def test_prompt_semantic_convention_is_fully_registered_without_duplicate_skill_owner(self) -> None:
        discovered: set[str] = set()
        for pattern in self.manifest["prompt_semantic_test_globs"]:
            matches = {
                path.relative_to(REPO_ROOT).as_posix()
                for path in REPO_ROOT.glob(pattern)
                if path.is_file()
            }
            self.assertTrue(matches, f"prompt semantic glob matched no tests: {pattern}")
            discovered.update(matches)

        excludes = set(self.manifest["prompt_semantic_test_excludes"])
        self.assertEqual(len(excludes), len(self.manifest["prompt_semantic_test_excludes"]))
        self.assertTrue(excludes.issubset(discovered))
        discovered.difference_update(excludes)

        registered = set(self.manifest["self_tests"])
        registered.remove("tests/test_deterministic_test_floor.py")
        self.assertEqual(discovered, registered)
        self.assertIn("tests/test_afk_deterministic_testing_prompt.py", registered)
        self.assertIn("tests/test_test_floor_evolution_prompt.py", registered)
        self.assertNotIn("tests/test_skill_prompt_registry.py", registered)

    def test_direct_test_dependencies_are_exact_and_cover_product_requirements(self) -> None:
        test_lines = [
            line.strip()
            for line in TEST_REQUIREMENTS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(test_lines)
        for line in test_lines:
            self.assertRegex(line, r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?==[^=<>!~\s]+$")
        pinned_names = {requirement_name(line) for line in test_lines}
        product_names = {
            requirement_name(line)
            for line in PRODUCT_REQUIREMENTS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertTrue(product_names)
        self.assertTrue(product_names.issubset(pinned_names))
        self.assertIn("pytest", pinned_names)

    def test_test_floor_runs_its_own_regression_before_product_lanes(self) -> None:
        manifest, validators = floor.load_contract(MANIFEST)
        labels = [label for label, _ in floor.build_steps(manifest, validators)]
        self.assertIn("test-floor-self-tests", labels)
        self.assertLess(labels.index("test-floor-self-tests"), labels.index("artifact-engine-tests"))
        self.assertLess(labels.index("test-floor-self-tests"), labels.index("validator:harness-completeness"))

    def test_artifact_suite_stays_in_sync_with_existing_ci_owner(self) -> None:
        workflow = ARTIFACT_WORKFLOW.read_text(encoding="utf-8")
        primary_job = workflow.split("\n  canonical-local-path-prompt-repair:", 1)[0]
        workflow_tests = set(re.findall(r"tests/test_[A-Za-z0-9_]+\.py", primary_job))
        self.assertTrue(workflow_tests)
        self.assertEqual(workflow_tests, set(self.manifest["artifact_tests"]))

        workflow_imports = set(re.findall(r"\bimport (triage\.[A-Za-z0-9_.]+)", primary_job))
        self.assertTrue(workflow_imports)
        self.assertEqual(workflow_imports, set(self.manifest["artifact_imports"]))

    def test_artifact_skip_allowlist_matches_private_input_boundaries(self) -> None:
        self.assertEqual(
            set(self.manifest["allowed_artifact_skip_reasons"]),
            {
                "private operator reference workbook not present",
                "private real workbook not present",
                "Real roster log not present",
            },
        )
        source_text = "\n".join(
            (REPO_ROOT / path).read_text(encoding="utf-8")
            for path in self.manifest["artifact_tests"]
        )
        for reason in self.manifest["allowed_artifact_skip_reasons"]:
            self.assertIn(f'reason="{reason}"', source_text)

    def test_skip_parser_accepts_only_registered_reasons(self) -> None:
        output = """173 passed, 3 skipped in 8.39s
SKIPPED [1] tests/test_one.py:10: private operator reference workbook not present
SKIPPED [1] tests/test_two.py:20: private real workbook not present
SKIPPED [1] tests/test_three.py:30: Real roster log not present
"""
        observed = floor.validate_artifact_skip_reasons(
            output, self.manifest["allowed_artifact_skip_reasons"]
        )
        self.assertEqual(len(observed), 3)
        unexpected = output.replace(
            "Real roster log not present", "required service unexpectedly unavailable"
        )
        with self.assertRaisesRegex(floor.ContractError, "unregistered artifact-test skip"):
            floor.validate_artifact_skip_reasons(
                unexpected, self.manifest["allowed_artifact_skip_reasons"]
            )

    def test_skip_parser_fails_if_pytest_hides_skip_reason(self) -> None:
        with self.assertRaisesRegex(floor.ContractError, "exposed 0 parseable reasons"):
            floor.validate_artifact_skip_reasons(
                "173 passed, 1 skipped in 8.39s\n",
                self.manifest["allowed_artifact_skip_reasons"],
            )

    def test_registered_validator_profile_is_blocking_and_complete(self) -> None:
        profile_name = self.manifest["validator_profile"]
        profile = self.validators["profiles"][profile_name]
        self.assertTrue(profile)
        by_id = {item["id"]: item for item in self.validators["validators"]}
        for validator_id in profile:
            self.assertIn(validator_id, by_id)
            self.assertIs(by_id[validator_id]["blocking"], True)
            self.assertTrue(by_id[validator_id]["command"].strip())

    def test_empty_required_test_lists_fail_closed(self) -> None:
        for field in ("self_tests", "artifact_tests"):
            with self.subTest(field=field):
                broken = dict(self.manifest)
                broken[field] = []
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "manifest.json"
                    path.write_text(json.dumps(broken), encoding="utf-8")
                    with self.assertRaises(floor.ContractError):
                        floor.load_contract(path)

    def test_wrong_python_minor_fails_closed(self) -> None:
        broken = dict(self.manifest)
        broken["python_version"] = "0.0"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaisesRegex(floor.ContractError, "Python mismatch"):
                floor.load_contract(path)

    def test_unknown_validator_id_fails_closed(self) -> None:
        registry = json.loads(VALIDATORS.read_text(encoding="utf-8"))
        registry["profiles"]["deterministic-test-fixture"] = ["does-not-exist"]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "validators.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            broken = dict(self.manifest)
            broken["validator_registry"] = str(registry_path)
            broken["validator_profile"] = "deterministic-test-fixture"
            manifest_path = tmp_path / "manifest.json"
            manifest_path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(floor.ContractError):
                floor.load_contract(manifest_path)

    def test_python_validator_commands_use_active_interpreter(self) -> None:
        argv = floor.command_argv("python -m unittest tests.test_harness_contract -v")
        self.assertEqual(argv[0], floor.sys.executable)

    def test_patch_hygiene_does_not_require_full_history_merge_base(self) -> None:
        manifest, validators = floor.load_contract(MANIFEST)
        steps = dict(floor.build_steps(manifest, validators))
        patch = steps["branch-patch-hygiene"]
        if "origin/main" in patch:
            self.assertEqual(["git", "diff", "--check", "origin/main", "HEAD"], patch)
            self.assertNotIn("...", " ".join(patch))

    def test_workflow_is_thin_read_only_exact_head_shallow_and_has_no_unrequested_schedule(self) -> None:
        workflow = FLOOR_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn("PYTHONHASHSEED: \"0\"", workflow)
        self.assertIn("TZ: UTC", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", workflow)
        self.assertIn("fetch-depth: 1", workflow)
        self.assertIn("Verify exact candidate and fetch shallow main evidence", workflow)
        self.assertIn('test "$actual" = "$EXPECTED_SHA"', workflow)
        self.assertIn("+refs/heads/main:refs/remotes/origin/main", workflow)
        self.assertIn("python -m pip install -r requirements-test-floor.txt", workflow)
        self.assertNotIn("python -m pip install -r requirements.txt", workflow)
        self.assertEqual(workflow.count("scripts/run_deterministic_test_floor.py"), 2)
        self.assertEqual(workflow.count("scripts/run_private_input_test_floor.py"), 1)
        self.assertNotIn("tests/test_nw_prj_neuron_track_hours.py", workflow)
        self.assertNotIn("tests.test_harness_contract", workflow)

    def test_workflow_negative_canary_uses_current_manifest_owned_failure_gate(self) -> None:
        workflow = FLOOR_WORKFLOW.read_text(encoding="utf-8")
        expected = self.manifest["required_canary_failure"]
        self.assertEqual(expected, "test-floor-self-tests")
        manifest, validators = floor.load_contract(MANIFEST)
        labels = [label for label, _ in floor.build_steps(manifest, validators)]
        self.assertIn(expected, labels)
        self.assertLess(labels.index(expected), labels.index("validator:skill-prompt-registry-tests"))
        self.assertLess(labels.index(expected), labels.index("validator:prompt-kit-parity"))
        self.assertIn("web/prompt-kit/index.html", workflow)
        self.assertIn("negative-canary-report.json", workflow)
        self.assertIn("harness/test-floor.v1.json", workflow)
        self.assertIn("manifest['required_canary_failure']", workflow)
        self.assertIn("earliest registered failure gate", workflow)
        self.assertIn("if [ \"$status\" -eq 0 ]; then", workflow)
        self.assertNotIn("expected = 'validator:skill-prompt-registry-tests'", workflow)

    def test_private_input_requirements_exactly_own_registered_skips(self) -> None:
        manifest, records = private_floor.load_requirements(MANIFEST)
        self.assertEqual(len(records), 3)
        self.assertEqual(
            {record["missing_reason"] for record in records},
            set(manifest["allowed_artifact_skip_reasons"]),
        )
        self.assertEqual(
            {record["id"] for record in records},
            {"neuron-real-roster", "one-marcus-real-recon", "one-marcus-operator-reference"},
        )
        for record in records:
            self.assertIn(record["test_selector"].split("::", 1)[0], manifest["artifact_tests"])

    def test_private_input_gate_is_fail_closed_and_can_become_ready(self) -> None:
        _manifest, records = private_floor.load_requirements(MANIFEST)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(len(private_floor.missing_requirements(records, root)), 3)
            for record in records:
                target = root / record["input_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"fixture")
            self.assertEqual(private_floor.missing_requirements(records, root), [])
            argv = private_floor.pytest_argv(records)
            self.assertEqual(argv[0], private_floor.sys.executable)
            for record in records:
                self.assertIn(record["test_selector"], argv)

    def test_private_input_contract_rejects_path_escape(self) -> None:
        broken = dict(self.manifest)
        broken["private_input_requirements"] = [
            dict(item) for item in self.manifest["private_input_requirements"]
        ]
        broken["private_input_requirements"][0]["input_path"] = "../secret.xlsx"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaisesRegex(private_floor.ContractError, "repository-relative"):
                private_floor.load_requirements(path)

    def test_private_input_skip_counter_is_explicit(self) -> None:
        self.assertEqual(private_floor._pytest_skip_count("3 passed in 0.2s\n"), 0)
        self.assertEqual(private_floor._pytest_skip_count("2 passed, 1 skipped in 0.2s\n"), 1)
        self.assertEqual(private_floor._pytest_skip_count("1 passed, 2 skipped in 0.2s\n"), 2)

    def test_private_input_ready_path_reports_pass_only_after_zero_skip_test_result(self) -> None:
        completed = private_floor.subprocess.CompletedProcess(
            args=["pytest"],
            returncode=0,
            stdout="3 passed in 0.10s\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "private-pass.json"
            with (
                mock.patch.object(private_floor, "missing_requirements", return_value=[]),
                mock.patch.object(private_floor, "_git_value", side_effect=["deadbeef", "synthetic"]),
                mock.patch.object(private_floor.subprocess, "run", return_value=completed),
            ):
                status = private_floor.run(MANIFEST, report_path)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(status, 0)
        self.assertEqual(report["status"], "PASS")
        self.assertIsNone(report["failed_step"])
        self.assertEqual(report["test"]["returncode"], 0)
        self.assertEqual(report["test"]["skip_count"], 0)

    def test_private_input_ready_path_rejects_even_successful_pytest_with_a_skip(self) -> None:
        completed = private_floor.subprocess.CompletedProcess(
            args=["pytest"],
            returncode=0,
            stdout="2 passed, 1 skipped in 0.10s\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "private-skip.json"
            with (
                mock.patch.object(private_floor, "missing_requirements", return_value=[]),
                mock.patch.object(private_floor, "_git_value", side_effect=["deadbeef", "synthetic"]),
                mock.patch.object(private_floor.subprocess, "run", return_value=completed),
            ):
                status = private_floor.run(MANIFEST, report_path)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(status, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["failed_step"], "private-input-regressions")
        self.assertEqual(report["test"]["returncode"], 0)
        self.assertEqual(report["test"]["skip_count"], 1)

    def test_public_workflow_proves_private_gate_blocks_without_acquiring_secrets(self) -> None:
        workflow = FLOOR_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Private-input gate must block on clean public runner", workflow)
        self.assertIn("scripts/run_private_input_test_floor.py", workflow)
        self.assertIn("private-input-blocked-report.json", workflow)
        self.assertIn("report.get('status') != 'BLOCKED'", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("secrets.", workflow)


if __name__ == "__main__":
    unittest.main()
