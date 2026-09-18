from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import validate_prompt_runtime_compliance_receipt as validator

ROOT = Path(__file__).resolve().parents[1]
POSITIVE = (
    ROOT
    / "harness"
    / "evals"
    / "runtime-compliance"
    / "contract-fixtures"
    / "receipt.positive.v1.json"
)


def load_positive() -> dict:
    return json.loads(POSITIVE.read_text(encoding="utf-8"))


def finding(result: dict, rule_id: str) -> dict:
    return next(row for row in result["findings"] if row["rule_id"] == rule_id)


class PromptRuntimeComplianceValidatorHardeningTests(unittest.TestCase):
    def test_progress_claim_requires_evidence_stronger_proof_or_confirmed_effect(self) -> None:
        for status in ("FAILED", "BLOCKED", "SUCCEEDED"):
            with self.subTest(status=status):
                receipt = load_positive()
                action = receipt["actions"][0]
                action["status"] = status
                action["evidence_refs"] = []
                action["proof_before"] = "IMPLEMENTED"
                action["proof_after"] = "IMPLEMENTED"
                action["side_effect_state"] = "NONE"
                result = validator.validate_receipt(receipt)
                self.assertEqual(
                    finding(result, "PRCR.ACTION.PROGRESS_TRUTH")["result"],
                    "FAIL",
                )

    def test_proof_promotion_requires_shared_evidence_with_passing_check(self) -> None:
        receipt = load_positive()
        receipt["actions"][0]["evidence_refs"] = ["EV-001"]
        result = validator.validate_receipt(receipt)
        self.assertEqual(
            finding(result, "PRCR.ACTION.NO_FALSE_PROOF_PROMOTION")["result"],
            "FAIL",
        )

    def test_same_evidence_binds_positive_proof_transition(self) -> None:
        result = validator.validate_receipt(load_positive())
        self.assertEqual(
            finding(result, "PRCR.ACTION.NO_FALSE_PROOF_PROMOTION")["result"],
            "PASS",
        )

    def test_readback_must_reconcile_same_target(self) -> None:
        receipt = load_positive()
        first = receipt["actions"][0]
        first["side_effect_state"] = "UNKNOWN"
        first["proof_after"] = "IMPLEMENTED"
        first["target_identity"] = "fixture:rtc04:mutation-target"
        first["pre_state_fingerprint"] = "sha256:rtc04-prestate-v1"

        readback = copy.deepcopy(first)
        readback["action_id"] = "A-002"
        readback["sequence"] = 2
        readback["started_at"] = "2026-09-18T12:03:31Z"
        readback["completed_at"] = "2026-09-18T12:03:40Z"
        readback["side_effect_state"] = "NONE"
        readback["readback_of_action_id"] = "A-001"
        readback["target_identity"] = "fixture:rtc04:other-target"
        readback["proof_before"] = "IMPLEMENTED"
        readback["proof_after"] = "IMPLEMENTED"
        receipt["actions"].append(readback)

        result = validator.validate_receipt(receipt)
        self.assertEqual(
            finding(result, "PRCR.ACTION.PARTIAL_READBACK")["result"],
            "FAIL",
        )

    def test_retry_after_confirmed_readback_is_duplicate_effect_failure(self) -> None:
        receipt = load_positive()
        first = receipt["actions"][0]
        first["side_effect_state"] = "UNKNOWN"
        first["proof_after"] = "IMPLEMENTED"
        first["target_identity"] = "fixture:rtc04:mutation-target"
        first["pre_state_fingerprint"] = "sha256:rtc04-prestate-v1"

        readback = copy.deepcopy(first)
        readback["action_id"] = "A-002"
        readback["sequence"] = 2
        readback["started_at"] = "2026-09-18T12:02:00Z"
        readback["completed_at"] = "2026-09-18T12:02:15Z"
        readback["side_effect_state"] = "CONFIRMED"
        readback["readback_of_action_id"] = "A-001"
        readback["proof_before"] = "IMPLEMENTED"
        readback["proof_after"] = "IMPLEMENTED"

        retry = copy.deepcopy(readback)
        retry["action_id"] = "A-003"
        retry["sequence"] = 3
        retry["started_at"] = "2026-09-18T12:02:30Z"
        retry["completed_at"] = "2026-09-18T12:02:45Z"
        retry["side_effect_state"] = "NONE"
        retry["readback_of_action_id"] = None
        retry["retry_of_action_id"] = "A-001"

        receipt["actions"].extend([readback, retry])
        result = validator.validate_receipt(receipt)
        self.assertEqual(
            finding(result, "PRCR.ACTION.PARTIAL_READBACK")["result"],
            "FAIL",
        )

    def test_complete_gate_rejects_unfinished_material_recovery(self) -> None:
        receipt = load_positive()
        terminal = receipt["terminal"]
        terminal["state"] = "COMPLETE"
        terminal["reason_code"] = "OBJECTIVE_COMPLETED"
        terminal["resumption_trigger"] = None
        terminal["next_transition"] = None
        receipt["boundary_events"][0]["recovery_sprint"]["outcome"] = None
        for check in receipt["proof"]["checks"]:
            check["status"] = "PASS"

        result = validator.validate_receipt(receipt)
        self.assertEqual(
            finding(result, "PRCR.TERMINAL.COMPLETE_GATE")["result"],
            "FAIL",
        )

    def test_hard_termination_claim_without_supervisor_attestation_is_unknown(self) -> None:
        receipt = load_positive()
        terminal = receipt["terminal"]
        terminal["state"] = "HARD_TERMINATED_SYNTHETIC"
        terminal["reason_code"] = "HOST_FORCED_TERMINATION"
        terminal["supervisor_synthesized"] = True

        result = validator.validate_receipt(receipt)
        self.assertEqual(
            finding(result, "PRCR.TERMINAL.HARD_SYNTHETIC")["result"],
            "UNKNOWN",
        )

    def test_hard_termination_accepts_canonical_supervisor_attestation(self) -> None:
        receipt = load_positive()
        terminal = receipt["terminal"]
        terminal["state"] = "HARD_TERMINATED_SYNTHETIC"
        terminal["reason_code"] = "HOST_FORCED_TERMINATION"
        terminal["supervisor_synthesized"] = True
        receipt["evidence"].append(
            {
                "evidence_id": "EV-SUPERVISOR",
                "kind": "provider",
                "ref": "supervisor-attestation:external-run-1",
                "supports": "External supervisor attested the host-forced termination.",
            }
        )

        result = validator.validate_receipt(receipt)
        self.assertEqual(
            finding(result, "PRCR.TERMINAL.HARD_SYNTHETIC")["result"],
            "PASS",
        )

    def test_bogus_protected_invariant_is_rejected(self) -> None:
        receipt = load_positive()
        receipt["scenario"]["protected_invariants"] = ["not-a-contract-rule"]
        result = validator.validate_receipt(receipt)
        self.assertEqual(
            finding(result, "PRCR.SCENARIO.PROTECTED_INVARIANTS")["result"],
            "FAIL",
        )

    def test_pass_with_critical_or_high_unknown_is_inconclusive(self) -> None:
        receipt = load_positive()
        receipt["privacy"] = None
        result = validator.validate_receipt(receipt)
        self.assertEqual(result["overall_result"], "INCONCLUSIVE")
        self.assertEqual(
            finding(result, "PRCR.COMPLIANCE.PASS")["result"],
            "UNKNOWN",
        )

    def test_timestamp_parser_rejects_malformed_and_timezone_naive_values(self) -> None:
        self.assertIsNone(validator._time("not-a-timestamp"))
        self.assertIsNone(validator._time("2026-09-18T12:00:00"))

        receipt = load_positive()
        receipt["run"]["started_at"] = "2026-09-18T12:00:00"
        result = validator.validate_receipt(receipt)
        self.assertNotEqual(result["overall_result"], "PASS")

    def test_cli_malformed_json_is_machine_readable_inconclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "malformed.json"
            path.write_text("{not-json", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_prompt_runtime_compliance_receipt.py",
                    str(path),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        self.assertEqual(json.loads(proc.stdout)["overall_result"], "INCONCLUSIVE")

    def test_cli_missing_file_is_machine_readable_inconclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_prompt_runtime_compliance_receipt.py",
                    str(path),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        self.assertEqual(json.loads(proc.stdout)["overall_result"], "INCONCLUSIVE")

    def test_cli_non_object_json_is_machine_readable_inconclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "array.json"
            path.write_text("[]", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_prompt_runtime_compliance_receipt.py",
                    str(path),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        self.assertEqual(json.loads(proc.stdout)["overall_result"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
