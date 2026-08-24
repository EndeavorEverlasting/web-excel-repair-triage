from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts import run_deterministic_test_floor as floor


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
        self.assertGreater(len(self.manifest["artifact_imports"]), 0)
        self.assertGreater(len(self.manifest["artifact_tests"]), 0)
        self.assertTrue(TEST_REQUIREMENTS.is_file())
        for rel in self.manifest["compile_targets"] + self.manifest["self_tests"] + self.manifest["artifact_tests"]:
            self.assertTrue((REPO_ROOT / rel).exists(), rel)

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
        self.assertNotIn("tests/test_nw_prj_neuron_track_hours.py", workflow)
        self.assertNotIn("tests.test_harness_contract", workflow)

    def test_workflow_negative_canary_uses_earliest_real_generated_parity_blocker(self) -> None:
        workflow = FLOOR_WORKFLOW.read_text(encoding="utf-8")
        expected = self.manifest["required_canary_failure"]
        self.assertEqual(expected, "validator:skill-prompt-registry-tests")
        manifest, validators = floor.load_contract(MANIFEST)
        labels = [label for label, _ in floor.build_steps(manifest, validators)]
        self.assertLess(labels.index(expected), labels.index("validator:prompt-kit-parity"))
        self.assertIn("web/prompt-kit/index.html", workflow)
        self.assertIn("negative-canary-report.json", workflow)
        self.assertIn(expected, workflow)
        self.assertIn("earliest registered failure gate", workflow)
        self.assertIn("if [ \"$status\" -eq 0 ]; then", workflow)


if __name__ == "__main__":
    unittest.main()
