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

    def test_current_contract_and_register_pass(self) -> None:
        result = regression.validate_all(copy.deepcopy(self.contract), copy.deepcopy(self.register))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["families"], 1)
        self.assertGreaterEqual(result["occurrences"], 6)
        self.assertFalse(result["matrix_is_exhaustive"])
        self.assertFalse(result["hosted_provider_is_semantic_owner"])

    def test_trailing_whitespace_is_systemic_cross_repo_evidence(self) -> None:
        family = self.register["families"][0]
        self.assertEqual(family["id"], "TRAILING_WHITESPACE")
        self.assertEqual(family["status"], "SYSTEMIC")
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
        register["families"][0]["prompt_strengthening"] = "ONE_PROMPT_ONLY"
        with self.assertRaisesRegex(regression.RegressionSafetyError, "shared prompt policy"):
            regression.validate_register(register, self.contract)

    def test_systemic_family_requires_recurrence_evidence(self) -> None:
        register = copy.deepcopy(self.register)
        register["families"][0]["occurrences"] = register["families"][0]["occurrences"][:1]
        with self.assertRaisesRegex(regression.RegressionSafetyError, "evidenced occurrences"):
            regression.validate_register(register, self.contract)

    def test_matrix_is_not_the_only_intake_surface(self) -> None:
        sources = set(self.contract["recurrence"]["incident_sources"])
        self.assertIn("retrospective_matrix", sources)
        self.assertIn("local_validator", sources)
        self.assertIn("hosted_ci", sources)
        self.assertIn("code_review", sources)
        self.assertIn("runtime_observation", sources)
        self.assertIn("operator_feedback", sources)
        self.assertIn("commit_history", sources)
        self.assertIn("one intake source", self.contract["matrix_boundary"].lower())

    def test_every_compiled_prompt_inherits_regression_safety_exactly_once(self) -> None:
        prompts = builder.load_prompt_kit_registry()
        self.assertGreater(len(prompts), 100)
        missing = []
        duplicated = []
        for prompt in prompts:
            content = str(prompt.get("copyContent", ""))
            count = content.count(MARKER)
            if count == 0:
                missing.append(prompt["id"])
            elif count != 1:
                duplicated.append((prompt["id"], count))
        self.assertEqual(missing, [])
        self.assertEqual(duplicated, [])

    def test_local_first_contract_does_not_invent_merge_authority(self) -> None:
        local_first = " ".join(self.contract["local_first_proof"]["rules"]).lower()
        self.assertIn("local profile", local_first)
        self.assertIn("exact base/head", local_first)
        self.assertIn("provider", local_first)
        self.assertIn("merge authority", local_first)
        self.assertIn("still requires provider mutation", local_first)

    def test_required_loop_retains_negative_and_positive_controls(self) -> None:
        loop = self.contract["required_loop"]
        self.assertLess(loop.index("REPAIR_INSTANCE"), loop.index("CLASSIFY_DEFECT_FAMILY"))
        self.assertLess(loop.index("WRITE_NEGATIVE_FIXTURE"), loop.index("STRENGTHEN_CANONICAL_OWNER"))
        self.assertLess(loop.index("WRITE_POSITIVE_CONTROL"), loop.index("RUN_LOCAL_REQUIRED_CHECKS"))
        self.assertEqual(loop[-1], "INTEGRATE_AND_RETAIN_REGRESSION")


if __name__ == "__main__":
    unittest.main()
