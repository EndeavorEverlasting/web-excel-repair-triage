from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prompt_runtime_partition",
    ROOT / "scripts" / "prompt_runtime_partition.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def evidence(
    *,
    visibility: str = "PUBLIC_TRACKED",
    ref: str = "repo:plan@abc123",
    public_provider_ref_verified: bool = False,
) -> dict:
    return {
        "evidence_type": "repository_state",
        "source_owner": "TokenCorridor",
        "sanitized_ref": ref,
        "revision_or_freshness": "sha:abc123",
        "visibility": visibility,
        "proof_ceiling": "repository/provider evidence",
        "public_provider_ref_verified": public_provider_ref_verified,
    }


def unit(**facts) -> dict:
    base = {
        "current_runtime_available": False,
        "current_runtime_authorized": False,
        "local_runtime_required": False,
        "ci_remote_required": False,
        "operator_physical_required": False,
    }
    base.update(facts)
    return {
        "work_unit_id": "wu-1",
        "required_capabilities": ["provider.read"],
        "capability_facts": base,
        "provider_access": [],
        "inherited_evidence": [evidence()],
    }


class RuntimePartitionPrototypeTests(unittest.TestCase):
    def test_chat_runtime_with_google_provider_keeps_host_and_provider_separate(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["provider_access"] = [{
            "provider_family": "google_drive",
            "operation": "read spreadsheet metadata",
            "authority_state": "VERIFIED",
            "mutation_authority": False,
        }]
        decision = MOD.partition_work_unit(payload)
        self.assertEqual(decision.execution_environment, "CURRENT_CHAT_RUNTIME")
        self.assertEqual(decision.provider_access[0]["provider_family"], "google_drive")
        self.assertTrue(decision.execute_now)

    def test_provider_presence_does_not_select_host_by_itself(self) -> None:
        payload = unit()
        payload["provider_access"] = [{
            "provider_family": "github",
            "operation": "read pull request",
            "authority_state": "AVAILABLE_UNVERIFIED",
            "mutation_authority": False,
        }]
        decision = MOD.partition_work_unit(payload)
        self.assertEqual(decision.execution_environment, "UNKNOWN_RUNTIME")
        self.assertFalse(decision.execute_now)

    def test_local_only_work_goes_local(self) -> None:
        decision = MOD.partition_work_unit(unit(local_runtime_required=True))
        self.assertEqual(decision.execution_environment, "LOCAL_AGENT_RUNTIME")

    def test_conflicting_hard_hosts_require_split(self) -> None:
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "split it before placement"):
            MOD.partition_work_unit(unit(local_runtime_required=True, ci_remote_required=True))

    def test_private_external_evidence_requires_opaque_alias(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["inherited_evidence"] = [
            evidence(visibility="PROTECTED_EXTERNAL", ref="https://docs.google.com/spreadsheets/d/private-id")
        ]
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "opaque"):
            MOD.partition_work_unit(payload)

    def test_raw_google_url_is_rejected_even_if_mislabeled_public(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["inherited_evidence"] = [
            evidence(visibility="PUBLIC_TRACKED", ref="https://drive.google.com/file/d/private-id")
        ]
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "raw Google Workspace URL"):
            MOD.partition_work_unit(payload)

    def test_private_external_opaque_alias_passes(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["inherited_evidence"] = [
            evidence(visibility="PROTECTED_EXTERNAL", ref="opaque:prompt-scratch/live-workbook")
        ]
        decision = MOD.partition_work_unit(payload)
        self.assertEqual(decision.evidence_inputs[0]["visibility"], "PROTECTED_EXTERNAL")

    def test_private_github_url_requires_opaque_or_verified_public_status(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["inherited_evidence"] = [
            evidence(
                visibility="SANITIZED_OPAQUE",
                ref="https://github.com/EndeavorEverlasting/TokenCorridor/blob/main/plan.md",
            )
        ]
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "verified public status"):
            MOD.partition_work_unit(payload)

    def test_verified_public_github_url_may_be_tracked(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["inherited_evidence"] = [
            evidence(
                visibility="PUBLIC_TRACKED",
                ref="https://github.com/EndeavorEverlasting/web-excel-repair-triage/blob/main/README.md",
                public_provider_ref_verified=True,
            )
        ]
        decision = MOD.partition_work_unit(payload)
        self.assertTrue(decision.evidence_inputs[0]["public_provider_ref_verified"])

    def test_malformed_enum_values_fail_with_runtime_partition_error(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["provider_access"] = [{
            "provider_family": "github",
            "operation": "read pull request",
            "authority_state": ["VERIFIED"],
            "mutation_authority": False,
        }]
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "authority_state is invalid"):
            MOD.partition_work_unit(payload)

        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["inherited_evidence"][0]["visibility"] = ["PUBLIC_TRACKED"]
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "visibility is invalid"):
            MOD.partition_work_unit(payload)

    def test_p04_and_p05_project_same_shared_decision(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        decision = MOD.partition_work_unit(payload)
        p04 = MOD.project_p04(decision)
        p05 = MOD.project_p05(decision)
        self.assertEqual(p04["execution_environment"], p05["EXECUTION ENVIRONMENT"])
        self.assertEqual(p04["evidence_inputs"], p05["INHERITED EVIDENCE"])

    def test_projection_records_are_isolated_copies(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["provider_access"] = [{
            "provider_family": "github",
            "operation": "read pull request",
            "authority_state": "VERIFIED",
            "mutation_authority": False,
        }]
        decision = MOD.partition_work_unit(payload)
        p04 = MOD.project_p04(decision)
        p05 = MOD.project_p05(decision)
        p04["provider_access"][0]["operation"] = "mutated"
        p05["INHERITED EVIDENCE"][0]["proof_ceiling"] = "mutated"
        self.assertEqual(decision.provider_access[0]["operation"], "read pull request")
        self.assertEqual(decision.evidence_inputs[0]["proof_ceiling"], "repository/provider evidence")

    def test_already_executed_here_requires_boolean(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["already_executed_here"] = "false"
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "must be boolean"):
            MOD.partition_work_unit(payload)

    def test_already_executed_here_is_rejected_for_local_work(self) -> None:
        payload = unit(local_runtime_required=True)
        payload["already_executed_here"] = True
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "CURRENT_CHAT_RUNTIME"):
            MOD.partition_work_unit(payload)

    def test_already_executed_here_requires_evidence(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["inherited_evidence"] = []
        payload["already_executed_here"] = True
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "requires inherited_evidence"):
            MOD.partition_work_unit(payload)

    def test_repartition_after_current_runtime_completion_suppresses_repeat_execution(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        first = MOD.partition_work_unit(payload)
        self.assertTrue(first.execute_now)
        payload["inherited_evidence"].append(evidence(ref="repo:current-runtime-result@def456"))
        payload["already_executed_here"] = True
        completed = MOD.partition_work_unit(payload)
        self.assertFalse(completed.execute_now)
        self.assertTrue(completed.already_executed_here)

    def test_p05_completed_current_runtime_step_is_not_fake_handoff(self) -> None:
        payload = unit(current_runtime_available=True, current_runtime_authorized=True)
        payload["already_executed_here"] = True
        decision = MOD.partition_work_unit(payload)
        self.assertFalse(decision.execute_now)
        panel = MOD.project_p05(decision)
        self.assertTrue(panel["ALREADY EXECUTED HERE"])
        self.assertEqual(panel["RUNTIME HANDOFF"], "none")

    def test_cli_emits_p04_projection_from_work_unit_json(self) -> None:
        payload = unit(local_runtime_required=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "work-unit.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                returncode = MOD.main(["p04", "--input", str(input_path)])
        self.assertEqual(returncode, 0)
        emitted = json.loads(stdout.getvalue())
        self.assertEqual(emitted["schema_version"], "planning-runtime-partition-cli/v1")
        self.assertEqual(emitted["surface"], "P04")
        self.assertEqual(emitted["work_unit_id"], "wu-1")
        self.assertEqual(emitted["projection"], MOD.project_p04(MOD.partition_work_unit(payload)))


if __name__ == "__main__":
    unittest.main()
