from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PromptRuntimePartitionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {
            p["id"]: p for p in json.loads((ROOT / "docs/prompts.json").read_text(encoding="utf-8"))
        }
        profiles = json.loads(
            (ROOT / "harness/prompt-topology/prompt-capability-profiles.v1.json").read_text(
                encoding="utf-8"
            )
        )["profiles"]
        cls.profiles = {p["prompt_id"]: p for p in profiles}
        cls.catalog = {
            c["capability_id"]
            for c in json.loads(
                (ROOT / "harness/prompt-topology/semantic-capability-catalog.v1.json").read_text(
                    encoding="utf-8"
                )
            )["capabilities"]
        }
        cls.overrides = {
            o["id"]
            for o in json.loads(
                (ROOT / "registry/prompts/prompt-overrides.v1.json").read_text(encoding="utf-8")
            )["overrides"]
        }

    def test_no_p04_or_p05_override_invented(self) -> None:
        self.assertNotIn("P04", self.overrides)
        self.assertNotIn("P05", self.overrides)

    def test_shared_capability_assigned_to_both_planners(self) -> None:
        self.assertIn("planning.runtime_partition", self.catalog)
        for pid in ("P04", "P05"):
            caps = {
                row["capability_id"]: row for row in self.profiles[pid]["direct_assignments"]
            }
            self.assertIn("planning.runtime_partition", caps)
            row = caps["planning.runtime_partition"]
            self.assertEqual(row["presence"], "REQUIRED")
            self.assertEqual(row["ownership"], "PRIMARY")
            self.assertEqual(row["capability_relation"], "IMPLEMENTS")

    def test_p04_runtime_partition_preserves_launch_order_and_p07_ownership(self) -> None:
        text = self.prompts["P04"]["copyContent"]
        self.assertIn("RUNTIME PARTITION / EXECUTION PLACEMENT", text)
        self.assertIn("choose exactly one HOST", text)
        self.assertIn("PROVIDER routes", text)
        self.assertIn("planning.runtime_partition", text)
        self.assertIn("LAUNCH ORDER stays first", text)
        self.assertIn("P07 retains implementation ownership", text)
        runtime_slice = text.split("RUNTIME PARTITION", 1)[1][:1200]
        self.assertNotIn("CONNECTED_PROVIDER", runtime_slice)
        self.assertLess(
            text.index("RUNTIME PARTITION / EXECUTION PLACEMENT"),
            text.index("FACTORING PASS"),
        )
        order = text.split("OUTPUT ORDER", 1)[-1]
        self.assertIn("1. LAUNCH ORDER", order)
        self.assertLess(order.index("1. LAUNCH ORDER"), order.index("2. PARALLEL DISPATCH MANIFEST"))

    def test_p05_runtime_partition_keeps_launch_order_first(self) -> None:
        text = self.prompts["P05"]["copyContent"]
        self.assertIn("RUNTIME PARTITION / EXECUTION PLACEMENT", text)
        self.assertIn("same shared planning.runtime_partition contract as P04", text)
        self.assertIn("LAUNCH ORDER remains first substantive section", text)
        self.assertIn("INHERITED EVIDENCE", text)
        self.assertIn("RUNTIME HANDOFF", text)
        self.assertLess(
            text.index("The first substantive section must be LAUNCH ORDER."),
            text.index("RUNTIME PARTITION / EXECUTION PLACEMENT"),
        )
        self.assertLess(
            text.index("RUNTIME PARTITION / EXECUTION PLACEMENT"),
            text.index("3. FACTORING PASS"),
        )

    def test_dispatch_contract_requires_runtime_partition_lane_fields(self) -> None:
        contract = json.loads(
            (ROOT / "harness/contracts/prompt-parallel-dispatch.v1.json").read_text(encoding="utf-8")
        )
        for field in ("runtime_partition_input", "runtime_partition"):
            self.assertIn(field, contract["required_lane_fields"])
        runtime = contract["runtime_partition"]
        self.assertEqual(
            runtime["contract"],
            "harness/contracts/planning-runtime-partition.v1.json",
        )
        self.assertEqual(runtime["implementation"], "scripts/prompt_runtime_partition.py")
        self.assertTrue(contract["policy"]["runtime_partition_projection_required"])
        shared = json.loads(
            (ROOT / "harness/contracts/planning-runtime-partition.v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(shared["schema_version"], "planning-runtime-partition/v1")
        self.assertIn("P04", shared["consumers"])
        self.assertIn("P05", shared["consumers"])
        for field in (
            "evidence_type",
            "source_owner",
            "sanitized_ref",
            "revision_or_freshness",
            "visibility",
            "proof_ceiling",
        ):
            self.assertIn(field, shared["evidence_record"]["required_fields"])
        self.assertIn("P04", shared["projection_rules"])
        self.assertIn("P05", shared["projection_rules"])
        self.assertEqual(shared["canonical_implementation"], "scripts/prompt_runtime_partition.py")
        self.assertTrue((ROOT / "scripts/prompt_runtime_partition.py").is_file())
        self.assertTrue((ROOT / "scripts/planning_runtime_partition.py").is_file())


if __name__ == "__main__":
    unittest.main()
