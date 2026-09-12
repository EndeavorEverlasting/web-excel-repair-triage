#!/usr/bin/env python3
"""Fail-closed static contract validator for executable Prompt Topology Phase A."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "harness" / "prompt-topology" / "schema.v1.json"
CONFIG = ROOT / "harness" / "prompt-topology" / "config.v1.json"
REFINEMENTS = ROOT / "harness" / "prompt-topology" / "phase-a-refinements.v1.json"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-topology-classifier.v1.json"
RUNTIME_FILES = [
    ROOT / "harness" / "prompt-topology" / "EXECUTABLE_PHASE_A.md",
    ROOT / "scripts" / "prompt-topology" / "topology_core.py",
    ROOT / "scripts" / "prompt-topology" / "topology_graph.py",
    ROOT / "scripts" / "prompt-topology" / "topology_cluster.py",
    ROOT / "scripts" / "prompt-topology" / "pipeline.py",
    ROOT / "scripts" / "prompt-topology" / "run.py",
    ROOT / "scripts" / "prompt-topology" / "validate.py",
    ROOT / "tests" / "test_prompt_topology_phase_a.py",
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
    contract = load(CONTRACT)

    require(schema.get("schema_version") == "prompt-topology/v1", "base schema version drift")
    require("projection_artifact" in schema.get("$defs", {}), "historical future projection contract was deleted")
    require(schema["$defs"]["projection_artifact"]["properties"]["algorithm"].get("const") == "umap", "future projection contract drift")
    require(cfg.get("schema_version") == "prompt-topology-config/v1", "base config version drift")
    require(cfg["pipeline"]["clustering"]["algorithm"] == "hdbscan", "base clustering contract must remain HDBSCAN")
    require(cfg["pipeline"]["projection_3d"]["visualization_only"], "projection must remain visualization-only")

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
    forbidden = refinements["phase_boundary"]["forbidden"]
    require("3D coordinates" in forbidden and "live telemetry" in forbidden and "prompt renumbering" in forbidden, "Phase A forbidden boundary drift")

    require("executable Phase A" in contract.get("lane", ""), "contract still reports design-only lane")
    require(contract["authority"].get("phase_a_refinements") == "harness/prompt-topology/phase-a-refinements.v1.json", "contract is not bound to Phase A refinements")
    require(contract["pipeline_contract"]["phase_a_channels"] == EXPECTED_CHANNELS, "contract channel drift")
    require(contract["pipeline_contract"]["reserved_channels"] == RESERVED, "contract reserved channel drift")
    require(contract["pipeline_contract"]["canonical_artifact"] == "artifacts/prompt-topology/topology.v1.json", "contract artifact path drift")
    require("persistent cluster_id" in contract["pipeline_contract"]["cluster_identity"], "contract cluster identity drift")

    missing = [str(path.relative_to(ROOT)) for path in RUNTIME_FILES if not path.is_file()]
    require(not missing, f"runtime owners missing: {missing}")

    summary = (
        "Prompt topology Phase A contract: PASS — mature design schema/config preserved; exact executable refinements register "
        "persistent cluster identity, separate membership fingerprint, renderer-neutral topology.v1.json, multi-channel edges, "
        "advisory opportunities, deterministic rebuild proof, and the Phase A boundary."
    )
    print(summary if args.summary else json.dumps({"status": "PASS", "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
