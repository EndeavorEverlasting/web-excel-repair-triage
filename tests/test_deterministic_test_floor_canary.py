from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import run_deterministic_test_floor_canary as canary


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/deterministic-test-floor-canary.v1.json"
SEMANTIC_WEAKENING_CONTRACT = (
    ROOT / "harness/contracts/prompt-semantic-weakening-canary.v1.json"
)


class DeterministicTestFloorCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = canary.load_contract(CONTRACT)
        cls.semantic_contract = canary.load_contract(SEMANTIC_WEAKENING_CONTRACT)

    def test_contract_binds_real_target_witness_and_canonical_floor(self) -> None:
        self.assertEqual(self.contract["schema_version"], "deterministic-test-floor-canary/v1")
        self.assertEqual(self.contract["canary_id"], "generated-prompt-kit-drift")
        self.assertEqual(self.contract["target_path"], "web/prompt-kit/index.html")
        self.assertEqual(self.contract["mutation"]["mode"], "append_text")
        self.assertIn("deterministic-test-floor-negative-canary", self.contract["mutation"]["text"])
        self.assertIn("tests/test_agentic_loop_prompts.py::", " ".join(self.contract["witness"]["argv"]))
        self.assertEqual(
            self.contract["full_floor"]["runner"],
            "scripts/run_deterministic_test_floor.py",
        )
        self.assertEqual(
            self.contract["full_floor"]["expected_failed_step"],
            "test-floor-self-tests",
        )

    def test_semantic_weakening_contract_targets_real_p07_without_mutating_source(self) -> None:
        contract = self.semantic_contract
        self.assertEqual(contract["canary_id"], "p07-semantic-weakening")
        self.assertEqual(contract["target_path"], "docs/prompts.json")
        self.assertEqual(contract["mutation"]["mode"], "replace_text")
        self.assertEqual(contract["mutation"]["expected_occurrences"], 1)
        self.assertIn(
            "scripts/validate_prompt_semantic_coverage.py",
            " ".join(contract["witness"]["argv"]),
        )
        self.assertIn(
            "PSC009 BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION",
            contract["witness"]["required_failure_signatures"],
        )
        target = ROOT / contract["target_path"]
        original = target.read_bytes()
        mutated = canary._apply_declared_mutation(original, contract["mutation"])
        self.assertNotEqual(mutated, original)
        self.assertEqual(mutated.decode("utf-8").count("CANARY_WEAKENED_P07"), 1)
        self.assertEqual(target.read_bytes(), original)

    def test_replace_text_mutation_fails_closed_on_occurrence_drift(self) -> None:
        mutation = copy.deepcopy(self.semantic_contract["mutation"])
        mutation["old_text"] = "THIS TEXT IS INTENTIONALLY ABSENT"
        with self.assertRaisesRegex(canary.ContractError, "occurrence mismatch"):
            canary._apply_declared_mutation(b"canonical prompt", mutation)

    def test_replace_text_contract_rejects_noop_mutation(self) -> None:
        broken = copy.deepcopy(self.semantic_contract)
        broken["mutation"]["new_text"] = broken["mutation"]["old_text"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "canary.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaisesRegex(canary.ContractError, "must change"):
                canary.load_contract(path)

    def test_proof_accepts_declared_mutation_specific_failure(self) -> None:
        marker = self.contract["witness"]["required_failure_signatures"][0]
        errors = canary.evaluate_proof(
            self.contract,
            clean_witness={"returncode": 0, "stdout_tail": "1 passed", "stderr_tail": ""},
            mutated_witness={
                "returncode": 1,
                "stdout_tail": f"AssertionError: generated site contains {marker}",
                "stderr_tail": "",
            },
            floor_process={"returncode": 1},
            floor_receipt={"status": "FAIL", "failed_step": "test-floor-self-tests"},
            before_digest="a" * 64,
            after_digest="a" * 64,
        )
        self.assertEqual(errors, [])

    def test_same_broad_gate_wrong_cause_is_rejected(self) -> None:
        errors = canary.evaluate_proof(
            self.contract,
            clean_witness={"returncode": 0, "stdout_tail": "1 passed", "stderr_tail": ""},
            mutated_witness={
                "returncode": 1,
                "stdout_tail": "FAILED tests/test_unrelated.py::test_unrelated_contract",
                "stderr_tail": "unrelated assertion",
            },
            floor_process={"returncode": 1},
            floor_receipt={"status": "FAIL", "failed_step": "test-floor-self-tests"},
            before_digest="b" * 64,
            after_digest="b" * 64,
        )
        self.assertTrue(any(error.startswith("WRONG_FAILURE_SIGNATURE") for error in errors))
        self.assertNotEqual(errors, [])

    def test_wrong_full_floor_gate_is_rejected_even_with_right_witness(self) -> None:
        marker = self.contract["witness"]["required_failure_signatures"][0]
        errors = canary.evaluate_proof(
            self.contract,
            clean_witness={"returncode": 0, "stdout_tail": "", "stderr_tail": ""},
            mutated_witness={"returncode": 1, "stdout_tail": marker, "stderr_tail": ""},
            floor_process={"returncode": 1},
            floor_receipt={"status": "FAIL", "failed_step": "validator:prompt-kit-parity"},
            before_digest="c" * 64,
            after_digest="c" * 64,
        )
        self.assertTrue(any(error.startswith("WRONG_FULL_FLOOR_GATE") for error in errors))

    def test_restore_mismatch_is_never_accepted(self) -> None:
        marker = self.contract["witness"]["required_failure_signatures"][0]
        errors = canary.evaluate_proof(
            self.contract,
            clean_witness={"returncode": 0, "stdout_tail": "", "stderr_tail": ""},
            mutated_witness={"returncode": 1, "stdout_tail": marker, "stderr_tail": ""},
            floor_process={"returncode": 1},
            floor_receipt={"status": "FAIL", "failed_step": "test-floor-self-tests"},
            before_digest="d" * 64,
            after_digest="e" * 64,
        )
        self.assertIn("RESTORE_MISMATCH", errors)

    def test_atomic_write_replaces_complete_bytes_without_temp_residue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target.txt"
            target.write_bytes(b"before")
            canary._atomic_write_bytes(target, b"after-complete")
            self.assertEqual(target.read_bytes(), b"after-complete")
            self.assertEqual(list(target.parent.glob(f".{target.name}.canary-*")), [])

    def test_fresh_floor_report_discards_stale_receipt_before_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "floor.json"
            report.write_text(
                json.dumps({"status": "FAIL", "failed_step": "test-floor-self-tests"}),
                encoding="utf-8",
            )
            self.assertTrue(report.exists())
            canary._prepare_fresh_report(report)
            self.assertFalse(report.exists())

    def test_missing_floor_receipt_cannot_prove_expected_gate(self) -> None:
        marker = self.contract["witness"]["required_failure_signatures"][0]
        errors = canary.evaluate_proof(
            self.contract,
            clean_witness={"returncode": 0, "stdout_tail": "", "stderr_tail": ""},
            mutated_witness={"returncode": 1, "stdout_tail": marker, "stderr_tail": ""},
            floor_process={"returncode": 1},
            floor_receipt=None,
            before_digest="f" * 64,
            after_digest="f" * 64,
        )
        self.assertIn("FULL_FLOOR_RECEIPT_NOT_FAIL", errors)

    def test_contract_rejects_path_escape_before_mutation(self) -> None:
        broken = copy.deepcopy(self.contract)
        broken["target_path"] = "../outside.html"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "canary.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaisesRegex(canary.ContractError, "repository-relative"):
                canary.load_contract(path)


if __name__ == "__main__":
    unittest.main()
