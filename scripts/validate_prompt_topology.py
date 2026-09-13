#!/usr/bin/env python3
"""Fail-closed static contract validator for executable Prompt Topology Phase A+B."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "harness" / "prompt-topology" / "schema.v1.json"
CONFIG = ROOT / "harness" / "prompt-topology" / "config.v1.json"
REFINEMENTS = ROOT / "harness" / "prompt-topology" / "phase-a-refinements.v1.json"
PHASE_B = ROOT / "harness" / "prompt-topology" / "phase-b-projection.v1.json"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-topology-classifier.v1.json"
RUNTIME_FILES = [
    ROOT / "harness" / "prompt-topology" / "EXECUTABLE_PHASE_A.md",
    ROOT / "harness" / "prompt-topology" / "EXECUTABLE_PHASE_B.md",
    ROOT / "scripts" / "prompt-topology" / "topology_core.py",
    ROOT / "scripts" / "prompt-topology" / "topology_graph.py",
    ROOT / "scripts" / "prompt-topology" / "topology_cluster.py",
    ROOT / "scripts" / "prompt-topology" / "pipeline.py",
    ROOT / "scripts" / "prompt-topology" / "run.py",
    ROOT / "scripts" / "prompt-topology" / "validate.py",
    ROOT / "scripts" / "prompt-topology" / "projection.py",
    ROOT / "scripts" / "prompt-topology" / "project.py",
    ROOT / "scripts" / "prompt-topology" / "validate_projection.py",
    ROOT / "tests" / "test_prompt_topology_phase_a.py",
    ROOT / "tests" / "test_prompt_topology_phase_b.py",
    ROOT / "requirements-prompt-topology.txt",
]
EXPECTED_CHANNELS = [
    "SEMANTIC_NEIGHBOR", "WORKFLOW_NEXT", "CLASS_FAMILY",
    "SHARED_SCOPE", "SHARED_EVIDENCE", "TUTORIAL_ROUTE",
]
RESERVED = ["CO_USAGE", "TRANSITION", "SUBSTITUTION", "COMPLEMENT"]


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"[FAIL] {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"[FAIL] expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[FAIL] {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    schema = load(SCHEMA)
    cfg = load(CONFIG)
    refinements = load(REFINEMENTS)
    phase_b = load(PHASE_B)
    contract = load(CONTRACT)

    require(schema.get("schema_version") == "prompt-topology/v1", "base schema version drift")
    require("projection_artifact" in schema.get("$defs", {}), "projection contract was deleted")
    require(schema["$defs"]["projection_artifact"]["properties"]["algorithm"].get("const") == "umap", "projection schema algorithm drift")
    require(cfg.get("schema_version") == "prompt-topology-config/v1", "base config version drift")
    require(cfg["pipeline"]["clustering"]["algorithm"] == "hdbscan", "base clustering contract must remain HDBSCAN")
    projection_cfg = cfg["pipeline"]["projection_3d"]
    require(projection_cfg["visualization_only"], "projection must remain visualization-only")
    require(projection_cfg["algorithm"] == "umap", "projection config must remain UMAP")
    require(projection_cfg["parameters"] == {
        "n_components": 3,
        "n_neighbors": 15,
        "min_dist": 0.15,
        "metric": "cosine",
        "random_seed": 42,
    }, "Phase B UMAP parameters drift")

    require(refinements.get("schema_version") == "prompt-topology-phase-a-refinements/v1", "Phase A refinements version drift")
    supersedes = refinements.get("supersedes", {})
    identity = supersedes.get("config.pipeline.clustering.cluster_id_policy", {})
    require(identity.get("reconcile_min_jaccard") == 0.5, "cluster reconciliation threshold drift")
    require("membership_fingerprint_sha256" in identity, "exact membership fingerprint refinement missing")
    runtime_cluster = supersedes.get("schema.$defs.cluster_record.identity", {})
    required_runtime = set(runtime_cluster.get("required_runtime_fields", []))
    require({"cluster_id", "membership_fingerprint_sha256", "lineage", "representative_prompt_id"} <= required_runtime, "runtime cluster identity refinement incomplete")
    artifact = supersedes.get("phase_a_artifact", {})
    require(artifact.get("path") == "artifacts/prompt-topology/topology.v1.json", "canonical Phase A artifact path drift")
    require(artifact.get("renderer_neutral") is True, "canonical Phase A topology must be renderer-neutral")
    require(refinements["edges"]["phase_a_channels"] == EXPECTED_CHANNELS, "Phase A channel order drift")
    require(refinements["edges"]["reserved_behavior_channels"] == RESERVED, "reserved behavior channel drift")
    require(refinements["opportunities"]["advisory_only"] is True, "opportunity output must remain advisory")
    forbidden_a = refinements["phase_boundary"]["forbidden"]
    require("3D coordinates" in forbidden_a and "live telemetry" in forbidden_a and "prompt renumbering" in forbidden_a, "Phase A forbidden boundary drift")

    require(phase_b.get("schema_version") == "prompt-topology-phase-b-projection/v1", "Phase B contract version drift")
    require(phase_b["phase_a_input"] == "artifacts/prompt-topology/topology.v1.json", "Phase B must consume canonical Phase A topology")
    require(phase_b["projection"]["algorithm"] == "umap", "Phase B projection algorithm drift")
    require(phase_b["projection"]["visualization_only"] is True, "Phase B must remain visualization-only")
    require(phase_b["projection"]["input"] == "semantic_embedding", "Phase B must project semantic vectors")
    require("cluster labels" in phase_b["projection"]["forbidden_inputs"], "cluster labels must never drive projection")
    require(phase_b["canonical_artifacts"]["projection"]["path"] == "artifacts/prompt-topology/projection-3d.json", "Phase B projection path drift")
    require(phase_b["canonical_artifacts"]["state"]["path"] == "artifacts/prompt-topology/projection-state.v1.json", "Phase B state path drift")
    require(phase_b["alignment"]["method"] == "orthogonal-procrustes-rigid-no-scale", "Phase B alignment method drift")
    require(phase_b["alignment"]["minimum_anchors"] >= 3, "Phase B anchor floor too weak")
    require(phase_b["spatial_stability"]["rms_displacement_limit"] > 0, "Phase B RMS limit missing")
    require(phase_b["spatial_stability"]["max_displacement_limit"] >= phase_b["spatial_stability"]["rms_displacement_limit"], "Phase B displacement limits invalid")
    require(phase_b["validation"]["repeat_build_byte_identity"] is True, "Phase B repeat determinism must be required")
    require(phase_b["validation"]["shuffled_source_byte_identity"] is True, "Phase B shuffled-source determinism must be required")
    require("Phase C" in phase_b["phase_boundary"]["next_phase"], "Phase B successor boundary missing")

    require("executable Phase A" in contract.get("lane", "") and "Phase B" in contract.get("lane", ""), "contract does not report executable Phase A+B lane")
    require(contract["authority"].get("phase_a_refinements") == "harness/prompt-topology/phase-a-refinements.v1.json", "contract is not bound to Phase A refinements")
    require(contract["authority"].get("phase_b_projection") == "harness/prompt-topology/phase-b-projection.v1.json", "contract is not bound to Phase B projection")
    require(contract["pipeline_contract"]["phase_a_channels"] == EXPECTED_CHANNELS, "contract channel drift")
    require(contract["pipeline_contract"]["reserved_channels"] == RESERVED, "contract reserved channel drift")
    require(contract["pipeline_contract"]["canonical_artifact"] == "artifacts/prompt-topology/topology.v1.json", "contract artifact path drift")
    require(contract["pipeline_contract"]["projection"]["phase"] == "Phase B executable", "contract still reports projection as future")
    require(contract["pipeline_contract"]["projection"]["visualization_only"] is True, "contract projection must remain visualization-only")
    require("persistent cluster_id" in contract["pipeline_contract"]["cluster_identity"], "contract cluster identity drift")
    require(contract["artifacts"]["phase_b_projection"] == "artifacts/prompt-topology/projection-3d.json", "contract projection artifact drift")
    require(contract["artifacts"]["phase_b_state"] == "artifacts/prompt-topology/projection-state.v1.json", "contract projection state artifact drift")

    missing = [str(path.relative_to(ROOT)) for path in RUNTIME_FILES if not path.is_file()]
    require(not missing, f"runtime owners missing: {missing}")

    summary = (
        "Prompt topology Phase A+B contract: PASS — Phase A semantic topology remains authoritative; "
        "Phase B executes deterministic UMAP(3), exact topology binding, projection epochs, rigid shared-anchor alignment, "
        "displacement limits, spatial-stability validation, and repeat/shuffled-source reconstruction while Phase C viewer work remains separate."
    )
    print(summary if args.summary else json.dumps({"status": "PASS", "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
