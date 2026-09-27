from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prompt_invocation_fidelity",
    ROOT / "scripts/prompt_invocation_fidelity.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class PromptInvocationFidelityTests(unittest.TestCase):
    def test_contract_declares_terminal_merit(self) -> None:
        contract = json.loads(
            (ROOT / "harness/contracts/prompt-retrospective-evaluation.v1.json").read_text(
                encoding="utf-8"
            )
        )
        merit = contract["terminal_merits"]["INVOCATION_FIDELITY"]
        self.assertEqual(
            merit["values"],
            ["PASS", "FAIL", "NOT_APPLICABLE", "UNKNOWN"],
        )
        self.assertIn("INVOCATION_FIDELITY", contract["record_contract"]["terminal_merits"])
        self.assertIn(
            "INVOCATION_FIDELITY FAIL is terminal",
            " ".join(contract["independence_rules"]),
        )

    def test_negative_invoked_p04_rewritten_without_execution_fails(self) -> None:
        event = {
            "prompt_id": "P04",
            "operator_request": "Invoke P04 on repo C:/tmp/triage with the attached context.",
            "agent_output": "Here is an improved version of the prompt with cleaner wording.",
            "executed_workflow": False,
            "produced_artifacts": [],
        }
        result = MOD.classify_invocation_fidelity(event)
        self.assertEqual(result["INVOCATION_FIDELITY"], "FAIL")
        self.assertTrue(result["terminal"])

    def test_positive_invoked_p04_execution_passes(self) -> None:
        event = {
            "prompt_id": "P04",
            "operator_request": "Invoke P04 on the refreshed Triage main.",
            "agent_output": "LAUNCH ORDER\n1. Lane A\nPARALLEL DISPATCH MANIFEST validated.",
            "executed_workflow": True,
            "produced_artifacts": ["Outputs/prompt-parallel-dispatch/manifest.json"],
        }
        result = MOD.classify_invocation_fidelity(event)
        self.assertEqual(result["INVOCATION_FIDELITY"], "PASS")
        self.assertFalse(result["terminal"])

    def test_positive_explicit_rewrite_request_passes(self) -> None:
        event = {
            "prompt_id": "P04",
            "operator_request": "Please rewrite/upgrade P04 for clarity; do not execute factoring.",
            "agent_output": "Suggested prompt rewrite attached; no repository factoring executed.",
            "executed_workflow": False,
            "mutation_only": True,
            "produced_artifacts": [],
        }
        result = MOD.classify_invocation_fidelity(event)
        self.assertEqual(result["INVOCATION_FIDELITY"], "PASS")
        self.assertTrue(result["mutation_requested"])


if __name__ == "__main__":
    unittest.main()
