from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts" / "prompt-topology"
sys.path.insert(0, str(SCRIPT_DIR))

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

pipeline = load_module("phase_b_pipeline", SCRIPT_DIR / "pipeline.py")
projection = load_module("phase_b_projection", SCRIPT_DIR / "projection.py")

SECTIONS = [
    {"id": "build-repair", "name": "Build & Repair", "types": ["BUILD", "REPAIR"]},
    {"id": "validate-protect", "name": "Validate & Protect", "types": ["VALIDATE"]},
]


def prompt(pid: str, seq: int, title: str, body: str, *, kind: str = "BUILD", role: str = "BUILD"):
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
        "nextStep": "Run tests",
        "copyContent": body,
        "keywords": ["repository", "test", title.split()[0].lower()],
        "category": "standard",
        "color": "blue",
        "copySheet": "Prompt Kit",
    }


class PhaseBProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = [
            prompt("P1", 1, "Build repository validator", "build repository validator tests deterministic evidence"),
            prompt("P2", 2, "Repair repository validator", "repair repository validator tests deterministic evidence"),
            prompt("P3", 3, "Build repository harness", "build repository harness validator deterministic tests"),
            prompt("P4", 4, "Validate repository harness", "validate repository harness tests proof deterministic", kind="VALIDATE", role="VALIDATE"),
            prompt("P5", 5, "Garden pollinator notes", "parsley flowers pollinators garden soil frost", kind="REPAIR", role="REPAIR"),
            prompt("P6", 6, "Build CI validator", "build ci validator repository tests deterministic evidence"),
            prompt("P7", 7, "Repair CI validator", "repair ci validator repository tests deterministic evidence"),
            prompt("P8", 8, "Build test floor", "build test floor repository validator deterministic evidence"),
        ]
        cls.routes = {
            item["id"]: {
                "classifier_section": "Build & Repair" if item["type"] != "VALIDATE" else "Validate & Protect"
            }
            for item in cls.prompts
        }
        cls.phase_a_config = pipeline.RuntimeConfig(
            min_cluster_size=3,
            min_samples=2,
            embedding_dimensions=128,
            pca_dimensions=8,
            neighbor_top_k=3,
        )
        cls.projection_config = projection.ProjectionConfig(
            n_neighbors=4,
            random_seed=42,
            rms_displacement_limit=0.45,
            max_displacement_limit=1.25,
        )
        cls.topology = pipeline.build_topology(
            cls.prompts,
            SECTIONS,
            tutorial_routes=cls.routes,
            config=cls.phase_a_config,
        )

    def build(self, prompts=None, **kwargs):
        return projection.build_projection(
            self.topology,
            prompts or self.prompts,
            SECTIONS,
            phase_a_config=self.phase_a_config,
            config=self.projection_config,
            **kwargs,
        )

    def test_projection_has_exact_node_parity_and_required_provenance(self):
        artifact, state = self.build()
        self.assertEqual("umap", artifact["algorithm"])
        self.assertEqual(3, artifact["parameters"]["n_components"])
        self.assertEqual("cosine", artifact["parameters"]["metric"])
        self.assertEqual(42, artifact["parameters"]["random_seed"])
        self.assertEqual(
            [node["prompt_id"] for node in self.topology["nodes"]],
            sorted(artifact["points"], key=pipeline.prompt_key),
        )
        self.assertEqual(self.topology["content_hash_sha256"], state["topology_content_hash_sha256"])
        self.assertEqual("semantic_embedding", state["provenance"]["input"])
        self.assertTrue(state["provenance"]["visualization_only"])
        projection.validate_projection_bundle(
            self.topology,
            artifact,
            state,
            config=self.projection_config,
        )

    def test_repeated_and_shuffled_source_are_byte_identical(self):
        first_projection, first_state = self.build()
        second_projection, second_state = self.build()
        shuffled_projection, shuffled_state = self.build(prompts=list(reversed(self.prompts)))
        self.assertEqual(projection.projection_bytes(first_projection), projection.projection_bytes(second_projection))
        self.assertEqual(projection.projection_bytes(first_projection), projection.projection_bytes(shuffled_projection))
        self.assertEqual(projection.state_bytes(first_state), projection.state_bytes(second_state))
        self.assertEqual(projection.state_bytes(first_state), projection.state_bytes(shuffled_state))

    def test_unchanged_topology_reuses_exact_epoch_and_bytes(self):
        first_projection, first_state = self.build()
        repeated_projection, repeated_state = self.build(
            previous_projection=first_projection,
            previous_state=first_state,
        )
        self.assertEqual(projection.projection_bytes(first_projection), projection.projection_bytes(repeated_projection))
        self.assertEqual(projection.state_bytes(first_state), projection.state_bytes(repeated_state))
        self.assertEqual(first_state["epoch_id"], repeated_state["epoch_id"])

    def test_rigid_anchor_alignment_recovers_previous_frame_without_scaling(self):
        previous = np.asarray([
            [-1.0, 0.0, 0.5],
            [0.0, 1.0, -0.5],
            [1.0, 0.0, 0.25],
            [0.0, -1.0, -0.25],
        ])
        angle = np.deg2rad(37)
        rotation = np.asarray([
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle), np.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ])
        current = previous @ rotation.T + np.asarray([3.0, -2.0, 4.0])
        prompt_ids = ["P1", "P2", "P3", "P4"]
        previous_points = {
            pid: {"x": float(previous[i, 0]), "y": float(previous[i, 1]), "z": float(previous[i, 2])}
            for i, pid in enumerate(prompt_ids)
        }
        aligned, evidence = projection._align_to_previous(
            current,
            prompt_ids,
            previous_points,
            minimum_anchors=3,
        )
        self.assertTrue(np.allclose(aligned, previous, atol=1e-10))
        self.assertEqual("ANCHORED", evidence["mode"])
        self.assertLess(evidence["max_displacement"], 1e-9)

    def test_changed_epoch_fails_closed_when_shared_anchor_displacement_exceeds_limits(self):
        first_projection, first_state = self.build()
        unstable_previous = copy.deepcopy(first_projection)
        unstable_previous["points"]["P1"]["x"] += 5.0
        unstable_state = copy.deepcopy(first_state)
        unstable_state["topology_content_hash_sha256"] = "f" * 64
        unstable_projection_sha = projection._projection_sha256(unstable_previous)
        unstable_state["projection_sha256"] = unstable_projection_sha
        unstable_state["epoch_id"] = projection.EPOCH_PREFIX + unstable_projection_sha[:12].upper()
        unstable_state["content_hash_sha256"] = projection.sha256_payload(
            projection._state_without_hash(unstable_state)
        )
        strict = projection.ProjectionConfig(
            n_neighbors=4,
            random_seed=42,
            rms_displacement_limit=0.01,
            max_displacement_limit=0.02,
        )
        with self.assertRaisesRegex(ValueError, "spatial stability exceeded displacement limits"):
            projection.build_projection(
                self.topology,
                self.prompts,
                SECTIONS,
                phase_a_config=self.phase_a_config,
                config=strict,
                previous_projection=unstable_previous,
                previous_state=unstable_state,
            )

    def test_changed_topology_rejects_tampered_predecessor_before_alignment(self):
        first_projection, first_state = self.build()
        tampered = copy.deepcopy(first_projection)
        tampered["points"]["P1"]["x"] += 0.5
        changed_state = copy.deepcopy(first_state)
        changed_state["topology_content_hash_sha256"] = "f" * 64
        changed_state["content_hash_sha256"] = projection.sha256_payload(
            projection._state_without_hash(changed_state)
        )
        with self.assertRaisesRegex(ValueError, "previous projection state projection hash mismatch"):
            self.build(previous_projection=tampered, previous_state=changed_state)

    def test_projection_generation_cannot_mutate_registry_or_phase_a_topology(self):
        prompt_before = copy.deepcopy(self.prompts)
        topology_before = pipeline.topology_bytes(self.topology)
        self.build()
        self.assertEqual(prompt_before, self.prompts)
        self.assertEqual(topology_before, pipeline.topology_bytes(self.topology))

    def test_projection_point_parity_fails_closed(self):
        artifact, state = self.build()
        broken = copy.deepcopy(artifact)
        broken["points"].pop("P8")
        with self.assertRaisesRegex(ValueError, "projection point parity failure"):
            projection.validate_projection_bundle(
                self.topology,
                broken,
                state,
                config=self.projection_config,
            )


if __name__ == "__main__":
    unittest.main()
