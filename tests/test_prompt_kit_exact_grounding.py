from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs" / "prompt-kit-exact-grounding.js"
CONTRACT = ROOT / "harness" / "exact-grounding" / "agent-command-boundary.v1.json"
DOC = ROOT / "docs" / "PROMPT_KIT_EXACT_GROUNDING.md"

class PromptKitExactGroundingTests(unittest.TestCase):
    def test_runtime_self_test_covers_zero_entropy_boundary(self) -> None:
        completed = subprocess.run(["node", str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "PASS")
        by_case = {item["case"]: item for item in report["checks"]}
        self.assertEqual(by_case["hallucinated_identifier"]["outcome"], "CONTRADICTION_BLOCK")
        self.assertEqual(by_case["hallucinated_operation"]["outcome"], "UNSOURCED_BLOCK")
        self.assertEqual(by_case["in_context_constraint_contradiction"]["outcome"], "CONTRADICTION_BLOCK")
        self.assertEqual(by_case["schema_mismatch"]["outcome"], "SCHEMA_MISMATCH")
        self.assertEqual(by_case["malformed_grounding_source"]["outcome"], "GROUNDING_FAILURE")
        self.assertEqual(by_case["malformed_nested_contract"]["outcome"], "GROUNDING_FAILURE")
        self.assertEqual(by_case["stale_structure_refresh"]["outcome"], "GROUNDING_FAILURE_THEN_GROUNDED_PASS")
        self.assertEqual(by_case["valid_exact_signature"]["sideEffectExecutions"], 1)
        self.assertEqual(by_case["valid_exact_signature"]["consistencyPasses"], 2)

    def test_contract_is_machine_readable_and_host_owned(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema_version"], "prompt-kit-agent-grounding-contract/v1")
        self.assertEqual(contract["execution_authority"], "host_command_kernel")
        self.assertEqual(contract["model_authority"], "proposal_only")
        self.assertEqual(contract["required_command_fields"], ["type", "promptId", "source"])
        self.assertEqual(contract["exact_fields"]["source"]["allowed"], ["agent"])
        self.assertEqual(set(contract["outcomes"]), {"GROUNDED_PASS", "UNSOURCED_BLOCK", "CONTRADICTION_BLOCK", "SCHEMA_MISMATCH", "GROUNDING_FAILURE"})

    def test_docs_keep_scope_lean_and_failure_deterministic(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        for marker in ("live `CommandKernel.handlers` registry", "live `PromptCatalog.byId` registry", "structural SHA-256 version", "No model critic can override", "exactly once"):
            self.assertIn(marker, text)

    def test_interceptor_delegates_only_after_second_validation(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        first = source.index("const first = this.validate(proposal);")
        second = source.index("const second = this.validate(proposal);")
        delegate = source.index("const result = await this.kernel.execute(proposal.command);")
        self.assertLess(first, second)
        self.assertLess(second, delegate)
        self.assertIn("second.packetDigest !== first.packetDigest", source)
        self.assertIn("second.sourceVersion !== first.sourceVersion", source)

    def test_proposal_schema_version_is_grounded_not_remembered(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        helper = source[source.index("function proposalFromPacket"):source.index("async function expectBlocked")]
        self.assertIn("schemaVersion: packet.proposalSchemaVersion", helper)
        self.assertNotIn("'prompt-kit-grounded-command/v1'", helper)
        self.assertIn("proposalSchemaVersion: contract.proposal_schema_version", source)
        self.assertIn("packetSchemaVersion: contract.packet_schema_version", source)

    def test_nested_contract_shapes_are_validated_fail_closed(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("sameStringSet(allowed, ['agent'])", source)
        self.assertIn("Grounding authority boundary drifted", source)
        self.assertIn("Exact-field authority record is malformed", source)

if __name__ == "__main__": unittest.main()
