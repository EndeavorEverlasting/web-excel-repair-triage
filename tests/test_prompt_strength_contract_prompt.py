from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_prompt_strength import PromptStrengthError, validate_documents, validate_paths

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/prompt-strength.v1.json"
MATRIX = ROOT / "harness/evals/prompt-strength/adversarial-regression-matrix.v1.json"
DISPATCH_SEED = ROOT / "harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json"
DISPATCH_MANIFEST = ROOT / "Outputs/prompt-parallel-dispatch/manifest.json"


class PromptStrengthContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_current_documents_validate(self) -> None:
        summary = validate_paths()
        self.assertEqual(summary["dimensions"], 21)
        self.assertEqual(summary["cases"], 31)
        self.assertEqual(summary["dimensions"], summary["covered_dimensions"])

    def test_validator_cli_passes_with_expected_summary(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_prompt_strength.py", "--summary"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("PROMPT STRENGTH: PASS", completed.stdout)
        self.assertIn("dimensions=21", completed.stdout)
        self.assertIn("cases=31", completed.stdout)

    def _validate_dispatch_manifest(self, manifest_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "scripts/prompt_parallel_dispatch.py",
                "validate",
                "--manifest",
                str(manifest_path),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_historical_dispatch_seed_validates_independently(self) -> None:
        self.assertTrue(DISPATCH_SEED.is_file(), "historical prompt-strength dispatch seed must be tracked")
        completed = self._validate_dispatch_manifest(DISPATCH_SEED.relative_to(ROOT))
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_primary_manifest_is_tracked_and_validates_independently(self) -> None:
        self.assertTrue(DISPATCH_MANIFEST.is_file(), "primary dispatch manifest must be tracked")
        completed = self._validate_dispatch_manifest(DISPATCH_MANIFEST.relative_to(ROOT))
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_active_manifest_may_rotate_without_mutating_historical_seed(self) -> None:
        seed_before = DISPATCH_SEED.read_bytes()
        rotated = json.loads(seed_before.decode("utf-8"))
        rotated["run_id"] = "runtime-compliance-rotation-regression"
        rotated["lanes"][0]["lane_id"] = "lane-runtime-compliance-rotation"
        rotated["lanes"][0]["mission"] = (
            "Prove the global active dispatch manifest can rotate to a different valid "
            "orchestration without mutating the historical prompt-strength seed."
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            rotated_path = tmp_dir / "rotated-manifest.json"
            rotated_path.write_text(json.dumps(rotated, indent=2) + "\n", encoding="utf-8")
            self.assertNotEqual(
                rotated_path.read_bytes(),
                seed_before,
                "rotation fixture must differ from the historical seed",
            )
            rotated_completed = self._validate_dispatch_manifest(rotated_path)
            self.assertEqual(
                rotated_completed.returncode,
                0,
                rotated_completed.stderr or rotated_completed.stdout,
            )

            malformed = copy.deepcopy(rotated)
            del malformed["graph_width"]
            malformed_path = tmp_dir / "malformed-manifest.json"
            malformed_path.write_text(json.dumps(malformed, indent=2) + "\n", encoding="utf-8")
            malformed_completed = self._validate_dispatch_manifest(malformed_path)
            self.assertNotEqual(
                malformed_completed.returncode,
                0,
                "malformed active manifest must fail validation",
            )

        self.assertEqual(
            DISPATCH_SEED.read_bytes(),
            seed_before,
            "historical prompt-strength seed must remain unmutated after rotation",
        )

    def test_efficient_profile_cannot_drop_immutable_dimension(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["profiles"]["efficient"]["required_dimensions"].remove("canonical_identity")
        with self.assertRaisesRegex(PromptStrengthError, "efficient profile non-weakening drift"):
            validate_documents(mutated, self.matrix)

    def test_exhaustive_profile_covers_every_dimension(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["profiles"]["exhaustive"]["required_dimensions"].remove("residual_compute_sweep")
        with self.assertRaisesRegex(PromptStrengthError, "exhaustive profile coverage drift"):
            validate_documents(mutated, self.matrix)

    def test_dimension_requires_complete_typed_contract(self) -> None:
        for field in ("class", "summary", "weakening_forbidden", "evidence_terms"):
            mutated = copy.deepcopy(self.contract)
            del mutated["dimensions"][0][field]
            with self.subTest(field=field), self.assertRaisesRegex(
                PromptStrengthError, "dimension missing required fields"
            ):
                validate_documents(mutated, self.matrix)

    def test_malformed_profile_fails_closed_as_prompt_strength_error(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["profiles"]["exhaustive"] = "not-an-object"
        with self.assertRaisesRegex(PromptStrengthError, "profile must be an object"):
            validate_documents(mutated, self.matrix)

    def test_unknown_matrix_dimension_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"][0]["dimensions"].append("invented_dimension")
        with self.assertRaisesRegex(PromptStrengthError, "unknown dimension"):
            validate_documents(self.contract, mutated)

    def test_case_cannot_claim_unsupported_execution_profile(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"][0]["profiles"] = ["turbo"]
        with self.assertRaisesRegex(PromptStrengthError, "unsupported profile"):
            validate_documents(self.contract, mutated)

    def test_assertions_must_be_nonempty_string_lists(self) -> None:
        for malformed in ({"text": "not-a-list"}, "not-a-list", [""]):
            mutated = copy.deepcopy(self.matrix)
            mutated["cases"][0]["positive_assertions"] = malformed
            with self.subTest(malformed=malformed), self.assertRaisesRegex(
                PromptStrengthError, "string-list positive and negative assertions"
            ):
                validate_documents(self.contract, mutated)

    def test_each_case_requires_negative_control(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"][0]["negative_assertions"] = []
        with self.assertRaisesRegex(PromptStrengthError, "positive and negative assertions"):
            validate_documents(self.contract, mutated)

    def test_dimension_credit_requires_semantic_evidence(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        case = next(item for item in mutated["cases"] if item["case_id"] == "PSA-005")
        case["dimensions"] = ["plan_durability"]
        with self.assertRaisesRegex(PromptStrengthError, "dimension lacks semantic evidence"):
            validate_documents(self.contract, mutated)

    def test_dependency_snapshot_requires_exact_revision(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["supporting_owners"]["local_proof_dependency"]["head_sha_at_reconciliation"] = "PR #535"
        with self.assertRaisesRegex(PromptStrengthError, "dependency revision invalid"):
            validate_documents(mutated, self.matrix)

    def test_matrix_dependency_snapshot_requires_exact_revision(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["source_floor"]["active_dependencies"]["p07_effective_identity"]["head_sha_at_reconciliation"] = "latest"
        with self.assertRaisesRegex(PromptStrengthError, "matrix dependency revision invalid"):
            validate_documents(self.contract, mutated)

    def test_silent_stop_boundary_is_a_required_regression(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"] = [item for item in mutated["cases"] if item["case_id"] != "PSA-031"]
        mutated["case_contract"]["minimum_cases"] = 30
        with self.assertRaisesRegex(PromptStrengthError, "silent-stop boundary regression"):
            validate_documents(self.contract, mutated)

    def test_focused_test_path_is_bound_to_semantic_floor_convention(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["validation"]["focused_tests"] = "tests/test_prompt_strength_contract.py"
        with self.assertRaisesRegex(PromptStrengthError, "test path drifted"):
            validate_documents(mutated, self.matrix)

    def test_generated_html_cannot_become_authority(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["representation_invariants"]["generated_html_is_authority"] = True
        with self.assertRaisesRegex(PromptStrengthError, "generated HTML"):
            validate_documents(mutated, self.matrix)

    def test_serial_calls_cannot_count_as_parallelism(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["parallelism_invariants"]["serial_tool_calls_are_parallelism"] = True
        with self.assertRaisesRegex(PromptStrengthError, "serial tool calls"):
            validate_documents(mutated, self.matrix)


if __name__ == "__main__":
    unittest.main()
