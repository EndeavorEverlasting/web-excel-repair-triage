from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.validate_prompt_strength import PromptStrengthError, validate_documents, validate_paths

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/prompt-strength.v1.json"
MATRIX = ROOT / "harness/evals/prompt-strength/adversarial-regression-matrix.v1.json"
DISPATCH_SEED = ROOT / "harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json"


class PromptStrengthContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_current_documents_validate(self) -> None:
        summary = validate_paths()
        self.assertGreaterEqual(summary["dimensions"], 20)
        self.assertGreaterEqual(summary["cases"], 24)
        self.assertEqual(summary["dimensions"], summary["covered_dimensions"])

    def test_validator_cli_passes_with_expected_summary(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_prompt_strength.py", "--summary"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PROMPT STRENGTH: PASS", completed.stdout)
        self.assertIn("dimensions=21", completed.stdout)
        self.assertIn("cases=30", completed.stdout)

    def test_dispatch_seed_passes_repository_validator(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/prompt_parallel_dispatch.py",
                "validate",
                "--manifest",
                str(DISPATCH_SEED.relative_to(ROOT)),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_efficient_profile_cannot_drop_immutable_dimension(self) -> None:
        mutated = copy.deepcopy(self.contract)
        required = mutated["profiles"]["efficient"]["required_dimensions"]
        required.remove("canonical_identity")
        with self.assertRaisesRegex(PromptStrengthError, "efficient profile non-weakening drift"):
            validate_documents(mutated, self.matrix)

    def test_exhaustive_profile_covers_every_dimension(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["profiles"]["exhaustive"]["required_dimensions"].remove("residual_compute_sweep")
        with self.assertRaisesRegex(PromptStrengthError, "exhaustive profile coverage drift"):
            validate_documents(mutated, self.matrix)

    def test_unknown_matrix_dimension_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"][0]["dimensions"].append("invented_dimension")
        with self.assertRaisesRegex(PromptStrengthError, "unknown dimension"):
            validate_documents(self.contract, mutated)

    def test_each_case_requires_negative_control(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"][0]["negative_assertions"] = []
        with self.assertRaisesRegex(PromptStrengthError, "positive and negative assertions"):
            validate_documents(self.contract, mutated)

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
