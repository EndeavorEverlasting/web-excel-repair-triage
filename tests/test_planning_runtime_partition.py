from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "planning_runtime_partition",
    ROOT / "scripts/planning_runtime_partition.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def evidence(*, durable_ref: str = "opaque:plan-rev-abc", visibility: str = "public_tracked") -> dict:
    return {
        "evidence_type": "canonical_plan_revision",
        "source_owner_class": "repository_plan",
        "durable_ref": durable_ref,
        "revision_or_freshness": "sha:deadbeef",
        "visibility": visibility,
        "proof_ceiling": "repository_static",
    }


class PlanningRuntimePartitionShimTests(unittest.TestCase):
    def test_shim_validates_dispatch_lane_metadata(self) -> None:
        lane = {
            "execution_environment": "CURRENT_CHAT_RUNTIME",
            "provider_access": ["google_drive"],
            "required_capabilities": ["provider.read"],
            "evidence_inputs": [evidence()],
        }
        meta = MOD.validate_lane_runtime_metadata(lane, lane_id="lane-a")
        self.assertEqual(meta["execution_environment"], "CURRENT_CHAT_RUNTIME")
        self.assertEqual(meta["provider_access"][0]["provider_family"], "google_drive")

    def test_shim_rejects_private_google_url_in_tracked_evidence(self) -> None:
        lane = {
            "execution_environment": "LOCAL_AGENT_RUNTIME",
            "provider_access": [],
            "required_capabilities": ["local.toolchain"],
            "evidence_inputs": [
                evidence(
                    durable_ref="https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view"
                )
            ],
        }
        with self.assertRaisesRegex(MOD.RuntimePartitionError, "Google Workspace URL"):
            MOD.validate_lane_runtime_metadata(lane, lane_id="lane-a")

    def test_canonical_owner_projects_for_p04_and_p05(self) -> None:
        decision = MOD.partition_work_unit(
            {
                "work_unit_id": "wu-1",
                "required_capabilities": ["provider.read"],
                "capability_facts": {
                    "current_runtime_available": True,
                    "current_runtime_authorized": True,
                    "local_runtime_required": False,
                    "ci_remote_required": False,
                    "operator_physical_required": False,
                },
                "provider_access": [
                    {
                        "provider_family": "google_drive",
                        "operation": "read",
                        "authority_state": "VERIFIED",
                        "mutation_authority": False,
                    }
                ],
                "inherited_evidence": [
                    {
                        "evidence_type": "repository_state",
                        "source_owner": "Triage",
                        "sanitized_ref": "opaque:plan",
                        "revision_or_freshness": "sha:abc",
                        "visibility": "PUBLIC_TRACKED",
                        "proof_ceiling": "unit",
                        "public_provider_ref_verified": False,
                    }
                ],
            }
        )
        p04 = MOD.project_p04(decision)
        p05 = MOD.project_p05(decision)
        self.assertEqual(p04["execution_environment"], p05["EXECUTION ENVIRONMENT"])
        self.assertEqual(p04["provider_access"], p05["PROVIDER / ACCESS ROUTE"])


if __name__ == "__main__":
    unittest.main()
