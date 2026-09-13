from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_PATH = ROOT / "scripts" / "prompt-topology" / "pipeline.py"
sys.path.insert(0, str(PIPELINE_PATH.parent))
spec = importlib.util.spec_from_file_location("prompt_topology_pipeline", PIPELINE_PATH)
assert spec and spec.loader
pipeline = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pipeline
spec.loader.exec_module(pipeline)

SECTIONS = [
    {"id": "build-repair", "name": "Build & Repair", "types": ["BUILD", "REPAIR"]},
    {"id": "validate-protect", "name": "Validate & Protect", "types": ["VALIDATE"]},
]


def prompt(pid: str, seq: int, title: str, body: str, *, kind: str = "BUILD", role: str = "BUILD", next_step: str = "Run tests", keywords=None):
    return {
        "id": pid,
        "seq": f"{seq:02d}",
        "name": title,
        "type": kind,
        "class": "SPRINT / BUILD + MUTATE" if kind != "VALIDATE" else "PROOF",
        "sprintRole": role,
        "useWhen": title,
        "inspectFirst": "scripts/example.py tests/example.py",
        "expectedOutput": "tracked implementation and proof",
        "proofGate": "python tests/example.py",
        "nextStep": next_step,
        "copyContent": body,
        "keywords": keywords or ["repository", "test"],
        "category": "standard",
        "color": "blue",
        "copySheet": "Prompt Kit",
    }


class PhaseATopologyTests(unittest.TestCase):
    def setUp(self):
        self.prompts = [
            prompt("P1", 1, "Build repository validator", "build repository validator tests deterministic evidence", next_step="Then use P2"),
            prompt("P2", 2, "Repair repository validator", "repair repository validator tests deterministic evidence"),
            prompt("P3", 3, "Build repository harness", "build repository harness validator deterministic tests"),
            prompt("P4", 4, "Validate repository harness", "validate repository harness tests proof deterministic", kind="VALIDATE", role="VALIDATE"),
            prompt("P5", 5, "Garden pollinator notes", "parsley flowers pollinators garden soil frost", kind="REPAIR", role="REPAIR", keywords=["garden", "pollinator"]),
            prompt("P6", 6, "Build CI validator", "build ci validator repository tests deterministic evidence"),
            prompt("P7", 7, "Repair CI validator", "repair ci validator repository tests deterministic evidence"),
            prompt("P8", 8, "Build test floor", "build test floor repository validator deterministic evidence"),
        ]
        self.routes = {
            item["id"]: {"classifier_section": "Build & Repair" if item["type"] != "VALIDATE" else "Validate & Protect"}
            for item in self.prompts
        }
        self.config = pipeline.RuntimeConfig(min_cluster_size=3, min_samples=2, embedding_dimensions=128, pca_dimensions=8, neighbor_top_k=3)

    def test_every_canonical_prompt_is_exactly_one_node_and_input_is_not_mutated(self):
        before = copy.deepcopy(self.prompts)
        artifact = pipeline.build_topology(self.prompts, SECTIONS, tutorial_routes=self.routes, config=self.config)
        self.assertEqual([p["id"] for p in self.prompts], [p["id"] for p in before])
        self.assertEqual({p["id"] for p in self.prompts}, {n["prompt_id"] for n in artifact["nodes"]})
        self.assertEqual(len(self.prompts), len(artifact["nodes"]))

    def test_unknown_endpoint_and_self_edge_fail_closed(self):
        artifact = pipeline.build_topology(self.prompts, SECTIONS, tutorial_routes=self.routes, config=self.config)
        broken = copy.deepcopy(artifact)
        broken["edges"][0]["target"] = "P999"
        unhashed = dict(broken); unhashed.pop("content_hash_sha256", None)
        broken["content_hash_sha256"] = pipeline.sha256_payload(unhashed)
        with self.assertRaisesRegex(ValueError, "unknown edge endpoint"):
            pipeline.validate_topology(broken, [p["id"] for p in self.prompts])
        broken = copy.deepcopy(artifact)
        broken["edges"][0]["target"] = broken["edges"][0]["source"]
        unhashed = dict(broken); unhashed.pop("content_hash_sha256", None)
        broken["content_hash_sha256"] = pipeline.sha256_payload(unhashed)
        with self.assertRaisesRegex(ValueError, "self edge"):
            pipeline.validate_topology(broken, [p["id"] for p in self.prompts])

    def test_multi_channel_edge_and_semantic_neighbor_evidence_are_stable(self):
        artifact = pipeline.build_topology(self.prompts, SECTIONS, tutorial_routes=self.routes, config=self.config)
        edge = next(e for e in artifact["edges"] if {e["source"], e["target"]} == {"P1", "P2"})
        channels = [c["type"] for c in edge["channels"]]
        self.assertIn("SEMANTIC_NEIGHBOR", channels)
        self.assertIn("WORKFLOW_NEXT", channels)
        self.assertIn("CLASS_FAMILY", channels)
        self.assertEqual(channels, sorted(channels, key=pipeline.CHANNEL_ORDER.index))

    def test_obvious_cluster_plus_unrelated_outlier_executes_real_hdbscan(self):
        ids = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
        vectors = np.array([
            [0.0, 0.0], [0.02, 0.0], [0.0, 0.02],
            [5.0, 5.0], [5.02, 5.0], [5.0, 5.02],
            [100.0, -100.0],
        ], dtype=float)
        clusters, outliers, _ = pipeline.cluster_vectors(ids, vectors, min_cluster_size=3, min_samples=2)
        self.assertEqual(2, len(clusters))
        self.assertEqual(["P7"], outliers)

    def test_membership_expansion_preserves_persistent_id_but_changes_fingerprint(self):
        first = pipeline.reconcile_clusters([["P1", "P2", "P3"]], None)
        previous = [{"cluster_id": first[0]["cluster_id"], "member_prompt_ids": ["P1", "P2", "P3"]}]
        second = pipeline.reconcile_clusters([["P1", "P2", "P3", "P4"]], previous)
        self.assertEqual(first[0]["cluster_id"], second[0]["cluster_id"])
        self.assertNotEqual(first[0]["membership_fingerprint_sha256"], second[0]["membership_fingerprint_sha256"])
        self.assertEqual("EXPANDED", second[0]["lineage"])

    def test_unrelated_cluster_cannot_inherit_previous_identity(self):
        previous = [{"cluster_id": "C-ABCDEF", "member_prompt_ids": ["P1", "P2", "P3"]}]
        current = pipeline.reconcile_clusters([["P6", "P7", "P8"]], previous)
        self.assertNotEqual("C-ABCDEF", current[0]["cluster_id"])
        self.assertEqual("NEW", current[0]["lineage"])

    def test_opportunity_state_fixtures(self):
        self.assertEqual("REDUNDANT", pipeline.classify_opportunity({"redundancy_penalty": 90}, lineage="UNCHANGED", member_count=5)[0])
        self.assertEqual("FRAGMENTED", pipeline.classify_opportunity({"workflow_gap": 90}, lineage="UNCHANGED", member_count=5)[0])
        self.assertEqual("AMBIGUOUS", pipeline.classify_opportunity({"ambiguity": 90}, lineage="UNCHANGED", member_count=5)[0])
        self.assertEqual(("HEALTHY", "NONE"), pipeline.classify_opportunity({"semantic_gap": 5, "workflow_gap": 0}, lineage="UNCHANGED", member_count=8)[:2])

    def test_opportunity_scoring_cannot_mutate_registry_truth(self):
        before = copy.deepcopy(self.prompts)
        artifact = pipeline.build_topology(self.prompts, SECTIONS, tutorial_routes=self.routes, config=self.config)
        self.assertTrue(artifact["opportunities"])
        self.assertEqual(before, self.prompts)

    def test_repeated_and_shuffled_input_are_byte_identical(self):
        first = pipeline.topology_bytes(pipeline.build_topology(self.prompts, SECTIONS, tutorial_routes=self.routes, config=self.config))
        second = pipeline.topology_bytes(pipeline.build_topology(self.prompts, SECTIONS, tutorial_routes=self.routes, config=self.config))
        shuffled = list(reversed(self.prompts))
        routes = {key: self.routes[key] for key in reversed(list(self.routes))}
        third = pipeline.topology_bytes(pipeline.build_topology(shuffled, SECTIONS, tutorial_routes=routes, config=self.config))
        self.assertEqual(first, second)
        self.assertEqual(first, third)


if __name__ == "__main__":
    unittest.main()
