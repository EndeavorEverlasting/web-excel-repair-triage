#!/usr/bin/env python3
"""Tests for run_local_required_checks.py (local CI gate substitute)."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_local_required_checks import REQUIRED_CHECKS_PROFILE


class TestLocalRequiredChecks(unittest.TestCase):
    """Verify local required-checks runner invokes the right profile and produces receipts."""

    def test_required_checks_profile_exists(self):
        """The required_checks profile must be registered in validators.v1.json."""
        registry_path = REPO_ROOT / "harness" / "validators.v1.json"
        self.assertTrue(registry_path.exists())
        registry = json.loads(registry_path.read_text("utf-8"))
        self.assertIn("profiles", registry)
        self.assertIn(REQUIRED_CHECKS_PROFILE, registry["profiles"])
        profile_validators = registry["profiles"][REQUIRED_CHECKS_PROFILE]
        self.assertIsInstance(profile_validators, list)
        self.assertGreater(len(profile_validators), 0)

        # Required checks must include governance and harness gates
        profile_set = set(profile_validators)
        required_gates = {
            "harness-completeness",
            "harness-contract-tests",
            "pr-merge-gate-audit",
            "pr-merge-gate-tests",
        }
        self.assertTrue(required_gates.issubset(profile_set))

    def test_local_required_checks_script_exists_and_compiles(self):
        """The run_local_required_checks.py script must exist and compile."""
        script_path = REPO_ROOT / "scripts" / "run_local_required_checks.py"
        self.assertTrue(script_path.exists())
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"run_local_required_checks.py failed to compile: {result.stderr}",
        )

    def test_local_required_checks_invocation_dry_run(self):
        """Invoke run_local_required_checks.py with a test report path (allows failure)."""
        script_path = REPO_ROOT / "scripts" / "run_local_required_checks.py"
        test_report = REPO_ROOT / "Outputs" / "test-local-required-checks-receipt.json"
        test_report.parent.mkdir(parents=True, exist_ok=True)
        if test_report.exists():
            test_report.unlink()

        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--report",
                str(test_report),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        # The script may fail (exit code 1) if validators fail, but should not crash (exit code 2)
        self.assertIn(
            result.returncode,
            [0, 1],
            f"run_local_required_checks.py crashed (exit {result.returncode}): {result.stderr}",
        )

        # Receipt must exist and be valid JSON with expected fields
        self.assertTrue(
            test_report.exists(),
            f"Receipt not created at {test_report}. stdout={result.stdout} stderr={result.stderr}",
        )
        receipt = json.loads(test_report.read_text("utf-8"))
        self.assertIn("schema_version", receipt)
        self.assertIn("status", receipt)
        self.assertIn("profile", receipt)
        self.assertEqual(receipt["profile"], REQUIRED_CHECKS_PROFILE)
        self.assertIn("steps", receipt)
        self.assertIsInstance(receipt["steps"], list)
        self.assertGreater(len(receipt["steps"]), 0)

        # Clean up test receipt
        test_report.unlink()

    def test_pr_merge_gate_contract_references_local_required_checks(self):
        """The pr-merge-gate contract must reference run_local_required_checks.py."""
        contract_path = REPO_ROOT / "harness" / "contracts" / "pr-merge-gate.v1.json"
        self.assertTrue(contract_path.exists())
        contract = json.loads(contract_path.read_text("utf-8"))
        self.assertIn("degraded_check_rules", contract)
        rules = contract["degraded_check_rules"]
        self.assertIn("local_proof_validators", rules)
        validators = rules["local_proof_validators"]
        self.assertIsInstance(validators, list)

        # Check that run_local_required_checks.py is named
        self.assertTrue(
            any("run_local_required_checks.py" in v for v in validators),
            f"run_local_required_checks.py not found in local_proof_validators: {validators}",
        )


if __name__ == "__main__":
    unittest.main()
