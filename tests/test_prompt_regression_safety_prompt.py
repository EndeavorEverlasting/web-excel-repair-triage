from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as builder
from scripts import validate_prompt_regression_safety as regression

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-regression-safety.v1.json"
REGISTER = ROOT / "harness" / "evals" / "prompt-regression" / "defect-families.v1.json"
MARKER = "REGRESSION SAFETY / RECURRING DEFECT CONTRACT"


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


class PromptRegressionSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.register = json.loads(REGISTER.read_text(encoding="utf-8"))
        cls.policy = regression.load_json(regression.POLICY_PATH)
        cls.floor = regression.load_json(regression.TEST_FLOOR_PATH)
        cls.required_checks = regression.load_json(regression.REQUIRED_CHECKS_PATH)
        cls.validators = regression.load_json(regression.VALIDATORS_PATH)
        cls.pre_commit_text = regression.PRE_COMMIT_PATH.read_text(encoding="utf-8")

    def wiring_kwargs(self) -> dict[str, object]:
        return {
            "policy": copy.deepcopy(self.policy),
            "floor": copy.deepcopy(self.floor),
            "required_checks": copy.deepcopy(self.required_checks),
            "validators": copy.deepcopy(self.validators),
            "pre_commit_text": self.pre_commit_text,
        }

    def test_current_contract_and_register_pass(self) -> None:
        result = regression.validate_all(copy.deepcopy(self.contract), copy.deepcopy(self.register))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["families"], len(self.register["families"]))
        self.assertEqual(
            {family["id"] for family in self.register["families"]},
            {"TRAILING_WHITESPACE", "PROVIDER_QUOTA_TERMINATION"},
        )
        self.assertGreaterEqual(
            result["occurrences"],
            sum(len(family["occurrences"]) for family in self.register["families"]),
        )
        self.assertFalse(result["matrix_is_exhaustive"])
        self.assertFalse(result["hosted_provider_is_semantic_owner"])

    def test_trailing_whitespace_is_systemic_cross_repo_evidence(self) -> None:
        family = self.register["families"][0]
        self.assertEqual(family["id"], "TRAILING_WHITESPACE")
        self.assertEqual(family["status"], "SYSTEMIC")
        self.assertEqual(family["classification"], "PATCH_HYGIENE")
        self.assertTrue(family["recurring_across_repositories"])
        self.assertFalse(family["matrix_capture_required"])
        repositories = {item["repository"] for item in family["occurrences"]}
        self.assertIn("EndeavorEverlasting/web-excel-repair-triage", repositories)
        self.assertIn("EndeavorEverlasting/AgentSwitchboard", repositories)
        self.assertGreaterEqual(len(family["occurrences"]), self.contract["recurrence"]["systemic_threshold"])

    def test_whitespace_family_binds_working_staged_and_exact_candidate_checks(self) -> None:
        family = self.register["families"][0]
        expected = {
            "git diff --check",
            "git diff --cached --check",
            "git diff --check {base_sha}...{head_sha}",
        }
        self.assertEqual(set(family["detector_commands"]), expected)
        self.assertEqual(set(self.contract["repository_hygiene"]["patch_hygiene_commands"]), expected)

    def test_patch_hygiene_negative_and_positive_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(run_git(repo, "init", "-q").returncode, 0)
            self.assertEqual(run_git(repo, "config", "user.name", "Regression Fixture").returncode, 0)
            self.assertEqual(run_git(repo, "config", "user.email", "fixture@example.invalid").returncode, 0)
            sample = repo / "sample.txt"
            sample.write_text("baseline\n", encoding="utf-8")
            self.assertEqual(run_git(repo, "add", "sample.txt").returncode, 0)
            self.assertEqual(run_git(repo, "commit", "-qm", "baseline").returncode, 0)
            base = run_git(repo, "rev-parse", "HEAD").stdout.strip()

            sample.write_text("bad trailing whitespace  \n", encoding="utf-8")
            working = run_git(repo, "diff", "--check")
            self.assertNotEqual(working.returncode, 0)
            self.assertIn("trailing whitespace", (working.stdout + working.stderr).lower())

            self.assertEqual(run_git(repo, "add", "sample.txt").returncode, 0)
            staged = run_git(repo, "diff", "--cached", "--check")
            self.assertNotEqual(staged.returncode, 0)
            self.assertIn("trailing whitespace", (staged.stdout + staged.stderr).lower())

            self.assertEqual(run_git(repo, "commit", "-qm", "bad candidate").returncode, 0)
            exact_bad = run_git(repo, "diff", "--check", f"{base}...HEAD")
            self.assertNotEqual(exact_bad.returncode, 0)
            self.assertIn("trailing whitespace", (exact_bad.stdout + exact_bad.stderr).lower())

            self.assertEqual(run_git(repo, "reset", "--hard", base).returncode, 0)
            sample.write_text("clean candidate\n", encoding="utf-8")
            self.assertEqual(run_git(repo, "diff", "--check").returncode, 0)
            self.assertEqual(run_git(repo, "add", "sample.txt").returncode, 0)
            self.assertEqual(run_git(repo, "diff", "--cached", "--check").returncode, 0)
            self.assertEqual(run_git(repo, "commit", "-qm", "clean candidate").returncode, 0)
            self.assertEqual(run_git(repo, "diff", "--check", f"{base}...HEAD").returncode, 0)

    def test_systemic_family_cannot_degrade_to_prompt_by_prompt_cleanup(self) -> None:
        register = copy.deepcopy(self.register)
        register["families"][0]["prompt_strengthening"] = "SCOPED_SHARED_POLICY"
        with self.assertRaisesRegex(regression.RegressionSafetyError, "shared prompt policy"):
            regression.validate_register(register, self.contract)

    def test_systemic_family_requires_recurrence_evidence(self) -> None:
        register = copy.deepcopy(self.register)
        register["families"][0]["occurrences"] = register["families"][0]["occurrences"][:1]
        with self.assertRaisesRegex(regression.RegressionSafetyError, "evidenced occurrences"):
            regression.validate_register(register, self.contract)

    def test_contract_requires_local_required_check_as_incident_source(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["recurrence"]["incident_sources"].remove("local_required_check")
        with self.assertRaisesRegex(regression.RegressionSafetyError, "local_required_check"):
            regression.validate_contract(contract)

    def test_family_rejects_invalid_classification_and_detector_types(self) -> None:
        register = copy.deepcopy(self.register)
        register["families"][0]["classification"] = "ANYTHING"
        with self.assertRaisesRegex(regression.RegressionSafetyError, "classification"):
            regression.validate_register(register, self.contract)

        register = copy.deepcopy(self.register)
        register["families"][0]["detector_commands"][0] = 7
        with self.assertRaisesRegex(regression.RegressionSafetyError, "detector_commands"):
            regression.validate_register(register, self.contract)

    def test_family_rejects_missing_owner_bad_prevention_and_malformed_occurrence(self) -> None:
        register = copy.deepcopy(self.register)
        register["families"][0]["canonical_owner"] = ""
        with self.assertRaisesRegex(regression.RegressionSafetyError, "canonical_owner"):
            regression.validate_register(register, self.contract)

        register = copy.deepcopy(self.register)
        register["families"][0]["prevention_surfaces"][0] = 3
        with self.assertRaisesRegex(regression.RegressionSafetyError, "prevention_surfaces"):
            regression.validate_register(register, self.contract)

        register = copy.deepcopy(self.register)
        del register["families"][0]["occurrences"][0]["summary"]
        with self.assertRaisesRegex(regression.RegressionSafetyError, "occurrence is malformed"):
            regression.validate_register(register, self.contract)

    def test_occurrence_commit_must_be_exact_lowercase_sha(self) -> None:
        register = copy.deepcopy(self.register)
        register["families"][0]["occurrences"][0]["commit"] = "ABC123"
        with self.assertRaisesRegex(regression.RegressionSafetyError, "lowercase 40-hex"):
            regression.validate_register(register, self.contract)

    def test_matrix_is_not_the_only_intake_surface(self) -> None:
        sources = set(self.contract["recurrence"]["incident_sources"])
        for source in (
            "local_validator",
            "local_required_check",
            "hosted_ci",
            "code_review",
            "runtime_observation",
            "operator_feedback",
            "retrospective_matrix",
            "commit_history",
        ):
            self.assertIn(source, sources)
        self.assertIn("one intake source", self.contract["matrix_boundary"].lower())

    def test_governed_operational_prompts_inherit_contract_content_only_prompts_do_not(self) -> None:
        operational = builder.load_prompt_registry()
        content_only = builder.load_content_prompt_registry()
        self.assertGreater(len(operational), 100)
        missing = []
        duplicated = []
        for prompt in operational:
            count = str(prompt.get("copyContent", "")).count(MARKER)
            if count == 0:
                missing.append(prompt["id"])
            elif count != 1:
                duplicated.append((prompt["id"], count))
        self.assertEqual(missing, [])
        self.assertEqual(duplicated, [])
        leaked = [
            prompt["id"]
            for prompt in content_only
            if MARKER in str(prompt.get("copyContent", ""))
        ]
        self.assertEqual(leaked, [])

    def test_local_first_contract_does_not_invent_merge_authority(self) -> None:
        local_first = " ".join(self.contract["local_first_proof"]["rules"]).lower()
        self.assertIn("local profile", local_first)
        self.assertIn("exact base/head", local_first)
        self.assertIn("provider", local_first)
        self.assertIn("merge authority", local_first)
        self.assertIn("still requires provider mutation", local_first)

    def test_wiring_rejects_missing_exact_candidate_patch_command(self) -> None:
        kwargs = self.wiring_kwargs()
        required_checks = kwargs["required_checks"]
        assert isinstance(required_checks, dict)
        required_checks["destinations"]["main"]["exact_candidate_commands"].remove(
            "git diff --check {base_sha}...{head_sha}"
        )
        with self.assertRaisesRegex(regression.RegressionSafetyError, "executable list"):
            regression.validate_repository_wiring(self.contract, **kwargs)

    def test_wiring_rejects_metadata_only_or_nonblocking_patch_validator(self) -> None:
        kwargs = self.wiring_kwargs()
        validators = kwargs["validators"]
        assert isinstance(validators, dict)
        patch = next(row for row in validators["validators"] if row["id"] == "patch-hygiene")
        patch["command"] = "echo git diff --check"
        with self.assertRaisesRegex(regression.RegressionSafetyError, "patch-hygiene"):
            regression.validate_repository_wiring(self.contract, **kwargs)

        kwargs = self.wiring_kwargs()
        validators = kwargs["validators"]
        assert isinstance(validators, dict)
        staged = next(row for row in validators["validators"] if row["id"] == "patch-hygiene-staged")
        staged["blocking"] = False
        with self.assertRaisesRegex(regression.RegressionSafetyError, "patch-hygiene-staged"):
            regression.validate_repository_wiring(self.contract, **kwargs)

    def test_wiring_rejects_profile_or_hook_regression(self) -> None:
        kwargs = self.wiring_kwargs()
        validators = kwargs["validators"]
        assert isinstance(validators, dict)
        validators["profiles"]["pre_commit"].remove("patch-hygiene-staged")
        with self.assertRaisesRegex(regression.RegressionSafetyError, "pre_commit profile"):
            regression.validate_repository_wiring(self.contract, **kwargs)

        kwargs = self.wiring_kwargs()
        kwargs["pre_commit_text"] = "#!/bin/sh\nexit 0\n"
        with self.assertRaisesRegex(regression.RegressionSafetyError, "pre-commit hook"):
            regression.validate_repository_wiring(self.contract, **kwargs)

    def test_required_loop_retains_negative_and_positive_controls(self) -> None:
        loop = self.contract["required_loop"]
        self.assertLess(loop.index("REPAIR_INSTANCE"), loop.index("CLASSIFY_DEFECT_FAMILY"))
        self.assertLess(loop.index("WRITE_NEGATIVE_FIXTURE"), loop.index("STRENGTHEN_CANONICAL_OWNER"))
        self.assertLess(loop.index("WRITE_POSITIVE_CONTROL"), loop.index("RUN_LOCAL_REQUIRED_CHECKS"))
        self.assertEqual(loop[-1], "INTEGRATE_AND_RETAIN_REGRESSION")


if __name__ == "__main__":
    unittest.main()
