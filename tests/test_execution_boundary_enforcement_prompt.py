from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.execution_boundary_engine import (
    BoundaryEngineError,
    assert_case,
    evaluate_boundary,
)
from scripts.validate_execution_boundary_enforcement import (
    ExecutionBoundaryContractError,
    validate_documents,
    validate_paths,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "harness/contracts/execution-boundary-enforcement.v1.json"
TAXONOMY = ROOT / "harness/contracts/execution-boundary-taxonomy.v1.json"
MATRIX = ROOT / "harness/evals/execution-boundaries/boundary-regression-matrix.v1.json"
SHARED_POLICY = ROOT / "registry/prompts/actionable-next-step-policy.v1.json"
VALIDATORS = ROOT / "harness/validators.v1.json"


class ExecutionBoundaryEnforcementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.architecture = json.loads(ARCHITECTURE.read_text(encoding="utf-8"))
        self.taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        self.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        self.policy = json.loads(SHARED_POLICY.read_text(encoding="utf-8"))
        self.validators = json.loads(VALIDATORS.read_text(encoding="utf-8"))

    def validate(self, *, architecture=None, taxonomy=None, matrix=None, policy=None):
        return validate_documents(
            architecture if architecture is not None else self.architecture,
            taxonomy if taxonomy is not None else self.taxonomy,
            matrix if matrix is not None else self.matrix,
            shared_policy=policy if policy is not None else self.policy,
        )

    def test_current_documents_validate(self) -> None:
        summary = validate_paths()
        self.assertEqual(summary["layers"], 11)
        self.assertEqual(summary["families"], 14)
        self.assertEqual(summary["classes"], 58)
        self.assertEqual(summary["cases"], 59)

    def test_validator_cli_passes_with_summary(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_execution_boundary_enforcement.py", "--summary"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("EXECUTION BOUNDARY ENFORCEMENT: PASS", completed.stdout)
        self.assertIn("classes=58", completed.stdout)
        self.assertIn("cases=59", completed.stdout)


    def test_boundary_checks_are_blocking_in_normal_local_profiles(self) -> None:
        required = {
            "execution-boundary-enforcement-audit",
            "execution-boundary-enforcement-tests",
            "privacy-failure-observatory-audit",
            "privacy-failure-observatory-tests",
        }
        definitions = {item["id"]: item for item in self.validators["validators"]}
        self.assertTrue(required.issubset(definitions))
        for validator_id in required:
            self.assertIs(definitions[validator_id]["blocking"], True)
        for profile in ("required_checks", "harness", "pre_push"):
            with self.subTest(profile=profile):
                self.assertTrue(required.issubset(set(self.validators["profiles"][profile])))

    def test_duplicate_taxonomy_class_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.taxonomy)
        duplicate = copy.deepcopy(mutated["families"][0]["classes"][0])
        mutated["families"][1]["classes"].append(duplicate)
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "duplicate taxonomy class"):
            self.validate(taxonomy=mutated)

    def test_unknown_default_recovery_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.taxonomy)
        mutated["families"][0]["classes"][0]["default_recovery"] = "JUST_STOP"
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "invalid default recovery"):
            self.validate(taxonomy=mutated)

    def test_every_class_requires_positive_and_negative_coverage(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        removed = next(case for case in mutated["cases"] if case["case_id"] == "EBR-001")
        mutated["cases"] = [case for case in mutated["cases"] if case["case_id"] != "EBR-001"]
        mutated["case_contract"]["minimum_cases"] = len(mutated["cases"])
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "every canonical class requires regression coverage"):
            self.validate(matrix=mutated)
        self.assertEqual(removed["classification"], "CR_TOOL_UNAVAILABLE")

    def test_positive_control_is_mandatory(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"][0]["positive_assertions"] = []
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "positive control missing"):
            self.validate(matrix=mutated)

    def test_negative_control_is_mandatory(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"][0]["negative_assertions"] = []
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "negative control missing"):
            self.validate(matrix=mutated)

    def test_semantic_abandonment_remains_first_class(self) -> None:
        mutated = copy.deepcopy(self.taxonomy)
        for family in mutated["families"]:
            family["classes"] = [item for item in family["classes"] if item["id"] != "EC_SEMANTIC_ABANDONMENT"]
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "required boundary class missing"):
            self.validate(taxonomy=mutated)

    def test_recovery_disclosure_case_is_mandatory(self) -> None:
        mutated = copy.deepcopy(self.matrix)
        mutated["cases"] = [case for case in mutated["cases"] if case["case_id"] != "EBR-013"]
        mutated["case_contract"]["minimum_cases"] = len(mutated["cases"])
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "critical bespoke regressions missing|every canonical class requires regression coverage"):
            self.validate(matrix=mutated)

    def test_partial_write_requires_readback_reconciliation(self) -> None:
        mutated_matrix = copy.deepcopy(self.matrix)
        mutated_taxonomy = copy.deepcopy(self.taxonomy)
        case = next(case for case in mutated_matrix["cases"] if case["case_id"] == "EBR-003")
        item = next(
            item for family in mutated_taxonomy["families"] for item in family["classes"]
            if item["id"] == "MT_PARTIAL_SIDE_EFFECT_POSSIBLE"
        )
        item["default_recovery"] = "RETRY_BOUNDED"
        case["expected_recovery"] = "RETRY_BOUNDED"
        case["expected_output"]["recovery_disposition"] = "RETRY_BOUNDED"
        case["expected_output"]["readback_required"] = False
        case["forbidden_outputs"] = [
            item for item in case["forbidden_outputs"] if item.get("field") != "readback_required"
        ]
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "partial-write case must reconcile"):
            self.validate(matrix=mutated_matrix, taxonomy=mutated_taxonomy)

    def test_hard_termination_requires_external_synthesis(self) -> None:
        mutated_matrix = copy.deepcopy(self.matrix)
        mutated_taxonomy = copy.deepcopy(self.taxonomy)
        case = next(case for case in mutated_matrix["cases"] if case["case_id"] == "EBR-015")
        item = next(
            item for family in mutated_taxonomy["families"] for item in family["classes"]
            if item["id"] == "HT_HOST_FORCED_TERMINATION"
        )
        item["default_recovery"] = "RESUME_FROM_CHECKPOINT"
        for candidate in mutated_matrix["cases"]:
            if candidate["classification"] == "HT_HOST_FORCED_TERMINATION":
                candidate["expected_recovery"] = "RESUME_FROM_CHECKPOINT"
                candidate["expected_output"]["recovery_disposition"] = "RESUME_FROM_CHECKPOINT"
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "hard-termination case must be supervisor-synthesized"):
            self.validate(matrix=mutated_matrix, taxonomy=mutated_taxonomy)

    def test_direct_active_to_complete_path_is_forbidden(self) -> None:
        mutated = copy.deepcopy(self.architecture)
        mutated["transition_invariants"] = [
            item for item in mutated["transition_invariants"]
            if "OBJECTIVE_ACTIVE may reach COMPLETE only through FINALIZING" not in item
        ]
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "direct completion must be forbidden"):
            self.validate(architecture=mutated)

    def test_public_transition_shape_cannot_drop_proved_checkpoint(self) -> None:
        mutated = copy.deepcopy(self.architecture)
        mutated["public_transition_contract"]["required_fields"].remove("PROVED")
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "public transition shape"):
            self.validate(architecture=mutated)

    def test_shared_policy_marker_is_required_in_both_inheritance_surfaces(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["next_step_suffix"] = mutated["next_step_suffix"].replace(
            "EXECUTION BOUNDARY ACCOUNTABILITY CONTRACT", "REMOVED BOUNDARY MARKER"
        )
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "marker missing"):
            self.validate(policy=mutated)

    def test_shared_policy_must_apply_to_every_prompt(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["applies_to"] = "Some prompts."
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "apply to every prompt"):
            self.validate(policy=mutated)

    def test_redaction_cannot_become_suppression(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["copy_content_appendix"] = mutated["copy_content_appendix"].replace(
            "Silence is never a terminal state.", "Silence may be used when details are private."
        )
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "silence is never"):
            self.validate(policy=mutated)


    def test_unknown_material_boundary_fallback_is_mandatory(self) -> None:
        mutated = copy.deepcopy(self.taxonomy)
        mutated["families"] = [
            family for family in mutated["families"] if family["id"] != "UNKNOWN_EVOLUTION"
        ]
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "required boundary class missing"):
            self.validate(taxonomy=mutated)

    def test_durable_outbox_layer_is_mandatory(self) -> None:
        mutated = copy.deepcopy(self.architecture)
        mutated["architecture_layers"] = [
            layer for layer in mutated["architecture_layers"]
            if layer["id"] != "durable_transition_outbox"
        ]
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "architecture layer coverage drifted"):
            self.validate(architecture=mutated)

    def test_boundary_event_requires_idempotent_delivery_identity(self) -> None:
        mutated = copy.deepcopy(self.architecture)
        mutated["boundary_event_envelope"]["required_fields"].remove("dedupe_key")
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "boundary event envelope required fields drifted"):
            self.validate(architecture=mutated)

    def test_state_machine_cannot_bypass_finalization(self) -> None:
        mutated = copy.deepcopy(self.architecture)
        mutated["state_machine"]["allowed_transitions"]["OBJECTIVE_ACTIVE"].append("COMPLETE")
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "direct active-to-complete"):
            self.validate(architecture=mutated)

    def test_every_material_boundary_opens_primary_recovery_sprint(self) -> None:
        contract = self.architecture["boundary_sprint_contract"]
        self.assertIn("Every MATERIAL or CRITICAL boundary", contract["applies_when"])
        self.assertIn("Classification is routing, not sprint eligibility.", contract["rules"])
        self.assertEqual(contract["executable_oracle"], "scripts/execution_boundary_engine.py")
        self.assertEqual(contract["state_transition"], "PRIMARY_RECOVERY_SPRINT_OPENED")
        mutated = copy.deepcopy(self.architecture)
        mutated["boundary_sprint_contract"]["applies_when"] = (
            "Only unknown or recurrent boundaries open a recovery sprint."
        )
        with self.assertRaisesRegex(
            ExecutionBoundaryContractError,
            "every material or critical boundary",
        ):
            self.validate(architecture=mutated)

    def test_shared_policy_cannot_make_taxonomy_a_sprint_eligibility_gate(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        self.assertIn("BOUNDARY-TO-SPRINT CONTINUATION", appendix)
        self.assertIn("classification is routing, not sprint eligibility", appendix.lower())
        mutated = copy.deepcopy(self.policy)
        mutated["copy_content_appendix"] = mutated["copy_content_appendix"].replace(
            "classification is routing, not sprint eligibility",
            "only unclassified boundaries are sprint eligible",
        )
        with self.assertRaisesRegex(
            ExecutionBoundaryContractError,
            "classification is routing, not sprint eligibility",
        ):
            self.validate(policy=mutated)

    def test_known_class_materializes_primary_recovery_sprint(self) -> None:
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "EBR-005")
        actual = evaluate_boundary(case["input_event"], self.architecture, self.taxonomy)
        self.assertEqual(actual["classification"], "OR_FANOUT_OR_TOOLCALL_CEILING")
        self.assertTrue(actual["primary_recovery_sprint_required"])
        self.assertTrue(actual["first_action_execution_required"])
        self.assertIn("PRIMARY_RECOVERY_SPRINT_OPENED", actual["execution_path"])
        self.assertEqual(
            actual["primary_recovery_sprint"]["first_executable_action"],
            case["expected_recovery"],
        )

    def test_engine_fails_if_primary_sprint_transition_is_removed(self) -> None:
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "EBR-005")
        mutated = copy.deepcopy(self.architecture)
        mutated["state_machine"]["allowed_transitions"]["RECOVERY_SELECTED"].remove(
            "PRIMARY_RECOVERY_SPRINT_OPENED"
        )
        with self.assertRaisesRegex(BoundaryEngineError, "transition unavailable"):
            evaluate_boundary(case["input_event"], mutated, self.taxonomy)

    def test_dual_lane_systemic_sprint_policy_is_mandatory(self) -> None:
        mutated = copy.deepcopy(self.architecture)
        del mutated["dual_lane_policy"]
        with self.assertRaisesRegex(ExecutionBoundaryContractError, "dual-lane"):
            self.validate(architecture=mutated)


    def test_executable_matrix_all_cases_match_expected_outputs(self) -> None:
        for case in self.matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                actual = assert_case(case, self.architecture, self.taxonomy)
                self.assertEqual(actual, case["expected_output"])

    def test_recovery_behavior_drift_breaks_executable_fixture(self) -> None:
        case = next(
            case for case in self.matrix["cases"]
            if case["classification"] == "EC_SEMANTIC_ABANDONMENT"
        )
        mutated = copy.deepcopy(self.taxonomy)
        item = next(
            item
            for family in mutated["families"]
            for item in family["classes"]
            if item["id"] == "EC_SEMANTIC_ABANDONMENT"
        )
        item["default_recovery"] = "CONTINUE_UNCHANGED"
        actual = evaluate_boundary(case["input_event"], self.architecture, mutated)
        self.assertNotEqual(actual, case["expected_output"])

    def test_transition_behavior_drift_fails_engine(self) -> None:
        case = next(
            case for case in self.matrix["cases"]
            if case["classification"] == "EC_SEMANTIC_ABANDONMENT"
        )
        mutated = copy.deepcopy(self.architecture)
        mutated["state_machine"]["allowed_transitions"]["BOUNDARY_OBSERVED"] = []
        with self.assertRaisesRegex(BoundaryEngineError, "transition unavailable"):
            evaluate_boundary(case["input_event"], mutated, self.taxonomy)

    def test_journal_behavior_drift_breaks_executable_fixture(self) -> None:
        case = next(
            case for case in self.matrix["cases"]
            if case["classification"] == "EC_SEMANTIC_ABANDONMENT"
        )
        mutated = copy.deepcopy(self.architecture)
        mutated["architecture_layers"] = [
            layer for layer in mutated["architecture_layers"]
            if layer["id"] != "append_only_journal"
        ]
        actual = evaluate_boundary(case["input_event"], mutated, self.taxonomy)
        self.assertNotEqual(actual, case["expected_output"])
        self.assertFalse(actual["journal_required"])

    def test_supervisor_behavior_drift_breaks_hard_termination_fixture(self) -> None:
        case = next(
            case for case in self.matrix["cases"]
            if case["classification"] == "HT_HOST_FORCED_TERMINATION"
        )
        mutated = copy.deepcopy(self.architecture)
        del mutated["external_supervisor_contract"]
        actual = evaluate_boundary(case["input_event"], mutated, self.taxonomy)
        self.assertNotEqual(actual, case["expected_output"])
        self.assertFalse(actual["supervisor_synthesized"])

    def test_unknown_detector_signal_uses_fail_safe_taxonomy_class(self) -> None:
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "EBR-058")
        actual = evaluate_boundary(case["input_event"], self.architecture, self.taxonomy)
        self.assertEqual(actual["classification"], "UE_UNCLASSIFIED_MATERIAL_BOUNDARY")
        self.assertTrue(actual["taxonomy_evolution_required"])

    def test_user_cancellation_reaches_stable_stop(self) -> None:
        case = next(case for case in self.matrix["cases"] if case["classification"] == "UC_CANCELLED")
        actual = evaluate_boundary(case["input_event"], self.architecture, self.taxonomy)
        self.assertEqual(actual["recovery_disposition"], "QUIESCE_UNCHANGED_BLOCKER")
        self.assertEqual(actual["execution_path"][-1], "QUIESCENT_BLOCKED")
        self.assertFalse(actual["primary_recovery_sprint_required"])
        self.assertFalse(actual["first_action_execution_required"])
        self.assertIsNone(actual["primary_recovery_sprint"])

    def test_dead_non_ht_signal_normalizes_to_hard_termination(self) -> None:
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "EBR-059")
        actual = evaluate_boundary(case["input_event"], self.architecture, self.taxonomy)
        self.assertEqual(actual["classification"], "HT_HOST_FORCED_TERMINATION")
        self.assertEqual(actual["recovery_disposition"], "SYNTHESIZE_TERMINATION")
        self.assertEqual(actual["execution_path"], ["HARD_TERMINATED_SYNTHETIC"])
        self.assertFalse(actual["primary_recovery_sprint_required"])
        self.assertFalse(actual["first_action_execution_required"])
        self.assertIsNone(actual["primary_recovery_sprint"])


if __name__ == "__main__":
    unittest.main()
