#!/usr/bin/env python3
"""Fail-closed static contract validator for executable Prompt Topology Phase A."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "harness" / "prompt-topology" / "schema.v1.json"
CONFIG = ROOT / "harness" / "prompt-topology" / "config.v1.json"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-topology-classifier.v1.json"
RUNTIME_FILES = [
    ROOT / "scripts" / "prompt-topology" / "pipeline.py",
    ROOT / "scripts" / "prompt-topology" / "run.py",
    ROOT / "scripts" / "prompt-topology" / "validate.py",
    ROOT / "tests" / "test_prompt_topology_phase_a.py",
    ROOT / "requirements-prompt-topology.txt",
]
EXPECTED_CHANNELS = [
    "SEMANTIC_NEIGHBOR",
    "WORKFLOW_NEXT",
    "CLASS_FAMILY",
    "SHARED_SCOPE",
    "SHARED_EVIDENCE",
    "TUTORIAL_ROUTE",
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
    contract = load(CONTRACT)

    require(schema.get("schema_version") == "prompt-topology/v1", "schema version drift")
    require(schema.get("artifact_schema_version") == "prompt-topology-artifact/v1", "artifact schema version drift")
    require(schema.get("artifact", {}).get("path") == "artifacts/prompt-topology/topology.v1.json", "canonical artifact path drift")
    cluster = schema["$defs"]["cluster"]
    required_cluster = set(cluster["required"])
    require("membership_fingerprint_sha256" in required_cluster, "cluster fingerprint missing")
    require("lineage" in required_cluster, "cluster lineage missing")
    description = cluster["properties"]["cluster_id"].get("description", "").lower()
    require("persistent" in description and "not recomputed solely from membership" in description, "cluster identity is not persistent-by-contract")

    edges = cfg["pipeline"]["edges"]
    require(edges["phase_a_channels"] == EXPECTED_CHANNELS, "Phase A channel order drift")
    require(edges["reserved_live_behavior_channels"] == RESERVED, "reserved behavior channels drift")
    require(cfg["pipeline"]["clustering"]["algorithm"] == "hdbscan", "clustering must be HDBSCAN")
    require(cfg["pipeline"]["clustering"]["cluster_identity"]["membership_hash_is_not_permanent_identity"] is True, "membership hash cannot be permanent cluster identity")
    require(cfg["artifact"]["canonical_path"] == "artifacts/prompt-topology/topology.v1.json", "config artifact path drift")
    require("3D coordinates" in cfg["phase_boundary"]["forbidden_in_phase_a"], "3D must remain outside Phase A")

    require(contract.get("lane") == "executable Phase A semantic topology", "contract still reports design-only lane")
    require(contract.get("canonical_artifact") == "artifacts/prompt-topology/topology.v1.json", "contract artifact path drift")
    require(contract["pipeline_contract"]["phase_a_channels"] == EXPECTED_CHANNELS, "contract channel drift")
    require(contract["pipeline_contract"]["reserved_channels"] == RESERVED, "contract reserved channel drift")
    require(contract["pipeline_contract"]["renderer_neutral"] is True, "canonical topology must be renderer-neutral")

    missing = [str(path.relative_to(ROOT)) for path in RUNTIME_FILES if not path.is_file()]
    require(not missing, f"runtime owners missing: {missing}")

    summary = (
        "Prompt topology Phase A contract: PASS — persistent cluster identity, separate membership fingerprint, "
        "canonical renderer-neutral artifact, opportunity ownership, Phase A channel boundary, and executable owners are registered."
    )
    print(summary if args.summary else json.dumps({"status": "PASS", "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
